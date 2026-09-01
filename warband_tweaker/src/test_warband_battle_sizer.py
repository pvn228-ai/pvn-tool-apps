import tempfile
import unittest
import os
import stat
from dataclasses import replace
from pathlib import Path
from unittest import mock

from warband_battle_sizer import (
    apply_config_updates,
    apply_item_updates,
    append_item_records,
    append_troop_records,
    apply_party_template_updates,
    apply_troop_updates,
    battle_continuation_state,
    battle_size_to_value,
    battle_reward_tweaks,
    campaign_time_tweaks,
    clone_module,
    discover_modules,
    format_party_template,
    format_item_record,
    find_terminal_item_sentinel,
    item_type_name,
    module_setting_category,
    normalize_item_id,
    normalize_troop_id,
    rebuild_item_flags,
    rebuild_capabilities,
    normalize_line_endings,
    parse_skills,
    parse_simple_triggers,
    parse_config_entries,
    parse_party_templates,
    parse_item_kinds,
    parse_troop_names,
    parse_troops,
    randomize_troop_face_words,
    recruitment_tweaks,
    rebuild_troop_flags,
    rebuild_troop_skill_words,
    remap_troop_upgrades_after_removal,
    set_battle_continuation,
    set_prisoner_price_tweaks,
    set_recruitment_tweaks,
    set_tavern_prisoner_sales,
    set_tournament_tweaks,
    tavern_prisoner_sales_state,
    tournament_tweaks,
    prisoner_price_tweaks,
    party_tweaks,
    siege_tweaks,
    set_battle_reward_tweaks,
    set_campaign_time_tweaks,
    set_party_tweaks,
    set_siege_tweaks,
    apply_skill_maximums,
    troop_skill_levels,
    troop_face_preset_pool,
    PartyStack,
    PartyTemplateRecord,
    ItemRecord,
    ItemAddition,
    ITEM_FLAG_OPTIONS,
    ITEM_KILL_INFO_MASK,
    CAPABILITY_OPTIONS,
    CAPABILITY_SHOOT_MASK,
    CAPABILITY_CARRY_MASK,
    CAPABILITY_RELOAD_MASK,
    BATTLE_CONTINUATION_TARGETS,
    TROOP_FLAG_OPTIONS,
    BattleSizerApp,
    pack_damage,
    unpack_damage,
    read_config,
    require_unchanged_text,
    replace_battle_size,
    validate_config_value,
    value_to_battle_size,
    write_config,
    write_config_batch,
    write_config_text,
)


