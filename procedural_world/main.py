"""Interactive procedural world explorer (Pygame).

Renders an effectively infinite, biome-rich world by streaming chunks around the
camera. Chunks are generated on demand (with a per-frame budget so panning stays
smooth), cached as 1px-per-tile surfaces, and scaled to the current zoom.

Controls
--------
  WASD / Arrows .... pan
  Mouse drag ....... pan
  Mouse wheel ...... zoom (toward cursor)
  + / - ............ zoom
  M ................ toggle minimap
  H ................ toggle help / HUD
  R ................ new random seed
  [ / ] ............ previous / next seed
  N ................ pause / resume day-night cycle
  , / . ............ scrub time of day
  P ................ save screenshot (png)
  Esc / Q .......... quit
"""

import argparse
import os
import random
import time

import numpy as np
import pygame

from worldgen import WorldGenerator, BIOME_NAMES

CHUNK = 64                 # tiles per chunk edge
GEN_BUDGET_PER_FRAME = 8   # max chunks generated per frame (keeps panning smooth)
MAX_CACHED_CHUNKS = 900    # LRU cap on generated chunks
DAY_LENGTH = 120.0         # seconds for one full day-night cycle

# Day-night lighting: a multiply color sampled across the day. Values < 255
# darken; warm hues at sunrise/sunset, deep blue at night, neutral at noon.
# time_of_day is 0..1 with 0.0 = midnight, 0.5 = noon.
_DAY_KEYS = [
    (0.00, (56, 76, 138)),    # midnight
    (0.22, (70, 92, 150)),    # pre-dawn
    (0.27, (240, 165, 120)),  # sunrise
    (0.33, (255, 226, 206)),  # early morning
    (0.50, (255, 255, 255)),  # noon
    (0.67, (255, 228, 205)),  # afternoon
    (0.73, (246, 165, 115)),  # sunset
    (0.80, (120, 105, 165)),  # dusk
    (0.88, (56, 76, 138)),    # night
    (1.00, (56, 76, 138)),
]


def day_tint(t):
    """Return the (r, g, b) multiply color for a time of day in [0, 1)."""
    t %= 1.0
    keys = _DAY_KEYS
    for i in range(len(keys) - 1):
        t0, c0 = keys[i]
        t1, c1 = keys[i + 1]
        if t0 <= t <= t1:
            f = 0.0 if t1 == t0 else (t - t0) / (t1 - t0)
            return tuple(c0[k] + (c1[k] - c0[k]) * f for k in range(3))
    return (255.0, 255.0, 255.0)


def day_phase(t):
    t %= 1.0
    if t < 0.22 or t >= 0.88:
        return "Night"
    if t < 0.30:
        return "Dawn"
    if t < 0.45:
        return "Morning"
    if t < 0.55:
        return "Noon"
    if t < 0.70:
        return "Afternoon"
    if t < 0.80:
        return "Dusk"
    return "Evening"


def clock_str(t):
    hours = (t % 1.0) * 24.0
    hh = int(hours)
    mm = int((hours - hh) * 60)
    return f"{hh:02d}:{mm:02d}"


