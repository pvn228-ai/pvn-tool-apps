"""The "living world" layer: flora, fauna, weather effects, and ambience.

  * FloraField  - deterministic per-tile scatter (trees, cacti, rocks, flowers)
                  read from a chunk's biome array. Same seed => same flora.
  * Fauna       - roaming creatures that spawn around the player, are biome- and
                  day/night-aware, wander, and flee when you get close.
  * WeatherFX   - rain / snow particles + fog driven by the climate layer.
  * Fireflies   - night-time ambience in grass/forest.

None of this is stored globally for the world; flora is a pure function of
position+seed, and fauna/particles live only near the player.
"""

import math
import random

import pygame

from worldgen import (
    DEEP_OCEAN, OCEAN, SHALLOW, BEACH, TUNDRA, SNOW, TAIGA, SHRUBLAND,
    GRASSLAND, TEMPERATE_FOREST, TEMPERATE_RAINFOREST, SAVANNA, DESERT,
    TROPICAL_FOREST, TROPICAL_RAINFOREST, MOUNTAIN, SNOW_PEAK,
)

WATER = {DEEP_OCEAN, OCEAN, SHALLOW}

# ---------------------------------------------------------------------------
# Flora  (deterministic scatter)
# ---------------------------------------------------------------------------
# biome -> (per-tile density, [(kind, weight), ...])
FLORA = {
    GRASSLAND: (0.10, [("grass", 3), ("flower", 1), ("bush", 0.4)]),
    SHRUBLAND: (0.14, [("bush", 3), ("grass", 1)]),
    SAVANNA: (0.05, [("tree", 1), ("grass", 2)]),
    TEMPERATE_FOREST: (0.30, [("tree", 4), ("bush", 1)]),
    TEMPERATE_RAINFOREST: (0.40, [("tree", 5), ("bush", 1)]),
    TROPICAL_FOREST: (0.34, [("tree", 4), ("bush", 1)]),
    TROPICAL_RAINFOREST: (0.42, [("tree", 5)]),
    TAIGA: (0.30, [("pine", 5)]),
    TUNDRA: (0.07, [("rock", 2), ("deadtree", 1)]),
    SNOW: (0.05, [("pine", 1), ("rock", 1)]),
    DESERT: (0.05, [("cactus", 2), ("rock", 2)]),
    BEACH: (0.02, [("rock", 1)]),
    MOUNTAIN: (0.12, [("rock", 4)]),
}


def _weighted(rng, kinds):
    total = sum(w for _, w in kinds)
    r = rng.random() * total
    for k, w in kinds:
        r -= w
        if r <= 0:
            return k
    return kinds[-1][0]


class FloraField:
    """Deterministic decorative scatter, computed once per chunk and cached."""

    def __init__(self, seed):
        self.seed = seed & 0xFFFFFFFF
        self._cache = {}

    def for_chunk(self, ch):
        key = (ch.cx, ch.cy)
        cached = self._cache.get(key)
        if cached is not None:
            return cached
        feats = []
        size = ch.size
        biome = ch.biome
        rng = random.Random((self.seed ^ (ch.cx * 73856093) ^ (ch.cy * 19349663))
                            & 0xFFFFFFFF)
        for ty in range(size):
            row = biome[ty]
            wy = ch.cy * size + ty
            for tx in range(size):
                spec = FLORA.get(int(row[tx]))
                if not spec:
                    continue
                density, kinds = spec
                if rng.random() < density:
                    kind = _weighted(rng, kinds)
                    fx = ch.cx * size + tx + rng.random()
                    fy = wy + rng.random()
                    scale = 0.7 + rng.random() * 0.6
                    feats.append((fx, fy, kind, scale))
        self._cache[key] = feats
        if len(self._cache) > 1200:          # bound memory
            self._cache.pop(next(iter(self._cache)))
        return feats

    def reset(self):
        self._cache.clear()


