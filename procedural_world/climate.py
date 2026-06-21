"""Climate & weather data layer (data only — no rendering).

Three tiers:

  1. Static climate  - elevation / temperature / moisture / biome per tile.
     (Provided by worldgen.WorldGenerator; wrapped here for one clean API.)
  2. Dynamic weather - wind, moving precipitation/cloud fronts that evolve
     deterministically from (seed, time). Sampled cheaply from noise.
  3. Effective conditions - what it's actually like at a tile *right now*:
     base climate + day/night swing + weather, via `conditions_at()`.

Everything is a pure function of position and time, so it is deterministic and
replayable. Nothing here draws anything; gameplay/visual systems consume it.
"""

import math

import numpy as np

from worldgen import PerlinNoise, BIOME_NAMES

# Effective temperature is tracked normalized (0..1) and mapped to a readable
# range for display.
TEMP_MIN_C = -12.0
TEMP_MAX_C = 42.0

WEATHER_DEFAULTS = dict(
    wind_scale=900.0,        # tiles per wind-field feature
    wind_time=0.05,          # how fast the wind field rotates (per day)
    weather_scale=520.0,     # tiles per precipitation feature
    weather_drift=0.18,      # how fast fronts drift across the world (per day)
    precip_threshold=0.55,   # below this the sky is dry
    cloud_threshold=0.42,
    diurnal_base=0.05,       # baseline day/night temperature swing (normalized)
    diurnal_arid=0.13,       # extra swing in dry places (deserts swing hardest)
    precip_chill=0.10,       # how much active precip cools the air
)

_COMPASS = ["E", "NE", "N", "NW", "W", "SW", "S", "SE"]


def _compass(vx, vy):
    # Screen space: -y is north.
    ang = (math.degrees(math.atan2(-vy, vx)) + 360.0) % 360.0
    return _COMPASS[int(((ang + 22.5) % 360) / 45)]


def temp_to_c(norm):
    return TEMP_MIN_C + (TEMP_MAX_C - TEMP_MIN_C) * norm


class Weather:
    """Time-evolving wind / precipitation / cloud fields (deterministic)."""

    def __init__(self, seed=0, params=None):
        self.p = dict(WEATHER_DEFAULTS)
        if params:
            self.p.update(params)
        self.n_wind_x = PerlinNoise(seed + 5001)
        self.n_wind_y = PerlinNoise(seed + 5003)
        self.n_precip = PerlinNoise(seed + 6007)
        self.n_cloud = PerlinNoise(seed + 7013)

    def wind(self, x, y, t):
        """Return (vx, vy unit vector, speed 0..1) at tile (x, y), time t (days)."""
        s = self.p["wind_scale"]
        ts = t * self.p["wind_time"]
        vx = float(self.n_wind_x.noise2(x / s + ts, y / s))
        vy = float(self.n_wind_y.noise2(x / s, y / s + ts))
        mag = math.hypot(vx, vy)
        speed = min(1.0, mag)
        if mag < 1e-6:
            return 1.0, 0.0, 0.0
        return vx / mag, vy / mag, speed

    def precip(self, x, y, t):
        """Precipitation intensity 0..1 (0 = dry)."""
        s = self.p["weather_scale"]
        drift = t * self.p["weather_drift"]
        raw = (float(self.n_precip.fbm(x / s + drift, y / s + drift * 0.3,
                                       octaves=3)) + 1.0) * 0.5
        thr = self.p["precip_threshold"]
        return max(0.0, min(1.0, (raw - thr) / (1.0 - thr)))

    def cloud(self, x, y, t):
        s = self.p["weather_scale"] * 0.8
        drift = t * self.p["weather_drift"]
        raw = (float(self.n_cloud.fbm(x / s + drift * 1.1, y / s, octaves=3))
               + 1.0) * 0.5
        thr = self.p["cloud_threshold"]
        base = max(0.0, min(1.0, (raw - thr) / (1.0 - thr)))
        return max(base, self.precip(x, y, t))  # rain implies cloud cover

    def diurnal_delta(self, time_of_day, moisture):
        """Normalized temperature offset from time of day (dry swings more)."""
        aridity = 1.0 - moisture
        amp = self.p["diurnal_base"] + self.p["diurnal_arid"] * aridity
        # warmest ~mid-afternoon (t=0.62), coldest ~pre-dawn (t=0.12)
        return amp * math.cos(2 * math.pi * (time_of_day - 0.62))


