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

from worldgen import (
    DEEP_OCEAN, OCEAN, SHALLOW, MOUNTAIN, SNOW_PEAK,
    GRASSLAND, SAVANNA, SHRUBLAND, TEMPERATE_FOREST, TROPICAL_FOREST, TAIGA,
    TEMPERATE_RAINFOREST, TROPICAL_RAINFOREST,
)

_OPEN_LAND = {GRASSLAND, SAVANNA, SHRUBLAND}
_WOODLAND = {TEMPERATE_FOREST, TROPICAL_FOREST, TAIGA,
             TEMPERATE_RAINFOREST, TROPICAL_RAINFOREST}

_UNSUITABLE = {DEEP_OCEAN, OCEAN, SHALLOW, MOUNTAIN, SNOW_PEAK}

ENGAGE_DIST2 = 4.0 ** 2    # army-vs-army contact distance (squared)
SIEGE_DIST2 = 3.0 ** 2     # army-vs-settlement siege distance (squared)

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
        self.dead = False

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
                 "speed", "home", "_chk")

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
        self._chk = random.uniform(0.0, 0.004)  # staggered terrain-check timer

    @property
    def strength(self):
        return int(sum(self.composition.values()))


# Director personalities: weights for aggression / expansion / militarism.
PROFILES = [
    ("Expansionist", dict(aggr=0.35, expand=0.95, mil=0.5)),
    ("Warmonger",    dict(aggr=0.90, expand=0.45, mil=0.95)),
    ("Merchant",     dict(aggr=0.20, expand=0.65, mil=0.40)),
    ("Defender",     dict(aggr=0.30, expand=0.45, mil=0.75)),
]
STRATEGIC_INTERVAL = 1.5   # game-days between strategic decisions


class FactionDirector:
    """The strategic AI for one faction: sets stances toward rivals, raises and
    orders armies, and decides expansion. Runs on a slow strategic tick."""

    def __init__(self, faction, seed):
        self.faction = faction
        self.rng = random.Random((seed ^ (faction.id * 2663)) & 0xFFFFFFFF)
        self.profile_name, self.profile = self.rng.choice(PROFILES)
        self.stance = {}        # other_faction_id -> 'hostile' | 'wary' | 'neutral'
        self._acc = 0.0

    def status(self):
        hostile = [o for o, s in self.stance.items() if s == "hostile"]
        return self.profile_name, hostile

    def update(self, dt_days, world):
        self._acc += dt_days
        if self._acc < STRATEGIC_INTERVAL:
            return
        self._acc = 0.0
        self._decide(world)

    def _decide(self, world):
        f = self.faction
        p = self.profile

        # 1) Stance toward bordering rivals.
        for oid in world.contacts.get(f.id, ()):
            roll = self.rng.random()
            if p["aggr"] > 0.75 or (p["aggr"] > 0.4 and roll < 0.35):
                self.stance[oid] = "hostile"
            elif roll < 0.5:
                self.stance[oid] = "wary"
            else:
                self.stance[oid] = "neutral"
            f.relations[oid] = self.stance[oid]

        # 2) Maintain a militarised number of armies.
        target = max(1, min(6, int(len(f.settlements) * 0.3 * (0.6 + p["mil"]))))
        cur = [a for a in world.armies if a.faction is f]
        if len(cur) < target:
            new = world.raise_army(f)
            if new:
                cur.append(new)

        # 3) Orders: send roughly half toward hostile frontiers, rest defend.
        enemy_pts = []
        for oid, st in self.stance.items():
            if st == "hostile" and oid < len(world.factions):
                enemy_pts.extend((s.x, s.y) for s in world.factions[oid].settlements)
        for i, a in enumerate(cur):
            if enemy_pts and i % 2 == 0:
                a.target = min(enemy_pts,
                               key=lambda t: (t[0] - a.x) ** 2 + (t[1] - a.y) ** 2)
            else:
                a.target = world._pick_target(f)

        # 4) Expansion: grow territory by founding outposts.
        if self.rng.random() < p["expand"] * 0.5:
            world.found_outpost(f)


