"""AI factions: settlements that own territory and grow over time.

Designed to scale to many factions. The world manager (`FactionWorld`) places
settlements deterministically on suitable land, assigns each to the nearest
faction "capital" (so territory is contiguous), maintains a chunk->faction claims
map for the territory overlay, and simulates each settlement (population, wealth,
stockpiles, soldiers, tier upgrades).

Pure-ish: placement is deterministic from the world seed; only the live economic
state evolves over time. No rendering here — the game consumes this data.
"""

import math
import random

import numpy as np

from worldgen import DEEP_OCEAN, OCEAN, SHALLOW, MOUNTAIN, SNOW_PEAK

_UNSUITABLE = {DEEP_OCEAN, OCEAN, SHALLOW, MOUNTAIN, SNOW_PEAK}

# Settlement tiers (data-driven so new tiers are easy to add).
OUTPOST, TOWN, CITY = 0, 1, 2
TIERS = [
    dict(name="Outpost", claim=1, pop_cap=140, marker=5, mil=0.06,
         up_pop=110, up_cost=500,
         prod=dict(food=2.0, wood=1.2, stone=0.8, gold=2.5),
         pop0=30, wealth0=250),
    dict(name="Town", claim=2, pop_cap=700, marker=8, mil=0.08,
         up_pop=560, up_cost=3000,
         prod=dict(food=7.0, wood=3.5, stone=3.0, gold=9.0),
         pop0=180, wealth0=1500),
    dict(name="City", claim=3, pop_cap=3200, marker=12, mil=0.10,
         up_pop=None, up_cost=None,
         prod=dict(food=22.0, wood=9.0, stone=9.0, gold=32.0),
         pop0=900, wealth0=9000),
]

# Faction palette / names (territory tint colors). Extend freely.
FACTION_DEFS = [
    ("Crimson Pact", (210, 70, 70)),
    ("Azure League", (70, 120, 210)),
    ("Verdant Clans", (90, 175, 90)),
    ("Gold Concord", (210, 175, 70)),
    ("Violet Order", (160, 90, 200)),
]

_SYL_A = ["ar", "bel", "cor", "dun", "el", "far", "gor", "hol", "ir", "kel",
          "lor", "mor", "nor", "or", "par", "ral", "sor", "tor", "ul", "var", "wyn"]
_SYL_B = ["ad", "an", "eth", "ial", "ond", "or", "us", "wyn", "ix", "ar", "en"]
_SUFFIX = ["", "", "ton", "burg", "hold", "gard", "fell", "stead", "watch"]


def _gen_name(rng):
    return (rng.choice(_SYL_A) + rng.choice(_SYL_B)).capitalize() + rng.choice(_SUFFIX)


_FIRST = ["Aldric", "Bryn", "Cael", "Doran", "Edric", "Fenna", "Gwen", "Hale",
          "Ivar", "Jor", "Kara", "Lys", "Mara", "Nils", "Orin", "Pell", "Rurik",
          "Sable", "Tova", "Ulf", "Vera", "Wystan"]
_EPITHET = ["", "", "", "the Bold", "the Grim", "Ironhand", "the Swift",
            "Stormborn", "of the Vale"]


def _gen_commander(rng):
    e = rng.choice(_EPITHET)
    return rng.choice(_FIRST) + (" " + e if e else "")


class Faction:
    def __init__(self, fid, name, color):
        self.id = fid
        self.name = name
        self.color = color
        self.settlements = []
        self.relations = {}   # other_faction_id -> attitude (future use)

    def totals(self):
        pop = sum(s.population for s in self.settlements)
        gold = sum(s.wealth for s in self.settlements)
        sol = sum(s.soldiers for s in self.settlements)
        return int(pop), int(gold), int(sol)


