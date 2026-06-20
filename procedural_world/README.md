# Procedural World Generator

An interactive, **effectively-infinite** procedural world explorer built with
Pygame + NumPy. Terrain is generated from Perlin noise; biomes use a
Whittaker-style elevation / temperature / moisture model. The world is streamed
in chunks around the camera, so you can pan and zoom across enormous maps without
ever generating the whole thing.

> Generate your own preview image with:
> `python main.py --seed 7 --render preview.png --rw 1536 --rh 900`

## Highlights

- **Infinite world** — every tile is a pure function of `(x, y, seed)`. Nothing is
  stored globally; chunks are generated on demand and cached (LRU), so memory stays
  bounded no matter how far you roam.
- **17 biomes** — deep ocean, ocean, shallows, beach, tundra, snow, taiga,
  shrubland, grassland, temperate forest/rainforest, savanna, desert, tropical
  forest/rainforest, mountain, and snow peak.
- **Realistic terrain** — fractal (fBm) Perlin elevation with **domain warping**
  for natural coastlines, altitude-based temperature lapse, and **hillshade**
  relief lighting.
- **Smooth streaming** — chunks generate within a per-frame budget so panning
  doesn't stutter; missing chunks fill in over the next frames.
- **Deterministic** — the same seed always produces the same world.

## Install & run

```bash
pip install -r requirements.txt
python main.py                 # random seed
python main.py --seed 7        # specific world
```

## Controls

| Key | Action |
|-----|--------|
| `WASD` / Arrows | Pan |
| Mouse drag | Pan |
| Mouse wheel | Zoom toward cursor |
| `+` / `-` | Zoom |
| `M` | Toggle minimap |
| `H` | Toggle help / HUD |
| `R` | New random seed |
| `[` / `]` | Previous / next seed |
| `P` | Save screenshot (PNG) |
| `Esc` / `Q` | Quit |

The HUD shows the seed, FPS, zoom, camera position, cached-chunk count, and the
biome / elevation / temperature / moisture of the tile under the cursor.

## Headless / offline use

```bash
# Sanity checks (determinism, biome variety, speed) — no window:
python main.py --selftest

# Render a detailed map straight to PNG (no window):
python main.py --seed 7 --render map.png --rw 1536 --rh 900 --ox -2000 --oy -1500

# Run N frames and exit (smoke test):
SDL_VIDEODRIVER=dummy python main.py --frames 60
```

## How it works

`worldgen.py` is the engine (no Pygame dependency for the math):

- `PerlinNoise` — vectorized 2D Perlin noise with `fbm()` (fractal Brownian motion).
- `WorldGenerator` — combines independent noise sources into elevation,
  temperature, and moisture fields. Each field is contrast-stretched around a pivot
  so the *full* range of biomes and altitudes is actually reached (raw Perlin
  clusters around the middle and would otherwise never produce deserts or peaks).
- `classify()` — maps the three fields to biome ids, with elevation overrides for
  beaches, mountains, peaks, and cold-highland snow.
- `generate_chunk()` — produces a chunk's biome/field arrays plus a ready-to-blit
  RGB color array (generated with a 1-tile pad so hillshade is seamless at borders).

`main.py` is the renderer:

- `ChunkManager` — generates, caches, and zoom-scales chunks; evicts least-recently
  used chunks past a cap.
- `Explorer` — camera, input, minimap, HUD, and the main loop.

## Tuning

World character is controlled by the `DEFAULTS` dict in `worldgen.py` — sea level,
continent scale, climate scale, contrast, mountain/snow thresholds, hillshade
strength, octave counts, and domain-warp strength. Pass overrides via
`WorldGenerator(seed, params={...})`.