class ChunkManager:
    """Generates, caches and scales chunks on demand."""

    def __init__(self, generator, chunk=CHUNK):
        self.gen = generator
        self.chunk = chunk
        self.base = {}      # (cx, cy) -> base Surface (chunk x chunk px)
        self.scaled = {}    # (cx, cy) -> (zoom_px, Surface)
        self.order = []     # MRU list of keys for LRU eviction
        self.budget = 0

    def reset(self, generator):
        self.gen = generator
        self.base.clear()
        self.scaled.clear()
        self.order.clear()

    def begin_frame(self):
        self.budget = GEN_BUDGET_PER_FRAME

    def _touch(self, key):
        # Move key to end (most-recently-used).
        try:
            self.order.remove(key)
        except ValueError:
            pass
        self.order.append(key)

    def _evict(self):
        while len(self.base) > MAX_CACHED_CHUNKS and self.order:
            old = self.order.pop(0)
            self.base.pop(old, None)
            self.scaled.pop(old, None)

    def _make_base(self, key):
        cx, cy = key
        ch = self.gen.generate_chunk(cx, cy, self.chunk)
        # color is (H, W, 3) [y, x]; make_surface wants (W, H, 3) [x, y].
        surf = pygame.surfarray.make_surface(np.transpose(ch.color, (1, 0, 2)))
        self.base[key] = surf
        self._touch(key)
        self._evict()
        return surf

    def get_render(self, cx, cy, zoom_px):
        """Return a chunk surface scaled to zoom_px (chunk edge in pixels).

        Generates the chunk if needed and the per-frame budget allows; otherwise
        returns None so the caller leaves the background showing (it fills in over
        the next frames).
        """
        key = (cx, cy)
        base = self.base.get(key)
        if base is None:
            if self.budget <= 0:
                return None
            self.budget -= 1
            base = self._make_base(key)
        else:
            self._touch(key)

        cached = self.scaled.get(key)
        if cached is not None and cached[0] == zoom_px:
            return cached[1]
        scaled = pygame.transform.scale(base, (zoom_px, zoom_px))
        self.scaled[key] = (zoom_px, scaled)
        return scaled