def draw_feature(screen, sx, sy, kind, px):
    """Draw one flora item at screen (sx, sy); px ~ on-screen size in pixels."""
    x, y = int(sx), int(sy)
    if kind == "tree":
        h = int(px * 1.6)
        pygame.draw.rect(screen, (90, 64, 40), (x - max(1, px // 6), y, max(2, px // 3), h // 2))
        pygame.draw.circle(screen, (34, 92, 48), (x, y - px // 4), px)
        pygame.draw.circle(screen, (44, 116, 60), (x - px // 4, y - px // 3), int(px * 0.7))
    elif kind == "pine":
        pygame.draw.rect(screen, (84, 58, 36), (x - max(1, px // 7), y, max(2, px // 4), px // 2))
        pygame.draw.polygon(screen, (40, 86, 56),
                            [(x, y - int(px * 1.6)), (x - px, y), (x + px, y)])
        pygame.draw.polygon(screen, (52, 104, 66),
                            [(x, y - int(px * 1.6)), (x - int(px * 0.6), y - px // 2),
                             (x + int(px * 0.6), y - px // 2)])
    elif kind == "bush":
        pygame.draw.circle(screen, (50, 104, 58), (x, y), px)
        pygame.draw.circle(screen, (64, 124, 70), (x - px // 3, y - px // 4), int(px * 0.6))
    elif kind == "cactus":
        g = (66, 132, 78)
        pygame.draw.rect(screen, g, (x - px // 3, y - px, int(px * 0.66), int(px * 1.6)))
        pygame.draw.rect(screen, g, (x - px, y - px // 2, px // 2, px // 3))
        pygame.draw.rect(screen, g, (x + px // 2, y - int(px * 0.7), px // 2, px // 3))
    elif kind == "rock":
        pygame.draw.circle(screen, (122, 120, 118), (x, y), px)
        pygame.draw.circle(screen, (92, 90, 90), (x, y), px, 1)
    elif kind == "flower":
        pygame.draw.line(screen, (60, 120, 60), (x, y), (x, y - px), 1)
        col = [(235, 90, 90), (240, 220, 90), (210, 120, 220), (240, 240, 245)][(x + y) % 4]
        pygame.draw.circle(screen, col, (x, y - px), max(1, px // 2))
    elif kind == "deadtree":
        pygame.draw.line(screen, (120, 110, 96), (x, y), (x, y - int(px * 1.5)), max(1, px // 4))
    elif kind == "grass":
        for o in (-px // 2, 0, px // 2):
            pygame.draw.line(screen, (78, 134, 64), (x + o, y), (x + o, y - px), 1)


# ---------------------------------------------------------------------------
# Fauna  (roaming creatures)
# ---------------------------------------------------------------------------
LAND_GRAZE = {GRASSLAND, SAVANNA, SHRUBLAND, TEMPERATE_FOREST, TAIGA,
              TROPICAL_FOREST, TEMPERATE_RAINFOREST, TROPICAL_RAINFOREST}

# kind -> properties
SPECIES = {
    "deer":   dict(color=(150, 110, 70),  size=0.5, speed=2.4, flee=6,  diurnal=True,
                   biomes=LAND_GRAZE, kind="land"),
    "rabbit": dict(color=(200, 190, 175), size=0.32, speed=3.2, flee=7,  diurnal=True,
                   biomes={GRASSLAND, SHRUBLAND, TEMPERATE_FOREST, SAVANNA}, kind="land"),
    "wolf":   dict(color=(110, 110, 120), size=0.5, speed=3.0, flee=0,  diurnal=False,
                   biomes={TEMPERATE_FOREST, TAIGA, GRASSLAND, TUNDRA}, kind="land"),
    "camel":  dict(color=(196, 168, 110), size=0.6, speed=1.8, flee=4,  diurnal=True,
                   biomes={DESERT}, kind="land"),
    "fish":   dict(color=(120, 200, 230), size=0.3, speed=2.6, flee=5,  diurnal=True,
                   biomes=WATER, kind="water"),
    "bird":   dict(color=(60, 60, 70),    size=0.3, speed=4.5, flee=0,  diurnal=True,
                   biomes=None, kind="air"),
}


class Critter:
    __slots__ = ("x", "y", "h", "timer", "spec", "name")

    def __init__(self, x, y, name, spec):
        self.x, self.y = x, y
        self.h = random.uniform(0, 2 * math.pi)
        self.timer = random.uniform(0.5, 2.5)
        self.spec = spec
        self.name = name


class Fauna:
    def __init__(self, seed, target=34):
        self.target = target
        self.critters = []

    def reset(self):
        self.critters.clear()

    def _active(self, spec, is_day):
        return spec["diurnal"] == is_day

    def update(self, dt, game, time_of_day):
        is_day = 0.25 <= time_of_day < 0.80
        px, py = game.player.x, game.player.y

        # Despawn far / now-inactive creatures.
        kept = []
        for c in self.critters:
            if abs(c.x - px) > 95 or abs(c.y - py) > 95:
                continue
            if not self._active(c.spec, is_day):
                continue
            kept.append(c)
        self.critters = kept

        # Spawn up to target around the player.
        attempts = 0
        while len(self.critters) < self.target and attempts < 24:
            attempts += 1
            ang = random.uniform(0, 2 * math.pi)
            dist = random.uniform(30, 70)
            sx = px + math.cos(ang) * dist
            sy = py + math.sin(ang) * dist
            b = game.biome_id(sx, sy)
            cand = [n for n, s in SPECIES.items()
                    if self._active(s, is_day)
                    and (s["biomes"] is None and b not in WATER and b not in (MOUNTAIN, SNOW_PEAK)
                         or s["biomes"] is not None and b in s["biomes"])]
            if not cand:
                continue
            name = random.choice(cand)
            self.critters.append(Critter(sx, sy, name, SPECIES[name]))

        # Move.
        for c in self.critters:
            s = c.spec
            c.timer -= dt
            if c.timer <= 0:
                c.h = random.uniform(0, 2 * math.pi)
                c.timer = random.uniform(0.6, 3.0)
            speed = s["speed"]
            if s["flee"]:
                d = math.hypot(c.x - px, c.y - py)
                if d < s["flee"]:
                    c.h = math.atan2(c.y - py, c.x - px)
                    speed *= 1.9
            nx = c.x + math.cos(c.h) * speed * dt
            ny = c.y + math.sin(c.h) * speed * dt
            if s["kind"] == "air":
                c.x, c.y = nx, ny
            elif s["kind"] == "water":
                if game.biome_id(nx, ny) in WATER:
                    c.x, c.y = nx, ny
                else:
                    c.h += math.pi * 0.7
            else:
                if game.walkable(nx, ny):
                    c.x, c.y = nx, ny
                else:
                    c.h += math.pi * 0.7

    def draw(self, screen, world_to_screen, zoom):
        for c in self.critters:
            sx, sy = world_to_screen(c.x, c.y)
            r = max(2, int(zoom * c.spec["size"]))
            if c.spec["kind"] == "air":
                # little shadow + body, drawn slightly raised
                pygame.draw.circle(screen, (0, 0, 0, 80),
                                   (int(sx), int(sy + r)), max(1, r // 2))
                pygame.draw.polygon(screen, c.spec["color"], [
                    (int(sx) - r, int(sy) - r), (int(sx), int(sy)),
                    (int(sx) + r, int(sy) - r)])
            else:
                pygame.draw.circle(screen, c.spec["color"], (int(sx), int(sy)), r)
                pygame.draw.circle(screen, (20, 20, 25), (int(sx), int(sy)), r, 1)


# ---------------------------------------------------------------------------
# Weather effects (rain / snow / fog)
# ---------------------------------------------------------------------------
class WeatherFX:
    def __init__(self):
        self.parts = []   # [x, y, vx, vy]
        self.mode = "Clear"

    def reset(self):
        self.parts.clear()

    def update(self, dt, weather, precip, wind, sw, sh):
        self.mode = weather
        if weather in ("Rain", "Storm"):
            target = int(60 + precip * (260 if weather == "Storm" else 160))
        elif weather == "Snow":
            target = int(40 + precip * 160)
        else:
            target = 0

        wx = wind[0]
        while len(self.parts) < target:
            self.parts.append([random.uniform(0, sw), random.uniform(-sh, sh), 0, 0])
        if len(self.parts) > target:
            del self.parts[target:]

        if self.mode == "Snow":
            for p in self.parts:
                p[1] += 70 * dt
                p[0] += (math.sin(p[1] * 0.05) * 12 + wx * 40) * dt
                if p[1] > sh:
                    p[0], p[1] = random.uniform(0, sw), -4
        elif self.mode in ("Rain", "Storm"):
            vy = 720 if self.mode == "Storm" else 560
            for p in self.parts:
                p[1] += vy * dt
                p[0] += wx * 160 * dt
                if p[1] > sh:
                    p[0], p[1] = random.uniform(0, sw), -10

    def draw(self, screen, sw, sh, wind):
        if self.mode == "Snow":
            for p in self.parts:
                pygame.draw.circle(screen, (240, 245, 250), (int(p[0]), int(p[1])), 2)
        elif self.mode in ("Rain", "Storm"):
            wx = wind[0]
            col = (170, 190, 220)
            ln = 12 if self.mode == "Rain" else 16
            for p in self.parts:
                x, y = int(p[0]), int(p[1])
                pygame.draw.line(screen, col, (x, y), (x - int(wx * 6), y + ln), 1)


# ---------------------------------------------------------------------------
# Fireflies (night ambience)
# ---------------------------------------------------------------------------
class Fireflies:
    def __init__(self):
        self.flies = []

    def reset(self):
        self.flies.clear()

    def update(self, dt, active, sw, sh):
        if not active:
            self.flies.clear()
            return
        while len(self.flies) < 28:
            self.flies.append([random.uniform(0, sw), random.uniform(0, sh),
                               random.uniform(0, 2 * math.pi), random.uniform(0, 1)])
        for f in self.flies:
            f[2] += random.uniform(-2, 2) * dt
            f[0] += math.cos(f[2]) * 18 * dt
            f[1] += math.sin(f[2]) * 18 * dt
            f[3] = (f[3] + dt * 1.5) % 1.0
            f[0] %= sw
            f[1] %= sh

    def draw(self, screen):
        for f in self.flies:
            glow = abs(math.sin(f[3] * math.pi))
            c = (int(180 + 60 * glow), int(210 + 40 * glow), int(120 * glow))
            pygame.draw.circle(screen, c, (int(f[0]), int(f[1])), 2)
