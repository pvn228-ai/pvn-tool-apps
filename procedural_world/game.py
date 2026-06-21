"""Playable world prototype.

Walk a character around the infinite procedural world, with terrain collision,
a follow-camera, the day-night cycle, and simple resource gathering. Built on the
same streaming chunk renderer as the explorer (main.py).

Controls
--------
  WASD / Arrows .... move
  E / Space ........ interact (gather from the tile or an adjacent feature)
  Mouse wheel ...... zoom
  N ................ pause / resume day-night cycle
  , / . ............ scrub time of day
  M ................ toggle minimap
  H ................ toggle help
  R ................ new world (random seed)
  P ................ screenshot
  Esc / Q .......... quit
"""

import argparse
import math
import os
import random
import time

import numpy as np
import pygame

from worldgen import (
    WorldGenerator, BIOME_NAMES,
    DEEP_OCEAN, OCEAN, SHALLOW, BEACH, TUNDRA, SNOW, TAIGA, SHRUBLAND,
    GRASSLAND, TEMPERATE_FOREST, TEMPERATE_RAINFOREST, SAVANNA, DESERT,
    TROPICAL_FOREST, TROPICAL_RAINFOREST, MOUNTAIN, SNOW_PEAK,
)
from main import ChunkManager, day_tint, day_phase, clock_str, CHUNK, DAY_LENGTH
from climate import Climate
from life import FloraField, Fauna, WeatherFX, Fireflies, draw_feature
from factions import FactionWorld, TIERS

# Tiles you cannot stand on.
BLOCKED = {DEEP_OCEAN, OCEAN, SHALLOW, MOUNTAIN, SNOW_PEAK}

# Movement speed multiplier per biome (rough terrain slows you down).
TERRAIN_SPEED = {
    GRASSLAND: 1.0, SAVANNA: 1.0, SHRUBLAND: 0.95, BEACH: 0.85, DESERT: 0.8,
    TEMPERATE_FOREST: 0.7, TROPICAL_FOREST: 0.7, TAIGA: 0.7,
    TEMPERATE_RAINFOREST: 0.6, TROPICAL_RAINFOREST: 0.6,
    SNOW: 0.6, TUNDRA: 0.65,
}

# What the tile you're standing on yields when gathered.
GATHER_ON = {
    TEMPERATE_FOREST: "wood", TROPICAL_FOREST: "wood", TAIGA: "wood",
    TEMPERATE_RAINFOREST: "wood", TROPICAL_RAINFOREST: "wood",
    GRASSLAND: "fiber", SAVANNA: "fiber", SHRUBLAND: "fiber",
    DESERT: "sand", BEACH: "shell", SNOW: "ice", TUNDRA: "ice",
}

# What adjacent (non-walkable) tiles yield.
GATHER_NEAR = {
    MOUNTAIN: "stone", SNOW_PEAK: "stone",
    DEEP_OCEAN: "fish", OCEAN: "fish", SHALLOW: "fish",
}

RESOURCE_COLOR = {
    "wood": (180, 120, 60), "fiber": (170, 210, 110), "sand": (230, 215, 150),
    "shell": (240, 220, 220), "ice": (200, 235, 245), "stone": (180, 180, 185),
    "fish": (120, 200, 235),
}

BASE_SPEED = 7.5       # tiles / second
GATHER_COOLDOWN = 0.18  # seconds between gathers


class Player:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.fx, self.fy = 0.0, 1.0  # facing (default: down)