class Explorer:
    def __init__(self, seed, width, height, chunk=CHUNK):
        pygame.init()
        pygame.display.set_caption("Procedural World Explorer")
        self.sw, self.sh = width, height
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas,monospace", 15)
        self.big = pygame.font.SysFont("consolas,monospace", 17, bold=True)

        self.chunk = chunk
        self.seed = seed
        self.gen = WorldGenerator(seed)
        self.cm = ChunkManager(self.gen, chunk)

        # Camera: world-tile coordinate at the screen centre, plus zoom in px/tile.
        self.cam_x = 0.0
        self.cam_y = 0.0
        self.zoom = 6.0
        self.min_zoom = 1.0
        self.max_zoom = 40.0

        self.show_minimap = True
        self.show_help = False
        self.dragging = False
        self.drag_anchor = (0, 0)

        # Day-night cycle.
        self.time_of_day = 0.5      # start at noon
        self.day_length = DAY_LENGTH
        self.cycle_running = True

        self._mini_surf = None
        self._mini_key = None
        self.bg = tuple(int(c) for c in self.gen.palette[0])  # deep ocean

    # -- coordinate helpers -------------------------------------------------
    def screen_to_world(self, sx, sy):
        wx = self.cam_x + (sx - self.sw / 2) / self.zoom
        wy = self.cam_y + (sy - self.sh / 2) / self.zoom
        return wx, wy

    def world_to_screen(self, wx, wy):
        sx = (wx - self.cam_x) * self.zoom + self.sw / 2
        sy = (wy - self.cam_y) * self.zoom + self.sh / 2
        return sx, sy

    # -- input --------------------------------------------------------------
    def set_seed(self, seed):
        self.seed = int(seed) & 0x7FFFFFFF
        self.gen = WorldGenerator(self.seed)
        self.cm.reset(self.gen)
        self._mini_key = None
        self.bg = tuple(int(c) for c in self.gen.palette[0])

    def zoom_at(self, sx, sy, factor):
        wx, wy = self.screen_to_world(sx, sy)
        self.zoom = float(np.clip(self.zoom * factor, self.min_zoom, self.max_zoom))
        # Keep the world point under the cursor fixed.
        self.cam_x = wx - (sx - self.sw / 2) / self.zoom
        self.cam_y = wy - (sy - self.sh / 2) / self.zoom

    def handle_event(self, e):
        if e.type == pygame.QUIT:
            return False
        if e.type == pygame.VIDEORESIZE:
            self.sw, self.sh = e.w, e.h
            self.screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
            self._mini_key = None
        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_q):
                return False
            elif e.key == pygame.K_m:
                self.show_minimap = not self.show_minimap
            elif e.key == pygame.K_h:
                self.show_help = not self.show_help
            elif e.key == pygame.K_r:
                self.set_seed(random.randint(0, 2**31 - 1))
            elif e.key == pygame.K_RIGHTBRACKET:
                self.set_seed(self.seed + 1)
            elif e.key == pygame.K_LEFTBRACKET:
                self.set_seed(self.seed - 1)
            elif e.key == pygame.K_n:
                self.cycle_running = not self.cycle_running
            elif e.key == pygame.K_COMMA:
                self.time_of_day = (self.time_of_day - 0.02) % 1.0
            elif e.key == pygame.K_PERIOD:
                self.time_of_day = (self.time_of_day + 0.02) % 1.0
            elif e.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                self.zoom_at(self.sw / 2, self.sh / 2, 1.25)
            elif e.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                self.zoom_at(self.sw / 2, self.sh / 2, 0.8)
            elif e.key == pygame.K_p:
                self.save_screenshot()
        elif e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 1:
                self.dragging = True
                self.drag_anchor = e.pos
            elif e.button == 4:
                self.zoom_at(*pygame.mouse.get_pos(), 1.15)
            elif e.button == 5:
                self.zoom_at(*pygame.mouse.get_pos(), 1 / 1.15)
        elif e.type == pygame.MOUSEBUTTONUP:
            if e.button == 1:
                self.dragging = False
        elif e.type == pygame.MOUSEMOTION and self.dragging:
            dx, dy = e.rel
            self.cam_x -= dx / self.zoom
            self.cam_y -= dy / self.zoom
        return True

    def handle_keys_held(self, dt):
        keys = pygame.key.get_pressed()
        speed = 320.0 / self.zoom * dt  # tiles/sec, constant on-screen feel
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            self.cam_y -= speed
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            self.cam_y += speed
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            self.cam_x -= speed
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            self.cam_x += speed

    # -- rendering ----------------------------------------------------------
    def draw_world(self):
        self.screen.fill(self.bg)
        self.cm.begin_frame()
        zoom_px = max(1, int(round(self.chunk * self.zoom)))

        # Visible world-tile bounds.
        wx0, wy0 = self.screen_to_world(0, 0)
        wx1, wy1 = self.screen_to_world(self.sw, self.sh)
        cx0 = int(np.floor(wx0 / self.chunk))
        cy0 = int(np.floor(wy0 / self.chunk))
        cx1 = int(np.floor(wx1 / self.chunk))
        cy1 = int(np.floor(wy1 / self.chunk))

        for cy in range(cy0, cy1 + 1):
            for cx in range(cx0, cx1 + 1):
                surf = self.cm.get_render(cx, cy, zoom_px)
                if surf is None:
                    continue
                sx, sy = self.world_to_screen(cx * self.chunk, cy * self.chunk)
                self.screen.blit(surf, (int(sx), int(sy)))

    def apply_lighting(self):
        """Tint the rendered world by the current time of day (multiply blend)."""
        r, g, b = day_tint(self.time_of_day)
        if r >= 254 and g >= 254 and b >= 254:
            return  # noon: no-op
        overlay = pygame.Surface((self.sw, self.sh))
        overlay.fill((int(r), int(g), int(b)))
        self.screen.blit(overlay, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

    def get_minimap(self):
        size = 200
        # Step small enough that neighbouring samples stay on the same landmass
        # (terrain features are ~240 tiles; far coarser just aliases into noise).
        step = max(4, CHUNK // 4)
        half = size // 2
        cxs = int(round(self.cam_x / step))
        cys = int(round(self.cam_y / step))
        key = (cxs, cys, step, self.seed)
        if key == self._mini_key and self._mini_surf is not None:
            return self._mini_surf, step, size
        x0 = (cxs - half) * step
        y0 = (cys - half) * step
        colors = self.gen.region_colors(x0, y0, size, size, step)
        surf = pygame.surfarray.make_surface(np.transpose(colors, (1, 0, 2)))
        self._mini_surf = surf
        self._mini_key = key
        self._mini_origin = (x0, y0)
        return surf, step, size

    def draw_minimap(self):
        surf, step, size = self.get_minimap()
        margin = 12
        x = self.sw - size - margin
        y = self.sh - size - margin
        self.screen.blit(surf, (x, y))
        pygame.draw.rect(self.screen, (235, 235, 235), (x, y, size, size), 2)
        # Camera marker.
        ox, oy = self._mini_origin
        mx = x + (self.cam_x - ox) / step
        my = y + (self.cam_y - oy) / step
        if x <= mx <= x + size and y <= my <= y + size:
            pygame.draw.circle(self.screen, (255, 60, 60), (int(mx), int(my)), 4)
            pygame.draw.circle(self.screen, (255, 255, 255), (int(mx), int(my)), 4, 1)
        label = self.font.render("Map (M)", True, (240, 240, 240))
        self.screen.blit(label, (x + 4, y - 18))

    def _text_panel(self, lines, x, y):
        pad = 6
        w = max(self.font.size(t)[0] for t in lines) + pad * 2
        h = len(lines) * 18 + pad * 2
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 150))
        self.screen.blit(panel, (x, y))
        for i, t in enumerate(lines):
            self.screen.blit(self.font.render(t, True, (240, 240, 240)),
                             (x + pad, y + pad + i * 18))

    def draw_hud(self, fps):
        mx, my = pygame.mouse.get_pos()
        wx, wy = self.screen_to_world(mx, my)
        b, e, t, m = self.gen.biome_at(int(np.floor(wx)), int(np.floor(wy)))
        paused = "" if self.cycle_running else " (paused)"
        lines = [
            f"seed {self.seed}   fps {fps:4.1f}   zoom {self.zoom:4.1f}px",
            f"pos  ({self.cam_x:8.0f}, {self.cam_y:8.0f})   chunks {len(self.cm.base)}",
            f"time {clock_str(self.time_of_day)} {day_phase(self.time_of_day)}{paused}",
            f"tile ({int(wx)}, {int(wy)})  {BIOME_NAMES[b]}",
            f"     elev {e:.2f}  temp {t:.2f}  moist {m:.2f}",
        ]
        self._text_panel(lines, 8, 8)
        hint = self.font.render("H: help", True, (220, 220, 220))
        self.screen.blit(hint, (8, self.sh - 22))

    def draw_help(self):
        lines = [
            "WASD / Arrows .. pan      Mouse drag .. pan",
            "Wheel / +/- .... zoom     M .......... minimap",
            "R .. random seed   [ ] .. seed -/+",
            "N .. pause day/night   , . .. scrub time",
            "P .. screenshot    H .. toggle help   Esc/Q .. quit",
        ]
        self._text_panel(lines, 8, 140)

    def save_screenshot(self):
        fn = f"world_seed{self.seed}_{int(time.time())}.png"
        pygame.image.save(self.screen, fn)
        print(f"saved {fn}")

    # -- main loop ----------------------------------------------------------
    def run(self, max_frames=None):
        running = True
        frames = 0
        while running:
            dt = self.clock.tick(60) / 1000.0
            for e in pygame.event.get():
                if not self.handle_event(e):
                    running = False
            self.handle_keys_held(dt)
            if self.cycle_running:
                self.time_of_day = (self.time_of_day + dt / self.day_length) % 1.0

            self.draw_world()
            self.apply_lighting()  # world only; minimap + HUD stay readable
            if self.show_minimap:
                self.draw_minimap()
            self.draw_hud(self.clock.get_fps())
            if self.show_help:
                self.draw_help()
            pygame.display.flip()

            frames += 1
            if max_frames is not None and frames >= max_frames:
                running = False
        pygame.quit()