class Climate:
    """Combines static climate (WorldGenerator) with dynamic Weather."""

    def __init__(self, generator, weather=None):
        self.gen = generator
        self.weather = weather or Weather(generator.seed)

    @staticmethod
    def classify_weather(precip, cloud, temp_c):
        if precip < 0.12:
            return "Cloudy" if cloud >= 0.5 else "Clear"
        if temp_c <= 0.5:
            return "Snow"
        if precip > 0.7:
            return "Storm"
        return "Rain"

    def conditions_at(self, x, y, time_of_day=0.5, day=0):
        """Effective conditions at a tile, combining all three tiers."""
        biome, elev, base_temp, moist = self.gen.biome_at(
            int(math.floor(x)), int(math.floor(y)))

        t_abs = day + time_of_day
        vx, vy, wspeed = self.weather.wind(x, y, t_abs)
        precip = self.weather.precip(x, y, t_abs)
        cloud = self.weather.cloud(x, y, t_abs)

        diurnal = self.weather.diurnal_delta(time_of_day, moist)
        chill = precip * self.weather.p["precip_chill"]
        eff = max(0.0, min(1.0, base_temp + diurnal - chill))
        temp_c = temp_to_c(eff)

        weather = self.classify_weather(precip, cloud, temp_c)
        visibility = max(0.1, 1.0 - 0.6 * precip - 0.25 * cloud)

        return {
            "biome": biome,
            "biome_name": BIOME_NAMES[biome],
            "elevation": elev,
            "moisture": moist,
            "base_temp": base_temp,
            "temperature": eff,
            "temp_c": temp_c,
            "weather": weather,
            "precip": precip,
            "cloud": cloud,
            "wind": (vx, vy),
            "wind_speed": wspeed,
            "wind_dir": _compass(vx, vy),
            "visibility": visibility,
        }


def selftest():
    from worldgen import WorldGenerator
    print("running climate selftest...")
    g = WorldGenerator(7)
    c = Climate(g)

    # Determinism.
    a = c.conditions_at(10, 20, 0.5, 0)
    b = c.conditions_at(10, 20, 0.5, 0)
    assert a == b, "conditions not deterministic"

    # Weather evolves over time somewhere.
    changed = any(
        abs(c.weather.precip(x, x * 2, 0.0) - c.weather.precip(x, x * 2, 2.0)) > 0.05
        for x in range(0, 2000, 50)
    )
    assert changed, "weather does not evolve over time"
    print("  weather evolves over time: OK")

    # Snow only where it's cold.
    bad = 0
    samples = 0
    for x in range(-1500, 1500, 60):
        for y in range(-1500, 1500, 60):
            cc = c.conditions_at(x, y, 0.5, 0)
            if cc["weather"] == "Snow":
                samples += 1
                if cc["temp_c"] > 1.0:
                    bad += 1
    print(f"  snow samples: {samples}, mis-classified warm-snow: {bad}")
    assert bad == 0, "snow appearing in warm areas"

    # Diurnal swing: a dry tile is warmer mid-afternoon than pre-dawn.
    # Pick a desert-ish (dry) tile if we can find one.
    dry = None
    for x in range(0, 4000, 30):
        _, _, _, m = g.biome_at(x, 0)
        if m < 0.3:
            dry = x
            break
    if dry is not None:
        noon = c.conditions_at(dry, 0, 0.62, 0)["temp_c"]
        dawn = c.conditions_at(dry, 0, 0.12, 0)["temp_c"]
        print(f"  dry tile x={dry}: afternoon {noon:+.1f}C vs pre-dawn {dawn:+.1f}C")
        assert noon > dawn, "diurnal swing wrong direction"

    # Wind is a unit vector.
    vx, vy, spd = c.weather.wind(123, 456, 0.3)
    assert abs(math.hypot(vx, vy) - 1.0) < 1e-6, "wind not normalized"
    print(f"  sample conditions @ (10,20): {a['temp_c']:+.1f}C {a['weather']} "
          f"wind {a['wind_dir']} precip {a['precip']:.2f}")
    print("climate selftest OK")


if __name__ == "__main__":
    selftest()