class BattleSizerTests(unittest.TestCase):
    def test_known_values(self):
        self.assertEqual(battle_size_to_value(150), 1.0)
        self.assertEqual(battle_size_to_value(300), 2.25)
        self.assertAlmostEqual(battle_size_to_value(1000), 8.0833333333)
        self.assertEqual(value_to_battle_size(3.9167), 500)

    def test_replaces_existing_setting(self):
        updated, value = replace_battle_size("foo = 1\nbattle_size = 1.0000\nbar = 2\n", 500)
        self.assertEqual(value, "3.9167")
        self.assertIn("battle_size = 3.9167", updated)
        self.assertEqual(updated.count("battle_size"), 1)

    def test_appends_missing_setting(self):
        updated, _ = replace_battle_size("foo = 1", 150)
        self.assertEqual(updated.splitlines()[-1], "battle_size = 1.0000")

    def test_writes_backup(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / "rgl_config.txt"
            config.write_text("battle_size = 1.0000\n", encoding="utf-8")
            backup, value = write_config(config, 750, False)
            self.assertTrue(backup.exists())
            self.assertEqual(value, "6.0000")
            self.assertIn("battle_size = 6.0000", config.read_text(encoding="utf-8"))

    def test_parser_keeps_duplicate_keys_by_line(self):
        text = "enable_blood = 1\r\n\r\nenable_blood = 0\r\n"
        entries = parse_config_entries(text)
        self.assertEqual([(entry.line_index, entry.key, entry.value) for entry in entries], [(0, "enable_blood", "1"), (2, "enable_blood", "0")])

    def test_multi_update_preserves_spacing_and_line_endings(self):
        text = "foo   =   1  \r\n\r\nbar = 2.5000\r\n"
        updated = apply_config_updates(text, {0: "7", 2: "3.1250"})
        self.assertEqual(updated, "foo   =   7  \r\n\r\nbar = 3.1250\r\n")

    def test_update_does_not_touch_unselected_duplicate(self):
        text = "same = 1\nsame = 2\n"
        updated = apply_config_updates(text, {1: "9"})
        self.assertEqual(updated, "same = 1\nsame = 9\n")

    def test_rejects_wrong_numeric_type_and_multiline(self):
        self.assertEqual(validate_config_value("2", " 9 "), "9")
        with self.assertRaises(ValueError):
            validate_config_value("2", "2.5")
        with self.assertRaises(ValueError):
            apply_config_updates("foo = 1\n", {0: "1\nbar = 2"})

    def test_general_writer_backups_and_preserves_encoding(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / "rgl_config.txt"
            config.write_bytes("name = café\r\nvalue = 1\r\n".encode("cp1252"))
            text, encoding = read_config(config)
            self.assertEqual(encoding, "cp1252")
            updated = apply_config_updates(text, {1: "5"})
            backup = write_config_text(config, updated, encoding, False)
            self.assertEqual(backup.read_bytes(), "name = café\r\nvalue = 1\r\n".encode("cp1252"))
            self.assertEqual(config.read_bytes(), "name = café\r\nvalue = 5\r\n".encode("cp1252"))

    def test_exact_external_change_guard_catches_comments_and_spacing(self):
        original = "# original comment\nvalue = 1\n"
        require_unchanged_text(original, original, "module.ini")
        with self.assertRaisesRegex(RuntimeError, "module.ini changed outside"):
            require_unchanged_text(original, "# edited comment\nvalue = 1\n", "module.ini")
        with self.assertRaisesRegex(RuntimeError, "module.ini changed outside"):
            require_unchanged_text(original, "# original comment\nvalue  =  1\n", "module.ini")

    def test_failed_write_restores_read_only_state(self):
        with tempfile.TemporaryDirectory() as folder:
            config = Path(folder) / "rgl_config.txt"
            config.write_text("value = 1\n", encoding="ascii")
            os.chmod(config, stat.S_IREAD)
            with self.assertRaises(UnicodeEncodeError):
                write_config_text(config, "value = café\n", "ascii", False)
            self.assertFalse(bool(config.stat().st_mode & stat.S_IWRITE))
            self.assertEqual(config.read_text(encoding="ascii"), "value = 1\n")
            os.chmod(config, stat.S_IWRITE)

    def test_batch_writer_commits_all_files_with_exact_backups(self):
        with tempfile.TemporaryDirectory() as folder:
            first = Path(folder) / "scripts.txt"
            second = Path(folder) / "conversation.txt"
            first.write_bytes(b"scripts original\r\n")
            second.write_bytes(b"conversation original\r\n")
            backups = write_config_batch([
                (first, "scripts updated\r\n", "ascii", False),
                (second, "conversation updated\r\n", "ascii", False),
            ])
            self.assertEqual(first.read_bytes(), b"scripts updated\r\n")
            self.assertEqual(second.read_bytes(), b"conversation updated\r\n")
            self.assertEqual(backups[0].read_bytes(), b"scripts original\r\n")
            self.assertEqual(backups[1].read_bytes(), b"conversation original\r\n")

    def test_batch_writer_rolls_back_every_file_after_late_replace_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            first = Path(folder) / "skills.txt"
            second = Path(folder) / "troops.txt"
            first.write_bytes(b"skills original\n")
            second.write_bytes(b"troops original\n")
            real_replace = os.replace
            replace_calls = 0

            def fail_second_replace(source, destination):
                nonlocal replace_calls
                replace_calls += 1
                if replace_calls == 2:
                    raise OSError("injected second-file failure")
                return real_replace(source, destination)

            with mock.patch("warband_battle_sizer.os.replace", side_effect=fail_second_replace):
                with self.assertRaisesRegex(OSError, "injected second-file failure"):
                    write_config_batch([
                        (first, "skills updated\n", "ascii", False),
                        (second, "troops updated\n", "ascii", False),
                    ])
            self.assertEqual(first.read_bytes(), b"skills original\n")
            self.assertEqual(second.read_bytes(), b"troops original\n")
            self.assertEqual(len(list(Path(folder).glob("*.backup-*"))), 2)

    def test_module_categories_include_tweaks_resources_and_unknowns(self):
        self.assertEqual(module_setting_category("time_multiplier"), "Campaign")
        self.assertEqual(module_setting_category("horse_charge_damage_multiplier"), "Combat")
        self.assertEqual(module_setting_category("load_resource"), "Resources")
        self.assertEqual(module_setting_category("some_mod_specific_key"), "Advanced")

    def test_discovers_only_valid_module_folders(self):
        with tempfile.TemporaryDirectory() as folder:
            install = Path(folder)
            native = install / "Modules" / "Native"
            mod = install / "Modules" / "Example Mod"
            invalid = install / "Modules" / "Not A Module"
            for path in (native, mod, invalid):
                path.mkdir(parents=True)
            native.joinpath("module.ini").write_text("module_name = Native\n", encoding="utf-8")
            mod.joinpath("module.ini").write_text("module_name = Example\n", encoding="utf-8")
            self.assertEqual([path.name for path in discover_modules(install)], ["Example Mod", "Native"])

    def test_clone_module_copies_files_and_changes_only_display_name(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "Modules" / "Native"
            source.mkdir(parents=True)
            source.joinpath("module.ini").write_bytes(
                b"module_name   =   Native\r\nload_resource = test\r\ntime_multiplier = 0.25\r\n"
            )
            source.joinpath("troops.txt").write_text("troopsfile version 2\n0\n", encoding="utf-8")
            destination = root / "Modules" / "Native Tweaked"
            result = clone_module(source, destination, "Native Tweaked")
            self.assertEqual(result, destination.resolve())
            self.assertTrue(destination.joinpath("troops.txt").is_file())
            cloned = destination.joinpath("module.ini").read_bytes()
            self.assertIn(b"module_name   =   Native Tweaked\r\n", cloned)
            self.assertIn(b"load_resource = test\r\n", cloned)
            self.assertIn(b"time_multiplier = 0.25\r\n", cloned)

    def test_clone_rejects_existing_destination_and_nested_clone(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "Native"
            source.mkdir()
            source.joinpath("module.ini").write_text("module_name = Native\n", encoding="utf-8")
            existing = Path(folder) / "Existing"
            existing.mkdir()
            with self.assertRaises(FileExistsError):
                clone_module(source, existing, "Existing")
            with self.assertRaises(ValueError):
                clone_module(source, source / "Nested", "Nested")

    def test_party_template_parser_handles_empty_and_filled_slots(self):
        text = (
            "partytemplatesfile version 1\r\n2\r\n"
            "pt_none none 2 0 1 7 -1 -1 -1 -1 -1 -1 \r\n"
            "pt_looters Looters 9 0 2 312 113 3 45 0 120 1 2 4 -1 -1 -1 -1 \r\n"
        )
        records = parse_party_templates(text)
        self.assertEqual(len(records), 2)
        self.assertEqual(records[0].stacks, ())
        self.assertEqual(records[1].stacks, (PartyStack(113, 3, 45, 0), PartyStack(120, 1, 2, 4)))

    def test_party_template_update_preserves_other_lines_and_crlf(self):
        text = (
            "partytemplatesfile version 1\r\n2\r\n"
            "pt_none none 2 0 1 7 -1 -1 -1 -1 -1 -1 \r\n"
            "pt_looters Looters 9 0 2 312 113 3 45 0 -1 -1 -1 -1 -1 \r\n"
        )
        records = parse_party_templates(text)
        changed = PartyTemplateRecord(records[1].line_index, "pt_looters", "Huge_Looter_Mob", 9, 0, 2, 312, (PartyStack(113, 10, 90, 0),))
        updated = apply_party_template_updates(text, {changed.line_index: changed})
        self.assertEqual(updated.splitlines(keepends=True)[2], text.splitlines(keepends=True)[2])
        self.assertTrue(updated.endswith("-1 -1 -1 -1 -1 \r\n"))
        reparsed = parse_party_templates(updated)
        self.assertEqual(reparsed[1].name, "Huge_Looter_Mob")
        self.assertEqual(reparsed[1].stacks[0].maximum, 90)

    def test_party_template_validation_rejects_bad_ranges_and_too_many_stacks(self):
        base = PartyTemplateRecord(2, "pt_test", "Test", 0, 0, 0, 0, (PartyStack(1, 5, 4, 0),))
        with self.assertRaises(ValueError):
            format_party_template(base)
        too_many = PartyTemplateRecord(2, "pt_test", "Test", 0, 0, 0, 0, tuple(PartyStack(1, 1, 1, 0) for _ in range(7)))
        with self.assertRaises(ValueError):
            format_party_template(too_many)

    def test_troop_name_parser_uses_record_order_as_numeric_index(self):
        text = (
            "troopsfile version 2\n2\n"
            "trp_player Player Player 0 0 0 0 1 0 0\n other data\n\n"
            "trp_looter Looter Looters 0 0 0 0 1 0 0\n other data\n"
        )
        self.assertEqual(parse_troop_names(text), [("trp_player", "Player"), ("trp_looter", "Looter")])

    @staticmethod
    def _troops_fixture(newline="\n"):
        inventory = " ".join(["0", "16777216", *(["-1", "0"] * 63)])
        records = []
        for index, troop_id in enumerate(("trp_player", "trp_looter")):
            records.append(newline.join((
                f"{troop_id} {'Player' if index == 0 else 'Looter'} {'Players' if index == 0 else 'Looters'} 0 {16 if index == 0 else 32768} 0 0 1 0 0",
                f"  {inventory}", "  10 11 12 13 14", " 1 2 3 4 5 6 7",
                "305419896 0 0 0 0 3221225472 ", "  1 2 3 4 5 6 7 8 ",
            )))
        return f"troopsfile version 2{newline}2 {newline}{newline}" + (newline * 2).join(records) + newline

    def test_full_troop_parser_and_lossless_targeted_update(self):
        text = self._troops_fixture("\r\n")
        records = parse_troops(text)
        self.assertEqual(len(records), 2)
        self.assertEqual(len(records[0].inventory), 64)
        self.assertEqual(records[0].inventory[0].modifier, 16777216)
        changed = records[0].__class__(**{**records[0].__dict__, "singular_name": "Commander", "attributes": (30, 20, 15, 12, 25)})
        updated = apply_troop_updates(text, {records[0].line_index: changed})
        reparsed = parse_troops(updated)
        self.assertEqual(reparsed[0].singular_name, "Commander")
        self.assertEqual(reparsed[0].attributes, (30, 20, 15, 12, 25))
        self.assertEqual(reparsed[1], records[1])
        self.assertIn("\r\n", updated)

    def test_troop_id_normalization(self):
        self.assertEqual(normalize_troop_id(" Swadian Knight-Captain "), "trp_swadian_knight_captain")
        self.assertEqual(normalize_troop_id("trp_custom_2"), "trp_custom_2")
        with self.assertRaises(ValueError):
            normalize_troop_id("trp_bad/id")

    def test_append_troop_keeps_existing_indexes_and_crlf(self):
        text = self._troops_fixture("\r\n")
        original = parse_troops(text)
        created = replace(
            original[1], line_index=-1, troop_id="trp_new_guard",
            singular_name="New_Guard", plural_name="New_Guards",
        )
        updated = append_troop_records(text, [created])
        records = parse_troops(updated)
        self.assertEqual(len(records), 3)
        self.assertEqual(updated.splitlines()[1].strip(), "3")
        self.assertEqual(records[:2], original)
        self.assertEqual(records[2].troop_id, "trp_new_guard")
        self.assertNotIn("\n", updated.replace("\r\n", ""))

    def test_append_multiple_troops_preserves_order_and_rejects_duplicate_ids(self):
        text = self._troops_fixture()
        source = parse_troops(text)[0]
        first = replace(source, line_index=-1, troop_id="trp_first_new", singular_name="First", plural_name="Firsts")
        second = replace(source, line_index=-2, troop_id="trp_second_new", singular_name="Second", plural_name="Seconds")
        updated = append_troop_records(text, [first, second])
        self.assertEqual([record.troop_id for record in parse_troops(updated)], ["trp_player", "trp_looter", "trp_first_new", "trp_second_new"])
        with self.assertRaisesRegex(ValueError, "already exists"):
            append_troop_records(text, [replace(first, troop_id="trp_player")])
        with self.assertRaisesRegex(ValueError, "already exists"):
            append_troop_records(text, [first, replace(second, troop_id="trp_first_new")])

    def test_removing_new_troop_remaps_later_upgrade_indexes_and_blocks_direct_refs(self):
        source = parse_troops(self._troops_fixture())[0]
        later = replace(source, troop_id="trp_later", upgrade_one=4, upgrade_two=1)
        remapped = remap_troop_upgrades_after_removal(later, 2)
        self.assertEqual((remapped.upgrade_one, remapped.upgrade_two), (3, 1))
        with self.assertRaisesRegex(ValueError, "upgrade path"):
            remap_troop_upgrades_after_removal(replace(later, upgrade_two=2), 2)

    def test_troop_skills_and_flags_preserve_unknown_bits(self):
        words = (0, 0, 0, 0, 0, 0xC0000000)
        levels = list(troop_skill_levels(words))
        levels[0], levels[36] = 7, 12
        rebuilt = rebuild_troop_skill_words(words, tuple(levels))
        self.assertEqual(troop_skill_levels(rebuilt)[0], 7)
        self.assertEqual(troop_skill_levels(rebuilt)[36], 12)
        self.assertEqual(rebuilt[5] & 0xFC000000, 0xC0000000)
        option_bits = {key: bit for key, _label, bit in TROOP_FLAG_OPTIONS}
        flags = rebuild_troop_flags(0x40000000, 1, {"hero", "guarantee_armor"})
        self.assertEqual(flags & 0x40000000, 0x40000000)
        self.assertTrue(flags & option_bits["hero"])
        self.assertTrue(flags & option_bits["guarantee_armor"])

    def test_face_randomizer_uses_valid_same_type_module_presets(self):
        records = parse_troops(self._troops_fixture())
        pool = troop_face_preset_pool(records, 0)
        self.assertEqual([entry[1] for entry in pool], [(1, 2, 3, 4), (5, 6, 7, 8)])
        pick_first = lambda choices: choices[0]
        ranged, donors, pool_size = randomize_troop_face_words(records, 0, records[0].face_words, chooser=pick_first)
        self.assertEqual(ranged, (5, 6, 7, 8, 1, 2, 3, 4))
        self.assertEqual(pool_size, 2)
        self.assertNotEqual(donors[0], donors[1])
        fixed, fixed_donors, _ = randomize_troop_face_words(records, 0, records[0].face_words, fixed=True, chooser=pick_first)
        self.assertEqual(fixed[:4], fixed[4:])
        self.assertEqual(fixed_donors[0], fixed_donors[1])
        with self.assertRaises(ValueError):
            randomize_troop_face_words(records, 1, records[0].face_words, chooser=pick_first)

    def test_troop_choice_falls_back_to_parsed_records_before_party_cache_loads(self):
        records = parse_troops(self._troops_fixture())
        holder = type("TroopChoiceHolder", (), {"troop_names": [], "troop_records": records})()
        self.assertEqual(BattleSizerApp._troop_choice(holder, 1), "1: trp_looter — Looter")

    def test_battle_continuation_patch_is_reversible_and_guarded(self):
        text = ""
        for name in sorted(BATTLE_CONTINUATION_TARGETS):
            text += f"{name} Example 0 0\r\n 1.000000 4.000000 100000000.000000 1 1006 0 3 1 2 3\r\n"
        self.assertEqual(battle_continuation_state(text), ("disabled", 8))
        enabled = set_battle_continuation(text, True)
        self.assertEqual(battle_continuation_state(enabled), ("enabled", 8))
        self.assertEqual(set_battle_continuation(enabled, False), text)
        partial = text.split("mst_", 1)[0] + "mst_" + text.split("mst_", 1)[1].replace("1 1006 0", "1 9999 0", 1)
        self.assertEqual(battle_continuation_state(partial)[0], "unsupported")
        with self.assertRaises(ValueError):
            set_battle_continuation(partial, True)

    @staticmethod
    def _gameplay_scripts_fixture(newline="\n"):
        local = 1224979098644774912
        relation = local + 1
        upper = local + 2
        return newline.join((
            "scriptsfile version 1", "5",
            "change_troop_renown -1", " 0",
            "update_volunteer_troops_in_village -1",
            f" 10 2133 2 {upper} 8 4 0 30 2 {relation} 4 2133 2 {upper} {relation} 2108 2 {upper} 2 2105 2 {upper} 6 5 0 2133 2 {upper} 0 3 0 2107 2 {upper} 3",
            "village_recruit_volunteers_recruit -1",
            f" 2 2123 3 {local + 3} {local + 4} 10 2122 3 {local + 5} {local + 6} 10",
            "update_mercenary_units_of_towns -1",
            f" 1 2136 3 {local + 7} 3 8",
            "game_get_prisoner_price -1",
            f" 7 2171 2 {local + 8} {local + 9} 2133 2 {local + 10} {local + 8} 2105 2 {local + 10} 10 2107 2 {local + 10} {local + 10} 2108 2 {local + 10} 6 5 0 2133 2 {local + 10} 50",
            "",
        ))

    @staticmethod
    def _gameplay_menus_fixture(newline="\n"):
        local = 1224979098644774912
        global_temp = 144115188075856007
        player = 360287970189639680
        reg9 = 72057594037927945
        script_ref = 936748722493063168
        return newline.join((
            "menusfile version 1", "2",
            "menu_tournament_bet 0 Bet none 0 2",
            f" mno_bet_100_denars  1 30 2 {local} 100  100_denars.  1 2133 2 {global_temp} 100  .  mno_bet_50_denars  1 30 2 {local} 50  50_denars.  1 2133 2 {global_temp} 50  . ",
            f"menu_town_tournament_won 0 Won none 3 2133 2 {reg9} 200 1062 2 250 {player} 1 3 {script_ref} {player} 20 0",
            "",
        ))

    def test_tournament_bets_prize_renown_and_xp_are_guarded_and_reversible(self):
        scripts = self._gameplay_scripts_fixture("\r\n")
        menus = self._gameplay_menus_fixture("\r\n")
        self.assertEqual(tournament_tweaks(menus, scripts), {"bet_amounts": (100, 50), "prize": 200, "renown": 20, "xp": 250})
        updated = set_tournament_tweaks(menus, scripts, (1000, 250), 750, 35, 900)
        self.assertEqual(tournament_tweaks(updated, scripts), {"bet_amounts": (1000, 250), "prize": 750, "renown": 35, "xp": 900})
        self.assertNotIn("\n", updated.replace("\r\n", ""))
        self.assertEqual(set_tournament_tweaks(updated, scripts, (100, 50), 200, 20, 250), menus)
        with self.assertRaises(ValueError):
            set_tournament_tweaks(menus, scripts, (100,), 200, 20, 250)

    def test_recruitment_and_mercenary_amounts_round_trip(self):
        scripts = self._gameplay_scripts_fixture()
        original = {"village_base": 8, "village_relation_bonus": 6, "village_multiplier": 3, "village_price": 10, "mercenary_min": 3, "mercenary_max": 7}
        self.assertEqual(recruitment_tweaks(scripts), original)
        requested = {"village_base": 20, "village_relation_bonus": 12, "village_multiplier": 5, "village_price": 3, "mercenary_min": 8, "mercenary_max": 15}
        updated = set_recruitment_tweaks(scripts, requested)
        self.assertEqual(recruitment_tweaks(updated), requested)
        self.assertEqual(set_recruitment_tweaks(updated, original), scripts)

    def test_prisoner_price_formula_round_trips(self):
        scripts = self._gameplay_scripts_fixture()
        original = {"prisoner_level_bonus": 10, "prisoner_divisor": 6, "prisoner_minimum": 50}
        requested = {"prisoner_level_bonus": 20, "prisoner_divisor": 4, "prisoner_minimum": 100}
        self.assertEqual(prisoner_price_tweaks(scripts), original)
        updated = set_prisoner_price_tweaks(scripts, requested)
        self.assertEqual(prisoner_price_tweaks(updated), requested)
        self.assertEqual(set_prisoner_price_tweaks(updated, original), scripts)

    @staticmethod
    def _siege_menus_fixture(newline="\n"):
        local = 1224979098644774912
        return newline.join((
            "menusfile version 1", "2",
            f"menu_construct_ladders 0 Ladders none 3 2121 3 {local} 14 {local + 1} 2107 2 {local} 2 2108 2 {local} 3 1",
            f" mno_build_ladders_cont 0 Build. 3 2121 3 {local + 2} 14 {local + 3} 2107 2 {local + 2} 2 2108 2 {local + 2} 3 .",
            f"menu_construct_siege_tower 0 Tower none 2 2121 3 {local} 15 {local + 1} 2107 2 {local} 6 1",
            f" mno_build_siege_tower_cont 0 Build. 2 2121 3 {local + 2} 15 {local + 3} 2107 2 {local + 2} 6 .",
            "",
        ))

    def test_siege_display_and_action_formulas_round_trip(self):
        text = self._siege_menus_fixture("\r\n")
        original = {"ladder_skill_base": 14, "ladder_time_multiplier": 2, "ladder_time_divisor": 3, "tower_skill_base": 15, "tower_time_multiplier": 6}
        requested = {"ladder_skill_base": 20, "ladder_time_multiplier": 4, "ladder_time_divisor": 5, "tower_skill_base": 18, "tower_time_multiplier": 3}
        self.assertEqual(siege_tweaks(text), original)
        updated = set_siege_tweaks(text, requested)
        self.assertEqual(siege_tweaks(updated), requested)
        self.assertNotIn("\n", updated.replace("\r\n", ""))
        self.assertEqual(set_siege_tweaks(updated, original), text)

    @staticmethod
    def _party_reward_scripts_fixture(newline="\n"):
        local = 1224979098644774912
        reg0 = 72057594037927936
        return newline.join((
            "scriptsfile version 1", "3",
            "game_get_party_companion_limit -1",
            f" 9 2133 2 {local} 30 2170 3 {local + 1} 1 {local + 2} 2172 3 {local + 3} {local + 2} 3 2107 2 {local + 1} 5 2105 2 {local} {local + 1} 2105 2 {local} {local + 3} 520 3 {local + 4} {local + 2} 7 2123 3 {local + 5} {local + 4} 25 2105 2 {local} {local + 5}",
            "calculate_player_faction_wage -1",
            f" 4 2108 2 {local} 2 2121 3 {local + 1} 14 {local + 2} 2107 2 {local + 3} {local + 1} 2108 2 {local + 3} 14",
            "party_give_xp_and_gold -1",
            f" 17 2120 3 {local} {local + 1} 10 2108 2 {local} 10 2122 3 {local + 2} {local} {local + 3} 2105 2 {local + 4} {local + 2} 2110 2 {local + 4} 40000 2133 2 {local + 5} {local + 4} 2136 3 {local + 6} 50 100 2107 2 {local + 5} {local + 6} 2108 2 {local + 5} 100 1674 2 1 {local + 5} 2122 3 {local + 7} {local + 4} 10 2110 2 {local + 7} 60000 2136 3 {local + 6} 50 100 2107 2 {local + 7} {local + 6} 2108 2 {local + 7} 100 2108 2 {local + 7} {local + 8} 2133 2 {reg0} {local + 7}",
            "",
        ))

    def test_party_size_and_garrison_wage_rules_round_trip(self):
        text = self._party_reward_scripts_fixture()
        original = {"party_base_size": 30, "party_renown_divisor": 25, "garrison_wage_divisor": 2}
        requested = {"party_base_size": 75, "party_renown_divisor": 10, "garrison_wage_divisor": 4}
        self.assertEqual(party_tweaks(text), original)
        updated = set_party_tweaks(text, requested)
        self.assertEqual(party_tweaks(updated), requested)
        self.assertEqual(set_party_tweaks(updated, original), text)

    def test_post_battle_gold_and_xp_rules_round_trip(self):
        text = self._party_reward_scripts_fixture()
        original = {"battle_level_bonus": 10, "battle_gain_divisor": 10, "battle_gold_share": 10, "battle_gold_cap": 60000, "battle_gold_roll_min": 50, "battle_gold_roll_max": 100, "battle_gold_divisor": 100, "battle_xp_roll_min": 50, "battle_xp_roll_max": 100, "battle_xp_divisor": 100}
        requested = {"battle_level_bonus": 20, "battle_gain_divisor": 5, "battle_gold_share": 15, "battle_gold_cap": 120000, "battle_gold_roll_min": 100, "battle_gold_roll_max": 151, "battle_gold_divisor": 50, "battle_xp_roll_min": 75, "battle_xp_roll_max": 126, "battle_xp_divisor": 80}
        self.assertEqual(battle_reward_tweaks(text), original)
        updated = set_battle_reward_tweaks(text, requested)
        self.assertEqual(battle_reward_tweaks(updated), requested)
        self.assertEqual(set_battle_reward_tweaks(updated, original), text)

    @staticmethod
    def _campaign_scripts_and_triggers_fixture(newline="\n"):
        local = 1224979098644774912
        script_base = 936748722493063168
        scripts = newline.join((
            "scriptsfile version 1", "3",
            "consume_food -1", " 0",
            "update_mercenary_units_of_towns -1", " 0",
            "update_volunteer_troops_in_village -1", " 0", "",
        ))
        fief_ops = (
            f"2133 2 {local} 0 4 0 541 3 {local + 1} 0 4 4 0 541 3 {local + 1} 35 0 2133 2 {local} 1200 3 0 "
            f"5 0 541 3 {local + 1} 0 2 2133 2 {local} 1200 5 0 541 3 {local + 1} 0 3 2133 2 {local} 2400 3 0 "
            f"521 3 {local + 2} {local + 1} 50 2120 3 {local + 3} 20 {local + 2} 2107 2 {local} {local + 3} 2108 2 {local} 120"
        )
        triggers = newline.join((
            "simple_triggers_file version 1", "3",
            f"168.000000 18 {fief_ops}",
            f"14.000000 2 2108 2 {local} 3 1 1 {script_base}",
            f"72.000000 2 1 1 {script_base + 1} 1 2 {script_base + 2} {local + 1}",
            "",
        ))
        return scripts, triggers

    def test_fief_income_food_and_refresh_clocks_round_trip(self):
        scripts, text = self._campaign_scripts_and_triggers_fixture("\r\n")
        original = {"village_rent": 1200, "castle_rent": 1200, "town_rent": 2400, "prosperity_base": 20, "prosperity_divisor": 120, "fief_interval_hours": 168.0, "food_interval_hours": 14.0, "food_troops_per_unit": 3, "refresh_interval_hours": 72.0}
        requested = {"village_rent": 2000, "castle_rent": 1800, "town_rent": 5000, "prosperity_base": 40, "prosperity_divisor": 100, "fief_interval_hours": 120.0, "food_interval_hours": 20.5, "food_troops_per_unit": 5, "refresh_interval_hours": 48.0}
        self.assertEqual(len(parse_simple_triggers(text)), 3)
        self.assertEqual(campaign_time_tweaks(text, scripts), original)
        updated = set_campaign_time_tweaks(text, scripts, requested)
        self.assertEqual(campaign_time_tweaks(updated, scripts), requested)
        self.assertNotIn("\n", updated.replace("\r\n", ""))
        self.assertEqual(set_campaign_time_tweaks(updated, scripts, original), text)

    def test_tavern_keeper_prisoner_sales_toggle_updates_count_and_is_reversible(self):
        text = (
            "dialogsfile version 2\r\n2\r\n"
            "dlga_ransom_broker_talk:ransom_broker_sell_prisoners 69631 965 2 2159 1 72057594037927936 30 2 72057594037927936 1 Sell. 966 0 NO_VOICEOVER\r\n"
            "dlga_tavernkeeper_talk:close_window 69631 946 0 Leave. 6 0 NO_VOICEOVER\r\n"
        )
        self.assertEqual(tavern_prisoner_sales_state(text), "disabled")
        enabled = set_tavern_prisoner_sales(text, True)
        self.assertEqual(tavern_prisoner_sales_state(enabled), "enabled")
        self.assertEqual(enabled.splitlines()[1], "3")
        self.assertIn("I_have_prisoners_to_sell.", enabled)
        self.assertEqual(set_tavern_prisoner_sales(enabled, False), text)

    def test_skill_maximum_editor_preserves_flags_descriptions_and_crlf(self):
        text = "2\r\nskl_trade Trade 19 10 Trade_description\r\nskl_leadership Leadership 3 10 Leadership_description\r\n"
        records = parse_skills(text)
        updated = apply_skill_maximums(text, {records[1].line_index: 15})
        changed = parse_skills(updated)
        self.assertEqual(changed[0], records[0])
        self.assertEqual((changed[1].flags, changed[1].max_level, changed[1].description), (3, 15, "Leadership_description"))
        self.assertNotIn("\n", updated.replace("\r\n", ""))

    def test_raw_editor_line_ending_normalization_is_reversible(self):
        mixed = "one\r\ntwo\nthree\rfour\r\n"
        self.assertEqual(normalize_line_endings(mixed, "\n"), "one\ntwo\nthree\nfour\n")
        self.assertEqual(normalize_line_endings(mixed, "\r\n"), "one\r\ntwo\r\nthree\r\nfour\r\n")
        self.assertEqual(normalize_line_endings("last line has no newline", "\r\n"), "last line has no newline")
        with self.assertRaises(ValueError):
            normalize_line_endings("text", "invalid")

    def test_item_parser_reads_meshes_factions_and_trigger_blocks(self):
        text = (
            "itemsfile version 3\r\n2\r\n"
            " itm_sword Test_Sword Test_Swords 1 sword_mesh 0 2 3 100 4 1.500000 90 0 0 0 5 120 95 0 100 0 275 523\r\n"
            " 0\r\n0\r\n\r\n"
            " itm_armor Test_Armor Test_Armors 1 armor_mesh 0 13 0 500 0 12.000000 80 2 40 15 7 0 0 0 0 0 0 0\r\n"
            " 2\r\n 16 17\r\n1\r\n-50.000000 1 1 0\r\n"
        )
        items = parse_item_kinds(text)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].item_id, "itm_sword")
        self.assertEqual(item_type_name(items[0].item_flags), "One-handed weapon")
        self.assertEqual(items[1].factions, (16, 17))
        self.assertEqual(items[1].trigger_count, 1)

    def test_item_update_preserves_factions_triggers_and_other_records(self):
        text = (
            "itemsfile version 3\n2\n"
            " itm_sword Test_Sword Test_Swords 1 sword_mesh 0 2 3 100 4 1.500000 90 0 0 0 5 120 95 0 100 0 275 523\n"
            " 0\n0\n\n"
            " itm_armor Test_Armor Test_Armors 1 armor_mesh 0 13 0 500 0 12.000000 80 2 40 15 7 0 0 0 0 0 0 0\n"
            " 2\n 16 17\n1\n-50.000000 1 1 0\n"
        )
        first, second = parse_item_kinds(text)
        changed = ItemRecord(
            first.line_index, first.item_id, "Fine_Sword", "Fine_Swords", first.meshes,
            first.item_flags, first.capabilities, 750, first.modifiers, 1.25, first.abundance,
            first.head_armor, first.body_armor, first.leg_armor, first.difficulty, first.hit_points,
            110, first.missile_speed, 115, first.max_ammo, pack_damage(30, 1), pack_damage(36, 0),
            first.factions, first.trigger_count,
        )
        updated = apply_item_updates(text, {first.line_index: changed})
        reparsed = parse_item_kinds(updated)
        self.assertEqual(reparsed[0].value, 750)
        self.assertEqual(unpack_damage(reparsed[0].swing_damage), (36, 0))
        self.assertEqual(reparsed[1], second)
        self.assertIn("-50.000000 1 1 0\n", updated)

    def test_damage_packing_and_item_validation(self):
        for amount, damage_type in ((0, 0), (35, 1), (255, 2)):
            self.assertEqual(unpack_damage(pack_damage(amount, damage_type)), (amount, damage_type))
        with self.assertRaises(ValueError):
            pack_damage(256, 0)
        with self.assertRaises(ValueError):
            pack_damage(10, 4)

    def test_clone_inserts_before_last_end_marker_and_keeps_existing_indexes(self):
        def row(item_id, name, value=1):
            return f" {item_id} {name} {name} 1 mesh 0 11 0 {value} 0 1.000000 100 0 0 0 0 0 0 0 0 0 0 0\n 0\n0\n\n"

        text = "itemsfile version 3\n4\n" + row("itm_base", "Base", 10) + row("itm_items_end", "Items_End") + row("itm_modded", "Modded", 20) + row("itm_ccoop_new_items_end", "Items_End")
        original = parse_item_kinds(text)
        base = original[0]
        clone = ItemRecord(
            -1, "itm_base_copy", "Base_Copy", "Base_Copies", base.meshes, base.item_flags,
            base.capabilities, 25, base.modifiers, base.weight, base.abundance, base.head_armor,
            base.body_armor, base.leg_armor, base.difficulty, base.hit_points, base.speed_rating,
            base.missile_speed, base.weapon_length, base.max_ammo, base.thrust_damage,
            base.swing_damage, base.factions, base.trigger_count,
        )
        updated = append_item_records(text, [ItemAddition(clone, "itm_base")])
        records = parse_item_kinds(updated)
        self.assertEqual(len(records), 5)
        self.assertEqual(updated.splitlines()[1], "5")
        self.assertEqual([record.item_id for record in records[:3]], ["itm_base", "itm_items_end", "itm_modded"])
        self.assertEqual(records[-2].item_id, "itm_base_copy")
        self.assertEqual(find_terminal_item_sentinel(records).item_id, "itm_ccoop_new_items_end")

    def test_create_blank_item_and_reject_duplicate_or_missing_sentinel(self):
        text = (
            "itemsfile version 3\n1\n"
            " itm_items_end Items_End Items_End 1 shield_round_a 0 0 0 1 0 0.000000 100 0 0 0 0 0 0 0 0 0 0 0\n 0\n0\n\n"
        )
        end = parse_item_kinds(text)[0]
        created = ItemRecord(-1, "itm_new_goods", "New_Goods", "New_Goods", end.meshes, 11, 0, 100, 0, 1.0, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, (), 0)
        updated = append_item_records(text, [ItemAddition(created)])
        self.assertEqual([record.item_id for record in parse_item_kinds(updated)], ["itm_new_goods", "itm_items_end"])
        with self.assertRaises(ValueError):
            append_item_records(updated, [ItemAddition(created)])
        without_end = text.replace("itm_items_end Items_End Items_End", "itm_regular Regular Regular")
        with self.assertRaises(ValueError):
            append_item_records(without_end, [ItemAddition(created)])

    def test_clone_preserves_factions_and_trigger_operation_lines(self):
        text = (
            "itemsfile version 3\n2\n"
            " itm_triggered Triggered Triggered 1 mesh 0 13 0 50 0 2.000000 100 0 20 5 0 0 0 0 0 0 0 0\n"
            " 2\n 16 17\n1\n-50.000000 1 1 0\n\n"
            " itm_items_end Items_End Items_End 1 shield 0 0 0 1 0 0.000000 100 0 0 0 0 0 0 0 0 0 0 0\n 0\n0\n\n"
        )
        source = parse_item_kinds(text)[0]
        clone = ItemRecord(
            -1, "itm_triggered_copy", "Triggered_Copy", "Triggered_Copies", source.meshes,
            source.item_flags, source.capabilities, source.value, source.modifiers, source.weight,
            source.abundance, source.head_armor, source.body_armor, source.leg_armor,
            source.difficulty, source.hit_points, source.speed_rating, source.missile_speed,
            source.weapon_length, source.max_ammo, source.thrust_damage, source.swing_damage,
            source.factions, source.trigger_count,
        )
        updated = append_item_records(text, [ItemAddition(clone, source.item_id)])
        cloned = parse_item_kinds(updated)[1]
        self.assertEqual(cloned.factions, (16, 17))
        self.assertEqual(cloned.trigger_count, 1)
        self.assertEqual(updated.count("-50.000000 1 1 0"), 2)

    def test_clone_uses_exact_source_line_when_native_item_ids_are_duplicated(self):
        def row(mesh):
            return f" itm_duplicate Duplicate Duplicate 1 {mesh} 0 11 0 1 0 1.000000 100 0 0 0 0 0 0 0 0 0 0 0\n 0\n0\n\n"

        end = " itm_items_end Items_End Items_End 1 shield 0 0 0 1 0 0.000000 100 0 0 0 0 0 0 0 0 0 0 0\n 0\n0\n\n"
        text = "itemsfile version 3\n3\n" + row("first_mesh") + row("second_mesh") + end
        source = parse_item_kinds(text)[0]
        clone = replace(source, line_index=-1, item_id="itm_duplicate_copy", singular_name="Duplicate_Copy", plural_name="Duplicate_Copies")
        updated = append_item_records(text, [ItemAddition(clone, source.item_id, source.line_index)])
        cloned = next(record for record in parse_item_kinds(updated) if record.item_id == "itm_duplicate_copy")
        self.assertEqual(cloned.meshes[0].name, "first_mesh")
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            append_item_records(text, [ItemAddition(clone, source.item_id)])

    def test_item_id_normalization(self):
        self.assertEqual(normalize_item_id("New Great-Sword"), "itm_new_great_sword")
        self.assertEqual(normalize_item_id("ITM_Already_Good"), "itm_already_good")
        with self.assertRaises(ValueError):
            normalize_item_id("bad/id")

    def test_named_flag_rebuild_round_trips_and_preserves_unknown_bits(self):
        unknown_bit = 0x0000000200000000
        flags = 2 | 0xF00 | 0x10000 | 0x200000 | 0x1000000 | (3 << 56) | unknown_bit
        enabled = {key for key, _label, bit, _help in ITEM_FLAG_OPTIONS if flags & bit}
        rebuilt = rebuild_item_flags(flags, flags & 0xFF, flags & 0xF00, (flags & ITEM_KILL_INFO_MASK) >> 56, enabled)
        self.assertEqual(rebuilt, flags)
        rebuilt_without_merchandise = rebuild_item_flags(flags, 2, 0xF00, 3, enabled - {"merchandise"})
        self.assertEqual(rebuilt_without_merchandise & 0x10000, 0)
        self.assertEqual(rebuilt_without_merchandise & unknown_bit, unknown_bit)

    def test_named_capability_rebuild_round_trips_masks_and_unknown_bits(self):
        unknown_bit = 0x02000000
        capabilities = 0x1 | 0x8 | 0x30000 | 0x110000000 | 0x7000000000 | 0x8000000000000000 | unknown_bit
        enabled = {key for key, _label, bit, _help in CAPABILITY_OPTIONS if capabilities & bit}
        rebuilt = rebuild_capabilities(
            capabilities, capabilities & CAPABILITY_SHOOT_MASK, capabilities & CAPABILITY_CARRY_MASK,
            capabilities & CAPABILITY_RELOAD_MASK, enabled,
        )
        self.assertEqual(rebuilt, capabilities)
        changed = rebuild_capabilities(capabilities, 0x80000, 0x160000000, 0x8000000000, enabled)
        self.assertEqual(changed & CAPABILITY_SHOOT_MASK, 0x80000)
        self.assertEqual(changed & CAPABILITY_CARRY_MASK, 0x160000000)
        self.assertEqual(changed & CAPABILITY_RELOAD_MASK, 0x8000000000)
        self.assertEqual(changed & unknown_bit, unknown_bit)


if __name__ == "__main__":
    unittest.main()