def render_image(seed, out, tiles_w, tiles_h, ox=0, oy=0, chunk=CHUNK, time=None):
    """Headlessly render a full detailed map (no window) to a PNG.

    If ``time`` (0..1) is given, the day-night lighting for that time is baked in.
    """
    g = WorldGenerator(seed)
    cols = -(-tiles_w // chunk)
    rows = -(-tiles_h // chunk)
    img = np.zeros((rows * chunk, cols * chunk, 3), dtype=np.uint8)
    cx0 = ox // chunk
    cy0 = oy // chunk
    for r in range(rows):
        for c in range(cols):
            ch = g.generate_chunk(cx0 + c, cy0 + r, chunk)
            img[r * chunk:(r + 1) * chunk, c * chunk:(c + 1) * chunk] = ch.color
    img = img[:tiles_h, :tiles_w]
    if time is not None:
        tint = np.array(day_tint(time), dtype=np.float32) / 255.0
        img = np.clip(img.astype(np.float32) * tint, 0, 255).astype(np.uint8)
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    pygame.init()
    surf = pygame.surfarray.make_surface(np.transpose(img, (1, 0, 2)))
    pygame.image.save(surf, out)
    pygame.quit()
    print(f"rendered {tiles_w}x{tiles_h} map (seed {seed}) -> {out}")


def selftest():
    """Headless sanity check: deterministic, sensible biome distribution."""
    print("running selftest...")
    g = WorldGenerator(seed=42)
    ch = g.generate_chunk(0, 0, CHUNK)
    assert ch.color.shape == (CHUNK, CHUNK, 3), ch.color.shape
    assert ch.biome.shape == (CHUNK, CHUNK)

    # Determinism: same seed -> identical chunk.
    g2 = WorldGenerator(seed=42)
    ch2 = g2.generate_chunk(0, 0, CHUNK)
    assert np.array_equal(ch.color, ch2.color), "non-deterministic generation"

    # Different seed -> different world.
    g3 = WorldGenerator(seed=43)
    ch3 = g3.generate_chunk(0, 0, CHUNK)
    assert not np.array_equal(ch.color, ch3.color), "seed had no effect"

    # Biome variety across a wider area.
    seen = set()
    for cy in range(-3, 4):
        for cx in range(-3, 4):
            seen.update(np.unique(g.generate_chunk(cx, cy, CHUNK).biome).tolist())
    print(f"  distinct biomes across 7x7 chunks: {len(seen)}")
    for b in sorted(seen):
        print(f"    - {BIOME_NAMES[b]}")
    assert len(seen) >= 5, "world looks too uniform"

    # Speed.
    t0 = time.time()
    n = 40
    for i in range(n):
        g.generate_chunk(i, i * 2, CHUNK)
    dt = time.time() - t0
    print(f"  generated {n} chunks ({CHUNK}x{CHUNK}) in {dt*1000:.0f} ms "
          f"({dt/n*1000:.1f} ms/chunk)")
    print("selftest OK")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Procedural world explorer")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=800)
    ap.add_argument("--chunk", type=int, default=CHUNK)
    ap.add_argument("--selftest", action="store_true",
                    help="run headless sanity checks and exit")
    ap.add_argument("--frames", type=int, default=None,
                    help="run N frames then exit (for headless smoke tests)")
    ap.add_argument("--render", metavar="FILE",
                    help="headlessly render a detailed map to PNG and exit")
    ap.add_argument("--rw", type=int, default=1024, help="render width in tiles")
    ap.add_argument("--rh", type=int, default=640, help="render height in tiles")
    ap.add_argument("--ox", type=int, default=0, help="render origin x (tiles)")
    ap.add_argument("--oy", type=int, default=0, help="render origin y (tiles)")
    ap.add_argument("--time", type=float, default=None,
                    help="bake day-night lighting at this time (0..1) into --render")
    args = ap.parse_args(argv)

    if args.selftest:
        selftest()
        return

    if args.render:
        seed = args.seed if args.seed is not None else 0
        render_image(seed, args.render, args.rw, args.rh, args.ox, args.oy,
                     args.chunk, args.time)
        return

    seed = args.seed if args.seed is not None else random.randint(0, 2**31 - 1)
    app = Explorer(seed, args.width, args.height, args.chunk)
    app.run(max_frames=args.frames)


if __name__ == "__main__":
    main()
