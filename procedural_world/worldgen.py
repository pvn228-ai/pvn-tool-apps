"""Procedural world generation: Perlin noise terrain + Whittaker-style biomes.

The world is an infinite function of (x, y, seed). Nothing is stored globally;
any tile or chunk can be generated on demand, which is what lets the renderer
stream effectively unlimited maps.

All field math is vectorized with numpy so a whole chunk is generated in one shot.
"""

import numpy as np

# ---------------------------------------------------------------------------
# Biomes
# ---------------------------------------------------------------------------
DEEP_OCEAN = 0
OCEAN = 1
SHALLOW = 2
BEACH = 3
TUNDRA = 4
SNOW = 5
TAIGA = 6
SHRUBLAND = 7
GRASSLAND = 8
TEMPERATE_FOREST = 9
TEMPERATE_RAINFOREST = 10
SAVANNA = 11
DESERT = 12
TROPICAL_FOREST = 13
TROPICAL_RAINFOREST = 14
MOUNTAIN = 15
SNOW_PEAK = 16

BIOME_NAMES = [
    "Deep Ocean", "Ocean", "Shallows", "Beach", "Tundra", "Snow", "Taiga",
    "Shrubland", "Grassland", "Temperate Forest", "Temperate Rainforest",
    "Savanna", "Desert", "Tropical Forest", "Tropical Rainforest",
    "Mountain", "Snow Peak",
]

# RGB palette, indexed by biome id.
PALETTE = np.array([
    (18, 38, 86),     # deep ocean
    (28, 70, 140),    # ocean
    (54, 116, 186),   # shallows
    (212, 200, 142),  # beach
    (176, 180, 168),  # tundra
    (238, 242, 247),  # snow
    (74, 118, 96),    # taiga
    (138, 152, 96),   # shrubland
    (150, 184, 96),   # grassland
    (62, 130, 72),    # temperate forest
    (40, 104, 78),    # temperate rainforest
    (190, 184, 96),   # savanna
    (224, 206, 134),  # desert
    (52, 142, 64),    # tropical forest
    (28, 116, 54),    # tropical rainforest
    (112, 104, 98),   # mountain
    (250, 250, 255),  # snow peak
], dtype=np.uint8)


# ---------------------------------------------------------------------------
# Perlin noise (vectorized)
# ---------------------------------------------------------------------------
class PerlinNoise:
    """Classic 2D Perlin noise over numpy arrays, with fractal (fBm) support."""

    def __init__(self, seed=0):
        rng = np.random.default_rng(seed)
        perm = rng.permutation(256).astype(np.int32)
        self.perm = np.concatenate([perm, perm])  # length 512, avoids wrap math

    @staticmethod
    def _fade(t):
        return t * t * t * (t * (t * 6 - 15) + 10)

    @staticmethod
    def _lerp(a, b, t):
        return a + t * (b - a)

    @staticmethod
    def _grad(h, x, y):
        h = h & 3
        u = np.where(h < 2, x, y)
        v = np.where(h < 2, y, x)
        return np.where((h & 1) == 0, u, -u) + np.where((h & 2) == 0, v, -v)

    def noise2(self, x, y):
        p = self.perm
        xi = np.floor(x).astype(np.int64)
        yi = np.floor(y).astype(np.int64)
        xf = x - xi
        yf = y - yi
        xi &= 255
        yi &= 255
        u = self._fade(xf)
        v = self._fade(yf)

        aa = p[p[xi] + yi]
        ab = p[p[xi] + yi + 1]
        ba = p[p[xi + 1] + yi]
        bb = p[p[xi + 1] + yi + 1]

        x1 = self._lerp(self._grad(aa, xf, yf), self._grad(ba, xf - 1, yf), u)
        x2 = self._lerp(self._grad(ab, xf, yf - 1), self._grad(bb, xf - 1, yf - 1), u)
        return self._lerp(x1, x2, v)  # roughly [-1, 1]

    def fbm(self, x, y, octaves=6, lacunarity=2.0, gain=0.5):
        total = np.zeros_like(x, dtype=np.float64)
        freq = 1.0
        amp = 1.0
        norm = 0.0
        for _ in range(octaves):
            total += amp * self.noise2(x * freq, y * freq)
            norm += amp
            amp *= gain
            freq *= lacunarity
        return total / norm  # back to ~[-1, 1]