class Settlement:
    __slots__ = ("x", "y", "faction", "tier", "name",
                 "population", "wealth", "soldiers", "stock")

    def __init__(self, x, y, faction, tier, name):
        self.x = x
        self.y = y
        self.faction = faction
        self.tier = tier
        self.name = name
        t = TIERS[tier]
        self.population = float(t["pop0"])
        self.wealth = float(t["wealth0"])
        self.soldiers = self.population * t["mil"]
        self.stock = {"food": 0.0, "wood": 0.0, "stone": 0.0}

    @property
    def kind(self):
        return TIERS[self.tier]["name"]

    def chunk(self, chunk_size):
        return (int(math.floor(self.x)) // chunk_size,
                int(math.floor(self.y)) // chunk_size)

    def simulate(self, dt_days):
        """Advance the economy. Returns True if the settlement upgraded tier."""
        t = TIERS[self.tier]
        cap = t["pop_cap"]
        # Logistic population growth.
        self.population += 0.55 * self.population * (1 - self.population / cap) * dt_days
        # Output scales with how settled the place is.
        factor = 0.3 + 0.7 * (self.population / cap)
        for res, amt in t["prod"].items():
            if res == "gold":
                self.wealth += amt * factor * dt_days
            else:
                self.stock[res] = self.stock.get(res, 0.0) + amt * factor * dt_days
        # Soldiers drift toward the tier's military fraction of population.
        target = self.population * t["mil"]
        self.soldiers += (target - self.soldiers) * min(1.0, 0.5 * dt_days)
        # Upgrade when big and rich enough.
        if t["up_pop"] and self.population >= t["up_pop"] and self.wealth >= t["up_cost"]:
            self.wealth -= t["up_cost"]
            self.tier += 1
            return True
        return False


class Army:
    """An aggregate field army led by a commander/vassal.

    Strength is a *count* (composition-ready), never individual unit objects, so
    the world holds at most a few dozen of these tokens. Battles will resolve
    stack-vs-stack later.
    """
    __slots__ = ("x", "y", "faction", "leader", "composition", "target",
                 "speed", "home")

    def __init__(self, x, y, faction, leader, strength, home=None):
        self.x = x
        self.y = y
        self.faction = faction
        self.leader = leader
        # Single troop type for now; add cavalry/archers later with no refactor.
        self.composition = {"infantry": int(strength)}
        self.target = None        # (x, y) move order
        self.speed = 120.0        # tiles per game-day
        self.home = home          # settlement it was raised from

    @property
    def strength(self):
        return int(sum(self.composition.values()))


class FactionWorld:
    """Holds all factions/settlements and the chunk->faction claims map."""

    def __init__(self, seed, chunk_size, n_factions=3):
        self.seed = seed & 0xFFFFFFFF
        self.chunk_size = chunk_size
        self.n_factions = min(n_factions, len(FACTION_DEFS))
        self.factions = []
        self.settlements = []
        self.armies = []
        self.claims = {}          # (cx, cy) -> faction_id
        self._rng = random.Random(self.seed ^ 0x5151)

    # -- placement ----------------------------------------------------------
    def generate(self, gen, ox, oy, radius=520, spacing=58, max_settlements=55):
        self.factions = [Faction(i, *FACTION_DEFS[i]) for i in range(self.n_factions)]
        arng = random.Random(self.seed ^ 0xA5A5A5)
        anchors = [(ox + arng.uniform(-radius, radius),
                    oy + arng.uniform(-radius, radius))
                   for _ in range(self.n_factions)]

        # Candidate sites on a jittered coarse grid (deterministic per cell).
        cells = []
        gx0 = int((ox - radius) // spacing * spacing)
        gy0 = int((oy - radius) // spacing * spacing)
        cx = gx0
        while cx <= ox + radius:
            cy = gy0
            while cy <= oy + radius:
                r = random.Random((self.seed ^ (cx * 73856093) ^ (cy * 19349663))
                                  & 0xFFFFFFFF)
                if r.random() < 0.40:
                    jx = cx + r.uniform(spacing * 0.2, spacing * 0.8)
                    jy = cy + r.uniform(spacing * 0.2, spacing * 0.8)
                    cells.append((jx, jy, r))
                cy += spacing
            cx += spacing

        self.settlements = []
        if cells:
            ax = np.array([c[0] for c in cells], dtype=np.float64).reshape(1, -1)
            ay = np.array([c[1] for c in cells], dtype=np.float64).reshape(1, -1)
            e, t, m = gen._fields(ax, ay)
            biomes = gen._classify(e, t, m)[0]
            for i, (jx, jy, r) in enumerate(cells):
                if int(biomes[i]) in _UNSUITABLE:
                    continue
                tier = r.choices([OUTPOST, TOWN, CITY], weights=[0.62, 0.3, 0.08])[0]
                fid = min(range(self.n_factions),
                          key=lambda k: (jx - anchors[k][0]) ** 2 + (jy - anchors[k][1]) ** 2)
                self.settlements.append(
                    Settlement(jx, jy, self.factions[fid], tier, _gen_name(r)))

        self.settlements.sort(key=lambda s: (s.x - ox) ** 2 + (s.y - oy) ** 2)
        self.settlements = self.settlements[:max_settlements]
        for f in self.factions:
            f.settlements = [s for s in self.settlements if s.faction is f]
        # Guarantee every faction has at least one settlement (reassign nearest
        # from a faction that can spare one).
        for f in self.factions:
            if f.settlements:
                continue
            donors = [s for s in self.settlements if len(s.faction.settlements) > 1]
            if not donors:
                break
            ax, ay = anchors[f.id]
            s = min(donors, key=lambda s: (s.x - ax) ** 2 + (s.y - ay) ** 2)
            s.faction.settlements.remove(s)
            s.faction = f
            f.settlements.append(s)
        self.armies = []
        self._recompute_claims()

    # -- claims / territory -------------------------------------------------
    def _recompute_claims(self):
        claims = {}
        owner_d2 = {}
        cs = self.chunk_size
        for s in self.settlements:
            rad = TIERS[s.tier]["claim"]
            scx, scy = s.chunk(cs)
            for dy in range(-rad, rad + 1):
                for dx in range(-rad, rad + 1):
                    d2 = dx * dx + dy * dy
                    if d2 > rad * rad + rad:
                        continue
                    key = (scx + dx, scy + dy)
                    if key not in owner_d2 or d2 < owner_d2[key]:
                        owner_d2[key] = d2
                        claims[key] = s.faction.id
        self.claims = claims

    def owner_of_chunk(self, cx, cy):
        return self.claims.get((cx, cy))

    def nearest_settlement(self, x, y, max_dist=10.0):
        best, bestd = None, max_dist * max_dist
        for s in self.settlements:
            d2 = (s.x - x) ** 2 + (s.y - y) ** 2
            if d2 < bestd:
                best, bestd = s, d2
        return best

    def nearest_army(self, x, y, max_dist=8.0):
        best, bestd = None, max_dist * max_dist
        for a in self.armies:
            d2 = (a.x - x) ** 2 + (a.y - y) ** 2
            if d2 < bestd:
                best, bestd = a, d2
        return best

    # -- armies (aggregate stacks) ------------------------------------------
    def _pick_target(self, faction):
        if len(faction.settlements) <= 1:
            return None
        s = self._rng.choice(faction.settlements)
        return (s.x, s.y)

    def _update_armies(self, dt_days):
        # Maintain a target number of armies per faction, raised from settlement
        # garrisons (soldiers move from "in town" to "in the field").
        for f in self.factions:
            target = min(4, 1 + len(f.settlements) // 4)
            cur = sum(1 for a in self.armies if a.faction is f)
            if cur < target:
                pool = [s for s in f.settlements if s.soldiers >= 40]
                if pool:
                    s = self._rng.choice(pool)
                    n = int(s.soldiers * 0.6)
                    s.soldiers -= n
                    army = Army(s.x, s.y, f, _gen_commander(self._rng), n, home=s)
                    army.target = self._pick_target(f)
                    self.armies.append(army)

        # March each army toward its order; on arrival pick a new friendly town
        # (or occasionally disband back into its home garrison).
        for a in self.armies:
            if a.target is None:
                a.target = self._pick_target(a.faction)
                if a.target is None:
                    continue
            tx, ty = a.target
            dx, dy = tx - a.x, ty - a.y
            d = math.hypot(dx, dy)
            if d < 3.0:
                if self._rng.random() < 0.12 and a.home is not None:
                    a.home.soldiers += a.strength
                    a.composition = {"infantry": 0}
                a.target = self._pick_target(a.faction)
            else:
                step = min(d, a.speed * dt_days)
                a.x += dx / d * step
                a.y += dy / d * step
        self.armies = [a for a in self.armies if a.strength > 0]

    # -- simulation ---------------------------------------------------------
    def update(self, dt_days):
        if dt_days <= 0 or not self.settlements:
            return
        upgraded = False
        for s in self.settlements:
            if s.simulate(dt_days):
                upgraded = True
        if upgraded:
            self._recompute_claims()
        self._update_armies(dt_days)


def selftest():
    from worldgen import WorldGenerator
    print("running factions selftest...")
    g = WorldGenerator(7)
    fw = FactionWorld(7, 64, n_factions=3)
    fw.generate(g, 0, 0)
    assert fw.settlements, "no settlements placed"
    assert fw.claims, "no territory claimed"
    print(f"  factions: {[f.name for f in fw.factions]}")
    print(f"  settlements: {len(fw.settlements)}  claimed chunks: {len(fw.claims)}")
    kinds = {}
    for s in fw.settlements:
        kinds[s.kind] = kinds.get(s.kind, 0) + 1
    print(f"  by tier: {kinds}")

    # Determinism.
    fw2 = FactionWorld(7, 64, n_factions=3)
    fw2.generate(g, 0, 0)
    assert len(fw2.settlements) == len(fw.settlements)
    assert (fw2.settlements[0].x, fw2.settlements[0].y) == (fw.settlements[0].x, fw.settlements[0].y), \
        "placement not deterministic"
    print("  deterministic placement: OK")

    # Simulation grows population and can upgrade tiers.
    s = fw.settlements[0]
    pop0, tier0 = s.population, s.tier
    for _ in range(2000):
        fw.update(0.1)
    pop1 = sum(x.population for x in fw.settlements)
    print(f"  after sim: sample pop {pop0:.0f}->{s.population:.0f} (tier {tier0}->{s.tier}), "
          f"total pop {pop1:.0f}")
    assert s.population > pop0, "population did not grow"
    tot_pop, tot_gold, tot_sol = fw.factions[0].totals()
    print(f"  {fw.factions[0].name}: pop {tot_pop} gold {tot_gold} soldiers {tot_sol}")

    # Armies get raised and move.
    assert fw.armies, "no armies were raised"
    a = fw.armies[0]
    ax0, ay0 = a.x, a.y
    for _ in range(50):
        fw.update(0.1)
    moved = (a.x, a.y) != (ax0, ay0) if a in fw.armies else True
    print(f"  armies: {len(fw.armies)} (e.g. {a.leader}, {a.strength} infantry), moving: {moved}")
    assert moved, "armies did not move"
    print("factions selftest OK")


if __name__ == "__main__":
    selftest()
