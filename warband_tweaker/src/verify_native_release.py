"""Read-only release audit for the stock Warband Native module."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

import warband_battle_sizer as tweaker


EXPECTED_COUNTS = {
    "troops": 1078,
    "party_templates": 63,
    "items": 624,
    "factions": 34,
    "skills": 42,
    "text_files": 35,
}

EXPECTED_DUPLICATE_ITEM_IDS = {
    "itm_tutorial_spear", "itm_tutorial_club", "itm_tutorial_battle_axe",
    "itm_tutorial_arrows", "itm_tutorial_bolts", "itm_tutorial_short_bow",
    "itm_tutorial_crossbow", "itm_tutorial_throwing_daggers",
    "itm_tutorial_saddle_horse", "itm_tutorial_shield",
    "itm_tutorial_staff_no_attack", "itm_tutorial_staff", "itm_tutorial_sword",
    "itm_tutorial_axe", "itm_voulge",
}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


def audit_native(module_dir: Path) -> dict[str, int]:
    module_dir = module_dir.expanduser().resolve()
    require(module_dir.name.casefold() == "native", f"Expected the stock Native module, got: {module_dir}")
    require((module_dir / "module.ini").is_file(), f"module.ini was not found in: {module_dir}")

    def load(filename: str) -> str:
        path = module_dir / filename
        require(path.is_file(), f"Required Native file is missing: {filename}")
        return tweaker.read_config(path)[0]

    module_ini = load("module.ini")
    troops_text = load("troops.txt")
    parties_text = load("party_templates.txt")
    items_text = load("item_kinds1.txt")
    factions_text = load("factions.txt")
    skills_text = load("skills.txt")
    menus_text = load("menus.txt")
    scripts_text = load("scripts.txt")
    simple_text = load("simple_triggers.txt")
    conversation_text = load("conversation.txt")
    mission_text = load("mission_templates.txt")

    module_entries = tweaker.parse_config_entries(module_ini)
    require(any(entry.key.casefold() == "module_name" and entry.value.casefold() == "calradia" for entry in module_entries), "module.ini does not identify the stock Native campaign as Calradia.")
    troops = tweaker.parse_troops(troops_text)
    parties = tweaker.parse_party_templates(parties_text)
    items = tweaker.parse_item_kinds(items_text)
    factions = tweaker.parse_faction_names(factions_text)
    skills = tweaker.parse_skills(skills_text)

    counts = {
        "troops": len(troops),
        "party_templates": len(parties),
        "items": len(items),
        "factions": len(factions),
        "skills": len(skills),
        "text_files": len(list(module_dir.glob("*.txt"))),
    }
    require(counts == EXPECTED_COUNTS, f"Native record counts differ from the audited 1.174 layout: {counts}")
    require(len({record.troop_id for record in troops}) == len(troops), "troops.txt contains duplicate troop IDs.")
    require(len({record.template_id for record in parties}) == len(parties), "party_templates.txt contains duplicate IDs.")
    duplicate_items = {item_id for item_id, count in Counter(record.item_id for record in items).items() if count > 1}
    require(duplicate_items == EXPECTED_DUPLICATE_ITEM_IDS, f"Native's known duplicate item-ID set changed: {sorted(duplicate_items)}")
    require(tweaker.find_terminal_item_sentinel(items) is not None, "item_kinds1.txt has no safe terminal item marker.")

    for record in troops:
        tweaker.validate_troop_record(record, len(troops), len(items))
        require(0 <= record.faction < len(factions), f"{record.troop_id} has an invalid faction index.")
    for record in parties:
        tweaker.validate_party_template(record, len(troops))
        require(0 <= record.faction < len(factions), f"{record.template_id} has an invalid faction index.")

    rewritten_troops = tweaker.apply_troop_updates(troops_text, {record.line_index: record for record in troops})
    rewritten_parties = tweaker.apply_party_template_updates(parties_text, {record.line_index: record for record in parties})
    rewritten_items = tweaker.apply_item_updates(items_text, {record.line_index: record for record in items})
    require(tweaker.parse_troops(rewritten_troops) == troops, "Troop serialization changed parsed Native data.")
    require(tweaker.parse_party_templates(rewritten_parties) == parties, "Party-template serialization changed parsed Native data.")
    require(tweaker.parse_item_kinds(rewritten_items) == items, "Item serialization changed parsed Native data.")

    continuation_state, continuation_count = tweaker.battle_continuation_state(mission_text)
    require((continuation_state, continuation_count) == ("disabled", 8), "Native battle-continuation signatures do not match the audited layout.")
    require(tweaker.set_battle_continuation(mission_text, False) == mission_text, "Battle-continuation no-op was not lossless.")

    tournament = tweaker.tournament_tweaks(menus_text, scripts_text)
    require(tweaker.set_tournament_tweaks(menus_text, scripts_text, tuple(tournament["bet_amounts"]), int(tournament["prize"]), int(tournament["renown"]), int(tournament["xp"])) == menus_text, "Tournament tweak round-trip failed.")
    recruitment = tweaker.recruitment_tweaks(scripts_text)
    require(tweaker.set_recruitment_tweaks(scripts_text, recruitment) == scripts_text, "Recruitment tweak round-trip failed.")
    prisoner = tweaker.prisoner_price_tweaks(scripts_text)
    require(tweaker.set_prisoner_price_tweaks(scripts_text, prisoner) == scripts_text, "Prisoner-price tweak round-trip failed.")
    siege = tweaker.siege_tweaks(menus_text)
    require(tweaker.set_siege_tweaks(menus_text, siege) == menus_text, "Siege tweak round-trip failed.")
    party_rules = tweaker.party_tweaks(scripts_text)
    require(tweaker.set_party_tweaks(scripts_text, party_rules) == scripts_text, "Party-size tweak round-trip failed.")
    rewards = tweaker.battle_reward_tweaks(scripts_text)
    require(tweaker.set_battle_reward_tweaks(scripts_text, rewards) == scripts_text, "Battle-reward tweak round-trip failed.")
    clocks = tweaker.campaign_time_tweaks(simple_text, scripts_text)
    require(tweaker.set_campaign_time_tweaks(simple_text, scripts_text, clocks) == simple_text, "Campaign-time tweak round-trip failed.")
    tavern_state = tweaker.tavern_prisoner_sales_state(conversation_text)
    require(tavern_state in {"enabled", "disabled"}, "Tavern-prisoner signature is unsupported.")
    require(tweaker.set_tavern_prisoner_sales(conversation_text, tavern_state == "enabled") == conversation_text, "Tavern-prisoner tweak round-trip failed.")
    skill_roundtrip = tweaker.apply_skill_maximums(skills_text, {record.line_index: record.max_level for record in skills})
    require(tweaker.parse_skills(skill_roundtrip) == skills, "Skill serialization changed parsed Native data.")
    return counts


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the read-only PVN's Warband Tweaker Native release audit.")
    parser.add_argument("module", nargs="?", type=Path, default=Path(r"C:\Program Files (x86)\Mount&Blade Warband\Modules\Native"))
    args = parser.parse_args()
    counts = audit_native(args.module)
    print("Native 1.174 audit passed (read-only).")
    print(", ".join(f"{name.replace('_', ' ')}: {value}" for name, value in counts.items()))
    print("All structured serializers and guarded gameplay tweak signatures round-trip successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