# ---------------------------------------------------------------------------
# Biome classification
# ---------------------------------------------------------------------------
def classify(elev, temp, moist, sea_level,
             mountain_level=0.70, peak_level=0.82, snowline=0.58):
    """Map elevation/temperature/moisture fields to biome ids (vectorized)."""
    biome = np.empty(elev.shape, dtype=np.int32)

    land = elev >= sea_level
    deep = elev < sea_level - 0.10
    ocean = (~deep) & (elev < sea_level - 0.02)
    shallow = (~deep) & (~ocean) & (~land)

    biome[deep] = DEEP_OCEAN
    biome[ocean] = OCEAN
    biome[shallow] = SHALLOW

    # Temperature / moisture bands (Whittaker-style).
    cold = temp < 0.25
    cool = (temp >= 0.25) & (temp < 0.50)
    warm = (temp >= 0.50) & (temp < 0.72)
    hot = temp >= 0.72
    dry = moist < 0.30
    semi = (moist >= 0.30) & (moist < 0.55)
    wet = (moist >= 0.55) & (moist < 0.78)
    vwet = moist >= 0.78

    conds = [
        cold & dry, cold & ~dry,
        cool & dry, cool & semi, cool & (wet | vwet),
        warm & dry, warm & semi, warm & wet, warm & vwet,
        hot & dry, hot & semi, hot & wet, hot & vwet,
    ]
    picks = [
        TUNDRA, TAIGA,
        SHRUBLAND, GRASSLAND, TEMPERATE_FOREST,
        GRASSLAND, TEMPERATE_FOREST, TEMPERATE_FOREST, TEMPERATE_RAINFOREST,
        DESERT, SAVANNA, TROPICAL_FOREST, TROPICAL_RAINFOREST,
    ]
    land_biome = np.select(conds, picks, default=GRASSLAND)
    biome = np.where(land, land_biome, biome)

    # Elevation overrides (mountains / peaks / cold highlands).
    biome = np.where(land & (elev > mountain_level) & (elev <= peak_level),
                     MOUNTAIN, biome)
    biome = np.where(land & (elev > peak_level), SNOW_PEAK, biome)
    biome = np.where(land & (elev > snowline) & cold, SNOW, biome)

    # Coastline beaches.
    biome = np.where(land & (elev < sea_level + 0.015), BEACH, biome)
    return biome


# ---------------------------------------------------------------------------
# World generator
# ---------------------------------------------------------------------------
DEFAULTS = dict(
    sea_level=0.42,
    elev_scale=240.0,      # larger = bigger continents (tiles per noise unit)
    temp_scale=900.0,      # very large -> broad climate regions
    moist_scale=420.0,
    warp_scale=320.0,
    warp_strength=55.0,    # domain warp for more natural coastlines
    redistribution=1.15,   # >1 sinks midlands -> more ocean/lowland
    lapse=0.95,            # how strongly altitude cools temperature
    shade_strength=42.0,   # hillshade intensity
    elev_octaves=6,
    temp_octaves=3,
    moist_octaves=4,
    # Perlin output bunches around the middle; contrast-stretch each field
    # around a pivot so the full biome/elevation range is actually reached.
    elev_pivot=0.45,
    elev_contrast=1.5,
    temp_contrast=1.9,
    moist_contrast=2.0,
    mountain_level=0.68,   # land elevation -> bare mountain
    peak_level=0.80,       # land elevation -> snow peak
    snowline=0.58,         # cold highlands turn to snow above this
    color_smooth=2,        # blur radius (tiles) for land biome color blending
)

# Biomes whose color edges stay crisp (no blending): water + coastline.
_SHARP_EDGE_BIOMES = (DEEP_OCEAN, OCEAN, SHALLOW, BEACH)


class Chunk:
    __slots__ = ("cx", "cy", "size", "biome", "elev", "temp", "moist", "color")

    def __init__(self, cx, cy, size, biome, elev, temp, moist, color):
        self.cx, self.cy, self.size = cx, cy, size
        self.biome, self.elev, self.temp, self.moist = biome, elev, temp, moist
        self.color = color


