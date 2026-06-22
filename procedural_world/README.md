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
- **Day-night cycle** — time-of-day lighting (warm sunrise/sunset, deep blue
  night, neutral noon) that cycles automatically; pausable and scrubbable.
- **Climate & weather data layer** — per-tile temperature/moisture, plus dynamic
  wind and drifting rain/snow fronts (see `climate.py`).
- **Living world** — flora, roaming wildlife, weather effects and night fireflies
  in the play mode (see `life.py`).
- **Save / load** — `F5` saves the realm (seed + player, factions, settlements,
  armies, camps and AI state) to `world_save.json`; `F9` restores it.
- **Deterministic terrain** — the same seed always produces the same terrain,
  biomes, flora and settlement placement. (Dynamic state — wildlife, armies and
  evolving weather — runs in real time and is not seed-reproducible.)

## Install & run

```bash
pip install -r requirements.txt
python main.py                 # explore: free-fly camera over the world
python main.py --seed 7        # specific world
python game.py                 # play: walk a character around the world
```

## Play prototype (`game.py`)

A controllable character in a **living world**: terrain collision, follow-camera,
day-night cycle, resource gathering, **survival & combat** (health, fight wildlife
and hostile camps with `Space`, take damage from predators/raiders, die & respawn,
loot fallen creatures), and an **economy** (sell goods at towns for gold, build
**reputation**, take **bounties** to clear camps, and **swear allegiance** to a
faction), and you can grow from a lone adventurer into a **commander** —
**recruit a warband** at allied towns (troops that follow you and fight
stack-vs-stack against camps and enemy armies), and ultimately **found your own
realm** (`K`) by storming a settlement — your faction then holds territory on the
map, grows, and wars like any other. Plus a life layer —

- **Flora** — deterministic scatter of trees, pines, cacti, rocks, bushes, grass
  and flowers, placed by biome (forests are dense, deserts get cacti, etc.).
- **Wildlife** — deer, rabbits, camels, fish, birds and (at night) wolves roam
  around you. They're biome- and day/night-aware, wander, and flee when you
  approach. Population streams in/out around the player.
- **Weather you can feel** — rain and snow particles, wind-blown, with fog when
  visibility drops, all driven by the climate layer.
- **Ambience** — fireflies come out at night in grassland and forest.
- **AI factions & settlements** — outposts, towns and cities owned by rival
  factions, each tracking its own **population, wealth, stockpiles and soldiers**.
  They grow over time and upgrade tiers; their **territory is shown as a light
  colored tint** over claimed chunks, and standing near one shows its stats.
- **AI directors** — each faction has a strategic "brain" with a personality
  (Expansionist / Warmonger / Merchant / Defender) that sets **stances toward
  rivals** at their borders, raises and **orders armies** (mass at hostile
  frontiers vs. defend), and **expands by founding new outposts** so territory
  grows over time. Press **F** for a faction overview. The system (`factions.py`)
  supports any number of factions.
- **War & conquest** — hostile armies fight **stack-vs-stack** (no per-soldier
  units) with **troop composition** (infantry > cavalry > archers > infantry, and
  armies are flavored by where they're raised — open land favors cavalry, woods
  favor archers). They **siege and capture enemy settlements** (then garrison
  them), **flip territory** when a town changes hands, can **eliminate** rival
  factions, and a surviving faction is announced as **dominating the realm**.
  A bottom-left **event log** narrates battles, captures and eliminations, and the
  **minimap is tinted by faction territory**.
- **Neutral hostile camps** — bandit camps, raider outposts and beast lairs
  occupy patches of wilderness (shown with a dark-red hostile tint), **raid
  nearby settlements**, and grow stronger until a faction dispatches an army to
  **clear** them. Hostile to everyone.

| Key | Action |
|-----|--------|
| `WASD` / Arrows | Move (camera follows) |
| `E` | Gather from the tile or an adjacent feature |
| `Space` | Attack (creatures, or chip a hostile camp) |
| `T` / `B` / `G` | At a town: sell goods / buy a heal / swear allegiance |
| `C` | At an allied town: recruit troops into your warband |
| `K` | Claim a settlement with your warband (found / grow your own realm) |
| `F5` / `F9` | Save / load the game |
| Mouse wheel | Zoom |
| `N` | Pause / resume day-night cycle |
| `,` / `.` | Scrub time of day |
| `M` | Toggle minimap |
| `R` | New world |
| `H` | Toggle help |
| `P` | Screenshot |
| `Esc` / `Q` | Quit |

- You can't walk into water, mountains, or peaks; rough terrain (forest, snow)
  slows you down.
- Gathering yields biome-appropriate resources — wood (forests), fiber
  (grass/savanna), sand (desert), shells (beach), ice (snow/tundra), stone (next
  to mountains), and fish (next to water) — tracked in an inventory.

## Explore mode controls (`main.py`)

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
| `N` | Pause / resume day-night cycle |
| `,` / `.` | Scrub time of day |
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

# Bake day-night lighting into a render (--time 0..1; 0.27 sunrise, 0.5 noon, 0.73 sunset):
python main.py --seed 7 --render sunset.png --time 0.73

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