class Game:
    def __init__(self, seed, width, height):
        pygame.init()
        pygame.display.set_caption("Procedural World - Prototype")
        self.sw, self.sh = width, height
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("consolas,monospace", 15)
        self.bigfont = pygame.font.SysFont("consolas,monospace", 16, bold=True)

        self.seed = seed
        self.gen = WorldGenerator(seed)
        self.cm = ChunkManager(self.gen, CHUNK)
        self.climate = Climate(self.gen)

        # Living-world layers.
        self.flora = FloraField(seed)
        self.fauna = Fauna(seed)
        self.fx = WeatherFX()
        self.fireflies = Fireflies()
        self.factions = FactionWorld(seed, CHUNK)
        self._terr_cache = {}  # (faction_id, zoom_px) -> translucent Surface
        self._light_surf = None  # reusable full-screen lighting overlay
        self._fog_surf = None    # reusable full-screen fog overlay
        self.cond = None  # cached conditions for the player's tile this frame
        self._biome_cache = {}  # (tx, ty) -> biome id, for tiles outside loaded chunks

        self.zoom = 14.0
        self.min_zoom, self.max_zoom = 6.0, 40.0

        self.time_of_day = 0.35
        self.day = 0
        self.day_length = DAY_LENGTH
        self.cycle_running = True

        self.show_minimap = True
        self.show_help = False
        self.show_factions = False

        self.inventory = {}
        self.floaters = []          # transient "+1 wood" popups
        self._gather_timer = 0.0
        self._mini_surf = None
        self._mini_key = None

        sx, sy = self.find_spawn()
        self.player = Player(sx, sy)
        self.bg = tuple(int(c) for c in self.gen.palette[0])
        self.factions.generate(self.gen, self.player.x, self.player.y)

    # -- world helpers ------------------------------------------------------
    def biome_id(self, x, y):
        tx, ty = int(math.floor(x)), int(math.floor(y))
        # Fast path: read from an already-generated chunk (O(1), no noise).
        ch = self.cm.chunks.get((tx // CHUNK, ty // CHUNK))
        if ch is not None:
            return int(ch.biome[ty % CHUNK, tx % CHUNK])
        # Fallback for tiles outside loaded chunks: memoized noise query.
        key = (tx, ty)
        v = self._biome_cache.get(key)
        if v is None:
            v = self.gen.biome_at(tx, ty)[0]
            if len(self._biome_cache) > 50000:
                self._biome_cache.clear()
            self._biome_cache[key] = v
        return v

    def walkable(self, x, y):
        return self.biome_id(x, y) not in BLOCKED

    def find_spawn(self):
        """Spiral out from the origin to the first walkable land tile."""
        if self.walkable(0.5, 0.5):
            return 0.5, 0.5
        for r in range(1, 4000):
            for dx in range(-r, r + 1):
                for dy in (-r, r):
                    if self.walkable(dx + 0.5, dy + 0.5):
                        return dx + 0.5, dy + 0.5
                for dy in range(-r, r + 1):
                    for dx2 in (-r, r):
                        if self.walkable(dx2 + 0.5, dy + 0.5):
                            return dx2 + 0.5, dy + 0.5
        return 0.5, 0.5

    # -- coordinate helpers (camera follows the player) --------------------
    def world_to_screen(self, wx, wy):
        sx = (wx - self.player.x) * self.zoom + self.sw / 2
        sy = (wy - self.player.y) * self.zoom + self.sh / 2
        return sx, sy

    def screen_to_world(self, sx, sy):
        wx = self.player.x + (sx - self.sw / 2) / self.zoom
        wy = self.player.y + (sy - self.sh / 2) / self.zoom
        return wx, wy

    # -- input --------------------------------------------------------------
    def new_world(self, seed):
        self.seed = int(seed) & 0x7FFFFFFF
        self.gen = WorldGenerator(self.seed)
        self.cm.reset(self.gen)
        self.climate = Climate(self.gen)
        self.flora = FloraField(self.seed)
        self.fauna.reset()
        self.fx.reset()
        self.fireflies.reset()
        self.factions = FactionWorld(self.seed, CHUNK)
        self._terr_cache.clear()
        self._biome_cache.clear()
        self._mini_key = None
        self.bg = tuple(int(c) for c in self.gen.palette[0])
        sx, sy = self.find_spawn()
        self.player = Player(sx, sy)
        self.factions.generate(self.gen, self.player.x, self.player.y)
        self.floaters.clear()

    def handle_event(self, e):
        if e.type == pygame.QUIT:
            return False
        if e.type == pygame.VIDEORESIZE:
            self.sw, self.sh = e.w, e.h
            self.screen = pygame.display.set_mode((e.w, e.h), pygame.RESIZABLE)
            self._mini_key = None
            self._light_surf = None
            self._fog_surf = None
        elif e.type == pygame.KEYDOWN:
            if e.key in (pygame.K_ESCAPE, pygame.K_q):
                return False
            elif e.key in (pygame.K_e, pygame.K_SPACE):
                self.try_gather()
            elif e.key == pygame.K_m:
                self.show_minimap = not self.show_minimap
            elif e.key == pygame.K_h:
                self.show_help = not self.show_help
            elif e.key == pygame.K_f:
                self.show_factions = not self.show_factions
            elif e.key == pygame.K_n:
                self.cycle_running = not self.cycle_running
            elif e.key == pygame.K_COMMA:
                self.time_of_day = (self.time_of_day - 0.02) % 1.0
            elif e.key == pygame.K_PERIOD:
                self.time_of_day = (self.time_of_day + 0.02) % 1.0
            elif e.key == pygame.K_r:
                self.new_world(random.randint(0, 2**31 - 1))
            elif e.key == pygame.K_p:
                self.save_screenshot()
        elif e.type == pygame.MOUSEBUTTONDOWN:
            if e.button == 4:
                self.zoom = min(self.max_zoom, self.zoom * 1.15)
            elif e.button == 5:
                self.zoom = max(self.min_zoom, self.zoom / 1.15)
        return True

    def update(self, dt):
        if self.cycle_running:
            prev = self.time_of_day
            self.time_of_day = (prev + dt / self.day_length) % 1.0
            if self.time_of_day < prev:
                self.day += 1
        self._gather_timer = max(0.0, self._gather_timer - dt)

        keys = pygame.key.get_pressed()
        dx = (keys[pygame.K_d] or keys[pygame.K_RIGHT]) - (keys[pygame.K_a] or keys[pygame.K_LEFT])
        dy = (keys[pygame.K_s] or keys[pygame.K_DOWN]) - (keys[pygame.K_w] or keys[pygame.K_UP])
        if dx or dy:
            mag = math.hypot(dx, dy)
            dirx, diry = dx / mag, dy / mag
            self.player.fx, self.player.fy = dirx, diry
            biome = self.biome_id(self.player.x, self.player.y)
            speed = BASE_SPEED * TERRAIN_SPEED.get(biome, 1.0) * dt
            self._move(dirx * speed, diry * speed)

        # If continuously held, gather on a repeating cooldown.
        if (keys[pygame.K_e] or keys[pygame.K_SPACE]) and self._gather_timer == 0.0:
            self.try_gather()

        for f in self.floaters:
            f["life"] -= dt
        self.floaters = [f for f in self.floaters if f["life"] > 0]

        # Living world.
        self.cond = self.climate.conditions_at(
            self.player.x, self.player.y, self.time_of_day, self.day)
        self.fauna.update(dt, self, self.time_of_day)
        self.fx.update(dt, self.cond["weather"], self.cond["precip"],
                       self.cond["wind"], self.sw, self.sh)
        night = self.time_of_day < 0.22 or self.time_of_day >= 0.88
        firefly_biome = self.biome_id(self.player.x, self.player.y) in (
            GRASSLAND, SHRUBLAND, SAVANNA, TEMPERATE_FOREST, TROPICAL_FOREST)
        self.fireflies.update(dt, night and firefly_biome, self.sw, self.sh)

        # Faction economies advance in game-days.
        self.factions.update(dt / self.day_length)

    def _move(self, dx, dy):
        # Axis-separated so the player slides along walls instead of sticking.
        if self.walkable(self.player.x + dx, self.player.y):
            self.player.x += dx
        if self.walkable(self.player.x, self.player.y + dy):
            self.player.y += dy

    # -- interaction --------------------------------------------------------
    def gather_target(self):
        """Return (resource, world_x, world_y) the player can gather, or None."""
        px, py = self.player.x, self.player.y
        here = self.biome_id(px, py)
        if here in GATHER_ON:
            return GATHER_ON[here], math.floor(px), math.floor(py)
        # Otherwise look at the faced tile, then the 4-neighbours, for a feature.
        fx = int(math.floor(px + self.player.fx))
        fy = int(math.floor(py + self.player.fy))
        cells = [(fx, fy)] + [(int(px) + a, int(py) + b)
                              for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))]
        for cx, cy in cells:
            b = self.biome_id(cx + 0.5, cy + 0.5)
            if b in GATHER_NEAR:
                return GATHER_NEAR[b], cx, cy
        return None

    def try_gather(self):
        if self._gather_timer > 0.0:
            return
        tgt = self.gather_target()
        if not tgt:
            return
        res, tx, ty = tgt
        self.inventory[res] = self.inventory.get(res, 0) + 1
        self.floaters.append({
            "x": tx + 0.5, "y": ty + 0.5, "text": f"+1 {res}",
            "color": RESOURCE_COLOR.get(res, (255, 255, 255)), "life": 1.0,
        })
        self._gather_timer = GATHER_COOLDOWN

    # -- rendering ----------------------------------------------------------
    def draw_world(self):
        self.screen.fill(self.bg)
        self.cm.begin_frame()
        zoom_px = max(1, int(round(CHUNK * self.zoom)))
        wx0, wy0 = self.screen_to_world(0, 0)
        wx1, wy1 = self.screen_to_world(self.sw, self.sh)
        cx0, cy0 = int(np.floor(wx0 / CHUNK)), int(np.floor(wy0 / CHUNK))
        cx1, cy1 = int(np.floor(wx1 / CHUNK)), int(np.floor(wy1 / CHUNK))
        for cy in range(cy0, cy1 + 1):
            for cx in range(cx0, cx1 + 1):
                surf = self.cm.get_render(cx, cy, zoom_px)
                if surf is None:
                    continue
                sx, sy = self.world_to_screen(cx * CHUNK, cy * CHUNK)
                self.screen.blit(surf, (int(sx), int(sy)))

    def draw_flora(self):
        if self.zoom < 8:   # too far out to be worth drawing
            return
        drawn = 0
        wx0, wy0 = self.screen_to_world(-20, -20)
        wx1, wy1 = self.screen_to_world(self.sw + 20, self.sh + 20)
        cx0, cy0 = int(wx0 // CHUNK), int(wy0 // CHUNK)
        cx1, cy1 = int(wx1 // CHUNK), int(wy1 // CHUNK)
        for cy in range(cy0, cy1 + 1):
            for cx in range(cx0, cx1 + 1):
                ch = self.cm.chunks.get((cx, cy))
                if ch is None:
                    continue
                for fx, fy, kind, scale in self.flora.for_chunk(ch):
                    if fx < wx0 or fx > wx1 or fy < wy0 or fy > wy1:
                        continue
                    sx, sy = self.world_to_screen(fx, fy)
                    draw_feature(self.screen, sx, sy, kind,
                                 max(2, int(self.zoom * 0.5 * scale)))
                    drawn += 1
                    if drawn >= 1600:
                        return

    def _territory_surf(self, fid, zoom_px):
        key = (fid, zoom_px)
        s = self._terr_cache.get(key)
        if s is None:
            s = pygame.Surface((zoom_px, zoom_px), pygame.SRCALPHA)
            col = self.factions.factions[fid].color
            s.fill((col[0], col[1], col[2], 55))
            self._terr_cache[key] = s
        return s

    def draw_territory(self):
        claims = self.factions.claims
        if not claims:
            return
        zoom_px = max(1, int(round(CHUNK * self.zoom)))
        wx0, wy0 = self.screen_to_world(0, 0)
        wx1, wy1 = self.screen_to_world(self.sw, self.sh)
        cx0, cy0 = int(wx0 // CHUNK), int(wy0 // CHUNK)
        cx1, cy1 = int(wx1 // CHUNK), int(wy1 // CHUNK)
        for cy in range(cy0, cy1 + 1):
            for cx in range(cx0, cx1 + 1):
                fid = claims.get((cx, cy))
                if fid is None:
                    continue
                sx, sy = self.world_to_screen(cx * CHUNK, cy * CHUNK)
                self.screen.blit(self._territory_surf(fid, zoom_px), (int(sx), int(sy)))

    def draw_settlements(self):
        for s in self.factions.settlements:
            sx, sy = self.world_to_screen(s.x, s.y)
            if sx < -20 or sx > self.sw + 20 or sy < -20 or sy > self.sh + 20:
                continue
            r = TIERS[s.tier]["marker"]
            col = s.faction.color
            ix, iy = int(sx), int(sy)
            if s.tier == 2:        # city: square
                pygame.draw.rect(self.screen, col, (ix - r, iy - r, r * 2, r * 2))
                pygame.draw.rect(self.screen, (245, 245, 245), (ix - r, iy - r, r * 2, r * 2), 2)
            elif s.tier == 1:      # town: diamond
                pts = [(ix, iy - r), (ix + r, iy), (ix, iy + r), (ix - r, iy)]
                pygame.draw.polygon(self.screen, col, pts)
                pygame.draw.polygon(self.screen, (245, 245, 245), pts, 2)
            else:                  # outpost: circle
                pygame.draw.circle(self.screen, col, (ix, iy), r)
                pygame.draw.circle(self.screen, (245, 245, 245), (ix, iy), r, 1)
            if self.zoom >= 12:
                label = self.font.render(s.name, True, (245, 245, 245))
                label.set_alpha(220)
                self.screen.blit(label, (ix - label.get_width() // 2, iy - r - 18))

    def draw_armies(self):
        for a in self.factions.armies:
            sx, sy = self.world_to_screen(a.x, a.y)
            if sx < -20 or sx > self.sw + 20 or sy < -20 or sy > self.sh + 20:
                continue
            ix, iy = int(sx), int(sy)
            col = a.faction.color
            r = 6
            # Army token: a pennant (down-pointing triangle) to distinguish from towns.
            pts = [(ix - r, iy - r), (ix + r, iy - r), (ix, iy + r)]
            pygame.draw.polygon(self.screen, col, pts)
            pygame.draw.polygon(self.screen, (20, 20, 25), pts, 1)
            if self.zoom >= 10:
                lbl = self.font.render(str(a.strength), True, (250, 250, 250))
                lbl.set_alpha(230)
                self.screen.blit(lbl, (ix - lbl.get_width() // 2, iy - r - 16))

    def draw_factions_panel(self):
        fw = self.factions
        if not fw.factions:
            return
        rows = []
        for f in fw.factions:
            pop, gold, sol = f.totals()
            d = fw.directors[f.id]
            prof, hostile = d.status()
            na = sum(1 for a in fw.armies if a.faction is f)
            host = ", ".join(fw.factions[o].name.split()[0]
                             for o in hostile if o < len(fw.factions)) or "-"
            rows.append((f.color,
                         [f"{f.name}  [{prof}]",
                          f"  towns {len(f.settlements)}  pop {pop}  gold {gold}",
                          f"  armies {na}   hostile: {host}"]))
        pad = 6
        lines = ["Factions (F)"] + [t for _, r in rows for t in r]
        w = max(self.font.size(t)[0] for t in lines) + pad * 2
        h = len(lines) * 18 + pad * 2
        x = self.sw // 2 - w // 2
        panel = pygame.Surface((w, h), pygame.SRCALPHA)
        panel.fill((0, 0, 0, 165))
        self.screen.blit(panel, (x, 8))
        self.screen.blit(self.font.render("Factions (F)", True, (240, 240, 240)),
                         (x + pad, 8 + pad))
        y = 8 + pad + 18
        for col, r in rows:
            self.screen.blit(self.font.render(r[0], True, col), (x + pad, y))
            self.screen.blit(self.font.render(r[1], True, (225, 225, 225)), (x + pad, y + 18))
            self.screen.blit(self.font.render(r[2], True, (225, 225, 225)), (x + pad, y + 36))
            y += 54

    def apply_lighting(self):
        r, g, b = day_tint(self.time_of_day)
        if r >= 254 and g >= 254 and b >= 254:
            return
        if self._light_surf is None:
            self._light_surf = pygame.Surface((self.sw, self.sh))
        self._light_surf.fill((int(r), int(g), int(b)))
        self.screen.blit(self._light_surf, (0, 0), special_flags=pygame.BLEND_RGB_MULT)

    def draw_player(self):
        cx, cy = self.sw // 2, self.sh // 2  # player is always centred
        rad = int(max(6, min(20, self.zoom * 0.55)))
        # shadow
        shadow = pygame.Surface((rad * 2, rad), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 90), shadow.get_rect())
        self.screen.blit(shadow, (cx - rad, cy + rad // 2))
        # body
        pygame.draw.circle(self.screen, (245, 245, 250), (cx, cy), rad)
        pygame.draw.circle(self.screen, (30, 30, 40), (cx, cy), rad, 2)
        # facing indicator (eyes)
        ex = cx + int(self.player.fx * rad * 0.45)
        ey = cy + int(self.player.fy * rad * 0.45)
        pygame.draw.circle(self.screen, (40, 60, 120), (ex, ey), max(2, rad // 4))

    def draw_floaters(self):
        for f in self.floaters:
            sx, sy = self.world_to_screen(f["x"], f["y"])
            sy -= (1.0 - f["life"]) * 26
            txt = self.bigfont.render(f["text"], True, f["color"])
            txt.set_alpha(int(255 * min(1.0, f["life"] * 1.5)))
            self.screen.blit(txt, (sx - txt.get_width() / 2, sy - 30))

    def get_minimap(self):
        size = 144
        # Step small enough that neighbouring samples stay on the same landmass
        # (terrain features are ~240 tiles; far coarser just aliases into noise).
        step = max(4, CHUNK // 4)
        # Recomputing the minimap evaluates size*size noise points, so only do it
        # every several steps of travel (quantise the centre) to keep the
        # occasional recompute rare.
        quant = step * 6
        cxs = int(round(self.player.x / quant)) * 6
        cys = int(round(self.player.y / quant)) * 6
        half = size // 2
        key = (cxs, cys, step, self.seed)
        if key == self._mini_key and self._mini_surf is not None:
            return self._mini_surf, step, size
        x0, y0 = (cxs - half) * step, (cys - half) * step
        colors = self.gen.region_colors(x0, y0, size, size, step)
        self._mini_surf = pygame.surfarray.make_surface(np.transpose(colors, (1, 0, 2)))
        self._mini_key = key
        self._mini_origin = (x0, y0)
        return self._mini_surf, step, size

    def draw_minimap(self):
        surf, step, size = self.get_minimap()
        x, y = self.sw - size - 12, self.sh - size - 12
        self.screen.blit(surf, (x, y))
        pygame.draw.rect(self.screen, (235, 235, 235), (x, y, size, size), 2)
        ox, oy = self._mini_origin
        mx = x + (self.player.x - ox) / step
        my = y + (self.player.y - oy) / step
        if x <= mx <= x + size and y <= my <= y + size:
            pygame.draw.circle(self.screen, (255, 60, 60), (int(mx), int(my)), 4)
            pygame.draw.circle(self.screen, (255, 255, 255), (int(mx), int(my)), 4, 1)

    def _panel(self, lines, x, y):
        pad = 6
        w = max(self.font.size(t)[0] for t in lines) + pad * 2
        h = len(lines) * 18 + pad * 2
        p = pygame.Surface((w, h), pygame.SRCALPHA)
        p.fill((0, 0, 0, 150))
        self.screen.blit(p, (x, y))
        for i, t in enumerate(lines):
            self.screen.blit(self.font.render(t, True, (240, 240, 240)),
                             (x + pad, y + pad + i * 18))

    def draw_hud(self, fps):
        cond = self.cond or self.climate.conditions_at(
            self.player.x, self.player.y, self.time_of_day, self.day)
        paused = "" if self.cycle_running else " (paused)"
        lines = [
            f"seed {self.seed}   fps {fps:4.1f}   zoom {self.zoom:4.1f}px",
            f"pos ({self.player.x:7.1f}, {self.player.y:7.1f})  {cond['biome_name']}",
            f"day {self.day}  {clock_str(self.time_of_day)} "
            f"{day_phase(self.time_of_day)}{paused}",
            f"{cond['temp_c']:+.0f}°C  {cond['weather']}  "
            f"wind {cond['wind_dir']}  precip {int(cond['precip'] * 100)}%",
            f"creatures nearby: {len(self.fauna.critters)}",
        ]
        self._panel(lines, 8, 8)

        if self.inventory:
            inv = ["Inventory:"] + [f"  {k}: {v}" for k, v in sorted(self.inventory.items())]
            self._panel(inv, 8, 8 + 5 * 18 + 14)

        # Settlement info when standing near one.
        near = self.factions.nearest_settlement(self.player.x, self.player.y, 9.0)
        if near:
            st = near.stock
            info = [
                f"{near.name}  ({near.kind})",
                f"faction: {near.faction.name}",
                f"pop {int(near.population)}   soldiers {int(near.soldiers)}",
                f"wealth {int(near.wealth)}g",
                f"food {int(st['food'])}  wood {int(st['wood'])}  stone {int(st['stone'])}",
            ]
            self._panel(info, self.sw - 8 - max(self.font.size(t)[0] for t in info) - 12, 8)

        # Army info when standing near a marching stack.
        army = self.factions.nearest_army(self.player.x, self.player.y, 7.0)
        if army:
            ainfo = [
                f"Army of {army.leader}",
                f"faction: {army.faction.name}",
                f"strength: {army.strength} infantry",
            ]
            self._panel(ainfo, self.sw - 8 - max(self.font.size(t)[0] for t in ainfo) - 12,
                        8 + 6 * 18)

        tgt = self.gather_target()
        if tgt:
            prompt = self.bigfont.render(f"[E] gather {tgt[0]}", True, (255, 255, 180))
            self.screen.blit(prompt, (self.sw / 2 - prompt.get_width() / 2, self.sh / 2 + 28))

        hint = self.font.render("H: help", True, (220, 220, 220))
        self.screen.blit(hint, (8, self.sh - 22))

    def draw_help(self):
        lines = [
            "WASD / Arrows .. move",
            "E / Space ...... gather    Wheel .. zoom",
            "N .. pause day/night   , . .. scrub time",
            "M .. minimap   F .. factions   R .. new world",
            "P .. screenshot   H .. toggle help   Esc/Q .. quit",
        ]
        self._panel(lines, 8, 150)

    def save_screenshot(self):
        fn = f"play_seed{self.seed}_{int(time.time())}.png"
        pygame.image.save(self.screen, fn)
        print(f"saved {fn}")

    def draw_fog(self):
        cond = self.cond
        if not cond:
            return
        vis = cond["visibility"]
        if vis >= 0.85:
            return
        if self._fog_surf is None:
            self._fog_surf = pygame.Surface((self.sw, self.sh), pygame.SRCALPHA)
        shade = 210 if cond["weather"] == "Snow" else 170
        self._fog_surf.fill((shade, shade, shade, int((0.85 - vis) * 150)))
        self.screen.blit(self._fog_surf, (0, 0))

    def render(self, fps=0.0):
        self.draw_world()
        self.apply_lighting()
        self.draw_territory()      # faction tint over terrain
        self.draw_flora()          # scatter under entities
        self.draw_floaters()
        self.fauna.draw(self.screen, self.world_to_screen, self.zoom)
        self.draw_settlements()
        self.draw_armies()
        self.draw_player()
        self.fireflies.draw(self.screen)
        self.draw_fog()            # weather haze over the world
        wind = self.cond["wind"] if self.cond else (0.0, 0.0)
        self.fx.draw(self.screen, self.sw, self.sh, wind)
        if self.show_minimap:
            self.draw_minimap()
        self.draw_hud(fps)
        if self.show_factions:
            self.draw_factions_panel()
        if self.show_help:
            self.draw_help()

    def run(self, max_frames=None):
        running = True
        frames = 0
        while running:
            dt = self.clock.tick(60) / 1000.0
            for e in pygame.event.get():
                if not self.handle_event(e):
                    running = False
            self.update(dt)
            self.render(self.clock.get_fps())
            pygame.display.flip()
            frames += 1
            if max_frames is not None and frames >= max_frames:
                running = False
        pygame.quit()


def selftest():
    print("running game selftest...")
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    g = Game(seed=7, width=800, height=600)

    assert g.walkable(g.player.x, g.player.y), "spawned on a blocked tile"
    print(f"  spawn ({g.player.x:.1f}, {g.player.y:.1f}) "
          f"{BIOME_NAMES[g.biome_id(g.player.x, g.player.y)]}")

    # Collision: find an adjacent blocked tile and confirm we can't enter it.
    blocked_dir = None
    for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if not g.walkable(g.player.x + ddx, g.player.y + ddy):
            blocked_dir = (ddx, ddy)
            break
    if blocked_dir:
        bx, by = g.player.x, g.player.y
        g._move(blocked_dir[0] * 0.9, blocked_dir[1] * 0.9)
        assert (g.player.x, g.player.y) == (bx, by), "walked into a blocked tile"
        print(f"  collision OK (blocked {blocked_dir})")
    else:
        print("  (no blocked neighbour to test collision here)")

    # Movement into open space works.
    before = (g.player.x, g.player.y)
    for ddx, ddy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        if g.walkable(g.player.x + ddx * 0.5, g.player.y + ddy * 0.5):
            g._move(ddx * 0.5, ddy * 0.5)
            break
    assert (g.player.x, g.player.y) != before, "could not move into open space"
    print("  movement OK")

    # Gathering yields a resource.
    g._gather_timer = 0.0
    g.try_gather()
    if g.inventory:
        print(f"  gather OK -> {g.inventory}")

    # Render a few frames headless.
    for _ in range(5):
        g.update(1 / 60)
        g.render(60.0)
    pygame.quit()
    print("game selftest OK")


def render_demo(seed, out, width=1024, height=640, time_of_day=0.4):
    """Render a single framed scene with the player, headless, to PNG."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    g = Game(seed=seed, width=width, height=height)
    g.time_of_day = time_of_day
    g.inventory = {"wood": 3, "stone": 1}
    # Warm up chunk generation, then let the living world populate.
    for _ in range(40):
        g.cm.begin_frame()
        g.draw_world()
    for _ in range(60):
        g.update(1 / 30)
    g.render(60.0)
    pygame.image.save(g.screen, out)
    pygame.quit()
    print(f"rendered player demo (seed {seed}) -> {out}")


def main(argv=None):
    ap = argparse.ArgumentParser(description="Playable procedural world prototype")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--width", type=int, default=1280)
    ap.add_argument("--height", type=int, default=800)
    ap.add_argument("--selftest", action="store_true")
    ap.add_argument("--frames", type=int, default=None)
    ap.add_argument("--demo", metavar="FILE", help="render one player frame to PNG")
    ap.add_argument("--time", type=float, default=0.4)
    args = ap.parse_args(argv)

    if args.selftest:
        selftest()
        return
    if args.demo:
        render_demo(args.seed if args.seed is not None else 7, args.demo,
                    args.width, args.height, args.time)
        return

    seed = args.seed if args.seed is not None else random.randint(0, 2**31 - 1)
    Game(seed, args.width, args.height).run(max_frames=args.frames)


if __name__ == "__main__":
    main()