class WorldGenerator:
    def __init__(self, seed=0, params=None):
        self.seed = int(seed)
        self.p = dict(DEFAULTS)
        if params:
            self.p.update(params)
        self.palette = PALETTE
        # Independent noise sources from derived seeds.
        self.n_elev = PerlinNoise(self.seed)
        self.n_temp = PerlinNoise(self.seed + 1013)
        self.n_moist = PerlinNoise(self.seed + 2027)
        self.n_warp = PerlinNoise(self.seed + 7919)

    # -- field math ---------------------------------------------------------
    def _elevation(self, gx, gy):
        p = self.p
        wx = self.n_warp.fbm(gx / p["warp_scale"], gy / p["warp_scale"], octaves=2)
        wy = self.n_warp.fbm((gx + 311.7) / p["warp_scale"],
                             (gy - 187.3) / p["warp_scale"], octaves=2)
        fx = gx + wx * p["warp_strength"]
        fy = gy + wy * p["warp_strength"]
        e = self.n_elev.fbm(fx / p["elev_scale"], fy / p["elev_scale"],
                            octaves=p["elev_octaves"])
        e = (e + 1.0) * 0.5
        e = np.clip(e, 0.0, 1.0) ** p["redistribution"]
        # Contrast-stretch around a pivot: deepens oceans, raises peaks.
        e = p["elev_pivot"] + (e - p["elev_pivot"]) * p["elev_contrast"]
        return np.clip(e, 0.0, 1.0)

    def _temperature(self, gx, gy, elev):
        p = self.p
        t = self.n_temp.fbm(gx / p["temp_scale"], gy / p["temp_scale"],
                            octaves=p["temp_octaves"])
        t = (t + 1.0) * 0.5
        t = 0.5 + (t - 0.5) * p["temp_contrast"]   # use full climate range
        above = np.clip(elev - p["sea_level"], 0.0, None)
        t = t - above * p["lapse"]
        return np.clip(t, 0.0, 1.0)

    def _moisture(self, gx, gy):
        p = self.p
        m = self.n_moist.fbm(gx / p["moist_scale"], gy / p["moist_scale"],
                             octaves=p["moist_octaves"])
        m = (m + 1.0) * 0.5
        m = 0.5 + (m - 0.5) * p["moist_contrast"]
        return np.clip(m, 0.0, 1.0)

    def _hillshade(self, elev):
        dy, dx = np.gradient(elev)
        lx, ly = -0.7, -0.7  # light from the north-west
        s = 1.0 + (dx * lx + dy * ly) * self.p["shade_strength"]
        return np.clip(s, 0.55, 1.30)

    def _fields(self, gx, gy):
        elev = self._elevation(gx, gy)
        temp = self._temperature(gx, gy, elev)
        moist = self._moisture(gx, gy)
        return elev, temp, moist

    def _classify(self, elev, temp, moist):
        p = self.p
        return classify(elev, temp, moist, p["sea_level"],
                        p["mountain_level"], p["peak_level"], p["snowline"])

    def _smooth_color(self, color, biome):
        """Blend colors across land biome borders, keeping water/beach crisp.

        A masked separable Gaussian: each blendable tile averages only its
        blendable neighbours, so colour never bleeds across coastlines.
        """
        r = int(self.p["color_smooth"])
        if r <= 0:
            return color
        soft = (~np.isin(biome, _SHARP_EDGE_BIOMES)).astype(np.float32)
        offs = np.arange(-r, r + 1)
        sigma = r * 0.6 + 1e-6
        w = np.exp(-(offs ** 2) / (2 * sigma * sigma))
        w /= w.sum()

        def blur1d(a, axis):
            out = np.zeros_like(a)
            for k, wk in zip(offs, w):
                out += wk * np.roll(a, k, axis=axis)
            return out

        m = soft
        num = blur1d(blur1d(color * m[..., None], 0), 1)
        den = blur1d(blur1d(m, 0), 1)
        den = np.where(den > 1e-6, den, 1.0)[..., None]
        blended = num / den
        return np.where(soft[..., None] > 0, blended, color)

    # -- chunk generation ---------------------------------------------------
    def generate_chunk(self, cx, cy, size):
        """Generate one chunk. Padded so hillshade and colour blending are
        seamless across chunk borders."""
        pad = max(1, 2 * int(self.p["color_smooth"]))
        x0, y0 = cx * size, cy * size
        xs = np.arange(x0 - pad, x0 + size + pad, dtype=np.float64)
        ys = np.arange(y0 - pad, y0 + size + pad, dtype=np.float64)
        gx, gy = np.meshgrid(xs, ys)  # [row=y, col=x]

        elev, temp, moist = self._fields(gx, gy)
        biome = self._classify(elev, temp, moist)

        color = self.palette[biome].astype(np.float32)
        color = self._smooth_color(color, biome)

        shade = self._hillshade(elev)
        land = elev >= self.p["sea_level"]
        shade = np.where(land, shade, 1.0)[..., None]
        color = np.clip(color * shade, 0, 255)

        s = slice(pad, -pad)
        return Chunk(
            cx, cy, size,
            biome[s, s].copy(),
            elev[s, s].copy(),
            temp[s, s].copy(),
            moist[s, s].copy(),
            color[s, s].astype(np.uint8),
        )

    # -- single point query (HUD) ------------------------------------------
    def biome_at(self, x, y):
        gx = np.array([[float(x)]])
        gy = np.array([[float(y)]])
        elev, temp, moist = self._fields(gx, gy)
        b = int(self._classify(elev, temp, moist)[0, 0])
        return b, float(elev[0, 0]), float(temp[0, 0]), float(moist[0, 0])

    # -- coarse region (minimap) -------------------------------------------
    def region_colors(self, x0, y0, width, height, step):
        xs = np.arange(x0, x0 + width * step, step, dtype=np.float64)[:width]
        ys = np.arange(y0, y0 + height * step, step, dtype=np.float64)[:height]
        gx, gy = np.meshgrid(xs, ys)
        elev, temp, moist = self._fields(gx, gy)
        biome = self._classify(elev, temp, moist)
        return self.palette[biome]  # (height, width, 3) uint8