class FactionWorld:
    """Holds all factions/settlements and the chunk->faction claims map."""

    def __init__(self, seed, chunk_size, n_factions=3):
        self.seed = seed & 0xFFFFFFFF
        self.chunk_size = chunk_size
        self.n_factions = min(n_factions, len(FACTION_DEFS))
        self.factions = []
        self.settlements = []
        self.armies = []
        self.directors = []
        self.claims = {}          # (cx, cy) -> faction_id
        self.claims_version = 0   # bumped whenever claims change (for caches)
        self.contacts = {}        # faction_id -> set(bordering faction_ids)
        self.events = []          # recent world events (battles, captures)
        self._victory = False
        self._gen = None
        self._rng = random.Random(self.seed ^ 0x5151)

    # -- placement ----------------------------------------------------------
    def generate(self, gen, ox, oy, radius=520, spacing=58, max_settlements=55):
        self._gen = gen
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
        self.events = []
        self._victory = False
        self.directors = [FactionDirector(f, self.seed) for f in self.factions]
        self._recompute_claims()
        # Bootstrap an initial strategic decision so the world starts with stances
        # and a few armies instead of being inert for the first strategic tick.
        for d in self.directors:
            d._decide(self)

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
        self.claims_version += 1
        self._compute_contacts()

    def _compute_contacts(self):
        contacts = {f.id: set() for f in self.factions}
        for (cx, cy), fid in self.claims.items():
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                o = self.claims.get((cx + dx, cy + dy))
                if o is not None and o != fid:
                    contacts[fid].add(o)
                    contacts[o].add(fid)
        self.contacts = contacts

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

    def _make_composition(self, n, x, y):
        """Split a soldier count into troop types, flavored by local terrain
        (open land favors cavalry, woodland favors archers)."""
        b = self._gen.biome_at(int(x), int(y))[0] if self._gen else GRASSLAND
        inf = int(n * 0.5)
        if b in _OPEN_LAND:
            cav = int(n * 0.35)
            arch = n - inf - cav
        elif b in _WOODLAND:
            arch = int(n * 0.35)
            cav = n - inf - arch
        else:
            cav = int(n * 0.2)
            arch = n - inf - cav
        return {"infantry": inf, "cavalry": cav, "archers": arch}

    def raise_army(self, faction):
        """Raise one army from a settlement garrison. Returns it, or None."""
        pool = [s for s in faction.settlements if s.soldiers >= 40]
        if not pool:
            return None
        s = self._rng.choice(pool)
        n = int(s.soldiers * 0.6)
        s.soldiers -= n
        army = Army(s.x, s.y, faction, _gen_commander(self._rng), n, home=s)
        army.composition = self._make_composition(n, s.x, s.y)
        army.target = self._pick_target(faction)
        self.armies.append(army)
        return army

    def found_outpost(self, faction):
        """Found a new outpost on suitable land bordering the faction's territory,
        funded by its richest settlement. Returns True on success."""
        if self._gen is None or not faction.settlements:
            return False
        if len(self.settlements) >= 200 or len(faction.settlements) >= 60:
            return False  # keep claims recompute and rendering bounded
        rich = max(faction.settlements, key=lambda s: s.wealth)
        if rich.wealth < 800:
            return False
        owned = [c for c, fid in self.claims.items() if fid == faction.id]
        frontier = set()
        for (cx, cy) in owned:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                n = (cx + dx, cy + dy)
                if n not in self.claims:
                    frontier.add(n)
        if not frontier:
            return False
        cs = self.chunk_size
        for (cx, cy) in self._rng.sample(sorted(frontier), min(len(frontier), 6)):
            bx, by = cx * cs + cs // 2, cy * cs + cs // 2
            if self._gen.biome_at(bx, by)[0] in _UNSUITABLE:
                continue
            rich.wealth -= 800
            s = Settlement(bx + 0.5, by + 0.5, faction, OUTPOST, _gen_name(self._rng))
            self.settlements.append(s)
            faction.settlements.append(s)
            self._recompute_claims()
            return True
        return False

    def _move_armies(self, dt_days):
        """Mechanics only: march each army toward its current order, with a light
        throttled nudge so they don't park in water/mountains."""
        for a in self.armies:
            if a.target is None:
                a.target = self._pick_target(a.faction)
                if a.target is None:
                    continue
            tx, ty = a.target
            dx, dy = tx - a.x, ty - a.y
            d = math.hypot(dx, dy)
            if d < 3.0:
                if self._rng.random() < 0.06 and a.home is not None:
                    a.home.soldiers += a.strength
                    a.composition = {"infantry": 0}
                else:
                    a.target = self._pick_target(a.faction)
            else:
                step = min(d, a.speed * dt_days)
                a.x += dx / d * step
                a.y += dy / d * step
            # Occasional terrain check (staggered, ~every 0.004 game-days) to back
            # out of impassable tiles toward home — cheap straight-line steering.
            a._chk -= dt_days
            if a._chk <= 0:
                a._chk = 0.004
                if self._gen is not None and a.home is not None:
                    if self._gen.biome_at(int(a.x), int(a.y))[0] in _UNSUITABLE:
                        hx, hy = a.home.x - a.x, a.home.y - a.y
                        hd = math.hypot(hx, hy) or 1.0
                        a.x += hx / hd * 3.0
                        a.y += hy / hd * 3.0
        self.armies = [a for a in self.armies if a.strength > 0]

    # -- combat & conquest --------------------------------------------------
    def _hostile(self, fa, fb):
        return (fa.relations.get(fb.id) == "hostile"
                or fb.relations.get(fa.id) == "hostile")

    def _event(self, msg):
        if self.events and self.events[-1] == msg:
            return  # collapse consecutive duplicates
        self.events.append(msg)
        if len(self.events) > 12:
            self.events.pop(0)

    @staticmethod
    def _power(a, b):
        """Effective combat power of army a against b, with troop counters:
        infantry > cavalry > archers > infantry."""
        sa = a.strength
        if sa <= 0:
            return 0.0
        bt = b.strength or 1
        ci = b.composition.get("infantry", 0) / bt
        cc = b.composition.get("cavalry", 0) / bt
        ca = b.composition.get("archers", 0) / bt
        ai = a.composition.get("infantry", 0)
        ac = a.composition.get("cavalry", 0)
        aa = a.composition.get("archers", 0)
        bonus = 0.4 * (ai * cc + ac * ca + aa * ci) \
            - 0.4 * (ai * ca + ac * ci + aa * cc)
        return max(1.0, sa + bonus)

    @staticmethod
    def _scale_comp(army, keep):
        army.composition = {k: int(v * keep) for k, v in army.composition.items()}

    def _battle(self, a, b):
        pa, pb = self._power(a, b), self._power(b, a)
        if a.strength <= 0 or b.strength <= 0:
            return
        win, lose = (a, b) if self._rng.random() < pa / (pa + pb) else (b, a)
        cas = int(min(win.strength * 0.9, lose.strength * 0.6))
        self._scale_comp(win, (win.strength - cas) / max(1, win.strength))
        lose.composition = {"infantry": 0}
        win.target = None
        self._event(f"{win.faction.name} beat {lose.faction.name} in the field "
                    f"({win.strength} left)")

    def _siege(self, army, s):
        tier = TIERS[s.tier]
        defense = s.soldiers * 1.25 + tier["pop_cap"] * 0.015
        atk = army.strength
        if self._rng.random() < atk / (atk + defense + 1.0):
            old = s.faction
            cas = int(min(atk * 0.9, defense * 0.7))
            self._scale_comp(army, (atk - cas) / max(1, atk))
            # The capturing army leaves part of its remaining troops as garrison.
            garrison = int(army.strength * 0.3)
            self._scale_comp(army, 0.7)
            old.settlements.remove(s)
            s.faction = army.faction
            army.faction.settlements.append(s)
            s.population *= 0.6
            s.soldiers = garrison + s.population * tier["mil"] * 0.3
            s.wealth *= 0.5
            army.target = None
            self._recompute_claims()
            self._event(f"{army.faction.name} captured {s.name} from {old.name}!")
        else:
            cas = int(min(atk * 0.9, defense * 0.4))
            self._scale_comp(army, (atk - cas) / max(1, atk))
            s.soldiers = max(0.0, s.soldiers - atk * 0.3)
            # Retreat out of siege range so it doesn't re-assault every tick.
            dx, dy = army.x - s.x, army.y - s.y
            dd = math.hypot(dx, dy) or 1.0
            reach = SIEGE_DIST2 ** 0.5 + 2.0
            army.x, army.y = s.x + dx / dd * reach, s.y + dy / dd * reach
            army.target = (army.home.x, army.home.y) if army.home else None
            self._event(f"{army.faction.name}'s assault on {s.name} was repelled")

    def _resolve_combat(self):
        # Army vs army (mutually hostile, in contact).
        armies = self.armies
        for i in range(len(armies)):
            a = armies[i]
            if a.strength <= 0:
                continue
            for j in range(i + 1, len(armies)):
                b = armies[j]
                if b.strength <= 0 or a.faction is b.faction:
                    continue
                if self._hostile(a.faction, b.faction) and \
                        (a.x - b.x) ** 2 + (a.y - b.y) ** 2 <= ENGAGE_DIST2:
                    self._battle(a, b)
                    if a.strength <= 0:
                        break
        self.armies = [a for a in self.armies if a.strength > 0]
        # Army vs settlement (siege/capture).
        for a in list(self.armies):
            if a.strength <= 0:
                continue
            for s in self.settlements:
                if s.faction is a.faction or not self._hostile(a.faction, s.faction):
                    continue
                if (a.x - s.x) ** 2 + (a.y - s.y) ** 2 <= SIEGE_DIST2:
                    self._siege(a, s)
                    break
        self.armies = [a for a in self.armies if a.strength > 0]
        self._check_elimination()

    def _check_elimination(self):
        alive = [f for f in self.factions if f.settlements]
        for f in self.factions:
            if not f.settlements and not f.dead:
                f.dead = True
                self._event(f"{f.name} has been eliminated!")
        if len(alive) == 1 and not self._victory:
            self._victory = True
            self._event(f"{alive[0].name} dominates the realm!")

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
        for d in self.directors:        # strategic AI sets stances/orders/expansion
            d.update(dt_days, self)
        self._move_armies(dt_days)
        self._resolve_combat()


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

    # Directors exist with personalities.
    assert len(fw.directors) == len(fw.factions)
    print(f"  directors: {[(f.name, fw.directors[f.id].profile_name) for f in fw.factions]}")

    # Run the world: armies raise/move, directors set stances, factions expand.
    n0 = len(fw.settlements)
    for _ in range(400):
        fw.update(0.2)
    assert fw.armies, "no armies were raised"
    grew = len(fw.settlements) - n0
    stances = {fw.directors[f.id].profile_name: fw.directors[f.id].status()[1]
               for f in fw.factions}
    print(f"  after sim: armies {len(fw.armies)}, settlements {n0}->{len(fw.settlements)} (+{grew} founded)")
    print(f"  hostilities: { {f.name: sorted(fw.directors[f.id].status()[1]) for f in fw.factions} }")
    assert grew >= 0

    # Combat: force two hostile armies into contact -> one is destroyed.
    fa, fb = fw.factions[0], fw.factions[1]
    fa.relations[fb.id] = "hostile"
    fb.relations[fa.id] = "hostile"
    A = Army(0, 0, fa, "Test A", 300)
    B = Army(1, 0, fb, "Test B", 120)
    fw.armies = [A, B]
    fw._resolve_combat()
    survivors = [x for x in fw.armies if x.strength > 0]
    print(f"  battle: 300 vs 120 -> survivors {[(x.faction.name, x.strength) for x in survivors]}")
    assert len(survivors) == 1, "battle did not resolve to one survivor"

    # Troop counters: an equal cavalry army beats an archer army most of the time.
    cav = Army(0, 0, fa, "Cav", 0); cav.composition = {"infantry": 0, "cavalry": 200, "archers": 0}
    arc = Army(0, 0, fb, "Arc", 0); arc.composition = {"infantry": 0, "cavalry": 0, "archers": 200}
    wins = 0
    for _ in range(200):
        ca = Army(0, 0, fa, "c", 0); ca.composition = dict(cav.composition)
        ar = Army(0, 0, fb, "a", 0); ar.composition = dict(arc.composition)
        win, lose = (ca, ar) if fw._power(ca, ar) >= fw._power(ar, ca) else (ar, ca)
        wins += 1 if fw._power(ca, ar) > fw._power(ar, ca) else 0
    print(f"  counters: cavalry power vs archers favors cavalry: {wins>0} "
          f"(cav power {fw._power(cav, arc):.0f} vs arc power {fw._power(arc, cav):.0f})")
    assert fw._power(cav, arc) > fw._power(arc, cav), "troop counters not applied"

    # Conquest: army on an enemy settlement can capture it (territory flips).
    victim = fb.settlements[0]
    before = victim.faction.name
    army = Army(victim.x, victim.y, fa, "Sieger", 5000)
    fw.armies = [army]
    fw._siege(army, victim)
    print(f"  siege: {victim.name} {before} -> {victim.faction.name}")
    assert victim.faction is fa, "capture did not flip ownership"
    assert any("captured" in e for e in fw.events), "no capture event logged"
    print(f"  events: {fw.events[-1]}")
    print("factions selftest OK")


if __name__ == "__main__":
    selftest()
