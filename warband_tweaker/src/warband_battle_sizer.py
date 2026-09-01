from __future__ import annotations

import os
import re
import secrets
import shutil
import stat
import tempfile
from dataclasses import dataclass, replace
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk


APP_NAME = "PVN's Warband Tweaker"
APP_VERSION = "1.0.0"
APP_TITLE = f"{APP_NAME} v{APP_VERSION}"
CONFIG_PATTERN = re.compile(r"^(\s*battle_size\s*=\s*)([-+]?\d*\.?\d+)([ \t]*)(\r?\n)?$", re.IGNORECASE | re.MULTILINE)
CONFIG_LINE_PATTERN = re.compile(r"^(\s*)([A-Za-z_][A-Za-z0-9_]*)(\s*=\s*)(.*?)([ \t]*)(\r?\n)?$")

SETTING_HELP = {
    "battle_size": "Maximum troops active on the battlefield. Use the Battle Size tab for troop-based conversion.",
    "max_framerate": "Frame-rate limit used by the game.",
    "start_windowed": "Launch in a window instead of exclusive fullscreen.",
    "texture_detail": "Texture quality percentage.",
    "render_buffer_size": "Rendering buffer setting. Large changes can affect stability.",
    "force_vsync": "Synchronize frames with the monitor to reduce tearing.",
    "antialiasing": "Anti-aliasing sample level.",
    "shadowmap_quality": "Shadow-map quality preset.",
    "shader_quality": "Shader quality preset.",
    "music_volume": "Music volume, normally from 0.0000 to 1.0000.",
    "sound_volume": "Sound-effect volume, normally from 0.0000 to 1.0000.",
    "mouse_sensitivity": "Mouse sensitivity multiplier.",
    "number_of_corpses": "Number of corpses retained on the battlefield.",
    "number_of_ragdolls": "Number of active ragdolls.",
    "grass_density": "Battlefield grass density percentage.",
    "combat_speed": "Combat animation speed preset.",
    "combat_difficulty": "Damage/difficulty preset for the player.",
    "friend_combat_difficulty": "Damage/difficulty preset for friendly troops.",
    "reduce_combat_ai": "Combat AI difficulty reduction setting.",
    "reduce_campaign_ai": "Campaign AI difficulty reduction setting.",
    "cheat_mode": "Enable Warband cheat-mode functions.",
    "enable_edit_mode": "Enable Warband scene editing mode.",
    "show_framerate": "Show the frame-rate counter in game.",
    "enable_blood": "Enable blood effects.",
    "blood_stains": "Blood-stain detail preset.",
    "gamma": "Display gamma value.",
    "display_width": "Horizontal resolution. Zero lets the game choose.",
    "display_height": "Vertical resolution. Zero lets the game choose.",
}

BOOLEAN_KEYS = {
    "start_windowed", "use_pixel_shaders", "use_vertex_shaders", "fake_reflections",
    "show_framerate", "use_ondemand_textures_", "use_ondemand_textures_mt",
    "disable_music", "disable_sound", "disable_frequency_variation", "cheat_mode",
    "enable_edit_mode", "force_single_threading", "debug_mode", "alpha2coverage",
    "force_vsync", "postfx_dof", "postfx_autoexp", "use_instancing",
    "use_secure_connection", "look_for_server_on_this_machine", "invert_mouse",
    "enable_lighting", "enable_particles", "enable_character_shadows",
    "enable_accurate_shadows", "display_labels", "display_targeting_reticule",
    "anisotropic_filtering", "enable_environment_shadows", "use_winmm_audio",
    "enable_version_check", "enable_aspect_ratio_control", "realistic_headshots",
    "auto_gfx_quality", "enable_gamepad_vibration",
}

MODULE_SETTING_GROUPS = {
    "Campaign": {
        "time_multiplier", "seeing_range", "track_spotting_multiplier",
        "player_wounded_treshold", "hero_wounded_treshold",
        "skill_prisoner_management_bonus", "skill_leadership_bonus",
        "base_companion_limit", "player_xp_multiplier", "hero_xp_multiplier",
        "regulars_xp_multiplier",
    },
    "Combat": {
        "air_friction_arrow", "air_friction_bullet", "damage_interrupt_attack_threshold",
        "damage_interrupt_attack_threshold_mp", "extra_penetration_factor_soak",
        "extra_penetration_factor_reduction", "armor_soak_factor_against_cut",
        "armor_soak_factor_against_pierce", "armor_soak_factor_against_blunt",
        "armor_reduction_factor_against_cut", "armor_reduction_factor_against_pierce",
        "armor_reduction_factor_against_blunt", "horse_charge_damage_multiplier",
        "couched_lance_damage_multiplier", "fall_damage_multiplier",
        "shield_penetration_offset", "shield_penetration_factor",
        "missile_damage_speed_power", "melee_damage_speed_power",
        "crush_through_treshold", "lance_pike_effect_speed",
    },
    "World Map": {
        "map_min_x", "map_max_x", "map_min_y", "map_max_y", "map_sea_direction",
        "map_sea_wave_rotation", "map_sea_speed_x", "map_sea_speed_y",
        "map_river_direction", "map_river_speed_x", "map_river_speed_y",
        "map_tree_types", "map_snow_tree_types", "map_steppe_tree_types",
        "map_desert_tree_types", "map_max_distance", "has_tutorial",
    },
    "Gameplay Toggles": {
        "multiplayer_walk_enabled", "disable_food_slot", "limit_hair_colors",
        "show_faction_color", "show_quest_notes", "show_party_ids_instead_of_names",
        "can_crouch", "can_objects_make_sound", "disable_zoom", "use_advanced_formation",
        "use_crossbow_as_firearm", "can_reload_while_moving", "can_run_faster_with_skills",
        "use_phased_reload", "horses_try_running_away", "horses_rear_with_attack",
        "no_friendly_fire_for_bots", "can_adjust_camera_distance", "sync_ragdoll_effects",
        "has_forced_particles", "can_use_scene_props_in_single_player",
        "disable_attack_while_jumping", "disable_high_hdr", "has_accessories_for_female",
        "restrict_attacks_more_in_multiplayer", "display_wp_firearms",
    },
    "Compatibility": {
        "module_name", "compatible_with_warband", "compatible_multiplayer_version_no",
        "supports_directx_7", "reduce_texture_loader_memory_usage",
        "use_case_insensitive_mesh_searches", "use_texture_degration_cache",
        "num_hints", "auto_create_note_indices", "scan_module_textures",
        "scan_module_sounds", "dont_load_regular_troop_inventories",
        "disable_moveable_flag_optimization", "mission_object_prune_time",
    },
}

MODULE_BOOLEAN_KEYS = {
    "compatible_with_warband", "supports_directx_7", "reduce_texture_loader_memory_usage",
    "use_case_insensitive_mesh_searches", "use_texture_degration_cache", "has_tutorial",
    "multiplayer_walk_enabled", "disable_food_slot", "scan_module_textures",
    "scan_module_sounds", "limit_hair_colors", "show_faction_color", "show_quest_notes",
    "dont_load_regular_troop_inventories", "disable_moveable_flag_optimization",
    "show_party_ids_instead_of_names", "can_crouch", "can_objects_make_sound",
    "disable_zoom", "use_advanced_formation", "use_crossbow_as_firearm",
    "can_reload_while_moving", "can_run_faster_with_skills", "use_phased_reload",
    "horses_try_running_away", "horses_rear_with_attack", "no_friendly_fire_for_bots",
    "can_adjust_camera_distance", "sync_ragdoll_effects", "has_forced_particles",
    "can_use_scene_props_in_single_player", "disable_attack_while_jumping",
    "disable_high_hdr", "has_accessories_for_female", "restrict_attacks_more_in_multiplayer",
    "display_wp_firearms",
}

MODULE_SETTING_HELP = {
    "time_multiplier": "How quickly campaign time advances. Higher values make the world simulation run faster.",
    "seeing_range": "Base campaign-map visibility range.",
    "track_spotting_multiplier": "Multiplier applied when spotting tracks on the campaign map.",
    "player_wounded_treshold": "Player wound threshold. The engine key is intentionally misspelled.",
    "hero_wounded_treshold": "Hero wound threshold. The engine key is intentionally misspelled.",
    "skill_prisoner_management_bonus": "Additional prisoner capacity per Prisoner Management skill point.",
    "skill_leadership_bonus": "Additional party capacity per Leadership skill point.",
    "base_companion_limit": "Base number of companions allowed before skill bonuses.",
    "player_xp_multiplier": "Experience multiplier for the player.",
    "hero_xp_multiplier": "Experience multiplier for heroes and companions.",
    "regulars_xp_multiplier": "Experience multiplier for regular troops.",
    "horse_charge_damage_multiplier": "Global multiplier for horse charge damage.",
    "couched_lance_damage_multiplier": "Global multiplier for couched lance damage.",
    "fall_damage_multiplier": "Global multiplier for fall damage.",
    "module_name": "Name displayed for this module in the Warband launcher.",
    "can_crouch": "Allow crouching where supported by the module.",
    "can_reload_while_moving": "Allow compatible ranged weapons to reload while moving.",
    "disable_zoom": "Disable the normal battle-camera zoom function.",
    "show_faction_color": "Show faction colors in supported map and interface elements.",
}

TROOP_TYPES = {0: "Male", 1: "Female", 2: "Undead"}
TROOP_TYPE_MASK = 0x0000000F
TROOP_FLAG_OPTIONS = (
    ("hero", "Hero", 0x00000010),
    ("inactive", "Inactive", 0x00000020),
    ("unkillable", "Unkillable", 0x00000040),
    ("always_fall_dead", "Always fall dead", 0x00000080),
    ("no_capture_alive", "Cannot be captured alive", 0x00000100),
    ("mounted", "Mounted on campaign map", 0x00000400),
    ("merchant", "Merchant", 0x00001000),
    ("randomize_face", "Randomize face", 0x00008000),
    ("guarantee_boots", "Guarantee boots", 0x00100000),
    ("guarantee_armor", "Guarantee armor", 0x00200000),
    ("guarantee_helmet", "Guarantee helmet", 0x00400000),
    ("guarantee_gloves", "Guarantee gloves", 0x00800000),
    ("guarantee_horse", "Guarantee horse", 0x01000000),
    ("guarantee_shield", "Guarantee shield", 0x02000000),
    ("guarantee_ranged", "Guarantee ranged weapon", 0x04000000),
    ("guarantee_polearm", "Guarantee polearm", 0x08000000),
    ("unmoveable", "Locked in party window", 0x10000000),
)
TROOP_KNOWN_FLAG_MASK = TROOP_TYPE_MASK | sum(bit for _key, _label, bit in TROOP_FLAG_OPTIONS)
TROOP_ATTRIBUTES = ("Strength", "Agility", "Intelligence", "Charisma", "Level")
TROOP_PROFICIENCIES = ("One-handed", "Two-handed", "Polearm", "Archery", "Crossbow", "Throwing", "Firearm")
TROOP_SKILLS = (
    "Trade", "Leadership", "Prisoner Management", "Reserved 3", "Reserved 4", "Reserved 5", "Reserved 6", "Persuasion",
    "Engineer", "First Aid", "Surgery", "Wound Treatment", "Inventory Management", "Spotting", "Path-finding", "Tactics",
    "Tracking", "Trainer", "Reserved 18", "Reserved 19", "Reserved 20", "Reserved 21", "Looting", "Horse Archery",
    "Riding", "Athletics", "Shield", "Weapon Master", "Reserved 28", "Reserved 29", "Reserved 30", "Reserved 31",
    "Reserved 32", "Power Draw", "Power Throw", "Power Strike", "Ironflesh", "Reserved 37", "Reserved 38", "Reserved 39",
    "Reserved 40", "Reserved 41",
)
PLAYER_SKILL_INDICES = tuple(index for index, name in enumerate(TROOP_SKILLS) if not name.startswith("Reserved"))

GAMEPLAY_NUMERIC_FIELDS = (
    ("tournament_prize", "Tournament prize (denars)"),
    ("tournament_renown", "Tournament renown"),
    ("tournament_xp", "Tournament XP"),
    ("village_base", "Village base recruit pool"),
    ("village_relation_bonus", "Village relation bonus"),
    ("village_multiplier", "Village recruit multiplier"),
    ("village_price", "Recruit price per troop"),
    ("mercenary_min", "Tavern mercenary minimum"),
    ("mercenary_max", "Tavern mercenary maximum"),
    ("prisoner_level_bonus", "Prisoner price level bonus"),
    ("prisoner_divisor", "Prisoner price divisor"),
    ("prisoner_minimum", "Minimum prisoner price"),
    ("ladder_skill_base", "Ladder base hours factor"),
    ("ladder_time_multiplier", "Ladder time multiplier"),
    ("ladder_time_divisor", "Ladder time divisor"),
    ("tower_skill_base", "Siege-tower base hours factor"),
    ("tower_time_multiplier", "Siege-tower time multiplier"),
    ("village_rent", "Weekly village rent"),
    ("castle_rent", "Weekly castle rent"),
    ("town_rent", "Weekly town rent"),
    ("prosperity_base", "Fief prosperity base"),
    ("prosperity_divisor", "Fief tax/income divisor"),
    ("fief_interval_hours", "Fief income interval (hours)"),
    ("party_base_size", "Base party size"),
    ("party_renown_divisor", "Renown per party slot"),
    ("garrison_wage_divisor", "Garrison wage divisor"),
    ("food_interval_hours", "Food consumption interval (hours)"),
    ("food_troops_per_unit", "Troops per food unit"),
    ("refresh_interval_hours", "Mercenary/volunteer refresh (hours)"),
    ("battle_level_bonus", "Battle reward level bonus"),
    ("battle_gain_divisor", "Battle reward base divisor"),
    ("battle_gold_share", "Battle gold share multiplier"),
    ("battle_gold_cap", "Battle gold cap"),
    ("battle_gold_roll_min", "Battle gold roll minimum %"),
    ("battle_gold_roll_max", "Battle gold roll maximum % (exclusive)"),
    ("battle_gold_divisor", "Battle gold percent divisor"),
    ("battle_xp_roll_min", "Battle XP roll minimum %"),
    ("battle_xp_roll_max", "Battle XP roll maximum % (exclusive)"),
    ("battle_xp_divisor", "Battle XP percent divisor"),
)

QUICK_CONFIG_KEYS = (
    ("cheat_mode", "Cheat mode"), ("show_framerate", "Show FPS"),
    ("start_windowed", "Start windowed"), ("force_vsync", "VSync"),
    ("enable_blood", "Blood effects"),
)
QUICK_CONFIG_NUMERIC_KEYS = (
    ("number_of_corpses", "Corpses"), ("number_of_ragdolls", "Ragdolls"),
    ("combat_speed", "Combat speed"), ("combat_difficulty", "Player damage"),
    ("friend_combat_difficulty", "Friendly damage"), ("reduce_combat_ai", "Combat AI"),
    ("reduce_campaign_ai", "Campaign AI"),
)
QUICK_MODULE_KEYS = (
    ("can_crouch", "Allow crouching"), ("can_reload_while_moving", "Reload while moving"),
    ("can_run_faster_with_skills", "Skill-based running speed"), ("disable_zoom", "Disable battle zoom"),
    ("show_faction_color", "Show faction colors"), ("horses_try_running_away", "Loose horses flee"),
    ("horses_rear_with_attack", "Horses rear from attacks"), ("no_friendly_fire_for_bots", "No bot friendly fire"),
    ("disable_attack_while_jumping", "Disable attacks while jumping"),
)

BATTLE_CONTINUATION_TARGETS = {
    "mst_lead_charge", "mst_village_attack_bandits", "mst_village_raid",
    "mst_besiege_inner_battle_castle", "mst_besiege_inner_battle_town_center",
    "mst_castle_attack_walls_defenders_sally", "mst_castle_attack_walls_belfry",
    "mst_castle_attack_walls_ladder",
}
HERO_FALLEN_PATTERN = re.compile(r"^(?P<prefix>\s*1\.000000\s+4\.000000\s+100000000\.000000\s+)1\s+1006\s+0(?P<suffix>\s.*)$")
HERO_FALLEN_DISABLED_PATTERN = re.compile(r"^(?P<prefix>\s*1\.000000\s+4\.000000\s+100000000\.000000\s+)1\s+31\s+2\s+0\s+1(?P<suffix>\s.*)$")

ITEM_TYPES = {
    0: "Unknown / special", 1: "Horse", 2: "One-handed weapon", 3: "Two-handed weapon",
    4: "Polearm", 5: "Arrows", 6: "Bolts", 7: "Shield", 8: "Bow", 9: "Crossbow",
    10: "Thrown weapon", 11: "Goods", 12: "Head armor", 13: "Body armor",
    14: "Foot armor", 15: "Hand armor", 16: "Pistol", 17: "Musket",
    18: "Bullets", 19: "Animal", 20: "Book",
}

DAMAGE_TYPES = {0: "Cut", 1: "Pierce", 2: "Blunt", 3: "Reserved"}

ITEM_ATTACHMENT_OPTIONS = {
    0x000: "Default attachment", 0x100: "Force left hand", 0x200: "Force right hand",
    0x300: "Force left forearm", 0xF00: "Attach to armature",
}

ITEM_FLAG_OPTIONS = (
    ("unique", "Unique", 0x0000000000001000, "Normally prevents ordinary random generation."),
    ("always_loot", "Always loot", 0x0000000000002000, "Always eligible to appear as loot."),
    ("no_parry", "Cannot parry", 0x0000000000004000, "Weapon cannot be used to parry."),
    ("default_ammo", "Default ammunition", 0x0000000000008000, "Marks the default ammo item for its weapon type."),
    ("merchandise", "Sold by merchants", 0x0000000000010000, "Allows normal merchant stock generation."),
    ("wooden_attack", "Wooden attack sound", 0x0000000000020000, "Uses wooden impact behavior when attacking."),
    ("wooden_parry", "Wooden parry sound", 0x0000000000040000, "Uses wooden impact behavior when parrying."),
    ("food", "Food", 0x0000000000080000, "Treats the item as party food; food quality uses the head-armor stat slot."),
    ("cant_reload_horse", "Cannot reload on horseback", 0x0000000000100000, "Blocks mounted reloading."),
    ("two_handed", "Uses both hands", 0x0000000000200000, "Marks the item as two-handed."),
    ("primary", "Primary weapon", 0x0000000000400000, "Can be used in primary weapon mode."),
    ("secondary", "Secondary weapon", 0x0000000000800000, "Can be used in secondary weapon mode."),
    ("context_01000000", "Context: covers legs / hair visible / penetrates shield", 0x0000000001000000, "Same engine bit: armor covers legs, head armor does not cover hair, or missiles penetrate shields."),
    ("consumable", "Consumable", 0x0000000002000000, "Has a consumable quantity such as food or ammunition."),
    ("bonus_shield", "Bonus against shields", 0x0000000004000000, "Deals bonus damage against shields."),
    ("penalty_shield", "Penalty with shield", 0x0000000008000000, "Applies the weapon-with-shield handling penalty."),
    ("cant_use_horse", "Cannot use on horseback", 0x0000000010000000, "Prevents mounted use."),
    ("context_20000000", "Context: civilian / next item is melee", 0x0000000020000000, "Civilian equipment flag, or links a ranged item to the next melee-mode item."),
    ("context_40000000", "Context: fit to head / offset lance", 0x0000000040000000, "Fits armor to the head, or offsets a lance."),
    ("context_80000000", "Context: covers head / couchable", 0x0000000080000000, "Head-covering armor, or a couchable polearm."),
    ("crush_through", "Crush through blocks", 0x0000000100000000, "Allows suitable attacks to crush through a block."),
    ("remove_on_use", "Remove item on use", 0x0000000400000000, "Removes the item when it is used."),
    ("unbalanced", "Unbalanced", 0x0000000800000000, "Uses the unbalanced weapon recovery behavior."),
    ("covers_beard", "Covers beard", 0x0000001000000000, "Hides the beard mesh."),
    ("no_ground_pickup", "Cannot pick up from ground", 0x0000002000000000, "Prevents battlefield pickup."),
    ("knock_down", "Can knock down", 0x0000004000000000, "Enables knock-down behavior."),
    ("covers_hair", "Covers hair", 0x0000008000000000, "Hides hair for armor items."),
    ("show_body", "Force show body", 0x0000010000000000, "Forces the body mesh to remain visible."),
    ("show_left_hand", "Force show left hand", 0x0000020000000000, "Forces the left hand mesh to remain visible."),
    ("show_right_hand", "Force show right hand", 0x0000040000000000, "Forces the right hand mesh to remain visible."),
    ("partial_hair", "Partially covers hair", 0x0000080000000000, "Uses partial hair coverage."),
    ("extra_penetration", "Extra penetration", 0x0000100000000000, "Uses the module's extra penetration factors."),
    ("bayonet", "Has bayonet", 0x0000200000000000, "Marks a firearm as having a bayonet mode."),
    ("cant_reload_move", "Cannot reload while moving", 0x0000400000000000, "Blocks reloading during movement."),
    ("ignore_gravity", "Projectile ignores gravity", 0x0000800000000000, "Projectile trajectory ignores gravity."),
    ("ignore_friction", "Projectile ignores friction", 0x0001000000000000, "Projectile ignores air friction."),
    ("pike", "Is pike", 0x0002000000000000, "Enables pike-specific engine behavior."),
    ("offset_musket", "Offset musket", 0x0004000000000000, "Uses the musket positioning offset."),
    ("no_blur", "Disable motion blur", 0x0008000000000000, "Disables blur for the item."),
    ("cant_reload_move_mounted", "Cannot reload while mounted and moving", 0x0010000000000000, "Blocks moving mounted reloads."),
    ("upper_stab", "Has upper stab", 0x0020000000000000, "Enables the upper-stab attack direction."),
    ("disable_agent_sounds", "Disable agent sounds", 0x0040000000000000, "Disables non-voice agent sounds; useful for animals."),
)

ITEM_KILL_INFO_MASK = 0x0700000000000000
ITEM_FLAG_TOGGLE_MASK = sum(option[2] for option in ITEM_FLAG_OPTIONS)
ITEM_FLAG_KNOWN_MASK = 0xFF | 0xF00 | ITEM_FLAG_TOGGLE_MASK | ITEM_KILL_INFO_MASK

CAPABILITY_SHOOT_OPTIONS = {
    0x00000: "No shoot/throw action", 0x01000: "Shoot bow", 0x02000: "Shoot javelin",
    0x04000: "Shoot crossbow", 0x10000: "Throw stone", 0x20000: "Throw knife",
    0x30000: "Throw axe", 0x40000: "Throw javelin", 0x70000: "Shoot pistol",
    0x80000: "Shoot musket",
}

CAPABILITY_CARRY_OPTIONS = {
    0x000000000: "No carry position", 0x010000000: "Sword at left hip",
    0x020000000: "Axe at left hip", 0x030000000: "Dagger front-left",
    0x040000000: "Dagger front-right", 0x050000000: "Quiver front-right",
    0x060000000: "Quiver back-right", 0x070000000: "Quiver right vertical",
    0x080000000: "Quiver on back", 0x090000000: "Revolver right",
    0x0A0000000: "Pistol front-left", 0x0B0000000: "Bow case left",
    0x0C0000000: "Mace at left hip", 0x100000000: "Axe on back",
    0x110000000: "Sword on back", 0x120000000: "Kite shield",
    0x130000000: "Round shield", 0x140000000: "Buckler left",
    0x150000000: "Crossbow on back", 0x160000000: "Bow on back",
    0x170000000: "Spear", 0x180000000: "Board shield",
    0x210000000: "Katana", 0x220000000: "Wakizashi",
}

CAPABILITY_RELOAD_OPTIONS = {
    0x0000000000: "No reload animation", 0x7000000000: "Reload pistol", 0x8000000000: "Reload musket",
}

CAPABILITY_OPTIONS = (
    ("thrust_1h", "One-handed thrust", 0x0000000000000001, "Allows the one-handed thrust animation."),
    ("overswing_1h", "One-handed overhead", 0x0000000000000002, "Allows the one-handed overhead attack."),
    ("slash_right_1h", "One-handed slash right", 0x0000000000000004, "Allows a right-side one-handed slash."),
    ("slash_left_1h", "One-handed slash left", 0x0000000000000008, "Allows a left-side one-handed slash."),
    ("thrust_2h", "Two-handed thrust", 0x0000000000000010, "Allows the two-handed thrust animation."),
    ("overswing_2h", "Two-handed overhead", 0x0000000000000020, "Allows the two-handed overhead attack."),
    ("slash_right_2h", "Two-handed slash right", 0x0000000000000040, "Allows a right-side two-handed slash."),
    ("slash_left_2h", "Two-handed slash left", 0x0000000000000080, "Allows a left-side two-handed slash."),
    ("thrust_pole", "Polearm thrust", 0x0000000000000100, "Allows a polearm thrust."),
    ("overswing_pole", "Polearm overhead", 0x0000000000000200, "Allows a polearm overhead attack."),
    ("slash_right_pole", "Polearm slash right", 0x0000000000000400, "Allows a right-side polearm slash."),
    ("slash_left_pole", "Polearm slash left", 0x0000000000000800, "Allows a left-side polearm slash."),
    ("horse_thrust_1h", "Mounted one-handed thrust", 0x0000000000100000, "Allows a mounted one-handed thrust."),
    ("horse_over_right_1h", "Mounted overhead right", 0x0000000000200000, "Allows mounted right overhead attack."),
    ("horse_over_left_1h", "Mounted overhead left", 0x0000000000400000, "Allows mounted left overhead attack."),
    ("horse_slash_right_1h", "Mounted slash right", 0x0000000000800000, "Allows mounted right slash."),
    ("horse_slash_left_1h", "Mounted slash left", 0x0000000001000000, "Allows mounted left slash."),
    ("lance_thrust", "Lance thrust on foot", 0x0000000004000000, "Allows one-handed lance thrust."),
    ("lance_thrust_horse", "Lance thrust mounted", 0x0000000008000000, "Allows mounted one-handed lance thrust."),
    ("show_holster", "Show holster when drawn", 0x0000000800000000, "Keeps the holster mesh visible while drawn."),
    ("parry_forward_1h", "One-handed parry forward", 0x0000010000000000, "Allows forward one-handed parry."),
    ("parry_up_1h", "One-handed parry up", 0x0000020000000000, "Allows upward one-handed parry."),
    ("parry_right_1h", "One-handed parry right", 0x0000040000000000, "Allows right one-handed parry."),
    ("parry_left_1h", "One-handed parry left", 0x0000080000000000, "Allows left one-handed parry."),
    ("parry_forward_2h", "Two-handed parry forward", 0x0000100000000000, "Allows forward two-handed parry."),
    ("parry_up_2h", "Two-handed parry up", 0x0000200000000000, "Allows upward two-handed parry."),
    ("parry_right_2h", "Two-handed parry right", 0x0000400000000000, "Allows right two-handed parry."),
    ("parry_left_2h", "Two-handed parry left", 0x0000800000000000, "Allows left two-handed parry."),
    ("parry_forward_pole", "Polearm parry forward", 0x0001000000000000, "Allows forward polearm parry."),
    ("parry_up_pole", "Polearm parry up", 0x0002000000000000, "Allows upward polearm parry."),
    ("parry_right_pole", "Polearm parry right", 0x0004000000000000, "Allows right polearm parry."),
    ("parry_left_pole", "Polearm parry left", 0x0008000000000000, "Allows left polearm parry."),
    ("horse_slash_pole", "Mounted polearm slash", 0x0010000000000000, "Allows mounted polearm slash behavior."),
    ("overswing_spear", "Spear overhead", 0x0020000000000000, "Allows spear overhead attack."),
    ("overswing_musket", "Musket overhead", 0x0040000000000000, "Allows musket overhead melee attack."),
    ("thrust_musket", "Musket thrust", 0x0080000000000000, "Allows musket thrust melee attack."),
    ("force_64", "64-bit capability marker", 0x8000000000000000, "Engine marker used by the Module System's combined melee capabilities."),
)

CAPABILITY_SHOOT_MASK = 0x00000000000FF000
CAPABILITY_CARRY_MASK = 0x00000007F0000000
CAPABILITY_RELOAD_MASK = 0x000000F000000000
CAPABILITY_TOGGLE_MASK = sum(option[2] for option in CAPABILITY_OPTIONS)
CAPABILITY_KNOWN_MASK = CAPABILITY_SHOOT_MASK | CAPABILITY_CARRY_MASK | CAPABILITY_RELOAD_MASK | CAPABILITY_TOGGLE_MASK


@dataclass(frozen=True)
class ConfigEntry:
    line_index: int
    key: str
    value: str


@dataclass(frozen=True)
class PartyStack:
    troop_index: int
    minimum: int
    maximum: int
    member_flags: int = 0


@dataclass(frozen=True)
class PartyTemplateRecord:
    line_index: int
    template_id: str
    name: str
    flags: int
    menu: int
    faction: int
    personality: int
    stacks: tuple[PartyStack, ...]


@dataclass(frozen=True)
class ItemMesh:
    name: str
    flags: int


@dataclass(frozen=True)
class ItemRecord:
    line_index: int
    item_id: str
    singular_name: str
    plural_name: str
    meshes: tuple[ItemMesh, ...]
    item_flags: int
    capabilities: int
    value: int
    modifiers: int
    weight: float
    abundance: int
    head_armor: int
    body_armor: int
    leg_armor: int
    difficulty: int
    hit_points: int
    speed_rating: int
    missile_speed: int
    weapon_length: int
    max_ammo: int
    thrust_damage: int
    swing_damage: int
    factions: tuple[int, ...]
    trigger_count: int


@dataclass(frozen=True)
class ItemAddition:
    record: ItemRecord
    source_item_id: str | None = None
    source_line_index: int | None = None


@dataclass(frozen=True)
class TroopInventorySlot:
    item_index: int
    modifier: int = 0


@dataclass(frozen=True)
class TroopRecord:
    line_index: int
    troop_id: str
    singular_name: str
    plural_name: str
    image: str
    flags: int
    scene: int
    reserved: int
    faction: int
    upgrade_one: int
    upgrade_two: int
    inventory: tuple[TroopInventorySlot, ...]
    attributes: tuple[int, ...]
    proficiencies: tuple[int, ...]
    skill_words: tuple[int, ...]
    face_words: tuple[int, ...]


@dataclass(frozen=True)
class CompiledOperation:
    opcode: int
    operands: tuple[int, ...]
    operand_token_indices: tuple[int, ...]


@dataclass(frozen=True)
class CompiledMenuOption:
    line_index: int
    option_id: str
    condition_operations: tuple[CompiledOperation, ...]
    text_token_index: int
    consequence_operations: tuple[CompiledOperation, ...]


@dataclass(frozen=True)
class CompiledSimpleTrigger:
    line_index: int
    interval: float
    operations: tuple[CompiledOperation, ...]


@dataclass(frozen=True)
class SkillRecord:
    line_index: int
    skill_id: str
    name: str
    flags: int
    max_level: int
    description: str


def battle_size_to_value(troops: int) -> float:
    if troops < 30:
        raise ValueError("Battle size must be at least 30 troops.")
    return (troops - 30) / 120


def value_to_battle_size(value: float) -> int:
    return round(30 + (120 * value))


def replace_battle_size(text: str, troops: int) -> tuple[str, str]:
    formatted = f"{battle_size_to_value(troops):.4f}"
    if CONFIG_PATTERN.search(text):
        return CONFIG_PATTERN.sub(rf"\g<1>{formatted}\g<3>\g<4>", text, count=1), formatted
    separator = "" if not text or text.endswith(("\n", "\r")) else os.linesep
    return f"{text}{separator}battle_size = {formatted}{os.linesep}", formatted


def parse_config_entries(text: str) -> list[ConfigEntry]:
    entries: list[ConfigEntry] = []
    for index, line in enumerate(text.splitlines(keepends=True)):
        match = CONFIG_LINE_PATTERN.match(line)
        if match:
            entries.append(ConfigEntry(index, match.group(2), match.group(4)))
    return entries


def parse_party_templates(text: str) -> list[PartyTemplateRecord]:
    lines = text.splitlines(keepends=True)
    if len(lines) < 2 or not lines[0].strip().lower().startswith("partytemplatesfile version"):
        raise ValueError("This is not a supported party_templates.txt file.")
    try:
        expected_count = int(lines[1].strip())
    except ValueError as exc:
        raise ValueError("party_templates.txt has an invalid record count.") from exc
    records: list[PartyTemplateRecord] = []
    for line_index, line in enumerate(lines[2:], start=2):
        tokens = line.split()
        if not tokens:
            continue
        if len(tokens) < 12:
            raise ValueError(f"Party template on line {line_index + 1} is incomplete.")
        try:
            flags, menu, faction, personality = map(int, tokens[2:6])
        except ValueError as exc:
            raise ValueError(f"Party template on line {line_index + 1} has a non-numeric header field.") from exc
        stacks: list[PartyStack] = []
        position = 6
        for _slot in range(6):
            if position >= len(tokens):
                raise ValueError(f"Party template on line {line_index + 1} has fewer than six stack slots.")
            if tokens[position] == "-1":
                position += 1
                continue
            if position + 3 >= len(tokens):
                raise ValueError(f"Party template on line {line_index + 1} has a truncated troop stack.")
            try:
                troop_index, minimum, maximum, member_flags = map(int, tokens[position:position + 4])
            except ValueError as exc:
                raise ValueError(f"Party template on line {line_index + 1} has a non-numeric troop stack.") from exc
            stacks.append(PartyStack(troop_index, minimum, maximum, member_flags))
            position += 4
        if position != len(tokens):
            raise ValueError(f"Party template on line {line_index + 1} has unexpected extra fields.")
        record = PartyTemplateRecord(line_index, tokens[0], tokens[1], flags, menu, faction, personality, tuple(stacks))
        validate_party_template(record)
        records.append(record)
    if len(records) != expected_count:
        raise ValueError(f"party_templates.txt declares {expected_count} records but contains {len(records)}.")
    return records


def parse_troop_names(text: str) -> list[tuple[str, str]]:
    lines = text.splitlines()
    if len(lines) < 2 or not lines[0].strip().lower().startswith("troopsfile version"):
        raise ValueError("This is not a supported troops.txt file.")
    try:
        expected_count = int(lines[1].strip())
    except ValueError as exc:
        raise ValueError("troops.txt has an invalid record count.") from exc
    troops = []
    for line in lines[2:]:
        tokens = line.split()
        if tokens and tokens[0].startswith("trp_") and len(tokens) >= 3:
            troops.append((tokens[0], tokens[1].replace("_", " ")))
    if len(troops) != expected_count:
        raise ValueError(f"troops.txt declares {expected_count} records but contains {len(troops)}.")
    return troops


def normalize_troop_id(raw: str) -> str:
    troop_id = raw.strip().replace(" ", "_").replace("-", "_").lower()
    if not troop_id.startswith("trp_"):
        troop_id = f"trp_{troop_id}"
    if not re.fullmatch(r"trp_[a-z0-9_]+", troop_id) or troop_id == "trp_":
        raise ValueError("Troop IDs may contain only letters, numbers, and underscores after trp_.")
    return troop_id


def parse_troops(text: str) -> list[TroopRecord]:
    lines = text.splitlines(keepends=True)
    if len(lines) < 2 or not lines[0].strip().lower().startswith("troopsfile version"):
        raise ValueError("This is not a supported troops.txt file.")
    try:
        expected_count = int(lines[1].strip())
    except ValueError as exc:
        raise ValueError("troops.txt has an invalid record count.") from exc
    starts = [index for index, line in enumerate(lines[2:], start=2) if line.lstrip().startswith("trp_")]
    records: list[TroopRecord] = []
    boundaries = starts + [len(lines)]
    for start, end in zip(boundaries, boundaries[1:]):
        nonempty = [line.split() for line in lines[start:end] if line.strip()]
        if len(nonempty) != 6:
            raise ValueError(f"Troop record on line {start + 1} must contain six data lines.")
        header, inventory_tokens, attribute_tokens, proficiency_tokens, skill_tokens, face_tokens = nonempty
        if len(header) != 10:
            raise ValueError(f"Troop record on line {start + 1} has an unexpected header field count.")
        if len(inventory_tokens) != 128 or len(attribute_tokens) != 5 or len(proficiency_tokens) != 7 or len(skill_tokens) != 6 or len(face_tokens) != 8:
            raise ValueError(f"Troop record on line {start + 1} has an unexpected compiled field count.")
        try:
            numeric_header = list(map(int, header[4:]))
            inventory_values = list(map(int, inventory_tokens))
            attributes = tuple(map(int, attribute_tokens))
            proficiencies = tuple(map(int, proficiency_tokens))
            skill_words = tuple(map(int, skill_tokens))
            face_words = tuple(map(int, face_tokens))
        except ValueError as exc:
            raise ValueError(f"Troop record on line {start + 1} has a non-numeric compiled field.") from exc
        slots = tuple(TroopInventorySlot(inventory_values[index], inventory_values[index + 1]) for index in range(0, 128, 2))
        record = TroopRecord(
            start, header[0], header[1], header[2], header[3], *numeric_header,
            slots, attributes, proficiencies, skill_words, face_words,
        )
        validate_troop_record(record)
        records.append(record)
    if len(records) != expected_count:
        raise ValueError(f"troops.txt declares {expected_count} records but contains {len(records)}.")
    return records


def troop_skill_levels(skill_words: tuple[int, ...]) -> tuple[int, ...]:
    if len(skill_words) != 6:
        raise ValueError("A Warband troop must have six packed skill words.")
    return tuple((skill_words[index // 8] >> ((index % 8) * 4)) & 0xF for index in range(42))


def rebuild_troop_skill_words(base_words: tuple[int, ...], levels: tuple[int, ...]) -> tuple[int, ...]:
    if len(base_words) != 6 or len(levels) != 42:
        raise ValueError("Expected six skill words and 42 skill levels.")
    words = list(base_words)
    for index, level in enumerate(levels):
        if not 0 <= level <= 15:
            raise ValueError(f"{TROOP_SKILLS[index]} must be from 0 to 15.")
        shift = (index % 8) * 4
        words[index // 8] = (words[index // 8] & ~(0xF << shift)) | (level << shift)
    return tuple(words)


def rebuild_troop_flags(base_value: int, troop_type: int, enabled_keys: set[str]) -> int:
    if troop_type not in TROOP_TYPES:
        raise ValueError("Choose a supported troop type.")
    option_by_key = {key: bit for key, _label, bit in TROOP_FLAG_OPTIONS}
    unknown = enabled_keys - option_by_key.keys()
    if unknown:
        raise ValueError(f"Unknown troop flag controls: {', '.join(sorted(unknown))}")
    value = (base_value & ~TROOP_KNOWN_FLAG_MASK) | troop_type
    for key in enabled_keys:
        value |= option_by_key[key]
    return value


def troop_face_preset_pool(records: list[TroopRecord] | tuple[TroopRecord, ...], troop_type: int) -> tuple[tuple[str, tuple[int, ...]], ...]:
    """Return unique, non-empty, engine-produced 256-bit face presets for a troop type."""
    presets: list[tuple[str, tuple[int, ...]]] = []
    seen: set[tuple[int, ...]] = set()
    for record in records:
        if (record.flags & TROOP_TYPE_MASK) != troop_type:
            continue
        for label, words in (("Face 1", record.face_words[:4]), ("Face 2", record.face_words[4:])):
            preset = tuple(words)
            if any(preset) and preset not in seen:
                seen.add(preset)
                presets.append((f"{record.troop_id} {label}", preset))
    return tuple(presets)


def randomize_troop_face_words(
    records: list[TroopRecord] | tuple[TroopRecord, ...],
    troop_type: int,
    current: tuple[int, ...],
    fixed: bool = False,
    chooser=secrets.choice,
) -> tuple[tuple[int, ...], tuple[str, str], int]:
    """Build a valid face or face range by sampling same-type presets from the module."""
    if len(current) != 8:
        raise ValueError("A troop face must contain eight compiled words.")
    pool = troop_face_preset_pool(records, troop_type)
    if not pool:
        raise ValueError("No non-empty same-type face presets were found in this module.")

    first_candidates = tuple(entry for entry in pool if entry[1] != current[:4]) or pool
    first = chooser(first_candidates)
    if fixed:
        second = first
    else:
        second_candidates = tuple(entry for entry in pool if entry[1] not in {current[4:], first[1]})
        if not second_candidates:
            second_candidates = tuple(entry for entry in pool if entry[1] != first[1]) or pool
        second = chooser(second_candidates)
    return first[1] + second[1], (first[0], second[0]), len(pool)


def validate_troop_record(record: TroopRecord, troop_count: int | None = None, item_count: int | None = None) -> None:
    if not record.troop_id.startswith("trp_") or any(character.isspace() for character in record.troop_id):
        raise ValueError("A troop ID must start with trp_ and cannot contain spaces.")
    for label, value in (("singular name", record.singular_name), ("plural name", record.plural_name), ("image", record.image)):
        if not value or any(character.isspace() for character in value):
            raise ValueError(f"The troop {label} cannot be blank or contain spaces; use underscores.")
    if len(record.inventory) != 64 or len(record.attributes) != 5 or len(record.proficiencies) != 7 or len(record.skill_words) != 6 or len(record.face_words) != 8:
        raise ValueError("The troop does not have the required compiled field counts.")
    for slot in record.inventory:
        if slot.item_index < -1 or (item_count is not None and slot.item_index >= item_count):
            raise ValueError(f"Inventory item index {slot.item_index} is outside item_kinds1.txt.")
        if not 0 <= slot.modifier <= 0xFFFFFFFF:
            raise ValueError("Inventory modifier values must fit an unsigned 32-bit integer.")
    if any(not 0 <= value <= 0xFFFFFFFF for value in record.attributes):
        raise ValueError("Troop attributes and level must fit unsigned 32-bit integers.")
    if any(not 0 <= value <= 0xFFFFFFFF for value in record.proficiencies):
        raise ValueError("Weapon proficiencies must fit unsigned 32-bit integers.")
    if any(not 0 <= value <= 0xFFFFFFFF for value in record.skill_words):
        raise ValueError("Packed skill words must fit unsigned 32-bit integers.")
    if any(not 0 <= value <= 0xFFFFFFFFFFFFFFFF for value in record.face_words):
        raise ValueError("Face-code words must fit unsigned 64-bit integers.")
    for upgrade in (record.upgrade_one, record.upgrade_two):
        if upgrade < 0 or (troop_count is not None and upgrade >= troop_count):
            raise ValueError(f"Upgrade troop index {upgrade} is outside troops.txt.")


def format_troop_record(record: TroopRecord, newline: str = os.linesep) -> str:
    validate_troop_record(record)
    header = " ".join((
        record.troop_id, record.singular_name, record.plural_name, record.image,
        str(record.flags), str(record.scene), str(record.reserved), str(record.faction),
        str(record.upgrade_one), str(record.upgrade_two),
    ))
    inventory = " ".join(str(value) for slot in record.inventory for value in (slot.item_index, slot.modifier))
    attributes = " ".join(map(str, record.attributes))
    proficiencies = " ".join(map(str, record.proficiencies))
    skills = " ".join(map(str, record.skill_words))
    faces = " ".join(map(str, record.face_words))
    return newline.join((header, f"  {inventory}", f"  {attributes}", f" {proficiencies}", skills, f"  {faces}")) + newline


def apply_troop_updates(text: str, updates: dict[int, TroopRecord]) -> str:
    if not updates:
        return text
    lines = text.splitlines(keepends=True)
    records = parse_troops(text)
    current = {record.line_index: record for record in records}
    starts = [record.line_index for record in records]
    boundaries = {start: (starts[index + 1] if index + 1 < len(starts) else len(lines)) for index, start in enumerate(starts)}
    for line_index in sorted(updates, reverse=True):
        record = updates[line_index]
        original = current.get(line_index)
        if original is None:
            raise ValueError(f"Troop line {line_index + 1} no longer exists.")
        if record.troop_id != original.troop_id:
            raise ValueError("Troop IDs cannot be changed in this editor.")
        newline = "\r\n" if lines[line_index].endswith("\r\n") else "\n"
        end = boundaries[line_index]
        trailing_blank = "".join(line for line in lines[line_index:end] if not line.strip())
        lines[line_index:end] = [format_troop_record(record, newline) + trailing_blank]
    return "".join(lines)


def append_troop_records(text: str, additions: list[TroopRecord]) -> str:
    """Append new troops without changing any existing compiled troop index."""
    if not additions:
        return text
    existing = parse_troops(text)
    existing_ids = {record.troop_id.casefold() for record in existing}
    new_ids: set[str] = set()
    total_count = len(existing) + len(additions)
    for record in additions:
        normalized = normalize_troop_id(record.troop_id)
        if normalized != record.troop_id:
            raise ValueError(f"Troop ID is not normalized: {record.troop_id}")
        folded = record.troop_id.casefold()
        if folded in existing_ids or folded in new_ids:
            raise ValueError(f"Troop ID already exists: {record.troop_id}")
        validate_troop_record(record, total_count)
        new_ids.add(folded)

    lines = text.splitlines(keepends=True)
    count_match = re.match(r"^(\s*)\d+([ \t]*)(\r?\n)?$", lines[1])
    if not count_match:
        raise ValueError("troops.txt has an unsupported record-count line.")
    newline = "\r\n" if "\r\n" in text else "\n"
    lines[1] = f"{count_match.group(1)}{total_count}{count_match.group(2)}{count_match.group(3) or ''}"
    updated = "".join(lines)
    if updated.endswith(newline * 2):
        separator = ""
    elif updated.endswith(newline):
        separator = newline
    else:
        separator = newline * 2
    blocks = (newline * 2).join(format_troop_record(record, newline).rstrip("\r\n") for record in additions)
    result = f"{updated}{separator}{blocks}{newline}"
    parsed = parse_troops(result)
    if len(parsed) != total_count or [record.troop_id for record in parsed[-len(additions):]] != [record.troop_id for record in additions]:
        raise RuntimeError("New troop append failed its record-order verification.")
    return result


def remap_troop_upgrades_after_removal(record: TroopRecord, removed_index: int) -> TroopRecord:
    """Keep staged upgrade indexes correct when an earlier appended troop is removed."""
    upgrades = (record.upgrade_one, record.upgrade_two)
    if removed_index in upgrades:
        raise ValueError(f"{record.troop_id} still has an upgrade path to the troop being removed (index {removed_index}).")
    return replace(
        record,
        upgrade_one=record.upgrade_one - 1 if record.upgrade_one > removed_index else record.upgrade_one,
        upgrade_two=record.upgrade_two - 1 if record.upgrade_two > removed_index else record.upgrade_two,
    )


def parse_faction_names(text: str) -> list[tuple[str, str]]:
    lines = text.splitlines()
    if len(lines) < 2 or not lines[0].strip().lower().startswith("factionsfile version"):
        raise ValueError("This is not a supported factions.txt file.")
    try:
        expected = int(lines[1].strip())
    except ValueError as exc:
        raise ValueError("factions.txt has an invalid record count.") from exc
    records: list[tuple[str, str]] = []
    for line in lines[2:]:
        tokens = line.split()
        faction_position = next((index for index, token in enumerate(tokens[:2]) if token.startswith("fac_")), None)
        if faction_position is not None and faction_position + 1 < len(tokens):
            records.append((tokens[faction_position], tokens[faction_position + 1].replace("_", " ")))
    if len(records) != expected:
        raise ValueError(f"factions.txt declares {expected} records but contains {len(records)}.")
    return records


def battle_continuation_state(text: str) -> tuple[str, int]:
    current = ""
    found: dict[str, str] = {}
    for line in text.splitlines():
        stripped = line.lstrip()
        if stripped.startswith("mst_"):
            current = stripped.split()[0]
        if current not in BATTLE_CONTINUATION_TARGETS:
            continue
        if HERO_FALLEN_PATTERN.match(line):
            found[current] = "disabled"
        elif HERO_FALLEN_DISABLED_PATTERN.match(line):
            found[current] = "enabled"
    if set(found) != BATTLE_CONTINUATION_TARGETS:
        return "unsupported", len(found)
    states = set(found.values())
    return (states.pop() if len(states) == 1 else "mixed"), len(found)


def set_battle_continuation(text: str, enabled: bool) -> str:
    state, count = battle_continuation_state(text)
    if state == "unsupported":
        raise ValueError(f"This mission_templates.txt has {count} of the 8 recognized player-fall triggers; no changes were made.")
    if state == "mixed":
        raise ValueError("Player-fall triggers are in a mixed state; restore the file from a backup or edit it in Module Files.")
    if (state == "enabled") == enabled:
        return text
    current = ""
    changed: set[str] = set()
    output: list[str] = []
    for line in text.splitlines(keepends=True):
        stripped = line.lstrip()
        if stripped.startswith("mst_"):
            current = stripped.split()[0]
        body = line.rstrip("\r\n")
        ending = line[len(body):]
        if current in BATTLE_CONTINUATION_TARGETS:
            pattern = HERO_FALLEN_PATTERN if enabled else HERO_FALLEN_DISABLED_PATTERN
            match = pattern.match(body)
            if match:
                replacement = "1 31 2 0 1" if enabled else "1 1006 0"
                body = f"{match.group('prefix')}{replacement}{match.group('suffix')}"
                changed.add(current)
        output.append(body + ending)
    if changed != BATTLE_CONTINUATION_TARGETS:
        raise RuntimeError("The continuation patch did not match all eight guarded triggers; no file was written.")
    updated = "".join(output)
    expected = "enabled" if enabled else "disabled"
    if battle_continuation_state(updated) != (expected, 8):
        raise RuntimeError("The continuation patch failed its verification check.")
    return updated


SCRIPT_REFERENCE_BASE = 13 << 56
TROOP_REFERENCE_BASE = 5 << 56
REGISTER_REFERENCE_BASE = 1 << 56
PLAYER_TROOP_REFERENCE = TROOP_REFERENCE_BASE
TAVERN_PRISONER_DIALOG_ID = "dlga_pvn_tavernkeeper_sell_prisoners:ransom_broker_sell_prisoners"


def _parse_compiled_operations(tokens: list[str], start: int, count: int) -> tuple[tuple[CompiledOperation, ...], int]:
    operations: list[CompiledOperation] = []
    position = start
    for _ in range(count):
        if position + 1 >= len(tokens):
            raise ValueError("A compiled operation block is truncated.")
        try:
            opcode = int(tokens[position])
            operand_count = int(tokens[position + 1])
        except ValueError as exc:
            raise ValueError("A compiled operation header is not numeric.") from exc
        operand_start = position + 2
        operand_end = operand_start + operand_count
        if operand_count < 0 or operand_end > len(tokens):
            raise ValueError("A compiled operation has an invalid operand count.")
        try:
            operands = tuple(map(int, tokens[operand_start:operand_end]))
        except ValueError as exc:
            raise ValueError("A compiled operation operand is not numeric.") from exc
        operations.append(CompiledOperation(opcode, operands, tuple(range(operand_start, operand_end))))
        position = operand_end
    return tuple(operations), position


def _replace_nonspace_tokens(line: str, replacements: dict[int, str | int]) -> str:
    matches = list(re.finditer(r"\S+", line))
    if any(index < 0 or index >= len(matches) for index in replacements):
        raise IndexError("A compiled token replacement is outside the record.")
    updated = line
    for index in sorted(replacements, reverse=True):
        match = matches[index]
        updated = updated[:match.start()] + str(replacements[index]) + updated[match.end():]
    return updated


def _script_record(text: str, script_name: str) -> tuple[list[str], int, list[str], tuple[CompiledOperation, ...]]:
    lines = text.splitlines(keepends=True)
    header_index = next((index for index, line in enumerate(lines) if line.split() == [script_name, "-1"]), None)
    if header_index is None or header_index + 1 >= len(lines):
        raise ValueError(f"script_{script_name} was not found.")
    data_index = header_index + 1
    tokens = lines[data_index].split()
    if not tokens:
        raise ValueError(f"script_{script_name} has no operation block.")
    try:
        count = int(tokens[0])
    except ValueError as exc:
        raise ValueError(f"script_{script_name} has an invalid operation count.") from exc
    operations, end = _parse_compiled_operations(tokens, 1, count)
    if end != len(tokens):
        raise ValueError(f"script_{script_name} contains unexpected trailing tokens.")
    return lines, data_index, tokens, operations


def _replace_script_tokens(text: str, script_name: str, replacements: dict[int, str | int]) -> str:
    lines, data_index, _tokens, _operations = _script_record(text, script_name)
    lines[data_index] = _replace_nonspace_tokens(lines[data_index], replacements)
    return "".join(lines)


def _script_reference(text: str, script_name: str) -> int:
    lines = text.splitlines()
    names = [line.split()[0] for line in lines[2:] if len(line.split()) == 2 and line.split()[1] == "-1"]
    try:
        return SCRIPT_REFERENCE_BASE + names.index(script_name)
    except ValueError as exc:
        raise ValueError(f"script_{script_name} was not found.") from exc


def _menu_record(text: str, menu_name: str) -> tuple[list[str], int, list[str], tuple[CompiledOperation, ...]]:
    lines = text.splitlines(keepends=True)
    line_index = next((index for index, line in enumerate(lines) if line.lstrip().startswith(f"menu_{menu_name} ")), None)
    if line_index is None:
        raise ValueError(f"menu_{menu_name} was not found.")
    tokens = lines[line_index].split()
    if len(tokens) < 6 or tokens[0] != f"menu_{menu_name}":
        raise ValueError(f"menu_{menu_name} has an unsupported header.")
    try:
        count = int(tokens[4])
    except ValueError as exc:
        raise ValueError(f"menu_{menu_name} has an invalid operation count.") from exc
    operations, end = _parse_compiled_operations(tokens, 5, count)
    if end >= len(tokens):
        raise ValueError(f"menu_{menu_name} is missing its option count.")
    try:
        int(tokens[end])
    except ValueError as exc:
        raise ValueError(f"menu_{menu_name} has an invalid option count.") from exc
    if end + 1 != len(tokens):
        raise ValueError(f"menu_{menu_name} contains unexpected trailing tokens.")
    return lines, line_index, tokens, operations


def _parse_menu_options_line(tokens: list[str], line_index: int) -> tuple[CompiledMenuOption, ...]:
    options: list[CompiledMenuOption] = []
    position = 0
    while position < len(tokens):
        option_id = tokens[position]
        if not option_id.startswith("mno_") or position + 1 >= len(tokens):
            raise ValueError("A compiled menu-option line has an unsupported layout.")
        try:
            condition_count = int(tokens[position + 1])
        except ValueError as exc:
            raise ValueError(f"{option_id} has an invalid condition count.") from exc
        conditions, position = _parse_compiled_operations(tokens, position + 2, condition_count)
        if position + 1 >= len(tokens):
            raise ValueError(f"{option_id} is missing its text or consequence block.")
        text_token_index = position
        try:
            consequence_count = int(tokens[position + 1])
        except ValueError as exc:
            raise ValueError(f"{option_id} has an invalid consequence count.") from exc
        consequences, position = _parse_compiled_operations(tokens, position + 2, consequence_count)
        if position >= len(tokens) or tokens[position] != ".":
            raise ValueError(f"{option_id} is missing its record terminator.")
        position += 1
        options.append(CompiledMenuOption(line_index, option_id, conditions, text_token_index, consequences))
    return tuple(options)


def _menu_options(text: str, menu_name: str) -> tuple[list[str], tuple[CompiledMenuOption, ...]]:
    lines, menu_index, _tokens, _operations = _menu_record(text, menu_name)
    options: list[CompiledMenuOption] = []
    for line_index in range(menu_index + 1, len(lines)):
        stripped = lines[line_index].lstrip()
        if stripped.startswith("menu_"):
            break
        if stripped.startswith("mno_"):
            options.extend(_parse_menu_options_line(lines[line_index].split(), line_index))
    if not options:
        raise ValueError(f"menu_{menu_name} has no readable options.")
    return lines, tuple(options)


def _single_operation(operations: tuple[CompiledOperation, ...], predicate, label: str) -> CompiledOperation:
    matches = [operation for operation in operations if predicate(operation)]
    if len(matches) != 1:
        raise ValueError(f"Expected one guarded {label} operation, found {len(matches)}.")
    return matches[0]


def _tournament_bet_layout(text: str) -> tuple[list[str], tuple[tuple[CompiledMenuOption, CompiledOperation, CompiledOperation, int], ...]]:
    lines, options = _menu_options(text, "tournament_bet")
    layout = []
    for option in options:
        if not re.fullmatch(r"mno_bet_\d+_denars", option.option_id):
            continue
        affordability = _single_operation(
            option.condition_operations,
            lambda operation: operation.opcode == 30 and len(operation.operands) == 2 and 0 < operation.operands[1] < 1_000_000_000,
            f"{option.option_id} affordability",
        )
        assignment = _single_operation(
            option.consequence_operations,
            lambda operation: operation.opcode == 2133 and len(operation.operands) == 2 and 0 < operation.operands[1] < 1_000_000_000,
            f"{option.option_id} assignment",
        )
        amount = affordability.operands[1]
        if assignment.operands[1] != amount:
            raise ValueError(f"{option.option_id} uses mismatched affordability and bet values.")
        label_match = re.fullmatch(r"(\d+)_denars\.", lines[option.line_index].split()[option.text_token_index])
        if not label_match or int(label_match.group(1)) != amount:
            raise ValueError(f"{option.option_id} uses an unsupported display label.")
        layout.append((option, affordability, assignment, amount))
    if not layout:
        raise ValueError("No guarded tournament bet choices were found.")
    return lines, tuple(layout)


def tournament_tweaks(menus_text: str, scripts_text: str) -> dict[str, object]:
    _lines, bets = _tournament_bet_layout(menus_text)
    _menu_lines, _menu_index, _tokens, operations = _menu_record(menus_text, "town_tournament_won")
    renown_reference = _script_reference(scripts_text, "change_troop_renown")
    prize = _single_operation(operations, lambda op: op.opcode == 2133 and op.operands[:1] == (REGISTER_REFERENCE_BASE + 9,), "tournament prize")
    xp = _single_operation(operations, lambda op: op.opcode == 1062 and len(op.operands) == 2 and op.operands[1] == PLAYER_TROOP_REFERENCE, "tournament XP")
    renown = _single_operation(operations, lambda op: op.opcode == 1 and len(op.operands) == 3 and op.operands[0] == renown_reference and op.operands[1] == PLAYER_TROOP_REFERENCE, "tournament renown")
    return {
        "bet_amounts": tuple(entry[3] for entry in bets),
        "prize": prize.operands[1],
        "renown": renown.operands[2],
        "xp": xp.operands[0],
    }


def set_tournament_tweaks(menus_text: str, scripts_text: str, bet_amounts: tuple[int, ...], prize: int, renown: int, xp: int) -> str:
    if any(value <= 0 for value in bet_amounts) or len(set(bet_amounts)) != len(bet_amounts):
        raise ValueError("Tournament bet choices must be unique positive whole numbers.")
    if any(value < 0 for value in (prize, renown, xp)):
        raise ValueError("Tournament prize, renown, and XP cannot be negative.")
    lines, bets = _tournament_bet_layout(menus_text)
    if len(bet_amounts) != len(bets):
        raise ValueError(f"This module has {len(bets)} tournament bet choices; enter exactly {len(bets)} amounts.")
    by_line: dict[int, dict[int, str | int]] = {}
    for (option, affordability, assignment, _old), amount in zip(bets, bet_amounts):
        replacements = by_line.setdefault(option.line_index, {})
        replacements[affordability.operand_token_indices[1]] = amount
        replacements[option.text_token_index] = f"{amount}_denars."
        replacements[assignment.operand_token_indices[1]] = amount
    for line_index, replacements in by_line.items():
        lines[line_index] = _replace_nonspace_tokens(lines[line_index], replacements)
    updated = "".join(lines)
    lines, menu_index, _tokens, operations = _menu_record(updated, "town_tournament_won")
    renown_reference = _script_reference(scripts_text, "change_troop_renown")
    prize_op = _single_operation(operations, lambda op: op.opcode == 2133 and op.operands[:1] == (REGISTER_REFERENCE_BASE + 9,), "tournament prize")
    xp_op = _single_operation(operations, lambda op: op.opcode == 1062 and len(op.operands) == 2 and op.operands[1] == PLAYER_TROOP_REFERENCE, "tournament XP")
    renown_op = _single_operation(operations, lambda op: op.opcode == 1 and len(op.operands) == 3 and op.operands[0] == renown_reference and op.operands[1] == PLAYER_TROOP_REFERENCE, "tournament renown")
    lines[menu_index] = _replace_nonspace_tokens(lines[menu_index], {
        prize_op.operand_token_indices[1]: prize,
        xp_op.operand_token_indices[0]: xp,
        renown_op.operand_token_indices[2]: renown,
    })
    result = "".join(lines)
    expected = {"bet_amounts": bet_amounts, "prize": prize, "renown": renown, "xp": xp}
    if tournament_tweaks(result, scripts_text) != expected:
        raise RuntimeError("The tournament patch failed its verification check.")
    return result


def _volunteer_layout(operations: tuple[CompiledOperation, ...]) -> tuple[CompiledOperation, CompiledOperation, CompiledOperation]:
    matches = []
    for index in range(max(0, len(operations) - 5)):
        base = operations[index]
        if base.opcode != 2133 or len(base.operands) != 2 or index + 5 >= len(operations):
            continue
        variable = base.operands[0]
        sequence = operations[index + 1:index + 6]
        if (
            [operation.opcode for operation in sequence] == [4, 30, 2133, 2108, 2105]
            and sequence[2].operands[0] == variable
            and sequence[3].operands[0] == variable
            and sequence[4].operands[0] == variable
        ):
            multiplier = next((operation for operation in operations[index + 6:] if operation.opcode == 2107 and operation.operands[:1] == (variable,) and len(operation.operands) == 2), None)
            if multiplier:
                matches.append((base, sequence[4], multiplier))
    if len(matches) != 1:
        raise ValueError(f"Expected one guarded village volunteer formula, found {len(matches)}.")
    return matches[0]


def recruitment_tweaks(scripts_text: str) -> dict[str, int]:
    _lines, _index, _tokens, operations = _script_record(scripts_text, "update_volunteer_troops_in_village")
    base, relation_bonus, multiplier = _volunteer_layout(operations)
    _lines, _index, _tokens, recruit_ops = _script_record(scripts_text, "village_recruit_volunteers_recruit")
    gold_capacity = _single_operation(recruit_ops, lambda op: op.opcode == 2123 and len(op.operands) == 3 and 0 < op.operands[2] < 1_000_000, "village recruit affordability")
    total_cost = _single_operation(recruit_ops, lambda op: op.opcode == 2122 and len(op.operands) == 3 and 0 < op.operands[2] < 1_000_000, "village recruit cost")
    if gold_capacity.operands[2] != total_cost.operands[2]:
        raise ValueError("Village recruit price constants do not match.")
    _lines, _index, _tokens, mercenary_ops = _script_record(scripts_text, "update_mercenary_units_of_towns")
    mercenary_range = _single_operation(
        mercenary_ops,
        lambda op: op.opcode == 2136 and len(op.operands) == 3 and 0 <= op.operands[1] < op.operands[2] < 1_000_000,
        "tavern mercenary amount",
    )
    return {
        "village_base": base.operands[1],
        "village_relation_bonus": relation_bonus.operands[1],
        "village_multiplier": multiplier.operands[1],
        "village_price": gold_capacity.operands[2],
        "mercenary_min": mercenary_range.operands[1],
        "mercenary_max": mercenary_range.operands[2] - 1,
    }


def set_recruitment_tweaks(scripts_text: str, values: dict[str, int]) -> str:
    required = {"village_base", "village_relation_bonus", "village_multiplier", "village_price", "mercenary_min", "mercenary_max"}
    if set(values) != required or any(not isinstance(value, int) for value in values.values()):
        raise ValueError("Recruitment tweak values are incomplete.")
    if any(values[key] < 0 for key in ("village_base", "village_relation_bonus", "mercenary_min")):
        raise ValueError("Recruitment amounts cannot be negative.")
    if values["village_multiplier"] <= 0 or values["village_price"] <= 0:
        raise ValueError("Village amount multiplier and price must be positive.")
    if values["mercenary_max"] < values["mercenary_min"]:
        raise ValueError("Mercenary maximum must be at least the minimum.")
    _lines, _index, _tokens, operations = _script_record(scripts_text, "update_volunteer_troops_in_village")
    base, relation_bonus, multiplier = _volunteer_layout(operations)
    updated = _replace_script_tokens(scripts_text, "update_volunteer_troops_in_village", {
        base.operand_token_indices[1]: values["village_base"],
        relation_bonus.operand_token_indices[1]: values["village_relation_bonus"],
        multiplier.operand_token_indices[1]: values["village_multiplier"],
    })
    _lines, _index, _tokens, recruit_ops = _script_record(updated, "village_recruit_volunteers_recruit")
    gold_capacity = _single_operation(recruit_ops, lambda op: op.opcode == 2123 and len(op.operands) == 3 and 0 < op.operands[2] < 1_000_000, "village recruit affordability")
    total_cost = _single_operation(recruit_ops, lambda op: op.opcode == 2122 and len(op.operands) == 3 and 0 < op.operands[2] < 1_000_000, "village recruit cost")
    updated = _replace_script_tokens(updated, "village_recruit_volunteers_recruit", {
        gold_capacity.operand_token_indices[2]: values["village_price"],
        total_cost.operand_token_indices[2]: values["village_price"],
    })
    _lines, _index, _tokens, mercenary_ops = _script_record(updated, "update_mercenary_units_of_towns")
    mercenary_range = _single_operation(mercenary_ops, lambda op: op.opcode == 2136 and len(op.operands) == 3 and 0 <= op.operands[1] < op.operands[2] < 1_000_000, "tavern mercenary amount")
    updated = _replace_script_tokens(updated, "update_mercenary_units_of_towns", {
        mercenary_range.operand_token_indices[1]: values["mercenary_min"],
        mercenary_range.operand_token_indices[2]: values["mercenary_max"] + 1,
    })
    if recruitment_tweaks(updated) != values:
        raise RuntimeError("The recruitment patch failed its verification check.")
    return updated


def _siege_menu_layout(menus_text: str, menu_name: str, option_id: str, include_divisor: bool) -> tuple[
    list[str], int, CompiledOperation, CompiledOperation, CompiledOperation | None,
    CompiledMenuOption, CompiledOperation, CompiledOperation, CompiledOperation | None,
]:
    lines, menu_index, _tokens, operations = _menu_record(menus_text, menu_name)
    subtract = _single_operation(operations, lambda op: op.opcode == 2121 and len(op.operands) == 3, f"{menu_name} display base")
    multiply = _single_operation(operations, lambda op: op.opcode == 2107 and op.operands[:1] == (subtract.operands[0],), f"{menu_name} display multiplier")
    divide = _single_operation(operations, lambda op: op.opcode == 2108 and op.operands[:1] == (subtract.operands[0],), f"{menu_name} display divisor") if include_divisor else None
    _option_lines, options = _menu_options(menus_text, menu_name)
    option = next((entry for entry in options if entry.option_id == option_id), None)
    if option is None:
        raise ValueError(f"{option_id} was not found.")
    action_subtract = _single_operation(option.consequence_operations, lambda op: op.opcode == 2121 and len(op.operands) == 3, f"{menu_name} action base")
    action_multiply = _single_operation(option.consequence_operations, lambda op: op.opcode == 2107 and op.operands[:1] == (action_subtract.operands[0],), f"{menu_name} action multiplier")
    action_divide = _single_operation(option.consequence_operations, lambda op: op.opcode == 2108 and op.operands[:1] == (action_subtract.operands[0],), f"{menu_name} action divisor") if include_divisor else None
    if subtract.operands[1] != action_subtract.operands[1] or multiply.operands[1] != action_multiply.operands[1]:
        raise ValueError(f"{menu_name} display and action formulas do not match.")
    if include_divisor and (divide is None or action_divide is None or divide.operands[1] != action_divide.operands[1]):
        raise ValueError(f"{menu_name} display and action divisors do not match.")
    return lines, menu_index, subtract, multiply, divide, option, action_subtract, action_multiply, action_divide


def siege_tweaks(menus_text: str) -> dict[str, int]:
    ladder = _siege_menu_layout(menus_text, "construct_ladders", "mno_build_ladders_cont", True)
    tower = _siege_menu_layout(menus_text, "construct_siege_tower", "mno_build_siege_tower_cont", False)
    return {
        "ladder_skill_base": ladder[2].operands[1],
        "ladder_time_multiplier": ladder[3].operands[1],
        "ladder_time_divisor": ladder[4].operands[1],
        "tower_skill_base": tower[2].operands[1],
        "tower_time_multiplier": tower[3].operands[1],
    }


def set_siege_tweaks(menus_text: str, values: dict[str, int]) -> str:
    required = {"ladder_skill_base", "ladder_time_multiplier", "ladder_time_divisor", "tower_skill_base", "tower_time_multiplier"}
    if set(values) != required or any(not isinstance(value, int) or value <= 0 for value in values.values()):
        raise ValueError("Siege formula values must be positive whole numbers.")
    updated = menus_text
    for menu_name, option_id, prefix, include_divisor in (
        ("construct_ladders", "mno_build_ladders_cont", "ladder", True),
        ("construct_siege_tower", "mno_build_siege_tower_cont", "tower", False),
    ):
        lines, menu_index, subtract, multiply, divide, option, action_subtract, action_multiply, action_divide = _siege_menu_layout(updated, menu_name, option_id, include_divisor)
        lines[menu_index] = _replace_nonspace_tokens(lines[menu_index], {
            subtract.operand_token_indices[1]: values[f"{prefix}_skill_base"],
            multiply.operand_token_indices[1]: values[f"{prefix}_time_multiplier"],
            **({divide.operand_token_indices[1]: values["ladder_time_divisor"]} if divide else {}),
        })
        lines[option.line_index] = _replace_nonspace_tokens(lines[option.line_index], {
            action_subtract.operand_token_indices[1]: values[f"{prefix}_skill_base"],
            action_multiply.operand_token_indices[1]: values[f"{prefix}_time_multiplier"],
            **({action_divide.operand_token_indices[1]: values["ladder_time_divisor"]} if action_divide else {}),
        })
        updated = "".join(lines)
    if siege_tweaks(updated) != values:
        raise RuntimeError("The siege-time patch failed its verification check.")
    return updated


def _party_limit_layout(operations: tuple[CompiledOperation, ...]) -> tuple[CompiledOperation, CompiledOperation]:
    matches = []
    for index in range(len(operations) - 8):
        sequence = operations[index:index + 9]
        if [op.opcode for op in sequence] != [2133, 2170, 2172, 2107, 2105, 2105, 520, 2123, 2105]:
            continue
        limit = sequence[0].operands[0]
        if sequence[4].operands[0] == limit and sequence[5].operands[0] == limit and sequence[8].operands[0] == limit:
            matches.append((sequence[0], sequence[7]))
    if len(matches) != 1:
        raise ValueError(f"Expected one guarded party-size formula, found {len(matches)}.")
    return matches[0]


def _garrison_wage_layout(operations: tuple[CompiledOperation, ...]) -> CompiledOperation:
    matches = []
    for index in range(len(operations) - 3):
        sequence = operations[index:index + 4]
        if [op.opcode for op in sequence] == [2108, 2121, 2107, 2108] and sequence[0].operands[0] != sequence[3].operands[0]:
            matches.append(sequence[0])
    if len(matches) != 1:
        raise ValueError(f"Expected one guarded garrison-wage divisor, found {len(matches)}.")
    return matches[0]


def party_tweaks(scripts_text: str) -> dict[str, int]:
    _lines, _index, _tokens, limit_ops = _script_record(scripts_text, "game_get_party_companion_limit")
    base, renown_divisor = _party_limit_layout(limit_ops)
    _lines, _index, _tokens, wage_ops = _script_record(scripts_text, "calculate_player_faction_wage")
    garrison_divisor = _garrison_wage_layout(wage_ops)
    return {
        "party_base_size": base.operands[1],
        "party_renown_divisor": renown_divisor.operands[2],
        "garrison_wage_divisor": garrison_divisor.operands[1],
    }


def set_party_tweaks(scripts_text: str, values: dict[str, int]) -> str:
    required = {"party_base_size", "party_renown_divisor", "garrison_wage_divisor"}
    if set(values) != required or values["party_base_size"] < 0 or values["party_renown_divisor"] <= 0 or values["garrison_wage_divisor"] <= 0:
        raise ValueError("Party base size cannot be negative; renown and wage divisors must be positive.")
    _lines, _index, _tokens, operations = _script_record(scripts_text, "game_get_party_companion_limit")
    base, renown_divisor = _party_limit_layout(operations)
    updated = _replace_script_tokens(scripts_text, "game_get_party_companion_limit", {
        base.operand_token_indices[1]: values["party_base_size"],
        renown_divisor.operand_token_indices[2]: values["party_renown_divisor"],
    })
    _lines, _index, _tokens, operations = _script_record(updated, "calculate_player_faction_wage")
    garrison_divisor = _garrison_wage_layout(operations)
    updated = _replace_script_tokens(updated, "calculate_player_faction_wage", {garrison_divisor.operand_token_indices[1]: values["garrison_wage_divisor"]})
    if party_tweaks(updated) != values:
        raise RuntimeError("The party-rules patch failed its verification check.")
    return updated


def _battle_reward_layout(operations: tuple[CompiledOperation, ...]) -> tuple[CompiledOperation, ...]:
    level_bonus = _single_operation(operations, lambda op: op.opcode == 2120 and len(op.operands) == 3 and op.operands[2] > 0, "battle level bonus")
    reward_variable = level_bonus.operands[0]
    gain_divisor = _single_operation(operations, lambda op: op.opcode == 2108 and op.operands[:1] == (reward_variable,) and isinstance(op.operands[1], int), "battle reward divisor")
    stack_gain = _single_operation(operations, lambda op: op.opcode == 2122 and len(op.operands) == 3 and op.operands[1] == reward_variable, "battle stack reward")
    total_add = _single_operation(operations, lambda op: op.opcode == 2105 and len(op.operands) == 2 and op.operands[1] == stack_gain.operands[0], "battle total reward")
    total_variable = total_add.operands[0]
    cap = _single_operation(operations, lambda op: op.opcode == 2110 and op.operands[:1] == (total_variable,), "battle reward cap")
    assignments = [op for op in operations if op.opcode == 2133 and op.operands[1:] == (total_variable,)]
    if len(assignments) != 1:
        raise ValueError("The battle XP assignment is ambiguous.")
    xp_variable = assignments[0].operands[0]
    xp_start = operations.index(assignments[0])
    xp_end = next((index for index in range(xp_start + 1, len(operations)) if operations[index].opcode == 1674), None)
    if xp_end is None:
        raise ValueError("The battle XP award operation was not found.")
    xp_roll = _single_operation(operations[xp_start:xp_end], lambda op: op.opcode == 2136 and len(op.operands) == 3, "battle XP roll")
    xp_divisor = _single_operation(operations, lambda op: op.opcode == 2108 and op.operands[:1] == (xp_variable,), "battle XP divisor")
    gold_store = _single_operation(operations, lambda op: op.opcode == 2122 and len(op.operands) == 3 and op.operands[1] == total_variable and op.operands[2] > 0, "battle gold share")
    gold_variable = gold_store.operands[0]
    gold_cap = _single_operation(operations, lambda op: op.opcode == 2110 and op.operands[:1] == (gold_variable,), "battle gold cap")
    gold_start = operations.index(gold_cap)
    gold_roll = _single_operation(operations[gold_start:], lambda op: op.opcode == 2136 and len(op.operands) == 3 and any(step.opcode == 2107 and step.operands == (gold_variable, op.operands[0]) for step in operations[gold_start:]), "battle gold roll")
    gold_divisors = [op for op in operations if op.opcode == 2108 and op.operands[:1] == (gold_variable,)]
    if len(gold_divisors) != 2:
        raise ValueError("The battle gold divisor/share layout is unsupported.")
    gold_divisor = gold_divisors[0]
    return level_bonus, gain_divisor, cap, xp_roll, xp_divisor, gold_store, gold_cap, gold_roll, gold_divisor


def battle_reward_tweaks(scripts_text: str) -> dict[str, int]:
    _lines, _index, _tokens, operations = _script_record(scripts_text, "party_give_xp_and_gold")
    level, gain_div, _total_cap, xp_roll, xp_div, gold_store, gold_cap, gold_roll, gold_div = _battle_reward_layout(operations)
    return {
        "battle_level_bonus": level.operands[2],
        "battle_gain_divisor": gain_div.operands[1],
        "battle_gold_share": gold_store.operands[2],
        "battle_gold_cap": gold_cap.operands[1],
        "battle_gold_roll_min": gold_roll.operands[1],
        "battle_gold_roll_max": gold_roll.operands[2],
        "battle_gold_divisor": gold_div.operands[1],
        "battle_xp_roll_min": xp_roll.operands[1],
        "battle_xp_roll_max": xp_roll.operands[2],
        "battle_xp_divisor": xp_div.operands[1],
    }


def set_battle_reward_tweaks(scripts_text: str, values: dict[str, int]) -> str:
    required = {"battle_level_bonus", "battle_gain_divisor", "battle_gold_share", "battle_gold_cap", "battle_gold_roll_min", "battle_gold_roll_max", "battle_gold_divisor", "battle_xp_roll_min", "battle_xp_roll_max", "battle_xp_divisor"}
    if set(values) != required or values["battle_level_bonus"] < 0 or values["battle_gold_cap"] < 0:
        raise ValueError("Battle reward values are incomplete or negative.")
    for key in ("battle_gain_divisor", "battle_gold_share", "battle_gold_divisor", "battle_xp_divisor"):
        if values[key] <= 0:
            raise ValueError("Battle reward shares and divisors must be positive.")
    for prefix in ("battle_gold_roll", "battle_xp_roll"):
        if values[f"{prefix}_min"] < 0 or values[f"{prefix}_max"] <= values[f"{prefix}_min"]:
            raise ValueError("Battle reward roll maximums must be greater than their non-negative minimums.")
    _lines, _index, _tokens, operations = _script_record(scripts_text, "party_give_xp_and_gold")
    level, gain_div, _total_cap, xp_roll, xp_div, gold_store, gold_cap, gold_roll, gold_div = _battle_reward_layout(operations)
    updated = _replace_script_tokens(scripts_text, "party_give_xp_and_gold", {
        level.operand_token_indices[2]: values["battle_level_bonus"],
        gain_div.operand_token_indices[1]: values["battle_gain_divisor"],
        xp_roll.operand_token_indices[1]: values["battle_xp_roll_min"],
        xp_roll.operand_token_indices[2]: values["battle_xp_roll_max"],
        xp_div.operand_token_indices[1]: values["battle_xp_divisor"],
        gold_store.operand_token_indices[2]: values["battle_gold_share"],
        gold_cap.operand_token_indices[1]: values["battle_gold_cap"],
        gold_roll.operand_token_indices[1]: values["battle_gold_roll_min"],
        gold_roll.operand_token_indices[2]: values["battle_gold_roll_max"],
        gold_div.operand_token_indices[1]: values["battle_gold_divisor"],
    })
    if battle_reward_tweaks(updated) != values:
        raise RuntimeError("The battle-reward patch failed its verification check.")
    return updated


def parse_simple_triggers(text: str) -> list[CompiledSimpleTrigger]:
    lines = text.splitlines(keepends=True)
    if len(lines) < 2 or not lines[0].startswith("simple_triggers_file version "):
        raise ValueError("simple_triggers.txt has an unsupported header.")
    try:
        expected = int(lines[1].strip())
    except ValueError as exc:
        raise ValueError("simple_triggers.txt has an invalid record count.") from exc
    records = []
    for line_index, line in enumerate(lines[2:], start=2):
        if not line.strip():
            continue
        tokens = line.split()
        if len(tokens) < 2:
            raise ValueError(f"Simple trigger on line {line_index + 1} is truncated.")
        try:
            interval = float(tokens[0])
            count = int(tokens[1])
        except ValueError as exc:
            raise ValueError(f"Simple trigger on line {line_index + 1} has an invalid header.") from exc
        operations, end = _parse_compiled_operations(tokens, 2, count)
        if end != len(tokens):
            raise ValueError(f"Simple trigger on line {line_index + 1} has unexpected trailing tokens.")
        records.append(CompiledSimpleTrigger(line_index, interval, operations))
    if len(records) != expected:
        raise ValueError(f"simple_triggers.txt declares {expected} records but contains {len(records)}.")
    return records


def _simple_trigger_calling(simple_text: str, scripts_text: str, script_names: tuple[str, ...]) -> CompiledSimpleTrigger:
    references = {_script_reference(scripts_text, name) for name in script_names}
    matches = [record for record in parse_simple_triggers(simple_text) if references.issubset({op.operands[0] for op in record.operations if op.opcode == 1 and op.operands})]
    if len(matches) != 1:
        raise ValueError(f"Expected one guarded simple trigger calling {', '.join(script_names)}, found {len(matches)}.")
    return matches[0]


def _fief_income_layout(simple_text: str) -> tuple[CompiledSimpleTrigger, tuple[CompiledOperation, ...]]:
    matches = []
    for record in parse_simple_triggers(simple_text):
        operations = record.operations
        for index in range(len(operations) - 17):
            sequence = operations[index:index + 18]
            if [op.opcode for op in sequence] != [2133, 4, 541, 4, 541, 2133, 3, 5, 541, 2133, 5, 541, 2133, 3, 521, 2120, 2107, 2108]:
                continue
            rent_variable = sequence[0].operands[0]
            if all(sequence[offset].operands[:1] == (rent_variable,) for offset in (5, 9, 12, 16, 17)):
                matches.append((record, (sequence[5], sequence[9], sequence[12], sequence[15], sequence[17])))
    if len(matches) != 1:
        raise ValueError(f"Expected one guarded weekly fief-income formula, found {len(matches)}.")
    return matches[0]


def _food_time_layout(simple_text: str, scripts_text: str) -> tuple[CompiledSimpleTrigger, CompiledOperation]:
    record = _simple_trigger_calling(simple_text, scripts_text, ("consume_food",))
    calls = [op for op in record.operations if op.opcode == 1 and op.operands[0] == _script_reference(scripts_text, "consume_food")]
    if len(calls) != 1:
        raise ValueError("The food-consumption call is ambiguous.")
    divisions = [op for op in record.operations if op.opcode == 2108 and len(op.operands) == 2 and 0 < op.operands[1] < 1000]
    if len(divisions) != 1:
        raise ValueError("The troops-per-food-unit formula is ambiguous.")
    return record, divisions[0]


def campaign_time_tweaks(simple_text: str, scripts_text: str) -> dict[str, int | float]:
    fief_record, fief = _fief_income_layout(simple_text)
    food_record, food_divisor = _food_time_layout(simple_text, scripts_text)
    refresh_record = _simple_trigger_calling(simple_text, scripts_text, ("update_mercenary_units_of_towns", "update_volunteer_troops_in_village"))
    village, castle, town, prosperity, divisor = fief
    return {
        "village_rent": village.operands[1],
        "castle_rent": castle.operands[1],
        "town_rent": town.operands[1],
        "prosperity_base": prosperity.operands[1],
        "prosperity_divisor": divisor.operands[1],
        "fief_interval_hours": fief_record.interval,
        "food_interval_hours": food_record.interval,
        "food_troops_per_unit": food_divisor.operands[1],
        "refresh_interval_hours": refresh_record.interval,
    }


def set_campaign_time_tweaks(simple_text: str, scripts_text: str, values: dict[str, int | float]) -> str:
    required = {"village_rent", "castle_rent", "town_rent", "prosperity_base", "prosperity_divisor", "fief_interval_hours", "food_interval_hours", "food_troops_per_unit", "refresh_interval_hours"}
    if set(values) != required:
        raise ValueError("Campaign economy/time tweak values are incomplete.")
    for key in ("village_rent", "castle_rent", "town_rent", "prosperity_base"):
        if not isinstance(values[key], int) or values[key] < 0:
            raise ValueError("Fief rent and prosperity values must be non-negative whole numbers.")
    for key in ("prosperity_divisor", "food_troops_per_unit"):
        if not isinstance(values[key], int) or values[key] <= 0:
            raise ValueError("Campaign divisors must be positive whole numbers.")
    for key in ("fief_interval_hours", "food_interval_hours", "refresh_interval_hours"):
        if float(values[key]) <= 0:
            raise ValueError("Campaign time intervals must be positive numbers.")
    lines = simple_text.splitlines(keepends=True)
    fief_record, fief = _fief_income_layout(simple_text)
    village, castle, town, prosperity, divisor = fief
    lines[fief_record.line_index] = _replace_nonspace_tokens(lines[fief_record.line_index], {
        0: f"{float(values['fief_interval_hours']):.6f}",
        village.operand_token_indices[1]: values["village_rent"],
        castle.operand_token_indices[1]: values["castle_rent"],
        town.operand_token_indices[1]: values["town_rent"],
        prosperity.operand_token_indices[1]: values["prosperity_base"],
        divisor.operand_token_indices[1]: values["prosperity_divisor"],
    })
    updated = "".join(lines)
    lines = updated.splitlines(keepends=True)
    food_record, food_divisor = _food_time_layout(updated, scripts_text)
    lines[food_record.line_index] = _replace_nonspace_tokens(lines[food_record.line_index], {
        0: f"{float(values['food_interval_hours']):.6f}",
        food_divisor.operand_token_indices[1]: values["food_troops_per_unit"],
    })
    updated = "".join(lines)
    lines = updated.splitlines(keepends=True)
    refresh_record = _simple_trigger_calling(updated, scripts_text, ("update_mercenary_units_of_towns", "update_volunteer_troops_in_village"))
    lines[refresh_record.line_index] = _replace_nonspace_tokens(lines[refresh_record.line_index], {0: f"{float(values['refresh_interval_hours']):.6f}"})
    updated = "".join(lines)
    if campaign_time_tweaks(updated, scripts_text) != {key: float(value) if key.endswith("_hours") else value for key, value in values.items()}:
        raise RuntimeError("The campaign economy/time patch failed its verification check.")
    return updated


def _prisoner_price_layout(operations: tuple[CompiledOperation, ...]) -> tuple[CompiledOperation, CompiledOperation, CompiledOperation]:
    matches = []
    for index in range(len(operations) - 6):
        sequence = operations[index:index + 7]
        if [operation.opcode for operation in sequence] != [2171, 2133, 2105, 2107, 2108, 5, 2133]:
            continue
        price_variable = sequence[1].operands[0]
        if all(sequence[offset].operands[:1] == (price_variable,) for offset in (2, 3, 4, 6)):
            matches.append((sequence[2], sequence[4], sequence[6]))
    if len(matches) != 1:
        raise ValueError(f"Expected one guarded prisoner-price formula, found {len(matches)}.")
    return matches[0]


def prisoner_price_tweaks(scripts_text: str) -> dict[str, int]:
    _lines, _index, _tokens, operations = _script_record(scripts_text, "game_get_prisoner_price")
    level_bonus, divisor, minimum = _prisoner_price_layout(operations)
    return {"prisoner_level_bonus": level_bonus.operands[1], "prisoner_divisor": divisor.operands[1], "prisoner_minimum": minimum.operands[1]}


def set_prisoner_price_tweaks(scripts_text: str, values: dict[str, int]) -> str:
    required = {"prisoner_level_bonus", "prisoner_divisor", "prisoner_minimum"}
    if set(values) != required or values["prisoner_level_bonus"] < 0 or values["prisoner_divisor"] <= 0 or values["prisoner_minimum"] < 0:
        raise ValueError("Prisoner pricing needs a non-negative level bonus/minimum and a positive divisor.")
    _lines, _index, _tokens, operations = _script_record(scripts_text, "game_get_prisoner_price")
    level_bonus, divisor, minimum = _prisoner_price_layout(operations)
    updated = _replace_script_tokens(scripts_text, "game_get_prisoner_price", {
        level_bonus.operand_token_indices[1]: values["prisoner_level_bonus"],
        divisor.operand_token_indices[1]: values["prisoner_divisor"],
        minimum.operand_token_indices[1]: values["prisoner_minimum"],
    })
    if prisoner_price_tweaks(updated) != values:
        raise RuntimeError("The prisoner-price patch failed its verification check.")
    return updated


def _dialog_record_tokens(line: str) -> tuple[list[str], int]:
    tokens = line.split()
    if len(tokens) < 8 or not tokens[0].startswith("dlga_"):
        raise ValueError("A compiled dialog record has an unsupported layout.")
    try:
        condition_count = int(tokens[3])
    except ValueError as exc:
        raise ValueError("A compiled dialog has an invalid condition count.") from exc
    _conditions, text_index = _parse_compiled_operations(tokens, 4, condition_count)
    if text_index + 2 >= len(tokens):
        raise ValueError("A compiled dialog is missing text or its consequence block.")
    try:
        consequence_count = int(tokens[text_index + 2])
    except ValueError as exc:
        raise ValueError("A compiled dialog has an invalid consequence count.") from exc
    _consequences, end = _parse_compiled_operations(tokens, text_index + 3, consequence_count)
    if end >= len(tokens):
        raise ValueError("A compiled dialog is missing its voice-over field.")
    return tokens, text_index


def tavern_prisoner_sales_state(text: str) -> str:
    lines = text.splitlines()
    marker = [line for line in lines if line.split()[:1] == [TAVERN_PRISONER_DIALOG_ID]]
    if len(marker) == 1:
        _dialog_record_tokens(marker[0])
        return "enabled"
    if len(marker) > 1:
        return "unsupported"
    source = next((line for line in lines if line.startswith("dlga_ransom_broker_talk:ransom_broker_sell_prisoners ")), None)
    anchor = next((line for line in lines if line.startswith("dlga_tavernkeeper_talk:close_window ")), None)
    if not source or not anchor:
        return "unsupported"
    _dialog_record_tokens(source)
    _dialog_record_tokens(anchor)
    return "disabled"


def set_tavern_prisoner_sales(text: str, enabled: bool) -> str:
    state = tavern_prisoner_sales_state(text)
    if state == "unsupported":
        raise ValueError("This conversation.txt does not have the guarded Native tavern/ransom dialog layout.")
    if (state == "enabled") == enabled:
        return text
    lines = text.splitlines(keepends=True)
    count_match = re.match(r"^(\s*)\d+([ \t]*)(\r?\n)?$", lines[1]) if len(lines) > 1 else None
    if not count_match:
        raise ValueError("conversation.txt has an unsupported record-count line.")
    current_count = int(lines[1].strip())
    if enabled:
        source_index = next(index for index, line in enumerate(lines) if line.startswith("dlga_ransom_broker_talk:ransom_broker_sell_prisoners "))
        anchor_index = next(index for index, line in enumerate(lines) if line.startswith("dlga_tavernkeeper_talk:close_window "))
        source_tokens, text_index = _dialog_record_tokens(lines[source_index])
        anchor_tokens, _anchor_text = _dialog_record_tokens(lines[anchor_index])
        cloned = _replace_nonspace_tokens(lines[source_index], {
            0: TAVERN_PRISONER_DIALOG_ID,
            2: anchor_tokens[2],
            text_index: "I_have_prisoners_to_sell.",
        })
        lines.insert(anchor_index, cloned)
        new_count = current_count + 1
    else:
        marker_indices = [index for index, line in enumerate(lines) if line.split()[:1] == [TAVERN_PRISONER_DIALOG_ID]]
        if len(marker_indices) != 1:
            raise ValueError("The PVN tavern-prisoner dialog marker is missing or duplicated.")
        lines.pop(marker_indices[0])
        new_count = current_count - 1
    lines[1] = f"{count_match.group(1)}{new_count}{count_match.group(2)}{count_match.group(3) or ''}"
    updated = "".join(lines)
    expected = "enabled" if enabled else "disabled"
    if tavern_prisoner_sales_state(updated) != expected or len(updated.splitlines()) - 2 != new_count:
        raise RuntimeError("The tavern prisoner-sale patch failed its verification check.")
    return updated


def parse_skills(text: str) -> list[SkillRecord]:
    lines = text.splitlines(keepends=True)
    if not lines:
        raise ValueError("skills.txt is empty.")
    try:
        expected = int(lines[0].strip())
    except ValueError as exc:
        raise ValueError("skills.txt has an invalid record count.") from exc
    records: list[SkillRecord] = []
    for line_index, line in enumerate(lines[1:], start=1):
        if not line.strip():
            continue
        tokens = line.rstrip("\r\n").split(maxsplit=4)
        if len(tokens) != 5 or not tokens[0].startswith("skl_"):
            raise ValueError(f"Skill record on line {line_index + 1} is invalid.")
        try:
            flags, max_level = map(int, tokens[2:4])
        except ValueError as exc:
            raise ValueError(f"Skill record on line {line_index + 1} has non-numeric flags or maximum.") from exc
        if max_level < 0:
            raise ValueError(f"Skill record on line {line_index + 1} has a negative maximum.")
        records.append(SkillRecord(line_index, tokens[0], tokens[1], flags, max_level, tokens[4]))
    if len(records) != expected:
        raise ValueError(f"skills.txt declares {expected} records but contains {len(records)}.")
    return records


def apply_skill_maximums(text: str, maximums: dict[int, int]) -> str:
    if not maximums:
        return text
    lines = text.splitlines(keepends=True)
    records = {record.line_index: record for record in parse_skills(text)}
    for line_index, maximum in maximums.items():
        if line_index not in records:
            raise ValueError(f"Skill line {line_index + 1} no longer exists.")
        if maximum < 0 or maximum > 15:
            raise ValueError("Warband skill maximums must be between 0 and 15.")
        matches = list(re.finditer(r"\S+", lines[line_index]))
        if len(matches) != 5:
            raise ValueError(f"Skill record on line {line_index + 1} has an unsupported layout.")
        lines[line_index] = _replace_nonspace_tokens(lines[line_index], {3: maximum})
    updated = "".join(lines)
    reparsed = {record.line_index: record for record in parse_skills(updated)}
    if any(reparsed[index].max_level != maximum for index, maximum in maximums.items()):
        raise RuntimeError("The skill-maximum patch failed its verification check.")
    return updated


def validate_party_template(record: PartyTemplateRecord, troop_count: int | None = None) -> None:
    if not record.template_id.startswith("pt_") or any(character.isspace() for character in record.template_id):
        raise ValueError("A party-template ID must start with pt_ and cannot contain spaces.")
    if not record.name or any(character.isspace() for character in record.name):
        raise ValueError("A party-template name cannot be blank or contain spaces; use underscores.")
    if len(record.stacks) > 6:
        raise ValueError("Warband party templates can contain at most six troop stacks.")
    for stack in record.stacks:
        if stack.troop_index < 0 or (troop_count is not None and stack.troop_index >= troop_count):
            raise ValueError(f"Troop index {stack.troop_index} is outside troops.txt.")
        if stack.minimum < 0 or stack.maximum < 0:
            raise ValueError("Troop stack sizes cannot be negative.")
        if stack.minimum > stack.maximum:
            raise ValueError("A troop stack minimum cannot exceed its maximum.")


def format_party_template(record: PartyTemplateRecord, newline: str = os.linesep) -> str:
    validate_party_template(record)
    tokens = [
        record.template_id, record.name, str(record.flags), str(record.menu),
        str(record.faction), str(record.personality),
    ]
    for stack in record.stacks:
        tokens.extend((str(stack.troop_index), str(stack.minimum), str(stack.maximum), str(stack.member_flags)))
    tokens.extend("-1" for _ in range(6 - len(record.stacks)))
    return " ".join(tokens) + " " + newline


def apply_party_template_updates(text: str, updates: dict[int, PartyTemplateRecord]) -> str:
    lines = text.splitlines(keepends=True)
    current = {record.line_index: record for record in parse_party_templates(text)}
    default_newline = "\r\n" if "\r\n" in text else "\n"
    for line_index, record in updates.items():
        original = current.get(line_index)
        if original is None or line_index >= len(lines):
            raise ValueError(f"Party template line {line_index + 1} no longer exists.")
        if record.template_id != original.template_id:
            raise ValueError("Party-template IDs cannot be changed in this editor.")
        validate_party_template(record)
        newline = "\r\n" if lines[line_index].endswith("\r\n") else "\n" if lines[line_index].endswith("\n") else default_newline
        lines[line_index] = format_party_template(record, newline)
    return "".join(lines)


def item_type_name(item_flags: int) -> str:
    return ITEM_TYPES.get(item_flags & 0xFF, f"Unknown type {item_flags & 0xFF}")


def normalize_item_id(raw: str) -> str:
    item_id = raw.strip().replace(" ", "_").replace("-", "_")
    if not item_id.lower().startswith("itm_"):
        item_id = f"itm_{item_id}"
    item_id = item_id.lower()
    if not re.fullmatch(r"itm_[a-z0-9_]+", item_id):
        raise ValueError("Item IDs may contain only letters, numbers, and underscores.")
    if item_id == "itm_":
        raise ValueError("Enter a name after itm_.")
    return item_id


def rebuild_item_flags(base_value: int, type_code: int, attachment: int, kill_info: int, enabled_keys: set[str]) -> int:
    if type_code not in ITEM_TYPES:
        raise ValueError("Choose a valid item type.")
    if attachment & ~0xF00:
        raise ValueError("Attachment value exceeds the Module System attachment mask.")
    if not 0 <= kill_info <= 7:
        raise ValueError("Custom kill-info icon must be from 0 to 7.")
    option_by_key = {key: bit for key, _label, bit, _help in ITEM_FLAG_OPTIONS}
    unknown_keys = enabled_keys - option_by_key.keys()
    if unknown_keys:
        raise ValueError(f"Unknown item flag controls: {', '.join(sorted(unknown_keys))}")
    result = base_value & ~ITEM_FLAG_KNOWN_MASK
    result |= type_code | attachment | (kill_info << 56)
    for key in enabled_keys:
        result |= option_by_key[key]
    return result


def rebuild_capabilities(base_value: int, shoot_action: int, carry_position: int, reload_action: int, enabled_keys: set[str]) -> int:
    if shoot_action & ~CAPABILITY_SHOOT_MASK:
        raise ValueError("Shoot/throw action exceeds its Module System mask.")
    if carry_position & ~CAPABILITY_CARRY_MASK:
        raise ValueError("Carry position exceeds its Module System mask.")
    if reload_action & ~CAPABILITY_RELOAD_MASK:
        raise ValueError("Reload action exceeds its Module System mask.")
    option_by_key = {key: bit for key, _label, bit, _help in CAPABILITY_OPTIONS}
    unknown_keys = enabled_keys - option_by_key.keys()
    if unknown_keys:
        raise ValueError(f"Unknown capability controls: {', '.join(sorted(unknown_keys))}")
    result = base_value & ~CAPABILITY_KNOWN_MASK
    result |= shoot_action | carry_position | reload_action
    for key in enabled_keys:
        result |= option_by_key[key]
    return result


def unpack_damage(packed: int) -> tuple[int, int]:
    return packed & 0xFF, (packed >> 8) & 0x3


def pack_damage(amount: int, damage_type: int) -> int:
    if not 0 <= amount <= 255:
        raise ValueError("Damage amount must be from 0 to 255.")
    if damage_type not in DAMAGE_TYPES:
        raise ValueError("Damage type must be Cut, Pierce, Blunt, or Reserved.")
    return amount | (damage_type << 8)


def validate_item_record(record: ItemRecord) -> None:
    if not record.item_id.startswith("itm_") or any(character.isspace() for character in record.item_id):
        raise ValueError("An item ID must start with itm_ and cannot contain spaces.")
    for label, value in (("singular name", record.singular_name), ("plural name", record.plural_name)):
        if not value or any(character.isspace() for character in value):
            raise ValueError(f"The {label} cannot be blank or contain spaces; use underscores.")
    if not record.meshes:
        raise ValueError("An item needs at least one mesh entry.")
    for mesh in record.meshes:
        if not mesh.name or any(character.isspace() for character in mesh.name):
            raise ValueError("Item mesh names cannot be blank or contain spaces.")
    if record.weight < 0:
        raise ValueError("Item weight cannot be negative.")
    for label, value in (
        ("value", record.value), ("abundance", record.abundance), ("head armor", record.head_armor),
        ("body armor", record.body_armor), ("leg armor", record.leg_armor), ("difficulty", record.difficulty),
        ("hit points", record.hit_points), ("speed rating", record.speed_rating),
        ("missile speed", record.missile_speed), ("weapon length", record.weapon_length),
        ("maximum ammo", record.max_ammo),
    ):
        if value < 0:
            raise ValueError(f"Item {label} cannot be negative.")
    for packed in (record.thrust_damage, record.swing_damage):
        amount, damage_type = unpack_damage(packed)
        pack_damage(amount, damage_type)


def parse_item_kinds(text: str) -> list[ItemRecord]:
    lines = text.splitlines(keepends=True)
    if len(lines) < 2 or not lines[0].strip().lower().startswith("itemsfile version"):
        raise ValueError("This is not a supported item_kinds1.txt file.")
    try:
        expected_count = int(lines[1].strip())
    except ValueError as exc:
        raise ValueError("item_kinds1.txt has an invalid record count.") from exc
    starts = [index for index, line in enumerate(lines[2:], start=2) if line.lstrip().startswith("itm_")]
    records: list[ItemRecord] = []
    boundaries = starts + [len(lines)]
    for start, end in zip(boundaries, boundaries[1:]):
        tokens = lines[start].split()
        if len(tokens) < 4:
            raise ValueError(f"Item record on line {start + 1} is incomplete.")
        try:
            mesh_count = int(tokens[3])
        except ValueError as exc:
            raise ValueError(f"Item record on line {start + 1} has an invalid mesh count.") from exc
        tail_start = 4 + (mesh_count * 2)
        if mesh_count < 1 or len(tokens) != tail_start + 17:
            raise ValueError(f"Item record on line {start + 1} has an unexpected field count.")
        try:
            meshes = tuple(ItemMesh(tokens[4 + (index * 2)], int(tokens[5 + (index * 2)])) for index in range(mesh_count))
            tail = tokens[tail_start:]
            item_flags, capabilities, value, modifiers = map(int, tail[:4])
            weight = float(tail[4])
            numeric_tail = list(map(int, tail[5:]))
        except ValueError as exc:
            raise ValueError(f"Item record on line {start + 1} has a non-numeric field.") from exc
        nonempty = [index for index in range(start + 1, end) if lines[index].strip()]
        if len(nonempty) < 2:
            raise ValueError(f"Item record on line {start + 1} is missing factions or triggers.")
        cursor = 0
        try:
            faction_count = int(lines[nonempty[cursor]].strip())
        except ValueError as exc:
            raise ValueError(f"Item record on line {start + 1} has an invalid faction count.") from exc
        cursor += 1
        factions: tuple[int, ...] = ()
        if faction_count:
            if cursor >= len(nonempty):
                raise ValueError(f"Item record on line {start + 1} is missing faction IDs.")
            try:
                factions = tuple(map(int, lines[nonempty[cursor]].split()))
            except ValueError as exc:
                raise ValueError(f"Item record on line {start + 1} has an invalid faction ID.") from exc
            if len(factions) != faction_count:
                raise ValueError(f"Item record on line {start + 1} declares {faction_count} factions but lists {len(factions)}.")
            cursor += 1
        if cursor >= len(nonempty):
            raise ValueError(f"Item record on line {start + 1} is missing its trigger count.")
        try:
            trigger_count = int(lines[nonempty[cursor]].strip())
        except ValueError as exc:
            raise ValueError(f"Item record on line {start + 1} has an invalid trigger count.") from exc
        cursor += 1
        if len(nonempty) - cursor != trigger_count:
            raise ValueError(f"Item record on line {start + 1} declares {trigger_count} triggers but contains {len(nonempty) - cursor}.")
        record = ItemRecord(
            start, tokens[0], tokens[1], tokens[2], meshes, item_flags, capabilities,
            value, modifiers, weight, *numeric_tail, factions, trigger_count,
        )
        validate_item_record(record)
        records.append(record)
    if len(records) != expected_count:
        raise ValueError(f"item_kinds1.txt declares {expected_count} records but contains {len(records)}.")
    return records


def format_item_record(record: ItemRecord, newline: str = os.linesep) -> str:
    validate_item_record(record)
    tokens = [record.item_id, record.singular_name, record.plural_name, str(len(record.meshes))]
    for mesh in record.meshes:
        tokens.extend((mesh.name, str(mesh.flags)))
    tokens.extend((
        str(record.item_flags), str(record.capabilities), str(record.value), str(record.modifiers),
        f"{record.weight:.6f}", str(record.abundance), str(record.head_armor), str(record.body_armor),
        str(record.leg_armor), str(record.difficulty), str(record.hit_points), str(record.speed_rating),
        str(record.missile_speed), str(record.weapon_length), str(record.max_ammo),
        str(record.thrust_damage), str(record.swing_damage),
    ))
    return " " + " ".join(tokens) + newline


def apply_item_updates(text: str, updates: dict[int, ItemRecord]) -> str:
    lines = text.splitlines(keepends=True)
    current = {record.line_index: record for record in parse_item_kinds(text)}
    default_newline = "\r\n" if "\r\n" in text else "\n"
    for line_index, record in updates.items():
        original = current.get(line_index)
        if original is None or line_index >= len(lines):
            raise ValueError(f"Item line {line_index + 1} no longer exists.")
        if record.item_id != original.item_id:
            raise ValueError("Item IDs cannot be changed in this editor.")
        if record.meshes != original.meshes or record.factions != original.factions or record.trigger_count != original.trigger_count:
            raise ValueError("Meshes, faction restrictions, and triggers must be edited in the Advanced Module Files tab.")
        newline = "\r\n" if lines[line_index].endswith("\r\n") else "\n" if lines[line_index].endswith("\n") else default_newline
        lines[line_index] = format_item_record(record, newline)
    return "".join(lines)


def find_terminal_item_sentinel(records: list[ItemRecord]) -> ItemRecord | None:
    sentinels = []
    for record in records:
        item_id = record.item_id.casefold()
        singular = record.singular_name.replace("_", "").casefold()
        plural = record.plural_name.replace("_", "").casefold()
        if item_id.endswith(("items_end", "end_items")) or singular == "itemsend" or plural == "itemsend":
            sentinels.append(record)
    return sentinels[-1] if sentinels else None


def append_item_records(text: str, additions: list[ItemAddition]) -> str:
    if not additions:
        return text
    records = parse_item_kinds(text)
    sentinel = find_terminal_item_sentinel(records)
    if sentinel is None:
        raise ValueError("No terminal Items_End record was found; new items cannot be inserted safely.")
    existing_ids = {record.item_id.casefold() for record in records}
    new_ids: set[str] = set()
    records_by_id: dict[str, list[ItemRecord]] = {}
    for existing in records:
        records_by_id.setdefault(existing.item_id.casefold(), []).append(existing)
    record_by_line = {record.line_index: record for record in records}
    lines = text.splitlines(keepends=True)
    record_positions = {record.line_index: index for index, record in enumerate(records)}
    newline = "\r\n" if "\r\n" in text else "\n"
    blocks: list[str] = []
    for addition in additions:
        record = addition.record
        validate_item_record(record)
        folded_id = record.item_id.casefold()
        if folded_id in existing_ids or folded_id in new_ids:
            raise ValueError(f"Item ID already exists: {record.item_id}")
        if find_terminal_item_sentinel([record]) is not None:
            raise ValueError("A newly created item cannot use an Items_End sentinel name.")
        new_ids.add(folded_id)
        main_line = format_item_record(record, newline)
        if addition.source_item_id:
            source_key = addition.source_item_id.casefold()
            if addition.source_line_index is not None:
                source = record_by_line.get(addition.source_line_index)
                if source is not None and source.item_id.casefold() != source_key:
                    source = None
            else:
                matches = records_by_id.get(source_key, [])
                if len(matches) > 1:
                    raise ValueError(f"Clone source ID is ambiguous in this module: {addition.source_item_id}")
                source = matches[0] if matches else None
            if source is None:
                raise ValueError(f"Clone source no longer exists: {addition.source_item_id}")
            if record.meshes != source.meshes or record.factions != source.factions or record.trigger_count != source.trigger_count:
                raise ValueError("A cloned item's meshes, factions, and triggers must match its source record.")
            source_position = record_positions[source.line_index]
            source_end = records[source_position + 1].line_index if source_position + 1 < len(records) else len(lines)
            blocks.append(main_line + "".join(lines[source.line_index + 1:source_end]))
        else:
            if record.factions or record.trigger_count:
                raise ValueError("A new blank item cannot contain factions or triggers without a source block.")
            blocks.append(main_line + f" 0{newline}0{newline}{newline}")
    count_match = re.match(r"^([ \t]*)(\d+)([ \t]*)(\r?\n)?$", lines[1])
    if not count_match:
        raise ValueError("item_kinds1.txt has an invalid count line.")
    new_count = int(count_match.group(2)) + len(additions)
    lines[1] = f"{count_match.group(1)}{new_count}{count_match.group(3)}{count_match.group(4) or ''}"
    lines[sentinel.line_index:sentinel.line_index] = ["".join(blocks)]
    updated = "".join(lines)
    reparsed = parse_item_kinds(updated)
    updated_sentinel = find_terminal_item_sentinel(reparsed)
    if updated_sentinel is None or updated_sentinel.item_id != sentinel.item_id:
        raise ValueError("The terminal Items_End record was not preserved.")
    if len(reparsed) != len(records) + len(additions):
        raise ValueError("The inserted item count did not validate.")
    return updated


def apply_config_updates(text: str, updates: dict[int, str]) -> str:
    lines = text.splitlines(keepends=True)
    for line_index, new_value in updates.items():
        if "\n" in new_value or "\r" in new_value:
            raise ValueError("Config values must stay on one line.")
        if line_index < 0 or line_index >= len(lines):
            raise ValueError(f"Config line {line_index + 1} no longer exists.")
        match = CONFIG_LINE_PATTERN.match(lines[line_index])
        if not match:
            raise ValueError(f"Config line {line_index + 1} is no longer editable.")
        lines[line_index] = f"{match.group(1)}{match.group(2)}{match.group(3)}{new_value}{match.group(5)}{match.group(6) or ''}"
    return "".join(lines)


def normalize_line_endings(text: str, newline: str) -> str:
    if newline not in {"\n", "\r\n", "\r"}:
        raise ValueError("Unsupported line-ending style.")
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    return normalized if newline == "\n" else normalized.replace("\n", newline)


def validate_config_value(original: str, proposed: str) -> str:
    value = proposed.strip()
    if not value:
        raise ValueError("A config value cannot be blank.")
    if "\n" in value or "\r" in value:
        raise ValueError("A config value cannot contain a new line.")
    if re.fullmatch(r"[-+]?\d+", original.strip()) and not re.fullmatch(r"[-+]?\d+", value):
        raise ValueError("This setting requires a whole number.")
    if re.fullmatch(r"[-+]?(?:\d+\.?\d*|\.\d+)", original.strip()) and not re.fullmatch(r"[-+]?(?:\d+\.?\d*|\.\d+)", value):
        raise ValueError("This setting requires a numeric value.")
    return value


def read_config(path: Path) -> tuple[str, str]:
    raw = path.read_bytes()
    encodings = ("utf-8-sig", "utf-8", "cp1252") if raw.startswith(b"\xef\xbb\xbf") else ("utf-8", "cp1252")
    for encoding in encodings:
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1"), "latin-1"


def require_unchanged_text(original: str, latest: str, filename: str) -> None:
    if latest != original:
        raise RuntimeError(f"{filename} changed outside this app. Reload it before saving so outside changes are not overwritten.")


def find_default_config() -> Path | None:
    profile = Path(os.environ.get("USERPROFILE", Path.home()))
    candidates = [
        profile / "Documents" / "Mount&Blade Warband" / "rgl_config.txt",
        profile / "OneDrive" / "Documents" / "Mount&Blade Warband" / "rgl_config.txt",
        Path.home() / "Documents" / "Mount&Blade Warband" / "rgl_config.txt",
    ]
    return next((path for path in candidates if path.is_file()), None)


def find_warband_install() -> Path | None:
    candidates: list[Path] = []
    for variable in ("PROGRAMFILES(X86)", "PROGRAMFILES"):
        base = os.environ.get(variable)
        if base:
            candidates.extend([
                Path(base) / "Mount&Blade Warband",
                Path(base) / "Steam" / "steamapps" / "common" / "MountBlade Warband",
                Path(base) / "Steam" / "steamapps" / "common" / "Mount & Blade Warband",
            ])
    candidates.extend([
        Path("C:/Program Files (x86)/Mount&Blade Warband"),
        Path("C:/Program Files (x86)/Steam/steamapps/common/MountBlade Warband"),
        Path("C:/Program Files/Steam/steamapps/common/MountBlade Warband"),
    ])
    seen: set[Path] = set()
    for candidate in candidates:
        normalized = candidate.resolve()
        if normalized in seen:
            continue
        seen.add(normalized)
        if (normalized / "Modules").is_dir():
            return normalized
    return None


def discover_modules(warband_install: Path) -> list[Path]:
    modules_dir = warband_install / "Modules"
    if warband_install.name.lower() == "modules":
        modules_dir = warband_install
    if not modules_dir.is_dir():
        return []
    return sorted(
        (path for path in modules_dir.iterdir() if path.is_dir() and (path / "module.ini").is_file()),
        key=lambda path: path.name.casefold(),
    )


def module_setting_category(key: str) -> str:
    lowered = key.lower()
    if lowered in {"load_resource", "load_mod_resource"}:
        return "Resources"
    for category, keys in MODULE_SETTING_GROUPS.items():
        if lowered in keys:
            return category
    return "Advanced"


def clone_module(source: Path, destination: Path, module_name: str) -> Path:
    source = source.resolve()
    destination = destination.resolve()
    name = module_name.strip()
    if not (source / "module.ini").is_file():
        raise FileNotFoundError(f"The source is not a Warband module:\n{source}")
    if not name:
        raise ValueError("The cloned module needs a display name.")
    if any(character in name for character in "\r\n"):
        raise ValueError("The module name must stay on one line.")
    if destination.exists():
        raise FileExistsError(f"The destination already exists:\n{destination}")
    if source == destination or source in destination.parents:
        raise ValueError("The clone cannot be created inside its source module.")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)
    ini_path = destination / "module.ini"
    text, encoding = read_config(ini_path)
    entries = parse_config_entries(text)
    module_entry = next((entry for entry in entries if entry.key.lower() == "module_name"), None)
    if module_entry:
        updated = apply_config_updates(text, {module_entry.line_index: name})
    else:
        separator = "" if not text or text.endswith(("\n", "\r")) else os.linesep
        updated = f"{text}{separator}module_name = {name}{os.linesep}"
    ini_path.write_bytes(updated.encode(encoding))
    return destination


def write_config_text(path: Path, updated: str, encoding: str, lock_after: bool) -> Path:
    return write_config_batch([(path, updated, encoding, lock_after)])[0]


def write_config_batch(requests: list[tuple[Path, str, str, bool]]) -> list[Path]:
    """Write one or more text files as one rollback-protected operation.

    Every replacement is fully encoded and flushed before any target is changed.
    If a later replacement fails, earlier targets are restored byte-for-byte and
    to their original access mode. Timestamped backups remain available even
    after a rollback so the failed operation is still auditable.
    """
    if not requests:
        return []
    resolved = [path.resolve() for path, _updated, _encoding, _lock_after in requests]
    if len(set(resolved)) != len(resolved):
        raise ValueError("A batch save cannot contain the same file more than once.")

    stamp = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    states: list[dict[str, object]] = []
    for path, updated, encoding, lock_after in requests:
        if not path.is_file():
            raise FileNotFoundError(f"Config file not found:\n{path}")
        original_mode = path.stat().st_mode
        backup = path.with_name(f"{path.name}.backup-{stamp}")
        suffix = 1
        while backup.exists():
            backup = path.with_name(f"{path.name}.backup-{stamp}-{suffix}")
            suffix += 1
        states.append({
            "path": path,
            "updated": updated,
            "encoding": encoding,
            "lock_after": lock_after,
            "mode": original_mode,
            "original": path.read_bytes(),
            "backup": backup,
            "temp": None,
            "committed": False,
        })

    try:
        for state in states:
            path = state["path"]
            assert isinstance(path, Path)
            backup = state["backup"]
            assert isinstance(backup, Path)
            shutil.copy2(path, backup)
            with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as temp:
                temp.write(str(state["updated"]).encode(str(state["encoding"])))
                temp.flush()
                os.fsync(temp.fileno())
                state["temp"] = Path(temp.name)

        for state in states:
            path = state["path"]
            temp_path = state["temp"]
            original_mode = state["mode"]
            assert isinstance(path, Path) and isinstance(temp_path, Path) and isinstance(original_mode, int)
            if not bool(original_mode & stat.S_IWRITE):
                os.chmod(path, original_mode | stat.S_IWRITE)
            os.replace(temp_path, path)
            state["temp"] = None
            state["committed"] = True
            final_mode = original_mode & ~stat.S_IWRITE if state["lock_after"] or not bool(original_mode & stat.S_IWRITE) else original_mode | stat.S_IWRITE
            os.chmod(path, final_mode)
    except Exception as exc:
        rollback_errors: list[str] = []
        for state in reversed(states):
            path = state["path"]
            original_mode = state["mode"]
            assert isinstance(path, Path) and isinstance(original_mode, int)
            try:
                if state["committed"]:
                    if path.exists() and not bool(path.stat().st_mode & stat.S_IWRITE):
                        os.chmod(path, path.stat().st_mode | stat.S_IWRITE)
                    with tempfile.NamedTemporaryFile("wb", dir=path.parent, delete=False) as rollback_temp:
                        rollback_temp.write(state["original"])
                        rollback_temp.flush()
                        os.fsync(rollback_temp.fileno())
                        rollback_name = rollback_temp.name
                    os.replace(rollback_name, path)
                if path.exists():
                    os.chmod(path, original_mode)
            except Exception as rollback_exc:
                rollback_errors.append(f"{path.name}: {rollback_exc}")
        if rollback_errors:
            raise RuntimeError(f"Save failed and rollback was incomplete ({'; '.join(rollback_errors)}). Restore from the timestamped backups beside the files.") from exc
        raise
    finally:
        for state in states:
            temp_path = state["temp"]
            if isinstance(temp_path, Path) and temp_path.exists():
                try:
                    temp_path.unlink()
                except OSError:
                    pass

    return [state["backup"] for state in states if isinstance(state["backup"], Path)]


def write_config(path: Path, troops: int, lock_after: bool) -> tuple[Path, str]:
    text, encoding = read_config(path)
    updated, formatted = replace_battle_size(text, troops)
    return write_config_text(path, updated, encoding, lock_after), formatted


class BattleSizerApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1120x780")
        self.minsize(920, 680)
        self.configure(bg="#151916")

        self.path_var = tk.StringVar()
        self.size_var = tk.StringVar(value="500")
        self.value_var = tk.StringVar(value="battle_size = 3.9167")
        self.load_var = tk.StringVar()
        self.status_var = tk.StringVar(value="Choose or detect a Warband config file.")
        self.lock_var = tk.BooleanVar(value=False)
        self.search_var = tk.StringVar()
        self.edit_key_var = tk.StringVar(value="Select a variable")
        self.edit_help_var = tk.StringVar(value="Choose a row to inspect and edit its raw value.")
        self.edit_value_var = tk.StringVar()
        self.change_count_var = tk.StringVar(value="No staged changes")
        self.module_path_var = tk.StringVar()
        self.module_search_var = tk.StringVar()
        self.module_edit_key_var = tk.StringVar(value="Select a game tweak")
        self.module_edit_help_var = tk.StringVar(value="Choose a module.ini setting to inspect and edit.")
        self.module_edit_value_var = tk.StringVar()
        self.module_change_count_var = tk.StringVar(value="No staged module changes")
        self.party_search_var = tk.StringVar()
        self.party_module_var = tk.StringVar(value="No module loaded")
        self.party_id_var = tk.StringVar(value="Select a party template")
        self.party_name_var = tk.StringVar()
        self.party_flags_var = tk.StringVar()
        self.party_menu_var = tk.StringVar()
        self.party_faction_var = tk.StringVar()
        self.party_personality_var = tk.StringVar()
        self.party_troop_var = tk.StringVar()
        self.party_min_var = tk.StringVar()
        self.party_max_var = tk.StringVar()
        self.party_member_flags_var = tk.StringVar()
        self.party_change_count_var = tk.StringVar(value="No staged party changes")
        self.raw_search_var = tk.StringVar()
        self.raw_module_var = tk.StringVar(value="No module loaded")
        self.raw_file_var = tk.StringVar(value="Select a module text file")
        self.raw_state_var = tk.StringVar(value="No raw file loaded")
        self.item_search_var = tk.StringVar()
        self.item_filter_var = tk.StringVar(value="All item types")
        self.item_module_var = tk.StringVar(value="No module loaded")
        self.item_id_var = tk.StringVar(value="Select an item")
        self.item_type_edit_var = tk.StringVar()
        self.item_meta_var = tk.StringVar()
        self.item_end_var = tk.StringVar(value="End marker: not loaded")
        self.item_change_count_var = tk.StringVar(value="No staged item changes")
        self.item_fields = {
            name: tk.StringVar() for name in (
                "singular", "plural", "value", "weight", "abundance", "difficulty",
                "head_armor", "body_armor", "leg_armor", "hit_points", "speed_rating",
                "missile_speed", "weapon_length", "max_ammo", "thrust_amount",
                "swing_amount", "item_flags", "capabilities", "modifiers",
            )
        }
        self.item_thrust_type_var = tk.StringVar()
        self.item_swing_type_var = tk.StringVar()
        self.item_attachment_var = tk.StringVar()
        self.item_kill_info_var = tk.StringVar()
        self.item_unknown_flags_var = tk.StringVar()
        self.item_shoot_action_var = tk.StringVar()
        self.item_carry_position_var = tk.StringVar()
        self.item_reload_action_var = tk.StringVar()
        self.item_unknown_caps_var = tk.StringVar()
        self.item_flag_vars = {key: tk.BooleanVar(value=False) for key, _label, _bit, _help in ITEM_FLAG_OPTIONS}
        self.item_cap_vars = {key: tk.BooleanVar(value=False) for key, _label, _bit, _help in CAPABILITY_OPTIONS}
        self.quick_config_vars = {key: tk.StringVar() for key, _label in (*QUICK_CONFIG_KEYS, *QUICK_CONFIG_NUMERIC_KEYS)}
        self.quick_module_vars = {key: tk.StringVar() for key, _label in QUICK_MODULE_KEYS}
        self.continuation_var = tk.BooleanVar(value=False)
        self.continuation_state_var = tk.StringVar(value="Load a module to inspect mission_templates.txt")
        self.gameplay_module_var = tk.StringVar(value="No module loaded")
        self.gameplay_tournament_status_var = tk.StringVar(value="Load a module to inspect tournament records.")
        self.gameplay_recruitment_status_var = tk.StringVar(value="Load a module to inspect recruitment and prisoner records.")
        self.gameplay_player_status_var = tk.StringVar(value="Load a module to inspect player defaults and skill rules.")
        self.gameplay_siege_status_var = tk.StringVar(value="Load a module to inspect siege construction records.")
        self.gameplay_economy_status_var = tk.StringVar(value="Load a module to inspect fief income and campaign clocks.")
        self.gameplay_party_status_var = tk.StringVar(value="Load a module to inspect party-size and wage records.")
        self.gameplay_battle_status_var = tk.StringVar(value="Load a module to inspect post-battle reward records.")
        self.gameplay_bet_amounts_var = tk.StringVar()
        self.gameplay_vars = {key: tk.StringVar() for key, _label in GAMEPLAY_NUMERIC_FIELDS}
        self.gameplay_tavern_prisoners_var = tk.BooleanVar(value=False)
        self.gameplay_player_attribute_vars = [tk.StringVar() for _name in TROOP_ATTRIBUTES]
        self.gameplay_player_skill_vars = [tk.StringVar() for _name in TROOP_SKILLS]
        self.gameplay_skill_max_vars = [tk.StringVar() for _name in TROOP_SKILLS]
        self.troop_search_var = tk.StringVar()
        self.troop_module_var = tk.StringVar(value="No module loaded")
        self.troop_id_var = tk.StringVar(value="Select a troop")
        self.troop_meta_var = tk.StringVar()
        self.troop_change_count_var = tk.StringVar(value="No staged troop changes")
        self.troop_fields = {name: tk.StringVar() for name in (
            "singular", "plural", "image", "flags", "scene", "reserved", "faction",
            "upgrade_one", "upgrade_two",
        )}
        self.troop_type_var = tk.StringVar()
        self.troop_unknown_flags_var = tk.StringVar()
        self.troop_flag_vars = {key: tk.BooleanVar(value=False) for key, _label, _bit in TROOP_FLAG_OPTIONS}
        self.troop_attribute_vars = [tk.StringVar() for _name in TROOP_ATTRIBUTES]
        self.troop_proficiency_vars = [tk.StringVar() for _name in TROOP_PROFICIENCIES]
        self.troop_skill_vars = [tk.StringVar() for _name in TROOP_SKILLS]
        self.troop_face_vars = [tk.StringVar() for _index in range(8)]
        self.troop_face_status_var = tk.StringVar(value="Select a troop to inspect its face presets.")
        self.troop_item_var = tk.StringVar()
        self.troop_modifier_var = tk.StringVar()

        self.config_path: Path | None = None
        self.config_text = ""
        self.config_encoding = "utf-8"
        self.entries: list[ConfigEntry] = []
        self.pending: dict[int, str] = {}
        self.selected_line: int | None = None
        self.module_dir: Path | None = None
        self.module_ini_path: Path | None = None
        self.module_text = ""
        self.module_encoding = "utf-8"
        self.module_entries: list[ConfigEntry] = []
        self.module_pending: dict[int, str] = {}
        self.module_selected_line: int | None = None
        self.known_modules: list[Path] = []
        self.party_file_path: Path | None = None
        self.party_text = ""
        self.troop_text = ""
        self.party_encoding = "utf-8"
        self.party_records: list[PartyTemplateRecord] = []
        self.party_pending: dict[int, PartyTemplateRecord] = {}
        self.party_selected_line: int | None = None
        self.party_draft_stacks: list[PartyStack] = []
        self.troop_names: list[tuple[str, str]] = []
        self.raw_files: list[Path] = []
        self.raw_visible_files: list[Path] = []
        self.raw_path: Path | None = None
        self.raw_original = ""
        self.raw_encoding = "utf-8"
        self.raw_newline = "\n"
        self.raw_dirty = False
        self.item_file_path: Path | None = None
        self.item_text = ""
        self.item_encoding = "utf-8"
        self.item_records: list[ItemRecord] = []
        self.item_pending: dict[int, ItemRecord] = {}
        self.item_additions: dict[int, ItemAddition] = {}
        self.next_item_key = -1
        self.item_selected_line: int | None = None
        self.troop_file_path: Path | None = None
        self.troop_encoding = "utf-8"
        self.troop_records: list[TroopRecord] = []
        self.troop_pending: dict[int, TroopRecord] = {}
        self.troop_additions: dict[int, TroopRecord] = {}
        self.next_troop_key = -1
        self.troop_selected_line: int | None = None
        self.troop_draft_inventory: list[TroopInventorySlot] = []
        self.faction_names: list[tuple[str, str]] = []
        self.mission_file_path: Path | None = None
        self.mission_text = ""
        self.mission_encoding = "utf-8"
        self.gameplay_sources: dict[str, tuple[Path, str, str]] = {}
        self.gameplay_skill_records: list[SkillRecord] = []
        self.gameplay_player_line: int | None = None

        self._configure_styles()
        self._build_ui()
        self.size_var.trace_add("write", self._update_battle_preview)
        self.search_var.trace_add("write", self._refresh_tree)
        self.module_search_var.trace_add("write", self._refresh_module_tree)
        self.party_search_var.trace_add("write", self._refresh_party_tree)
        self.raw_search_var.trace_add("write", self._refresh_raw_file_list)
        self.item_search_var.trace_add("write", self._refresh_item_tree)
        self.item_filter_var.trace_add("write", self._refresh_item_tree)
        self.troop_search_var.trace_add("write", self._refresh_troop_tree)
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self._detect_config()
        self._detect_modules()
        self._update_battle_preview()

    def _configure_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TButton", font=("Segoe UI", 9, "bold"), padding=(12, 8), borderwidth=0)
        style.configure("Gold.TButton", background="#d7ba72", foreground="#171a17")
        style.map("Gold.TButton", background=[("active", "#ead294"), ("disabled", "#6c6758")])
        style.configure("Dark.TButton", background="#2b312c", foreground="#e9dfc5")
        style.map("Dark.TButton", background=[("active", "#3a433b")])
        style.configure("TCheckbutton", background="#151916", foreground="#c9c1ac", font=("Segoe UI", 9))
        style.map("TCheckbutton", background=[("active", "#151916")])
        style.configure("TNotebook", background="#151916", borderwidth=0)
        style.configure("TNotebook.Tab", background="#242a25", foreground="#a9a28f", padding=(18, 10), font=("Segoe UI", 9, "bold"))
        style.map("TNotebook.Tab", background=[("selected", "#d7ba72")], foreground=[("selected", "#171a17")])
        style.configure("Config.Treeview", background="#202520", foreground="#ded5bd", fieldbackground="#202520", rowheight=29, borderwidth=0, font=("Segoe UI", 9))
        style.configure("Config.Treeview.Heading", background="#303730", foreground="#d7ba72", font=("Segoe UI", 8, "bold"), relief="flat")
        style.map("Config.Treeview", background=[("selected", "#665938")], foreground=[("selected", "#fff6de")])
        style.configure("TCombobox", fieldbackground="#f4eddb", foreground="#201f1a", padding=6)

    def _build_ui(self) -> None:
        header = tk.Frame(self, bg="#101310", padx=26, pady=17)
        header.pack(fill="x")
        tk.Label(header, text="⚔", bg="#101310", fg="#d7ba72", font=("Segoe UI Symbol", 21)).pack(side="left", padx=(0, 13))
        titles = tk.Frame(header, bg="#101310")
        titles.pack(side="left")
        tk.Label(titles, text=APP_TITLE, bg="#101310", fg="#fff5dc", font=("Georgia", 20, "bold")).pack(anchor="w")
        tk.Label(titles, text="Battle sizing, player config, and module game tweaks", bg="#101310", fg="#918c80", font=("Segoe UI", 9)).pack(anchor="w")

        path_bar = tk.Frame(self, bg="#151916", padx=26, pady=14)
        path_bar.pack(fill="x")
        self.path_entry = tk.Entry(path_bar, textvariable=self.path_var, bg="#222722", fg="#ece4d0", insertbackground="#ece4d0", relief="flat", font=("Segoe UI", 9), highlightthickness=1, highlightbackground="#3c443d", highlightcolor="#b59550")
        self.path_entry.pack(side="left", fill="x", expand=True, ipady=8)
        ttk.Button(path_bar, text="Browse…", style="Dark.TButton", command=self._browse).pack(side="left", padx=(8, 0))
        ttk.Button(path_bar, text="Load", style="Dark.TButton", command=self._load_from_path).pack(side="left", padx=(8, 0))
        ttk.Button(path_bar, text="Open Folder", style="Dark.TButton", command=self._open_folder).pack(side="left", padx=(8, 0))

        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=26, pady=(0, 12))
        self.battle_tab = tk.Frame(self.notebook, bg="#151916", padx=16, pady=16)
        self.config_tab = tk.Frame(self.notebook, bg="#151916", padx=16, pady=16)
        self.module_tab = tk.Frame(self.notebook, bg="#151916", padx=16, pady=16)
        self.gameplay_tab = tk.Frame(self.notebook, bg="#151916", padx=16, pady=16)
        self.party_tab = tk.Frame(self.notebook, bg="#151916", padx=16, pady=16)
        self.raw_tab = tk.Frame(self.notebook, bg="#151916", padx=16, pady=16)
        self.item_tab = tk.Frame(self.notebook, bg="#151916", padx=16, pady=16)
        self.troop_tab = tk.Frame(self.notebook, bg="#151916", padx=16, pady=16)
        self.notebook.add(self.battle_tab, text="Quick Edit")
        self.notebook.add(self.config_tab, text="Player Config")
        self.notebook.add(self.module_tab, text="Game Tweaks")
        self.notebook.add(self.gameplay_tab, text="Gameplay Tweaks")
        self.notebook.add(self.party_tab, text="Party Templates")
        self.notebook.add(self.item_tab, text="Item Editor")
        self.notebook.add(self.troop_tab, text="Troop Editor")
        self.notebook.add(self.raw_tab, text="Module Files")
        self._build_battle_tab()
        self._build_config_tab()
        self._build_module_tab()
        self._build_gameplay_tab()
        self._build_party_tab()
        self._build_item_tab()
        self._build_troop_tab()
        self._build_raw_tab()

        footer = tk.Frame(self, bg="#101310", padx=26, pady=11)
        footer.pack(fill="x")
        tk.Label(footer, textvariable=self.status_var, bg="#101310", fg="#9ba199", anchor="w", justify="left", font=("Segoe UI", 9)).pack(side="left", fill="x", expand=True)
        tk.Label(footer, text=f"v{APP_VERSION}", bg="#101310", fg="#686f69", font=("Segoe UI", 8)).pack(side="right", padx=(12, 0))
        ttk.Checkbutton(footer, text="Lock config read-only after saving", variable=self.lock_var).pack(side="right")

    def _build_battle_tab(self) -> None:
        canvas = tk.Canvas(self.battle_tab, bg="#151916", highlightthickness=0)
        scroll = ttk.Scrollbar(self.battle_tab, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        content = tk.Frame(canvas, bg="#151916", padx=6, pady=4)
        window = canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window, width=event.width))

        tk.Label(content, text="BATTLE SIZE", bg="#151916", fg="#b99b59", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        battle_card = tk.Frame(content, bg="#222722", padx=16, pady=14, highlightthickness=1, highlightbackground="#3c443d")
        battle_card.pack(fill="x", pady=(7, 13))
        row = tk.Frame(battle_card, bg="#222722")
        row.pack(fill="x", pady=(0, 8))
        self.size_entry = tk.Entry(row, textvariable=self.size_var, bg="#f4eddb", fg="#201f1a", insertbackground="#201f1a", relief="flat", justify="center", font=("Consolas", 29, "bold"), width=11, highlightthickness=2, highlightbackground="#8e7749", highlightcolor="#d7ba72")
        self.size_entry.pack(side="left", ipady=10)
        tk.Label(row, text="soldiers", bg="#222722", fg="#a39c8b", font=("Segoe UI", 11)).pack(side="left", padx=14)
        preview = tk.Frame(row, bg="#222722")
        preview.pack(side="left", fill="x", expand=True, padx=(12, 0))
        tk.Label(preview, textvariable=self.value_var, bg="#222722", fg="#edcf86", font=("Consolas", 15, "bold")).pack(anchor="w")
        tk.Label(preview, textvariable=self.load_var, bg="#222722", fg="#b6ad99", font=("Segoe UI", 9)).pack(anchor="w")
        presets = tk.Frame(battle_card, bg="#222722")
        presets.pack(fill="x")
        for preset in (150, 300, 500, 750, 1000):
            ttk.Button(presets, text=f"{preset:,}", style="Dark.TButton", command=lambda value=preset: self.size_var.set(str(value))).pack(side="left", padx=(0, 7))
        actions = tk.Frame(battle_card, bg="#222722")
        actions.pack(fill="x", pady=(10, 0))
        self.apply_button = ttk.Button(actions, text="Apply Battle Size", style="Gold.TButton", command=self._apply_battle_size)
        self.apply_button.pack(side="left")
        tk.Label(actions, text="No artificial upper limit; very large battles can exceed Warband's engine limits.", bg="#222722", fg="#777f78", font=("Segoe UI", 8)).pack(side="left", padx=12)

        tk.Label(content, text="PLAYER & PERFORMANCE", bg="#151916", fg="#b99b59", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        player_card = tk.Frame(content, bg="#222722", padx=16, pady=12, highlightthickness=1, highlightbackground="#3c443d")
        player_card.pack(fill="x", pady=(7, 13))
        toggle_row = tk.Frame(player_card, bg="#222722")
        toggle_row.pack(fill="x")
        for column, (key, label) in enumerate(QUICK_CONFIG_KEYS):
            host = tk.Frame(toggle_row, bg="#222722")
            host.grid(row=column // 3, column=column % 3, sticky="ew", padx=(0, 12), pady=3)
            tk.Label(host, text=label, bg="#222722", fg="#a9a18e", font=("Segoe UI", 8)).pack(side="left")
            ttk.Combobox(host, textvariable=self.quick_config_vars[key], values=("0", "1"), state="readonly", width=4).pack(side="right", padx=(7, 0))
        for column in range(3):
            toggle_row.columnconfigure(column, weight=1)
        numeric = tk.Frame(player_card, bg="#222722")
        numeric.pack(fill="x", pady=(7, 0))
        for index, (key, label) in enumerate(QUICK_CONFIG_NUMERIC_KEYS):
            tk.Label(numeric, text=label, bg="#222722", fg="#a9a18e", font=("Segoe UI", 8)).grid(row=index // 4 * 2, column=index % 4, sticky="w", padx=(0, 10))
            tk.Entry(numeric, textvariable=self.quick_config_vars[key], bg="#f4eddb", fg="#201f1a", relief="flat", font=("Consolas", 9), width=12).grid(row=index // 4 * 2 + 1, column=index % 4, sticky="ew", padx=(0, 10), pady=(2, 5), ipady=3)
        for column in range(4):
            numeric.columnconfigure(column, weight=1)
        ttk.Button(player_card, text="Save Player Quick Edits", style="Gold.TButton", command=self._save_quick_config).pack(anchor="e", pady=(5, 0))

        tk.Label(content, text="MODULE GAMEPLAY", bg="#151916", fg="#b99b59", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        module_card = tk.Frame(content, bg="#222722", padx=16, pady=12, highlightthickness=1, highlightbackground="#3c443d")
        module_card.pack(fill="x", pady=(7, 13))
        module_grid = tk.Frame(module_card, bg="#222722")
        module_grid.pack(fill="x")
        for index, (key, label) in enumerate(QUICK_MODULE_KEYS):
            host = tk.Frame(module_grid, bg="#222722")
            host.grid(row=index // 3, column=index % 3, sticky="ew", padx=(0, 12), pady=3)
            tk.Label(host, text=label, bg="#222722", fg="#a9a18e", font=("Segoe UI", 8)).pack(side="left")
            ttk.Combobox(host, textvariable=self.quick_module_vars[key], values=("0", "1"), state="readonly", width=4).pack(side="right", padx=(7, 0))
        for column in range(3):
            module_grid.columnconfigure(column, weight=1)
        ttk.Button(module_card, text="Save Module Quick Edits", style="Gold.TButton", command=self._save_quick_module).pack(anchor="e", pady=(7, 0))

        tk.Label(content, text="BATTLE CONTINUATION", bg="#151916", fg="#b99b59", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        continuation_card = tk.Frame(content, bg="#29271f", padx=16, pady=12, highlightthickness=1, highlightbackground="#61573c")
        continuation_card.pack(fill="x", pady=(7, 8))
        ttk.Checkbutton(continuation_card, text="Continue battles after the player is knocked unconscious", variable=self.continuation_var).pack(anchor="w")
        tk.Label(continuation_card, textvariable=self.continuation_state_var, bg="#29271f", fg="#dbc98e", font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=(4, 7))
        ttk.Button(continuation_card, text="Apply Continuation Setting", style="Gold.TButton", command=self._apply_battle_continuation).pack(anchor="e")

    def _build_gameplay_tab(self) -> None:
        toolbar = tk.Frame(self.gameplay_tab, bg="#151916")
        toolbar.pack(fill="x", pady=(0, 10))
        tk.Label(toolbar, textvariable=self.gameplay_module_var, bg="#151916", fg="#d7ba72", font=("Segoe UI", 9, "bold")).pack(side="left")
        ttk.Button(toolbar, text="Reload", style="Dark.TButton", command=self._reload_gameplay_tweaks).pack(side="right")

        canvas = tk.Canvas(self.gameplay_tab, bg="#151916", highlightthickness=0)
        scroll = ttk.Scrollbar(self.gameplay_tab, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scroll.set)
        scroll.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)
        content = tk.Frame(canvas, bg="#151916", padx=5, pady=3)
        window = canvas.create_window((0, 0), window=content, anchor="nw")
        content.bind("<Configure>", lambda _event: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>", lambda event: canvas.itemconfigure(window, width=event.width))

        notice = tk.Frame(content, bg="#29271f", padx=14, pady=10, highlightthickness=1, highlightbackground="#61573c")
        notice.pack(fill="x", pady=(0, 12))
        tk.Label(notice, text="Version-aware compiled gameplay tweaks", bg="#29271f", fg="#dbc98e", font=("Segoe UI", 9, "bold"), anchor="w").pack(fill="x")
        tk.Label(notice, text="Native 1.174 is the canonical gameplay-tweak baseline. Matching module layouts are supported; unfamiliar signatures are refused. Clone original modules first. Existing saves keep the player's current attributes and skill levels; player defaults below apply to new campaigns.", bg="#29271f", fg="#a9a18e", font=("Segoe UI", 8), wraplength=980, justify="left", anchor="w").pack(fill="x", pady=(3, 0))

        def card(title: str) -> tk.Frame:
            tk.Label(content, text=title, bg="#151916", fg="#b99b59", font=("Segoe UI", 8, "bold")).pack(anchor="w")
            panel = tk.Frame(content, bg="#222722", padx=16, pady=13, highlightthickness=1, highlightbackground="#3c443d")
            panel.pack(fill="x", pady=(7, 13))
            return panel

        def field(parent: tk.Frame, label: str, variable: tk.StringVar, row: int, column: int = 0, width: int = 12) -> None:
            tk.Label(parent, text=label, bg="#222722", fg="#a9a18e", font=("Segoe UI", 8)).grid(row=row, column=column, sticky="w", padx=(0, 8), pady=4)
            tk.Entry(parent, textvariable=variable, bg="#f4eddb", fg="#201f1a", relief="flat", font=("Consolas", 9), width=width).grid(row=row, column=column + 1, sticky="ew", padx=(0, 18), pady=4, ipady=3)

        tournament = card("TOURNAMENT BETTING & REWARDS")
        tk.Label(tournament, textvariable=self.gameplay_tournament_status_var, bg="#222722", fg="#8e968d", font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=(0, 7))
        tournament_grid = tk.Frame(tournament, bg="#222722")
        tournament_grid.pack(fill="x")
        field(tournament_grid, "Bet choices (comma-separated)", self.gameplay_bet_amounts_var, 0, 0, 32)
        field(tournament_grid, "Winner prize (denars)", self.gameplay_vars["tournament_prize"], 0, 2)
        field(tournament_grid, "Winner renown", self.gameplay_vars["tournament_renown"], 1, 0)
        field(tournament_grid, "Winner XP", self.gameplay_vars["tournament_xp"], 1, 2)
        tournament_grid.columnconfigure(1, weight=2)
        tournament_grid.columnconfigure(3, weight=1)
        self.gameplay_tournament_save_button = ttk.Button(tournament, text="Save Tournament Tweaks", style="Gold.TButton", command=self._save_tournament_tweaks)
        self.gameplay_tournament_save_button.pack(anchor="e", pady=(7, 0))
        self.gameplay_tournament_save_button.state(["disabled"])

        siege = card("SIEGE CONSTRUCTION TIMES")
        tk.Label(siege, textvariable=self.gameplay_siege_status_var, bg="#222722", fg="#8e968d", font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=(0, 7))
        siege_grid = tk.Frame(siege, bg="#222722")
        siege_grid.pack(fill="x")
        labels = dict(GAMEPLAY_NUMERIC_FIELDS)
        siege_fields = ("ladder_skill_base", "ladder_time_multiplier", "ladder_time_divisor", "tower_skill_base", "tower_time_multiplier")
        for index, key in enumerate(siege_fields):
            field(siege_grid, labels[key], self.gameplay_vars[key], index // 3, (index % 3) * 2)
        for column in (1, 3, 5):
            siege_grid.columnconfigure(column, weight=1)
        tk.Label(siege, text="Hours are calculated from (base − best Engineer skill), then multiplied and—for ladders—divided. The display and actual build action are patched together.", bg="#222722", fg="#777f78", font=("Segoe UI", 8), anchor="w", justify="left", wraplength=1000).pack(fill="x", pady=(5, 0))
        self.gameplay_siege_save_button = ttk.Button(siege, text="Save Siege Time Tweaks", style="Gold.TButton", command=self._save_siege_tweaks)
        self.gameplay_siege_save_button.pack(anchor="e", pady=(7, 0))
        self.gameplay_siege_save_button.state(["disabled"])

        economy = card("FIEF INCOME & CAMPAIGN CLOCKS")
        tk.Label(economy, textvariable=self.gameplay_economy_status_var, bg="#222722", fg="#8e968d", font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=(0, 7))
        economy_grid = tk.Frame(economy, bg="#222722")
        economy_grid.pack(fill="x")
        economy_fields = ("village_rent", "castle_rent", "town_rent", "prosperity_base", "prosperity_divisor", "fief_interval_hours", "food_interval_hours", "food_troops_per_unit", "refresh_interval_hours")
        for index, key in enumerate(economy_fields):
            field(economy_grid, labels[key], self.gameplay_vars[key], index // 3, (index % 3) * 2)
        for column in (1, 3, 5):
            economy_grid.columnconfigure(column, weight=1)
        tk.Label(economy, text="Fief income = base rent × (prosperity + prosperity base) ÷ income divisor. Lower divisors pay more. Global campaign speed already exists in Game Tweaks and is not duplicated here.", bg="#222722", fg="#777f78", font=("Segoe UI", 8), anchor="w", justify="left", wraplength=1000).pack(fill="x", pady=(5, 0))
        self.gameplay_economy_save_button = ttk.Button(economy, text="Save Economy & Clock Tweaks", style="Gold.TButton", command=self._save_economy_tweaks)
        self.gameplay_economy_save_button.pack(anchor="e", pady=(7, 0))
        self.gameplay_economy_save_button.state(["disabled"])

        party = card("PARTY SIZE & WAGES")
        tk.Label(party, textvariable=self.gameplay_party_status_var, bg="#222722", fg="#8e968d", font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=(0, 7))
        party_grid = tk.Frame(party, bg="#222722")
        party_grid.pack(fill="x")
        party_fields = ("party_base_size", "party_renown_divisor", "garrison_wage_divisor")
        for index, key in enumerate(party_fields):
            field(party_grid, labels[key], self.gameplay_vars[key], 0, index * 2)
            party_grid.columnconfigure(index * 2 + 1, weight=1)
        tk.Label(party, text="Party limit adds base size + Charisma + Leadership bonus + renown ÷ divisor. Leadership and Prisoner Management bonuses remain in Game Tweaks (module.ini); lower garrison wage divisors reduce the discount.", bg="#222722", fg="#777f78", font=("Segoe UI", 8), anchor="w", justify="left", wraplength=1000).pack(fill="x", pady=(5, 0))
        self.gameplay_party_save_button = ttk.Button(party, text="Save Party & Wage Tweaks", style="Gold.TButton", command=self._save_party_tweaks)
        self.gameplay_party_save_button.pack(anchor="e", pady=(7, 0))
        self.gameplay_party_save_button.state(["disabled"])

        battle = card("POST-BATTLE GOLD & XP")
        tk.Label(battle, textvariable=self.gameplay_battle_status_var, bg="#222722", fg="#8e968d", font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=(0, 7))
        battle_grid = tk.Frame(battle, bg="#222722")
        battle_grid.pack(fill="x")
        battle_fields = ("battle_level_bonus", "battle_gain_divisor", "battle_gold_share", "battle_gold_cap", "battle_gold_roll_min", "battle_gold_roll_max", "battle_gold_divisor", "battle_xp_roll_min", "battle_xp_roll_max", "battle_xp_divisor")
        for index, key in enumerate(battle_fields):
            field(battle_grid, labels[key], self.gameplay_vars[key], index // 3, (index % 3) * 2)
        for column in (1, 3, 5):
            battle_grid.columnconfigure(column, weight=1)
        tk.Label(battle, text="Native computes rewards from defeated troop levels, contribution, a random percentage roll, and party shares. Lower percent divisors multiply the result (100 = stock 1×; 50 ≈ 2×). Maximum rolls are exclusive.", bg="#222722", fg="#777f78", font=("Segoe UI", 8), anchor="w", justify="left", wraplength=1000).pack(fill="x", pady=(5, 0))
        self.gameplay_battle_save_button = ttk.Button(battle, text="Save Battle Reward Tweaks", style="Gold.TButton", command=self._save_battle_reward_tweaks)
        self.gameplay_battle_save_button.pack(anchor="e", pady=(7, 0))
        self.gameplay_battle_save_button.state(["disabled"])

        recruitment = card("RECRUITMENT, MERCENARIES & PRISONERS")
        tk.Label(recruitment, textvariable=self.gameplay_recruitment_status_var, bg="#222722", fg="#8e968d", font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=(0, 7))
        recruitment_grid = tk.Frame(recruitment, bg="#222722")
        recruitment_grid.pack(fill="x")
        recruitment_fields = (
            "village_base", "village_relation_bonus", "village_multiplier", "village_price",
            "mercenary_min", "mercenary_max", "prisoner_level_bonus", "prisoner_divisor", "prisoner_minimum",
        )
        for index, key in enumerate(recruitment_fields):
            field(recruitment_grid, labels[key], self.gameplay_vars[key], index // 3, (index % 3) * 2)
        for column in (1, 3, 5):
            recruitment_grid.columnconfigure(column, weight=1)
        ttk.Checkbutton(recruitment, text="Let every tavern keeper buy regular prisoners", variable=self.gameplay_tavern_prisoners_var).pack(anchor="w", pady=(8, 2))
        tk.Label(recruitment, text="Prisoner price formula: ((troop level + bonus)² ÷ divisor), with the minimum used for special troop types.", bg="#222722", fg="#777f78", font=("Segoe UI", 8), anchor="w").pack(fill="x")
        self.gameplay_recruitment_save_button = ttk.Button(recruitment, text="Save Recruitment & Prisoner Tweaks", style="Gold.TButton", command=self._save_recruitment_tweaks)
        self.gameplay_recruitment_save_button.pack(anchor="e", pady=(7, 0))
        self.gameplay_recruitment_save_button.state(["disabled"])

        player = card("NEW-CAMPAIGN PLAYER STATS & SKILL RULES")
        tk.Label(player, textvariable=self.gameplay_player_status_var, bg="#222722", fg="#8e968d", font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=(0, 7))
        tk.Label(player, text="Leadership party-size bonus and Prisoner Management capacity per point are already editable in Game Tweaks (module.ini).", bg="#222722", fg="#d7ba72", font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=(0, 7))
        attribute_grid = tk.Frame(player, bg="#222722")
        attribute_grid.pack(fill="x", pady=(0, 10))
        for index, (label, variable) in enumerate(zip(TROOP_ATTRIBUTES, self.gameplay_player_attribute_vars)):
            field(attribute_grid, f"Player {label}", variable, 0, index * 2, 8)
            attribute_grid.columnconfigure(index * 2 + 1, weight=1)

        headers = tk.Frame(player, bg="#292e29", padx=8, pady=5)
        headers.pack(fill="x")
        tk.Label(headers, text="START = trp_player default  •  MAX = module skill cap", bg="#292e29", fg="#d7ba72", font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x")
        skill_columns = tk.Frame(player, bg="#222722")
        skill_columns.pack(fill="x", pady=(5, 0))
        halfway = (len(PLAYER_SKILL_INDICES) + 1) // 2
        for column, indices in enumerate((PLAYER_SKILL_INDICES[:halfway], PLAYER_SKILL_INDICES[halfway:])):
            block = tk.Frame(skill_columns, bg="#222722", padx=5)
            block.grid(row=0, column=column, sticky="nsew", padx=(0, 14 if column == 0 else 0))
            tk.Label(block, text="Skill", bg="#222722", fg="#777f78", font=("Segoe UI", 8, "bold")).grid(row=0, column=0, sticky="w")
            tk.Label(block, text="Start", bg="#222722", fg="#777f78", font=("Segoe UI", 8, "bold")).grid(row=0, column=1)
            tk.Label(block, text="Max", bg="#222722", fg="#777f78", font=("Segoe UI", 8, "bold")).grid(row=0, column=2)
            for row, skill_index in enumerate(indices, start=1):
                tk.Label(block, text=TROOP_SKILLS[skill_index], bg="#222722", fg="#a9a18e", font=("Segoe UI", 8)).grid(row=row, column=0, sticky="w", pady=2)
                tk.Entry(block, textvariable=self.gameplay_player_skill_vars[skill_index], bg="#f4eddb", fg="#201f1a", relief="flat", font=("Consolas", 9), width=6, justify="center").grid(row=row, column=1, padx=(8, 5), pady=2, ipady=2)
                tk.Entry(block, textvariable=self.gameplay_skill_max_vars[skill_index], bg="#f4eddb", fg="#201f1a", relief="flat", font=("Consolas", 9), width=6, justify="center").grid(row=row, column=2, pady=2, ipady=2)
            block.columnconfigure(0, weight=1)
            skill_columns.columnconfigure(column, weight=1)
        self.gameplay_player_save_button = ttk.Button(player, text="Save New-Campaign Player & Skill Rules", style="Gold.TButton", command=self._save_player_gameplay_tweaks)
        self.gameplay_player_save_button.pack(anchor="e", pady=(10, 0))
        self.gameplay_player_save_button.state(["disabled"])

        def scroll_page(event: tk.Event) -> str:
            delta = getattr(event, "delta", 0)
            if delta:
                canvas.yview_scroll(-3 if delta > 0 else 3, "units")
            return "break"

        def bind_scroll(widget: tk.Widget) -> None:
            widget.bind("<MouseWheel>", scroll_page, add="+")
            for child in widget.winfo_children():
                bind_scroll(child)

        bind_scroll(content)

    def _build_config_tab(self) -> None:
        toolbar = tk.Frame(self.config_tab, bg="#151916")
        toolbar.pack(fill="x", pady=(0, 10))
        tk.Label(toolbar, text="Search", bg="#151916", fg="#a9a28f", font=("Segoe UI", 9)).pack(side="left")
        search = tk.Entry(toolbar, textvariable=self.search_var, bg="#f4eddb", fg="#201f1a", insertbackground="#201f1a", relief="flat", font=("Segoe UI", 10), width=32)
        search.pack(side="left", padx=(8, 12), ipady=6)
        ttk.Button(toolbar, text="Reload File", style="Dark.TButton", command=self._reload_config).pack(side="left")
        tk.Label(toolbar, textvariable=self.change_count_var, bg="#151916", fg="#d7ba72", font=("Segoe UI", 9, "bold")).pack(side="right")

        body = tk.PanedWindow(self.config_tab, orient="horizontal", bg="#151916", sashwidth=7, sashrelief="flat", bd=0)
        body.pack(fill="both", expand=True)
        list_frame = tk.Frame(body, bg="#202520")
        editor = tk.Frame(body, bg="#222722", padx=18, pady=18)
        body.add(list_frame, minsize=480, stretch="always")
        body.add(editor, minsize=290)

        columns = ("setting", "value", "type", "state")
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", style="Config.Treeview", selectmode="browse")
        self.tree.heading("setting", text="SETTING")
        self.tree.heading("value", text="VALUE")
        self.tree.heading("type", text="TYPE")
        self.tree.heading("state", text="STATE")
        self.tree.column("setting", width=235, minwidth=170)
        self.tree.column("value", width=105, minwidth=80)
        self.tree.column("type", width=75, minwidth=60)
        self.tree.column("state", width=70, minwidth=55)
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._select_entry)

        tk.Label(editor, text="EDIT RAW VALUE", bg="#222722", fg="#8e968d", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        tk.Label(editor, textvariable=self.edit_key_var, bg="#222722", fg="#f1e5c5", font=("Georgia", 15, "bold"), wraplength=280, justify="left").pack(anchor="w", pady=(8, 6))
        tk.Label(editor, textvariable=self.edit_help_var, bg="#222722", fg="#a9a18e", font=("Segoe UI", 9), wraplength=280, justify="left").pack(anchor="w", pady=(0, 16))
        self.value_editor_host = tk.Frame(editor, bg="#222722")
        self.value_editor_host.pack(fill="x")
        self.value_editor: tk.Widget | None = None
        self._show_value_editor(False)
        button_row = tk.Frame(editor, bg="#222722")
        button_row.pack(fill="x", pady=(14, 0))
        self.stage_button = ttk.Button(button_row, text="Stage Change", style="Gold.TButton", command=self._stage_selected)
        self.stage_button.pack(side="left")
        self.revert_button = ttk.Button(button_row, text="Revert", style="Dark.TButton", command=self._revert_selected)
        self.revert_button.pack(side="left", padx=(8, 0))
        self.stage_button.state(["disabled"])
        self.revert_button.state(["disabled"])
        tk.Label(editor, text="Changes are staged until you click Save All. Numeric settings are validated against their original type.", bg="#222722", fg="#777f78", font=("Segoe UI", 8), wraplength=280, justify="left").pack(anchor="w", pady=(18, 0))

        save_bar = tk.Frame(self.config_tab, bg="#151916")
        save_bar.pack(fill="x", pady=(12, 0))
        self.save_all_button = ttk.Button(save_bar, text="Save All Changes", style="Gold.TButton", command=self._save_all_changes)
        self.save_all_button.pack(side="right")
        self.save_all_button.state(["disabled"])

    def _build_module_tab(self) -> None:
        picker = tk.Frame(self.module_tab, bg="#151916")
        picker.pack(fill="x", pady=(0, 10))
        tk.Label(picker, text="MODULE", bg="#151916", fg="#b99b59", font=("Segoe UI", 8, "bold")).pack(side="left")
        self.module_combo = ttk.Combobox(picker, textvariable=self.module_path_var, state="normal", font=("Segoe UI", 9))
        self.module_combo.pack(side="left", fill="x", expand=True, padx=(10, 8))
        self.module_combo.bind("<<ComboboxSelected>>", lambda _event: self._load_module_from_var())
        ttk.Button(picker, text="Load", style="Dark.TButton", command=self._load_module_from_var).pack(side="left")
        ttk.Button(picker, text="Browse…", style="Dark.TButton", command=self._browse_module).pack(side="left", padx=(8, 0))
        ttk.Button(picker, text="Clone Module…", style="Gold.TButton", command=self._clone_current_module).pack(side="left", padx=(8, 0))

        notice = tk.Frame(self.module_tab, bg="#29271f", padx=12, pady=9, highlightthickness=1, highlightbackground="#61573c")
        notice.pack(fill="x", pady=(0, 10))
        tk.Label(notice, text="Recommended: clone a module before tweaking it. Saves create timestamped module.ini backups.", bg="#29271f", fg="#dbc98e", font=("Segoe UI", 9), anchor="w").pack(fill="x")

        toolbar = tk.Frame(self.module_tab, bg="#151916")
        toolbar.pack(fill="x", pady=(0, 10))
        tk.Label(toolbar, text="Search game tweaks", bg="#151916", fg="#a9a28f", font=("Segoe UI", 9)).pack(side="left")
        tk.Entry(toolbar, textvariable=self.module_search_var, bg="#f4eddb", fg="#201f1a", insertbackground="#201f1a", relief="flat", font=("Segoe UI", 10), width=30).pack(side="left", padx=(8, 12), ipady=6)
        ttk.Button(toolbar, text="Reload module.ini", style="Dark.TButton", command=self._reload_module).pack(side="left")
        tk.Label(toolbar, textvariable=self.module_change_count_var, bg="#151916", fg="#d7ba72", font=("Segoe UI", 9, "bold")).pack(side="right")

        body = tk.PanedWindow(self.module_tab, orient="horizontal", bg="#151916", sashwidth=7, sashrelief="flat", bd=0)
        body.pack(fill="both", expand=True)
        list_frame = tk.Frame(body, bg="#202520")
        editor = tk.Frame(body, bg="#222722", padx=18, pady=18)
        body.add(list_frame, minsize=600, stretch="always")
        body.add(editor, minsize=300)

        columns = ("category", "setting", "value", "type", "state")
        self.module_tree = ttk.Treeview(list_frame, columns=columns, show=("tree", "headings"), style="Config.Treeview", selectmode="browse")
        self.module_tree.heading("#0", text="SECTION")
        self.module_tree.column("#0", width=168, minwidth=135, stretch=False)
        for column, title in (("category", "CATEGORY"), ("setting", "SETTING"), ("value", "VALUE"), ("type", "TYPE"), ("state", "STATE")):
            self.module_tree.heading(column, text=title)
        self.module_tree.column("category", width=115, minwidth=90)
        self.module_tree.column("setting", width=270, minwidth=190)
        self.module_tree.column("value", width=120, minwidth=80)
        self.module_tree.column("type", width=70, minwidth=55)
        self.module_tree.column("state", width=70, minwidth=55)
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.module_tree.yview)
        self.module_tree.configure(yscrollcommand=scroll.set)
        self.module_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.module_tree.bind("<<TreeviewSelect>>", self._select_module_entry)

        tk.Label(editor, text="EDIT MODULE VALUE", bg="#222722", fg="#8e968d", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        tk.Label(editor, textvariable=self.module_edit_key_var, bg="#222722", fg="#f1e5c5", font=("Georgia", 15, "bold"), wraplength=290, justify="left").pack(anchor="w", pady=(8, 6))
        tk.Label(editor, textvariable=self.module_edit_help_var, bg="#222722", fg="#a9a18e", font=("Segoe UI", 9), wraplength=290, justify="left").pack(anchor="w", pady=(0, 16))
        self.module_value_editor_host = tk.Frame(editor, bg="#222722")
        self.module_value_editor_host.pack(fill="x")
        self.module_value_editor: tk.Widget | None = None
        self._show_module_value_editor(False)
        button_row = tk.Frame(editor, bg="#222722")
        button_row.pack(fill="x", pady=(14, 0))
        self.module_stage_button = ttk.Button(button_row, text="Stage Change", style="Gold.TButton", command=self._stage_module_selected)
        self.module_stage_button.pack(side="left")
        self.module_revert_button = ttk.Button(button_row, text="Revert", style="Dark.TButton", command=self._revert_module_selected)
        self.module_revert_button.pack(side="left", padx=(8, 0))
        self.module_stage_button.state(["disabled"])
        self.module_revert_button.state(["disabled"])
        tk.Label(editor, text="Warband's misspelled engine keys are preserved exactly. Resource rows remain ordered and duplicates stay intact.", bg="#222722", fg="#777f78", font=("Segoe UI", 8), wraplength=290, justify="left").pack(anchor="w", pady=(18, 0))

        save_bar = tk.Frame(self.module_tab, bg="#151916")
        save_bar.pack(fill="x", pady=(12, 0))
        self.module_save_button = ttk.Button(save_bar, text="Save Module Tweaks", style="Gold.TButton", command=self._save_module_changes)
        self.module_save_button.pack(side="right")
        self.module_save_button.state(["disabled"])

    def _build_party_tab(self) -> None:
        toolbar = tk.Frame(self.party_tab, bg="#151916")
        toolbar.pack(fill="x", pady=(0, 10))
        tk.Label(toolbar, textvariable=self.party_module_var, bg="#151916", fg="#d7ba72", font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Label(toolbar, text="Search", bg="#151916", fg="#a9a28f", font=("Segoe UI", 9)).pack(side="left", padx=(22, 0))
        tk.Entry(toolbar, textvariable=self.party_search_var, bg="#f4eddb", fg="#201f1a", insertbackground="#201f1a", relief="flat", font=("Segoe UI", 10), width=26).pack(side="left", padx=(8, 12), ipady=6)
        ttk.Button(toolbar, text="Reload", style="Dark.TButton", command=self._reload_party_file).pack(side="left")
        tk.Label(toolbar, textvariable=self.party_change_count_var, bg="#151916", fg="#d7ba72", font=("Segoe UI", 9, "bold")).pack(side="right")

        notice = tk.Frame(self.party_tab, bg="#29271f", padx=12, pady=8, highlightthickness=1, highlightbackground="#61573c")
        notice.pack(fill="x", pady=(0, 10))
        tk.Label(notice, text="Edits party names, flags, faction/personality values, and up to six troop stacks. The troop list comes from this module's troops.txt.", bg="#29271f", fg="#dbc98e", font=("Segoe UI", 9), anchor="w").pack(fill="x")

        body = tk.PanedWindow(self.party_tab, orient="horizontal", bg="#151916", sashwidth=7, sashrelief="flat", bd=0)
        body.pack(fill="both", expand=True)
        list_frame = tk.Frame(body, bg="#202520")
        editor = tk.Frame(body, bg="#222722", padx=15, pady=13)
        body.add(list_frame, minsize=535, stretch="always")
        body.add(editor, minsize=430)

        columns = ("id", "name", "faction", "stacks", "state")
        self.party_tree = ttk.Treeview(list_frame, columns=columns, show="headings", style="Config.Treeview", selectmode="browse")
        for column, title in (("id", "ID"), ("name", "NAME"), ("faction", "FACTION"), ("stacks", "TROOPS"), ("state", "STATE")):
            self.party_tree.heading(column, text=title)
        self.party_tree.column("id", width=200, minwidth=145)
        self.party_tree.column("name", width=145, minwidth=100)
        self.party_tree.column("faction", width=65, minwidth=50)
        self.party_tree.column("stacks", width=80, minwidth=60)
        self.party_tree.column("state", width=70, minwidth=55)
        scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.party_tree.yview)
        self.party_tree.configure(yscrollcommand=scroll.set)
        self.party_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.party_tree.bind("<<TreeviewSelect>>", self._select_party_record)

        tk.Label(editor, textvariable=self.party_id_var, bg="#222722", fg="#f1e5c5", font=("Georgia", 14, "bold"), anchor="w").pack(fill="x")
        name_row = tk.Frame(editor, bg="#222722")
        name_row.pack(fill="x", pady=(8, 7))
        tk.Label(name_row, text="Display name", bg="#222722", fg="#a9a18e", font=("Segoe UI", 8)).pack(side="left")
        tk.Entry(name_row, textvariable=self.party_name_var, bg="#f4eddb", fg="#201f1a", relief="flat", font=("Consolas", 10)).pack(side="right", fill="x", expand=True, padx=(10, 0), ipady=4)

        header_grid = tk.Frame(editor, bg="#222722")
        header_grid.pack(fill="x", pady=(0, 8))
        header_fields = (("Flags", self.party_flags_var), ("Menu", self.party_menu_var), ("Faction", self.party_faction_var), ("Personality", self.party_personality_var))
        for index, (label, variable) in enumerate(header_fields):
            column = (index % 2) * 2
            row = index // 2
            tk.Label(header_grid, text=label, bg="#222722", fg="#8e968d", font=("Segoe UI", 8)).grid(row=row, column=column, sticky="w", pady=2)
            tk.Entry(header_grid, textvariable=variable, bg="#f4eddb", fg="#201f1a", relief="flat", font=("Consolas", 9), width=15).grid(row=row, column=column + 1, sticky="ew", padx=(6, 12), pady=2, ipady=3)
        header_grid.columnconfigure(1, weight=1)
        header_grid.columnconfigure(3, weight=1)

        tk.Label(editor, text="TROOP STACKS", bg="#222722", fg="#8e968d", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        stack_frame = tk.Frame(editor, bg="#202520")
        stack_frame.pack(fill="both", expand=True, pady=(5, 6))
        self.party_stack_tree = ttk.Treeview(stack_frame, columns=("slot", "troop", "min", "max", "flags"), show="headings", style="Config.Treeview", selectmode="browse", height=5)
        for column, title in (("slot", "#"), ("troop", "TROOP"), ("min", "MIN"), ("max", "MAX"), ("flags", "FLAGS")):
            self.party_stack_tree.heading(column, text=title)
        self.party_stack_tree.column("slot", width=28, stretch=False)
        self.party_stack_tree.column("troop", width=205, minwidth=130)
        self.party_stack_tree.column("min", width=45, stretch=False)
        self.party_stack_tree.column("max", width=45, stretch=False)
        self.party_stack_tree.column("flags", width=55, stretch=False)
        self.party_stack_tree.pack(fill="both", expand=True)
        self.party_stack_tree.bind("<<TreeviewSelect>>", self._select_party_stack)

        stack_edit = tk.Frame(editor, bg="#222722")
        stack_edit.pack(fill="x")
        tk.Label(stack_edit, text="Troop", bg="#222722", fg="#8e968d", font=("Segoe UI", 8)).grid(row=0, column=0, sticky="w")
        self.party_troop_combo = ttk.Combobox(stack_edit, textvariable=self.party_troop_var, state="normal", font=("Consolas", 9))
        self.party_troop_combo.grid(row=0, column=1, columnspan=5, sticky="ew", padx=(6, 0), pady=2)
        for column, label, variable in ((0, "Min", self.party_min_var), (2, "Max", self.party_max_var), (4, "Flags", self.party_member_flags_var)):
            tk.Label(stack_edit, text=label, bg="#222722", fg="#8e968d", font=("Segoe UI", 8)).grid(row=1, column=column, sticky="w", pady=3)
            tk.Entry(stack_edit, textvariable=variable, bg="#f4eddb", fg="#201f1a", relief="flat", font=("Consolas", 9), width=8).grid(row=1, column=column + 1, sticky="ew", padx=(4, 10), pady=3, ipady=3)
        stack_edit.columnconfigure(1, weight=1)
        stack_edit.columnconfigure(3, weight=1)
        stack_edit.columnconfigure(5, weight=1)

        stack_buttons = tk.Frame(editor, bg="#222722")
        stack_buttons.pack(fill="x", pady=(4, 7))
        ttk.Button(stack_buttons, text="Apply Stack", style="Dark.TButton", command=self._apply_party_stack).pack(side="left")
        ttk.Button(stack_buttons, text="Add Stack", style="Dark.TButton", command=self._add_party_stack).pack(side="left", padx=(6, 0))
        ttk.Button(stack_buttons, text="Remove Stack", style="Dark.TButton", command=self._remove_party_stack).pack(side="left", padx=(6, 0))

        actions = tk.Frame(editor, bg="#222722")
        actions.pack(fill="x")
        self.party_stage_button = ttk.Button(actions, text="Stage Party Changes", style="Gold.TButton", command=self._stage_party_record)
        self.party_stage_button.pack(side="left")
        self.party_revert_button = ttk.Button(actions, text="Revert Party", style="Dark.TButton", command=self._revert_party_record)
        self.party_revert_button.pack(side="left", padx=(8, 0))
        self.party_stage_button.state(["disabled"])
        self.party_revert_button.state(["disabled"])

        save_bar = tk.Frame(self.party_tab, bg="#151916")
        save_bar.pack(fill="x", pady=(12, 0))
        tk.Label(save_bar, text="A timestamped party_templates.txt backup is created before saving.", bg="#151916", fg="#777f78", font=("Segoe UI", 8)).pack(side="left")
        self.party_save_button = ttk.Button(save_bar, text="Save Party Templates", style="Gold.TButton", command=self._save_party_changes)
        self.party_save_button.pack(side="right")
        self.party_save_button.state(["disabled"])

    def _build_item_tab(self) -> None:
        toolbar = tk.Frame(self.item_tab, bg="#151916")
        toolbar.pack(fill="x", pady=(0, 10))
        tk.Label(toolbar, textvariable=self.item_module_var, bg="#151916", fg="#d7ba72", font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Label(toolbar, text="Search", bg="#151916", fg="#a9a28f", font=("Segoe UI", 9)).pack(side="left", padx=(18, 0))
        tk.Entry(toolbar, textvariable=self.item_search_var, bg="#f4eddb", fg="#201f1a", insertbackground="#201f1a", relief="flat", font=("Segoe UI", 10), width=17).pack(side="left", padx=(7, 10), ipady=6)
        self.item_filter_combo = ttk.Combobox(toolbar, textvariable=self.item_filter_var, state="readonly", width=18, values=("All item types", *ITEM_TYPES.values()))
        self.item_filter_combo.pack(side="left")
        ttk.Button(toolbar, text="Reload", style="Dark.TButton", command=self._reload_item_file).pack(side="left", padx=(8, 0))
        self.item_create_button = ttk.Button(toolbar, text="Create…", style="Gold.TButton", command=self._create_item)
        self.item_create_button.pack(side="left", padx=(8, 0))
        self.item_clone_button = ttk.Button(toolbar, text="Clone…", style="Dark.TButton", command=self._clone_item)
        self.item_clone_button.pack(side="left", padx=(8, 0))
        tk.Label(toolbar, textvariable=self.item_change_count_var, bg="#151916", fg="#d7ba72", font=("Segoe UI", 9, "bold")).pack(side="right")
        tk.Label(toolbar, textvariable=self.item_end_var, bg="#151916", fg="#8e968d", font=("Segoe UI", 8)).pack(side="right", padx=(0, 12))
        self.item_create_button.state(["disabled"])
        self.item_clone_button.state(["disabled"])

        body = tk.PanedWindow(self.item_tab, orient="horizontal", bg="#151916", sashwidth=7, sashrelief="flat", bd=0)
        body.pack(fill="both", expand=True)
        list_frame = tk.Frame(body, bg="#202520")
        editor = tk.Frame(body, bg="#222722", padx=14, pady=12)
        body.add(list_frame, minsize=570, stretch="always")
        body.add(editor, minsize=430)

        columns = ("index", "id", "name", "type", "value", "weight", "state")
        self.item_tree = ttk.Treeview(list_frame, columns=columns, show="headings", style="Config.Treeview", selectmode="browse")
        for column, title in (("index", "#"), ("id", "ID"), ("name", "NAME"), ("type", "TYPE"), ("value", "VALUE"), ("weight", "WEIGHT"), ("state", "STATE")):
            self.item_tree.heading(column, text=title)
        self.item_tree.column("index", width=52, minwidth=44, stretch=False, anchor="center")
        self.item_tree.column("id", width=175, minwidth=120)
        self.item_tree.column("name", width=135, minwidth=90)
        self.item_tree.column("type", width=135, minwidth=90)
        self.item_tree.column("value", width=60, minwidth=45)
        self.item_tree.column("weight", width=60, minwidth=45)
        self.item_tree.column("state", width=70, minwidth=55)
        item_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.item_tree.yview)
        self.item_tree.configure(yscrollcommand=item_scroll.set)
        self.item_tree.pack(side="left", fill="both", expand=True)
        item_scroll.pack(side="right", fill="y")
        self.item_tree.bind("<<TreeviewSelect>>", self._select_item_record)

        tk.Label(editor, textvariable=self.item_id_var, bg="#222722", fg="#f1e5c5", font=("Georgia", 14, "bold"), anchor="w").pack(fill="x")
        tk.Label(editor, textvariable=self.item_meta_var, bg="#222722", fg="#8e968d", font=("Segoe UI", 8), anchor="w", wraplength=420, justify="left").pack(fill="x", pady=(3, 8))

        item_notebook = ttk.Notebook(editor)
        self.item_detail_notebook = item_notebook
        item_notebook.pack(fill="both", expand=True)
        general = tk.Frame(item_notebook, bg="#222722", padx=12, pady=11)
        stats = tk.Frame(item_notebook, bg="#222722", padx=12, pady=11)
        raw_advanced = tk.Frame(item_notebook, bg="#222722", padx=12, pady=11)
        item_notebook.add(general, text="General")
        item_notebook.add(stats, text="Stats & Damage")

        scrolled_item_tabs: list[tuple[tk.Frame, tk.Canvas]] = []

        def add_scrolled_tab(title: str) -> tk.Frame:
            outer = tk.Frame(item_notebook, bg="#222722")
            canvas = tk.Canvas(outer, bg="#222722", highlightthickness=0, borderwidth=0)
            scrollbar = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
            canvas.configure(yscrollcommand=scrollbar.set)
            scrollbar.pack(side="right", fill="y")
            canvas.pack(side="left", fill="both", expand=True)
            inner = tk.Frame(canvas, bg="#222722", padx=10, pady=9)
            window_id = canvas.create_window((0, 0), window=inner, anchor="nw")
            inner.bind("<Configure>", lambda _event, target=canvas: target.configure(scrollregion=target.bbox("all")))
            canvas.bind("<Configure>", lambda event, target=canvas, window=window_id: target.itemconfigure(window, width=event.width))
            item_notebook.add(outer, text=title)
            scrolled_item_tabs.append((outer, canvas))
            return inner

        flag_panel = add_scrolled_tab("Item Flags")
        capability_panel = add_scrolled_tab("Capabilities")
        item_notebook.add(raw_advanced, text="Raw / Modifiers")

        def add_field(parent: tk.Frame, label: str, variable: tk.StringVar, row: int, column: int = 0) -> tk.Entry:
            tk.Label(parent, text=label, bg="#222722", fg="#a9a18e", font=("Segoe UI", 8)).grid(row=row, column=column, sticky="w", pady=4)
            entry = tk.Entry(parent, textvariable=variable, bg="#f4eddb", fg="#201f1a", relief="flat", font=("Consolas", 9))
            entry.grid(row=row, column=column + 1, sticky="ew", padx=(7, 12), pady=4, ipady=4)
            return entry

        add_field(general, "Singular name", self.item_fields["singular"], 0)
        add_field(general, "Plural name", self.item_fields["plural"], 1)
        tk.Label(general, text="Item type", bg="#222722", fg="#a9a18e", font=("Segoe UI", 8)).grid(row=2, column=0, sticky="w", pady=4)
        self.item_type_combo = ttk.Combobox(general, textvariable=self.item_type_edit_var, state="readonly", values=tuple(f"{code}: {name}" for code, name in ITEM_TYPES.items()))
        self.item_type_combo.grid(row=2, column=1, sticky="ew", padx=(7, 12), pady=4)
        add_field(general, "Value (denars)", self.item_fields["value"], 3)
        add_field(general, "Weight", self.item_fields["weight"], 4)
        add_field(general, "Abundance", self.item_fields["abundance"], 5)
        add_field(general, "Difficulty", self.item_fields["difficulty"], 6)
        general.columnconfigure(1, weight=1)

        stat_fields = (
            ("Head armor", "head_armor"), ("Body armor", "body_armor"),
            ("Leg armor", "leg_armor"), ("Hit points", "hit_points"),
            ("Speed rating", "speed_rating"), ("Missile speed", "missile_speed"),
            ("Weapon length", "weapon_length"), ("Maximum ammo", "max_ammo"),
        )
        for index, (label, key) in enumerate(stat_fields):
            add_field(stats, label, self.item_fields[key], index // 2, (index % 2) * 2)
        damage_types = tuple(f"{code}: {name}" for code, name in DAMAGE_TYPES.items())
        tk.Label(stats, text="Thrust damage", bg="#222722", fg="#a9a18e", font=("Segoe UI", 8)).grid(row=4, column=0, sticky="w", pady=(12, 4))
        thrust_host = tk.Frame(stats, bg="#222722")
        thrust_host.grid(row=4, column=1, columnspan=3, sticky="ew", padx=(7, 12), pady=(12, 4))
        tk.Entry(thrust_host, textvariable=self.item_fields["thrust_amount"], bg="#f4eddb", fg="#201f1a", relief="flat", font=("Consolas", 9), width=8).pack(side="left", fill="x", expand=True, ipady=4)
        ttk.Combobox(thrust_host, textvariable=self.item_thrust_type_var, state="readonly", values=damage_types, width=12).pack(side="left", padx=(7, 0))
        tk.Label(stats, text="Swing damage", bg="#222722", fg="#a9a18e", font=("Segoe UI", 8)).grid(row=5, column=0, sticky="w", pady=4)
        swing_host = tk.Frame(stats, bg="#222722")
        swing_host.grid(row=5, column=1, columnspan=3, sticky="ew", padx=(7, 12), pady=4)
        tk.Entry(swing_host, textvariable=self.item_fields["swing_amount"], bg="#f4eddb", fg="#201f1a", relief="flat", font=("Consolas", 9), width=8).pack(side="left", fill="x", expand=True, ipady=4)
        ttk.Combobox(swing_host, textvariable=self.item_swing_type_var, state="readonly", values=damage_types, width=12).pack(side="left", padx=(7, 0))
        stats.columnconfigure(1, weight=1)
        stats.columnconfigure(3, weight=1)

        add_field(flag_panel, "Raw item-flags value", self.item_fields["item_flags"], 0)
        tk.Label(flag_panel, text="Attachment", bg="#222722", fg="#a9a18e", font=("Segoe UI", 8)).grid(row=1, column=0, sticky="w", pady=4)
        ttk.Combobox(flag_panel, textvariable=self.item_attachment_var, state="readonly", values=tuple(f"{value}: {label}" for value, label in ITEM_ATTACHMENT_OPTIONS.items())).grid(row=1, column=1, sticky="ew", padx=(7, 12), pady=4)
        tk.Label(flag_panel, text="Custom kill icon", bg="#222722", fg="#a9a18e", font=("Segoe UI", 8)).grid(row=2, column=0, sticky="w", pady=4)
        ttk.Combobox(flag_panel, textvariable=self.item_kill_info_var, state="readonly", values=tuple(f"{value}: {'Default' if value == 0 else f'Custom icon {value}'}" for value in range(8))).grid(row=2, column=1, sticky="ew", padx=(7, 12), pady=4)
        tk.Label(flag_panel, textvariable=self.item_unknown_flags_var, bg="#222722", fg="#d7ba72", font=("Consolas", 8), anchor="w").grid(row=3, column=0, columnspan=2, sticky="ew", pady=(5, 9))
        tk.Label(flag_panel, text="NAMED FLAG BITS", bg="#222722", fg="#8e968d", font=("Segoe UI", 8, "bold")).grid(row=4, column=0, columnspan=2, sticky="w")
        for row, (key, label, _bit, help_text) in enumerate(ITEM_FLAG_OPTIONS, start=5):
            ttk.Checkbutton(flag_panel, text=label, variable=self.item_flag_vars[key]).grid(row=row, column=0, sticky="w", pady=2)
            tk.Label(flag_panel, text=help_text, bg="#222722", fg="#7f877f", font=("Segoe UI", 8), wraplength=235, justify="left").grid(row=row, column=1, sticky="w", padx=(8, 4), pady=2)
        flag_panel.columnconfigure(1, weight=1)

        add_field(capability_panel, "Raw capabilities value", self.item_fields["capabilities"], 0)
        capability_choices = (
            ("Shoot / throw", self.item_shoot_action_var, CAPABILITY_SHOOT_OPTIONS),
            ("Carry position", self.item_carry_position_var, CAPABILITY_CARRY_OPTIONS),
            ("Reload action", self.item_reload_action_var, CAPABILITY_RELOAD_OPTIONS),
        )
        for row, (label, variable, options) in enumerate(capability_choices, start=1):
            tk.Label(capability_panel, text=label, bg="#222722", fg="#a9a18e", font=("Segoe UI", 8)).grid(row=row, column=0, sticky="w", pady=4)
            ttk.Combobox(capability_panel, textvariable=variable, state="readonly", values=tuple(f"{value}: {name}" for value, name in options.items())).grid(row=row, column=1, sticky="ew", padx=(7, 12), pady=4)
        tk.Label(capability_panel, textvariable=self.item_unknown_caps_var, bg="#222722", fg="#d7ba72", font=("Consolas", 8), anchor="w").grid(row=4, column=0, columnspan=2, sticky="ew", pady=(5, 9))
        tk.Label(capability_panel, text="ATTACK, PARRY & BEHAVIOR BITS", bg="#222722", fg="#8e968d", font=("Segoe UI", 8, "bold")).grid(row=5, column=0, columnspan=2, sticky="w")
        for row, (key, label, _bit, help_text) in enumerate(CAPABILITY_OPTIONS, start=6):
            ttk.Checkbutton(capability_panel, text=label, variable=self.item_cap_vars[key]).grid(row=row, column=0, sticky="w", pady=2)
            tk.Label(capability_panel, text=help_text, bg="#222722", fg="#7f877f", font=("Segoe UI", 8), wraplength=235, justify="left").grid(row=row, column=1, sticky="w", padx=(8, 4), pady=2)
        capability_panel.columnconfigure(1, weight=1)

        def bind_mousewheel_tree(widget: tk.Widget, canvas: tk.Canvas) -> None:
            def scroll(event: tk.Event) -> str:
                if getattr(event, "num", None) == 4:
                    steps = -3
                elif getattr(event, "num", None) == 5:
                    steps = 3
                else:
                    delta = getattr(event, "delta", 0)
                    if not delta:
                        return "break"
                    steps = -3 if delta > 0 else 3
                canvas.yview_scroll(steps, "units")
                return "break"

            widget.bind("<MouseWheel>", scroll, add="+")
            widget.bind("<Button-4>", scroll, add="+")
            widget.bind("<Button-5>", scroll, add="+")
            for child in widget.winfo_children():
                bind_mousewheel_tree(child, canvas)

        for scroll_host, scroll_canvas in scrolled_item_tabs:
            bind_mousewheel_tree(scroll_host, scroll_canvas)

        add_field(raw_advanced, "Modifier bits", self.item_fields["modifiers"], 0)
        raw_advanced.columnconfigure(1, weight=1)
        tk.Label(raw_advanced, text="Item Flags and Capabilities now have decoded tabs. Their raw integer fields remain editable there, and any unknown mod-specific bits are preserved. Meshes, faction restrictions, and trigger operations remain untouched; use Module Files for those advanced structures.", bg="#222722", fg="#8e968d", font=("Segoe UI", 8), wraplength=390, justify="left").grid(row=1, column=0, columnspan=2, sticky="w", pady=(14, 0))

        actions = tk.Frame(editor, bg="#222722")
        actions.pack(fill="x", pady=(10, 0))
        self.item_stage_button = ttk.Button(actions, text="Stage Item Changes", style="Gold.TButton", command=self._stage_item_record)
        self.item_stage_button.pack(side="left")
        self.item_revert_button = ttk.Button(actions, text="Revert Item", style="Dark.TButton", command=self._revert_item_record)
        self.item_revert_button.pack(side="left", padx=(8, 0))
        self.item_save_button = ttk.Button(actions, text="Save Items", style="Gold.TButton", command=self._save_item_changes)
        self.item_save_button.pack(side="right")
        self.item_stage_button.state(["disabled"])
        self.item_revert_button.state(["disabled"])
        self.item_save_button.state(["disabled"])

    def _build_troop_tab(self) -> None:
        toolbar = tk.Frame(self.troop_tab, bg="#151916")
        toolbar.pack(fill="x", pady=(0, 10))
        tk.Label(toolbar, textvariable=self.troop_module_var, bg="#151916", fg="#d7ba72", font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Label(toolbar, text="Search", bg="#151916", fg="#a9a28f", font=("Segoe UI", 9)).pack(side="left", padx=(20, 0))
        tk.Entry(toolbar, textvariable=self.troop_search_var, bg="#f4eddb", fg="#201f1a", relief="flat", font=("Segoe UI", 10), width=24).pack(side="left", padx=(8, 10), ipady=6)
        ttk.Button(toolbar, text="Reload", style="Dark.TButton", command=self._reload_troop_file).pack(side="left")
        self.troop_create_button = ttk.Button(toolbar, text="Create…", style="Gold.TButton", command=self._create_troop)
        self.troop_create_button.pack(side="left", padx=(8, 0))
        self.troop_clone_button = ttk.Button(toolbar, text="Clone…", style="Dark.TButton", command=self._clone_troop)
        self.troop_clone_button.pack(side="left", padx=(8, 0))
        tk.Label(toolbar, textvariable=self.troop_change_count_var, bg="#151916", fg="#d7ba72", font=("Segoe UI", 9, "bold")).pack(side="right")
        self.troop_create_button.state(["disabled"])
        self.troop_clone_button.state(["disabled"])

        notice = tk.Frame(self.troop_tab, bg="#29271f", padx=12, pady=8, highlightthickness=1, highlightbackground="#61573c")
        notice.pack(fill="x", pady=(0, 10))
        tk.Label(notice, text="Full compiled troop editor: edit, create, or clone troops with identity, flags, stats, skills, inventory, upgrades, faction, scene, and face codes. New troops are appended so every existing index stays fixed.", bg="#29271f", fg="#dbc98e", font=("Segoe UI", 8), anchor="w").pack(fill="x")

        body = tk.PanedWindow(self.troop_tab, orient="horizontal", bg="#151916", sashwidth=7, bd=0)
        body.pack(fill="both", expand=True)
        list_frame = tk.Frame(body, bg="#202520")
        editor = tk.Frame(body, bg="#222722", padx=12, pady=10)
        body.add(list_frame, minsize=430, stretch="always")
        body.add(editor, minsize=520)

        self.troop_tree = ttk.Treeview(list_frame, columns=("index", "id", "name", "level", "state"), show="headings", style="Config.Treeview", selectmode="browse")
        for column, title in (("index", "#"), ("id", "ID"), ("name", "NAME"), ("level", "LVL"), ("state", "STATE")):
            self.troop_tree.heading(column, text=title)
        self.troop_tree.column("index", width=42, stretch=False)
        self.troop_tree.column("id", width=170, minwidth=120)
        self.troop_tree.column("name", width=145, minwidth=100)
        self.troop_tree.column("level", width=45, stretch=False)
        self.troop_tree.column("state", width=68, stretch=False)
        troop_scroll = ttk.Scrollbar(list_frame, orient="vertical", command=self.troop_tree.yview)
        self.troop_tree.configure(yscrollcommand=troop_scroll.set)
        self.troop_tree.pack(side="left", fill="both", expand=True)
        troop_scroll.pack(side="right", fill="y")
        self.troop_tree.bind("<<TreeviewSelect>>", self._select_troop_record)

        tk.Label(editor, textvariable=self.troop_id_var, bg="#222722", fg="#f1e5c5", font=("Georgia", 14, "bold"), anchor="w").pack(fill="x")
        tk.Label(editor, textvariable=self.troop_meta_var, bg="#222722", fg="#8e968d", font=("Segoe UI", 8), anchor="w").pack(fill="x", pady=(2, 7))
        details = ttk.Notebook(editor)
        details.pack(fill="both", expand=True)

        def scrolled_tab(title: str) -> tk.Frame:
            outer = tk.Frame(details, bg="#222722")
            tab_canvas = tk.Canvas(outer, bg="#222722", highlightthickness=0)
            tab_scroll = ttk.Scrollbar(outer, orient="vertical", command=tab_canvas.yview)
            tab_canvas.configure(yscrollcommand=tab_scroll.set)
            tab_scroll.pack(side="right", fill="y")
            tab_canvas.pack(side="left", fill="both", expand=True)
            inner = tk.Frame(tab_canvas, bg="#222722", padx=10, pady=9)
            window_id = tab_canvas.create_window((0, 0), window=inner, anchor="nw")
            inner.bind("<Configure>", lambda _event, target=tab_canvas: target.configure(scrollregion=target.bbox("all")))
            tab_canvas.bind("<Configure>", lambda event, target=tab_canvas, window=window_id: target.itemconfigure(window, width=event.width))
            details.add(outer, text=title)
            return inner

        general = scrolled_tab("General & Flags")
        stats = scrolled_tab("Stats & Skills")
        inventory = tk.Frame(details, bg="#222722", padx=10, pady=9)
        appearance = scrolled_tab("Face Workshop")
        details.add(inventory, text="Inventory (64)")

        def field(parent: tk.Frame, label: str, variable: tk.StringVar, row: int, column: int = 0) -> None:
            tk.Label(parent, text=label, bg="#222722", fg="#a9a18e", font=("Segoe UI", 8)).grid(row=row, column=column, sticky="w", pady=3)
            tk.Entry(parent, textvariable=variable, bg="#f4eddb", fg="#201f1a", relief="flat", font=("Consolas", 9)).grid(row=row, column=column + 1, sticky="ew", padx=(7, 12), pady=3, ipady=3)

        field(general, "Singular name", self.troop_fields["singular"], 0)
        field(general, "Plural name", self.troop_fields["plural"], 1)
        field(general, "Conversation image", self.troop_fields["image"], 2)
        tk.Label(general, text="Troop type", bg="#222722", fg="#a9a18e", font=("Segoe UI", 8)).grid(row=3, column=0, sticky="w", pady=3)
        ttk.Combobox(general, textvariable=self.troop_type_var, state="readonly", values=tuple(f"{code}: {name}" for code, name in TROOP_TYPES.items())).grid(row=3, column=1, sticky="ew", padx=(7, 12), pady=3)
        field(general, "Scene / entry bits", self.troop_fields["scene"], 4)
        field(general, "Reserved", self.troop_fields["reserved"], 5)
        tk.Label(general, text="Faction", bg="#222722", fg="#a9a18e", font=("Segoe UI", 8)).grid(row=6, column=0, sticky="w", pady=3)
        self.troop_faction_combo = ttk.Combobox(general, textvariable=self.troop_fields["faction"], state="normal")
        self.troop_faction_combo.grid(row=6, column=1, sticky="ew", padx=(7, 12), pady=3)
        for row, key in enumerate(("upgrade_one", "upgrade_two"), start=7):
            tk.Label(general, text=f"Upgrade path {row - 6}", bg="#222722", fg="#a9a18e", font=("Segoe UI", 8)).grid(row=row, column=0, sticky="w", pady=3)
            combo = ttk.Combobox(general, textvariable=self.troop_fields[key], state="normal")
            combo.grid(row=row, column=1, sticky="ew", padx=(7, 12), pady=3)
            if key == "upgrade_one":
                self.troop_upgrade_one_combo = combo
            else:
                self.troop_upgrade_two_combo = combo
        field(general, "Raw flags", self.troop_fields["flags"], 9)
        tk.Label(general, textvariable=self.troop_unknown_flags_var, bg="#222722", fg="#d7ba72", font=("Consolas", 8)).grid(row=10, column=0, columnspan=2, sticky="w", pady=(3, 6))
        for row, (key, label, _bit) in enumerate(TROOP_FLAG_OPTIONS, start=11):
            ttk.Checkbutton(general, text=label, variable=self.troop_flag_vars[key]).grid(row=row, column=0, columnspan=2, sticky="w", pady=1)
        general.columnconfigure(1, weight=1)

        tk.Label(stats, text="ATTRIBUTES & LEVEL", bg="#222722", fg="#8e968d", font=("Segoe UI", 8, "bold")).grid(row=0, column=0, columnspan=4, sticky="w")
        for index, (label, variable) in enumerate(zip(TROOP_ATTRIBUTES, self.troop_attribute_vars)):
            field(stats, label, variable, 1 + index // 2, (index % 2) * 2)
        proficiency_start = 5
        tk.Label(stats, text="WEAPON PROFICIENCIES", bg="#222722", fg="#8e968d", font=("Segoe UI", 8, "bold")).grid(row=proficiency_start, column=0, columnspan=4, sticky="w", pady=(9, 2))
        for index, (label, variable) in enumerate(zip(TROOP_PROFICIENCIES, self.troop_proficiency_vars)):
            field(stats, label, variable, proficiency_start + 1 + index // 2, (index % 2) * 2)
        skill_start = proficiency_start + 6
        tk.Label(stats, text="ALL 42 SKILL SLOTS (0–15)", bg="#222722", fg="#8e968d", font=("Segoe UI", 8, "bold")).grid(row=skill_start, column=0, columnspan=4, sticky="w", pady=(9, 2))
        for index, (label, variable) in enumerate(zip(TROOP_SKILLS, self.troop_skill_vars)):
            field(stats, label, variable, skill_start + 1 + index // 2, (index % 2) * 2)
        stats.columnconfigure(1, weight=1)
        stats.columnconfigure(3, weight=1)

        inv_host = tk.Frame(inventory, bg="#202520")
        inv_host.pack(fill="both", expand=True)
        self.troop_inventory_tree = ttk.Treeview(inv_host, columns=("slot", "item", "modifier"), show="headings", style="Config.Treeview", selectmode="browse", height=11)
        for column, title in (("slot", "SLOT"), ("item", "ITEM"), ("modifier", "MODIFIER")):
            self.troop_inventory_tree.heading(column, text=title)
        self.troop_inventory_tree.column("slot", width=48, stretch=False)
        self.troop_inventory_tree.column("item", width=300, minwidth=180)
        self.troop_inventory_tree.column("modifier", width=100, stretch=False)
        inv_scroll = ttk.Scrollbar(inv_host, orient="vertical", command=self.troop_inventory_tree.yview)
        self.troop_inventory_tree.configure(yscrollcommand=inv_scroll.set)
        self.troop_inventory_tree.pack(side="left", fill="both", expand=True)
        inv_scroll.pack(side="right", fill="y")
        self.troop_inventory_tree.bind("<<TreeviewSelect>>", self._select_troop_inventory_slot)
        inv_edit = tk.Frame(inventory, bg="#222722")
        inv_edit.pack(fill="x", pady=(7, 0))
        tk.Label(inv_edit, text="Item", bg="#222722", fg="#a9a18e", font=("Segoe UI", 8)).grid(row=0, column=0, sticky="w")
        self.troop_item_combo = ttk.Combobox(inv_edit, textvariable=self.troop_item_var, state="normal")
        self.troop_item_combo.grid(row=0, column=1, columnspan=3, sticky="ew", padx=(6, 0))
        tk.Label(inv_edit, text="Raw modifier", bg="#222722", fg="#a9a18e", font=("Segoe UI", 8)).grid(row=1, column=0, sticky="w", pady=(5, 0))
        tk.Entry(inv_edit, textvariable=self.troop_modifier_var, bg="#f4eddb", fg="#201f1a", relief="flat", font=("Consolas", 9)).grid(row=1, column=1, sticky="ew", padx=(6, 8), pady=(5, 0), ipady=3)
        ttk.Button(inv_edit, text="Apply Slot", style="Dark.TButton", command=self._apply_troop_inventory_slot).grid(row=1, column=2, padx=(0, 6), pady=(5, 0))
        ttk.Button(inv_edit, text="Clear Slot", style="Dark.TButton", command=self._clear_troop_inventory_slot).grid(row=1, column=3, pady=(5, 0))
        inv_edit.columnconfigure(1, weight=1)

        intro = tk.Frame(appearance, bg="#29271f", padx=11, pady=9, highlightthickness=1, highlightbackground="#61573c")
        intro.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 9))
        tk.Label(intro, text="SAFE FACE PRESET WORKSHOP", bg="#29271f", fg="#dbc98e", font=("Segoe UI", 8, "bold")).pack(anchor="w")
        tk.Label(intro, text="Randomization samples valid, non-empty face presets from troops of the same type in this module. It never invents arbitrary face-code bits.", bg="#29271f", fg="#bdb496", font=("Segoe UI", 8), wraplength=445, justify="left").pack(anchor="w", pady=(3, 0))

        face_flag = tk.Checkbutton(
            appearance, text="Randomize between Face 1 and Face 2 when this troop spawns",
            variable=self.troop_flag_vars["randomize_face"], bg="#222722", fg="#ded5bd",
            activebackground="#222722", activeforeground="#fff5dc", selectcolor="#303730",
            font=("Segoe UI", 9), anchor="w",
        )
        face_flag.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 7))

        face_actions = tk.Frame(appearance, bg="#222722")
        face_actions.grid(row=2, column=0, columnspan=2, sticky="ew")
        ttk.Button(face_actions, text="Randomize Range", style="Gold.TButton", command=lambda: self._randomize_troop_face(False)).grid(row=0, column=0, padx=(0, 6), pady=3, sticky="ew")
        ttk.Button(face_actions, text="Randomize Fixed Face", style="Dark.TButton", command=lambda: self._randomize_troop_face(True)).grid(row=0, column=1, padx=(0, 6), pady=3, sticky="ew")
        ttk.Button(face_actions, text="Swap Faces", style="Dark.TButton", command=self._swap_troop_faces).grid(row=0, column=2, pady=3, sticky="ew")
        ttk.Button(face_actions, text="Use Face 1 as Fixed", style="Dark.TButton", command=self._fix_troop_face_one).grid(row=1, column=0, padx=(0, 6), pady=3, sticky="ew")
        ttk.Button(face_actions, text="Reset Face", style="Dark.TButton", command=self._reset_troop_face).grid(row=1, column=1, padx=(0, 6), pady=3, sticky="ew")
        for column in range(3):
            face_actions.columnconfigure(column, weight=1)
        tk.Label(appearance, textvariable=self.troop_face_status_var, bg="#222722", fg="#d7ba72", font=("Segoe UI", 8), wraplength=445, justify="left").grid(row=3, column=0, columnspan=2, sticky="ew", pady=(5, 9))

        for face_index, title in enumerate(("FACE 1 — PRIMARY", "FACE 2 — RANGE END")):
            panel = tk.LabelFrame(appearance, text=title, bg="#202520", fg="#b99b59", bd=1, relief="solid", padx=10, pady=7, font=("Segoe UI", 8, "bold"))
            panel.grid(row=4 + face_index, column=0, columnspan=2, sticky="ew", pady=(0, 8))
            for word_index in range(4):
                variable = self.troop_face_vars[(face_index * 4) + word_index]
                column = (word_index % 2) * 2
                row = word_index // 2
                tk.Label(panel, text=f"Word {word_index + 1}", bg="#202520", fg="#a9a18e", font=("Segoe UI", 8)).grid(row=row, column=column, sticky="w", pady=3)
                tk.Entry(panel, textvariable=variable, bg="#f4eddb", fg="#201f1a", relief="flat", font=("Consolas", 8)).grid(row=row, column=column + 1, sticky="ew", padx=(6, 10), pady=3, ipady=3)
            panel.columnconfigure(1, weight=1)
            panel.columnconfigure(3, weight=1)

        tk.Label(appearance, text="Advanced: each face is a 256-bit code stored as four unsigned 64-bit words. Manual values remain editable and are validated when the troop is staged.", bg="#222722", fg="#7f877f", font=("Segoe UI", 8), wraplength=445, justify="left").grid(row=6, column=0, columnspan=2, sticky="w", pady=(1, 0))
        appearance.columnconfigure(0, weight=1)
        appearance.columnconfigure(1, weight=1)

        actions = tk.Frame(editor, bg="#222722")
        actions.pack(fill="x", pady=(9, 0))
        self.troop_stage_button = ttk.Button(actions, text="Stage Troop Changes", style="Gold.TButton", command=self._stage_troop_record)
        self.troop_stage_button.pack(side="left")
        self.troop_revert_button = ttk.Button(actions, text="Revert Troop", style="Dark.TButton", command=self._revert_troop_record)
        self.troop_revert_button.pack(side="left", padx=(7, 0))
        self.troop_save_button = ttk.Button(actions, text="Save Troops", style="Gold.TButton", command=self._save_troop_changes)
        self.troop_save_button.pack(side="right")
        for button in (self.troop_stage_button, self.troop_revert_button, self.troop_save_button):
            button.state(["disabled"])

    def _build_raw_tab(self) -> None:
        toolbar = tk.Frame(self.raw_tab, bg="#151916")
        toolbar.pack(fill="x", pady=(0, 10))
        tk.Label(toolbar, textvariable=self.raw_module_var, bg="#151916", fg="#d7ba72", font=("Segoe UI", 9, "bold")).pack(side="left")
        tk.Label(toolbar, text="Filter files", bg="#151916", fg="#a9a28f", font=("Segoe UI", 9)).pack(side="left", padx=(22, 0))
        tk.Entry(toolbar, textvariable=self.raw_search_var, bg="#f4eddb", fg="#201f1a", insertbackground="#201f1a", relief="flat", font=("Segoe UI", 10), width=24).pack(side="left", padx=(8, 12), ipady=6)
        ttk.Button(toolbar, text="Refresh Files", style="Dark.TButton", command=self._refresh_raw_files).pack(side="left")
        tk.Label(toolbar, textvariable=self.raw_state_var, bg="#151916", fg="#d7ba72", font=("Segoe UI", 9, "bold")).pack(side="right")

        notice = tk.Frame(self.raw_tab, bg="#29271f", padx=12, pady=8, highlightthickness=1, highlightbackground="#61573c")
        notice.pack(fill="x", pady=(0, 10))
        tk.Label(notice, text="Advanced editor for remaining module .txt files. Clone the module first: compiled operation files are version-specific and bad edits can prevent loading.", bg="#29271f", fg="#dbc98e", font=("Segoe UI", 9), anchor="w").pack(fill="x")

        body = tk.PanedWindow(self.raw_tab, orient="horizontal", bg="#151916", sashwidth=7, sashrelief="flat", bd=0)
        body.pack(fill="both", expand=True)
        files_frame = tk.Frame(body, bg="#202520", padx=7, pady=7)
        editor_frame = tk.Frame(body, bg="#222722", padx=10, pady=9)
        body.add(files_frame, minsize=240)
        body.add(editor_frame, minsize=620, stretch="always")

        tk.Label(files_frame, text="MODULE TEXT FILES", bg="#202520", fg="#b99b59", font=("Segoe UI", 8, "bold"), anchor="w").pack(fill="x", pady=(0, 6))
        list_host = tk.Frame(files_frame, bg="#202520")
        list_host.pack(fill="both", expand=True)
        self.raw_file_list = tk.Listbox(list_host, bg="#202520", fg="#ded5bd", selectbackground="#665938", selectforeground="#fff6de", relief="flat", borderwidth=0, font=("Consolas", 10), exportselection=False)
        file_scroll = ttk.Scrollbar(list_host, orient="vertical", command=self.raw_file_list.yview)
        self.raw_file_list.configure(yscrollcommand=file_scroll.set)
        self.raw_file_list.pack(side="left", fill="both", expand=True)
        file_scroll.pack(side="right", fill="y")
        self.raw_file_list.bind("<<ListboxSelect>>", self._select_raw_file)

        header = tk.Frame(editor_frame, bg="#222722")
        header.pack(fill="x", pady=(0, 7))
        tk.Label(header, textvariable=self.raw_file_var, bg="#222722", fg="#f1e5c5", font=("Georgia", 14, "bold"), anchor="w").pack(side="left", fill="x", expand=True)
        ttk.Button(header, text="Reload File", style="Dark.TButton", command=self._reload_raw_file).pack(side="right")

        text_host = tk.Frame(editor_frame, bg="#202520")
        text_host.pack(fill="both", expand=True)
        self.raw_text_widget = tk.Text(text_host, bg="#171b17", fg="#e5dcc5", insertbackground="#e5dcc5", selectbackground="#665938", relief="flat", undo=True, wrap="none", font=("Consolas", 9), padx=8, pady=8)
        raw_y = ttk.Scrollbar(text_host, orient="vertical", command=self.raw_text_widget.yview)
        raw_x = ttk.Scrollbar(text_host, orient="horizontal", command=self.raw_text_widget.xview)
        self.raw_text_widget.configure(yscrollcommand=raw_y.set, xscrollcommand=raw_x.set)
        self.raw_text_widget.grid(row=0, column=0, sticky="nsew")
        raw_y.grid(row=0, column=1, sticky="ns")
        raw_x.grid(row=1, column=0, sticky="ew")
        text_host.rowconfigure(0, weight=1)
        text_host.columnconfigure(0, weight=1)
        self.raw_text_widget.bind("<<Modified>>", self._raw_text_modified)

        save_bar = tk.Frame(editor_frame, bg="#222722")
        save_bar.pack(fill="x", pady=(8, 0))
        tk.Label(save_bar, text="Exact external-change check + timestamped backup before every save", bg="#222722", fg="#777f78", font=("Segoe UI", 8)).pack(side="left")
        self.raw_save_button = ttk.Button(save_bar, text="Save Raw Text File", style="Gold.TButton", command=self._save_raw_file)
        self.raw_save_button.pack(side="right")
        self.raw_save_button.state(["disabled"])

    def _sync_quick_config(self) -> None:
        by_key = {entry.key.lower(): entry for entry in self.entries}
        for key, variable in self.quick_config_vars.items():
            entry = by_key.get(key)
            variable.set(self.pending.get(entry.line_index, entry.value) if entry else "")

    def _sync_quick_module(self) -> None:
        by_key = {entry.key.lower(): entry for entry in self.module_entries}
        for key, variable in self.quick_module_vars.items():
            entry = by_key.get(key)
            variable.set(self.module_pending.get(entry.line_index, entry.value) if entry else "")

    def _save_quick_config(self) -> None:
        try:
            if not self.config_path:
                raise FileNotFoundError("Load rgl_config.txt first.")
            by_key = {entry.key.lower(): entry for entry in self.entries}
            touched = 0
            for key, variable in self.quick_config_vars.items():
                entry = by_key.get(key)
                value = variable.get().strip()
                if not entry or value == "":
                    continue
                validated = validate_config_value(entry.value, value)
                if validated == entry.value:
                    self.pending.pop(entry.line_index, None)
                else:
                    self.pending[entry.line_index] = validated
                touched += 1
            if not self.pending:
                self.status_var.set("Player quick edits already match rgl_config.txt.")
                self._sync_quick_config()
                return
            count = len(self.pending)
            backup = self._save_pending()
            self.status_var.set(f"Saved {count} player config change{'s' if count != 1 else ''}. Backup: {backup.name}")
            messagebox.showinfo(APP_TITLE, f"Saved {count} player quick edit{'s' if count != 1 else ''}.\n\nBackup created:\n{backup.name}\n\nRestart Warband to apply all settings.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _save_quick_module(self) -> None:
        try:
            if not self.module_ini_path:
                raise FileNotFoundError("Load a Warband module first.")
            by_key = {entry.key.lower(): entry for entry in self.module_entries}
            missing: list[str] = []
            for key, variable in self.quick_module_vars.items():
                entry = by_key.get(key)
                value = variable.get().strip()
                if not entry:
                    missing.append(key)
                    continue
                if value == "":
                    continue
                validated = validate_config_value(entry.value, value)
                if validated == entry.value:
                    self.module_pending.pop(entry.line_index, None)
                else:
                    self.module_pending[entry.line_index] = validated
            if not self.module_pending:
                suffix = f" ({len(missing)} unsupported settings hidden by this module.)" if missing else ""
                self.status_var.set(f"Module quick edits already match module.ini{suffix}")
                self._sync_quick_module()
                return
            count = len(self.module_pending)
            backup = self._save_module_pending()
            self.status_var.set(f"Saved {count} module quick edit{'s' if count != 1 else ''}. Backup: {backup.name}")
            messagebox.showinfo(APP_TITLE, f"Saved {count} module quick edit{'s' if count != 1 else ''}.\n\nBackup created:\n{backup.name}")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _load_battle_continuation(self, module_dir: Path) -> None:
        path = module_dir / "mission_templates.txt"
        self.mission_file_path = None
        self.mission_text = ""
        self.continuation_var.set(False)
        if not path.is_file():
            self.continuation_state_var.set("mission_templates.txt is not available in this module")
            return
        text, encoding = read_config(path)
        state, count = battle_continuation_state(text)
        self.mission_file_path = path
        self.mission_text = text
        self.mission_encoding = encoding
        self.continuation_var.set(state == "enabled")
        if state == "enabled":
            message = "Enabled — all 8 guarded player-fall triggers are disabled"
        elif state == "disabled":
            message = "Disabled — Native player knock-out behavior detected (8/8 triggers)"
        elif state == "mixed":
            message = "Mixed trigger state — use Module Files or restore a backup before changing"
        else:
            message = f"Unsupported mission-template layout ({count}/8 recognized triggers); no automatic edit"
        self.continuation_state_var.set(message)

    def _apply_battle_continuation(self) -> None:
        try:
            if not self.mission_file_path:
                raise FileNotFoundError("Load a supported module with mission_templates.txt first.")
            if self.raw_dirty and self.raw_path and self.raw_path.resolve() == self.mission_file_path.resolve():
                raise RuntimeError("Save or discard the raw mission_templates.txt edit first.")
            latest, encoding = read_config(self.mission_file_path)
            require_unchanged_text(self.mission_text, latest, self.mission_file_path.name)
            updated = set_battle_continuation(latest, self.continuation_var.get())
            if updated == latest:
                self._load_battle_continuation(self.mission_file_path.parent)
                self.status_var.set("Battle continuation already matches the selected setting.")
                return
            backup = write_config_text(self.mission_file_path, updated, encoding, False)
            path = self.mission_file_path
            self._load_battle_continuation(path.parent)
            if self.raw_path and self.raw_path.resolve() == path.resolve() and not self.raw_dirty:
                self._load_raw_file(path)
            self.status_var.set(f"Saved battle continuation setting. Backup: {backup.name}")
            messagebox.showinfo(APP_TITLE, f"Battle continuation is now {'enabled' if self.continuation_var.get() else 'disabled'}.\n\nOnly the eight guarded player-fall conditions were changed.\nBackup created:\n{backup.name}")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _load_gameplay_tweaks(self, module_dir: Path) -> None:
        self.gameplay_module_var.set(f"MODULE: {module_dir.name}")
        self.gameplay_sources = {}
        self.gameplay_skill_records = []
        self.gameplay_player_line = None
        for button in (
            self.gameplay_tournament_save_button, self.gameplay_siege_save_button, self.gameplay_economy_save_button,
            self.gameplay_party_save_button, self.gameplay_battle_save_button, self.gameplay_recruitment_save_button,
            self.gameplay_player_save_button,
        ):
            button.state(["disabled"])
        for variable in (self.gameplay_bet_amounts_var, *self.gameplay_vars.values(), *self.gameplay_player_attribute_vars, *self.gameplay_player_skill_vars, *self.gameplay_skill_max_vars):
            variable.set("")
        self.gameplay_tavern_prisoners_var.set(False)

        for filename in ("menus.txt", "scripts.txt", "simple_triggers.txt", "conversation.txt", "skills.txt", "troops.txt"):
            path = module_dir / filename
            if path.is_file():
                text, encoding = read_config(path)
                self.gameplay_sources[filename] = (path, text, encoding)

        try:
            menus_text = self.gameplay_sources["menus.txt"][1]
            scripts_text = self.gameplay_sources["scripts.txt"][1]
            values = tournament_tweaks(menus_text, scripts_text)
            self.gameplay_bet_amounts_var.set(", ".join(map(str, values["bet_amounts"])))
            self.gameplay_vars["tournament_prize"].set(str(values["prize"]))
            self.gameplay_vars["tournament_renown"].set(str(values["renown"]))
            self.gameplay_vars["tournament_xp"].set(str(values["xp"]))
            self.gameplay_tournament_status_var.set(f"{len(values['bet_amounts'])} guarded bet choices found in menus.txt.")
            self.gameplay_tournament_save_button.state(["!disabled"])
        except (KeyError, ValueError) as exc:
            self.gameplay_tournament_status_var.set(f"Unsupported in this module: {exc}")

        try:
            values = siege_tweaks(self.gameplay_sources["menus.txt"][1])
            for key, value in values.items():
                self.gameplay_vars[key].set(str(value))
            self.gameplay_siege_status_var.set("Guarded ladder and siege-tower display/action formulas are supported.")
            self.gameplay_siege_save_button.state(["!disabled"])
        except (KeyError, ValueError) as exc:
            self.gameplay_siege_status_var.set(f"Unsupported in this module: {exc}")

        try:
            scripts_text = self.gameplay_sources["scripts.txt"][1]
            simple_text = self.gameplay_sources["simple_triggers.txt"][1]
            values = campaign_time_tweaks(simple_text, scripts_text)
            for key, value in values.items():
                self.gameplay_vars[key].set(str(value))
            self.gameplay_economy_status_var.set("Weekly rents, prosperity scaling, food use, and refresh clocks are supported.")
            self.gameplay_economy_save_button.state(["!disabled"])
        except (KeyError, ValueError) as exc:
            self.gameplay_economy_status_var.set(f"Unsupported in this module: {exc}")

        try:
            values = party_tweaks(self.gameplay_sources["scripts.txt"][1])
            for key, value in values.items():
                self.gameplay_vars[key].set(str(value))
            self.gameplay_party_status_var.set("Base size, renown scaling, and the garrison wage discount are supported.")
            self.gameplay_party_save_button.state(["!disabled"])
        except (KeyError, ValueError) as exc:
            self.gameplay_party_status_var.set(f"Unsupported in this module: {exc}")

        try:
            values = battle_reward_tweaks(self.gameplay_sources["scripts.txt"][1])
            for key, value in values.items():
                self.gameplay_vars[key].set(str(value))
            self.gameplay_battle_status_var.set("Guarded post-battle gold and XP reward formulas are supported.")
            self.gameplay_battle_save_button.state(["!disabled"])
        except (KeyError, ValueError) as exc:
            self.gameplay_battle_status_var.set(f"Unsupported in this module: {exc}")

        try:
            scripts_text = self.gameplay_sources["scripts.txt"][1]
            conversation_text = self.gameplay_sources["conversation.txt"][1]
            values = {**recruitment_tweaks(scripts_text), **prisoner_price_tweaks(scripts_text)}
            for key, value in values.items():
                self.gameplay_vars[key].set(str(value))
            tavern_state = tavern_prisoner_sales_state(conversation_text)
            if tavern_state == "unsupported":
                raise ValueError("conversation.txt lacks the guarded tavern/ransom dialog records.")
            self.gameplay_tavern_prisoners_var.set(tavern_state == "enabled")
            self.gameplay_recruitment_status_var.set("Village, mercenary, prisoner-price, and tavern dialog records are supported.")
            self.gameplay_recruitment_save_button.state(["!disabled"])
        except (KeyError, ValueError) as exc:
            self.gameplay_recruitment_status_var.set(f"Unsupported in this module: {exc}")

        try:
            skills_text = self.gameplay_sources["skills.txt"][1]
            records = parse_skills(skills_text)
            if len(records) != len(TROOP_SKILLS):
                raise ValueError(f"Expected {len(TROOP_SKILLS)} skills but found {len(records)}.")
            player = next((record for record in self.troop_records if record.troop_id == "trp_player"), None)
            if player is None:
                raise ValueError("trp_player was not found in troops.txt.")
            levels = troop_skill_levels(player.skill_words)
            for variable, value in zip(self.gameplay_player_attribute_vars, player.attributes):
                variable.set(str(value))
            for index in PLAYER_SKILL_INDICES:
                self.gameplay_player_skill_vars[index].set(str(levels[index]))
                self.gameplay_skill_max_vars[index].set(str(records[index].max_level))
            self.gameplay_skill_records = records
            self.gameplay_player_line = player.line_index
            self.gameplay_player_status_var.set("Player defaults and all 24 named skill caps are editable. Existing saves keep their current player stats.")
            self.gameplay_player_save_button.state(["!disabled"])
        except (KeyError, ValueError) as exc:
            self.gameplay_player_status_var.set(f"Unsupported in this module: {exc}")

    def _reload_gameplay_tweaks(self) -> None:
        if not self.module_dir:
            return
        self._load_gameplay_tweaks(self.module_dir)
        self.status_var.set(f"Reloaded gameplay tweak sources for {self.module_dir.name}.")

    def _gameplay_latest(self, filename: str) -> tuple[Path, str, str]:
        if filename not in self.gameplay_sources:
            raise FileNotFoundError(f"{filename} is not available in the selected module.")
        path, original, _original_encoding = self.gameplay_sources[filename]
        if self.raw_dirty and self.raw_path and self.raw_path.resolve() == path.resolve():
            raise RuntimeError(f"Save or discard the raw {filename} edit first.")
        latest, encoding = read_config(path)
        require_unchanged_text(original, latest, filename)
        return path, latest, encoding

    def _refresh_raw_after_gameplay_save(self, changed_paths: list[Path]) -> None:
        if not self.raw_dirty and self.raw_path and any(self.raw_path.resolve() == path.resolve() for path in changed_paths):
            self._load_raw_file(self.raw_path)

    def _save_tournament_tweaks(self) -> None:
        try:
            amounts = tuple(int(part.strip()) for part in self.gameplay_bet_amounts_var.get().split(",") if part.strip())
            prize = int(self.gameplay_vars["tournament_prize"].get().strip())
            renown = int(self.gameplay_vars["tournament_renown"].get().strip())
            xp = int(self.gameplay_vars["tournament_xp"].get().strip())
            menu_path, menus_text, menu_encoding = self._gameplay_latest("menus.txt")
            _script_path, scripts_text, _script_encoding = self._gameplay_latest("scripts.txt")
            updated = set_tournament_tweaks(menus_text, scripts_text, amounts, prize, renown, xp)
            if updated == menus_text:
                self.status_var.set("Tournament tweaks already match the requested values.")
                return
            backup = write_config_text(menu_path, updated, menu_encoding, False)
            self._load_gameplay_tweaks(menu_path.parent)
            self._refresh_raw_after_gameplay_save([menu_path])
            self.status_var.set(f"Saved tournament betting and rewards. Backup: {backup.name}")
            messagebox.showinfo(APP_TITLE, f"Tournament betting and rewards saved.\n\nBackup created:\n{backup.name}\n\nRestart Warband before testing the changes.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _save_siege_tweaks(self) -> None:
        try:
            keys = ("ladder_skill_base", "ladder_time_multiplier", "ladder_time_divisor", "tower_skill_base", "tower_time_multiplier")
            values = {key: int(self.gameplay_vars[key].get().strip()) for key in keys}
            path, text, encoding = self._gameplay_latest("menus.txt")
            updated = set_siege_tweaks(text, values)
            if updated == text:
                self.status_var.set("Siege construction times already match the requested values.")
                return
            backup = write_config_text(path, updated, encoding, False)
            self._load_gameplay_tweaks(path.parent)
            self._refresh_raw_after_gameplay_save([path])
            self.status_var.set(f"Saved siege construction times. Backup: {backup.name}")
            messagebox.showinfo(APP_TITLE, f"Siege construction times saved.\n\nBackup created:\n{backup.name}\n\nRestart Warband before testing the changes.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _save_economy_tweaks(self) -> None:
        try:
            int_keys = ("village_rent", "castle_rent", "town_rent", "prosperity_base", "prosperity_divisor", "food_troops_per_unit")
            time_keys = ("fief_interval_hours", "food_interval_hours", "refresh_interval_hours")
            values: dict[str, int | float] = {key: int(self.gameplay_vars[key].get().strip()) for key in int_keys}
            values.update({key: float(self.gameplay_vars[key].get().strip()) for key in time_keys})
            simple_path, simple_text, simple_encoding = self._gameplay_latest("simple_triggers.txt")
            _script_path, scripts_text, _script_encoding = self._gameplay_latest("scripts.txt")
            updated = set_campaign_time_tweaks(simple_text, scripts_text, values)
            if updated == simple_text:
                self.status_var.set("Fief income and campaign clocks already match the requested values.")
                return
            backup = write_config_text(simple_path, updated, simple_encoding, False)
            self._load_gameplay_tweaks(simple_path.parent)
            self._refresh_raw_after_gameplay_save([simple_path])
            self.status_var.set(f"Saved fief income and campaign clocks. Backup: {backup.name}")
            messagebox.showinfo(APP_TITLE, f"Fief income and campaign clocks saved.\n\nBackup created:\n{backup.name}\n\nRestart Warband before testing the changes.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _save_party_tweaks(self) -> None:
        try:
            keys = ("party_base_size", "party_renown_divisor", "garrison_wage_divisor")
            values = {key: int(self.gameplay_vars[key].get().strip()) for key in keys}
            path, text, encoding = self._gameplay_latest("scripts.txt")
            updated = set_party_tweaks(text, values)
            if updated == text:
                self.status_var.set("Party size and wage rules already match the requested values.")
                return
            backup = write_config_text(path, updated, encoding, False)
            self._load_gameplay_tweaks(path.parent)
            self._refresh_raw_after_gameplay_save([path])
            self.status_var.set(f"Saved party size and wage rules. Backup: {backup.name}")
            messagebox.showinfo(APP_TITLE, f"Party size and wage rules saved.\n\nBackup created:\n{backup.name}\n\nRestart Warband before testing the changes.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _save_battle_reward_tweaks(self) -> None:
        try:
            keys = (
                "battle_level_bonus", "battle_gain_divisor", "battle_gold_share", "battle_gold_cap",
                "battle_gold_roll_min", "battle_gold_roll_max", "battle_gold_divisor",
                "battle_xp_roll_min", "battle_xp_roll_max", "battle_xp_divisor",
            )
            values = {key: int(self.gameplay_vars[key].get().strip()) for key in keys}
            path, text, encoding = self._gameplay_latest("scripts.txt")
            updated = set_battle_reward_tweaks(text, values)
            if updated == text:
                self.status_var.set("Post-battle gold and XP rules already match the requested values.")
                return
            backup = write_config_text(path, updated, encoding, False)
            self._load_gameplay_tweaks(path.parent)
            self._refresh_raw_after_gameplay_save([path])
            self.status_var.set(f"Saved post-battle gold and XP rules. Backup: {backup.name}")
            messagebox.showinfo(APP_TITLE, f"Post-battle gold and XP rules saved.\n\nBackup created:\n{backup.name}\n\nRestart Warband before testing the changes.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _save_recruitment_tweaks(self) -> None:
        try:
            recruitment_keys = ("village_base", "village_relation_bonus", "village_multiplier", "village_price", "mercenary_min", "mercenary_max")
            prisoner_keys = ("prisoner_level_bonus", "prisoner_divisor", "prisoner_minimum")
            recruitment_values = {key: int(self.gameplay_vars[key].get().strip()) for key in recruitment_keys}
            prisoner_values = {key: int(self.gameplay_vars[key].get().strip()) for key in prisoner_keys}
            script_path, scripts_text, script_encoding = self._gameplay_latest("scripts.txt")
            conversation_path, conversation_text, conversation_encoding = self._gameplay_latest("conversation.txt")
            updated_scripts = set_recruitment_tweaks(scripts_text, recruitment_values)
            updated_scripts = set_prisoner_price_tweaks(updated_scripts, prisoner_values)
            updated_conversation = set_tavern_prisoner_sales(conversation_text, self.gameplay_tavern_prisoners_var.get())
            changes: list[tuple[Path, str, str, bool]] = []
            if updated_scripts != scripts_text:
                changes.append((script_path, updated_scripts, script_encoding, False))
            if updated_conversation != conversation_text:
                changes.append((conversation_path, updated_conversation, conversation_encoding, False))
            if not changes:
                self.status_var.set("Recruitment and prisoner tweaks already match the requested values.")
                return
            backup_paths = write_config_batch(changes)
            changed_paths = [change[0] for change in changes]
            backups = [backup.name for backup in backup_paths]
            self._load_gameplay_tweaks(script_path.parent)
            self._refresh_raw_after_gameplay_save(changed_paths)
            self.status_var.set(f"Saved recruitment and prisoner tweaks. {len(backups)} backup file{'s' if len(backups) != 1 else ''} created.")
            messagebox.showinfo(APP_TITLE, "Recruitment, mercenary, and prisoner tweaks saved.\n\nBackups created:\n" + "\n".join(backups) + "\n\nRestart Warband before testing the changes.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _save_player_gameplay_tweaks(self) -> None:
        if self.troop_pending or self.troop_additions:
            messagebox.showerror(APP_TITLE, "Save or revert staged Troop Editor changes before changing player defaults here.")
            return
        try:
            if self.gameplay_player_line is None or not self.gameplay_skill_records:
                raise ValueError("Load supported player and skill records first.")
            troop_path, troops_text, troop_encoding = self._gameplay_latest("troops.txt")
            skill_path, skills_text, skill_encoding = self._gameplay_latest("skills.txt")
            records = parse_troops(troops_text)
            player = next((record for record in records if record.line_index == self.gameplay_player_line and record.troop_id == "trp_player"), None)
            if player is None:
                raise ValueError("trp_player changed outside the gameplay editor; reload first.")
            attributes = tuple(int(variable.get().strip()) for variable in self.gameplay_player_attribute_vars)
            levels = list(troop_skill_levels(player.skill_words))
            maximum_updates: dict[int, int] = {}
            for index in PLAYER_SKILL_INDICES:
                level = int(self.gameplay_player_skill_vars[index].get().strip())
                maximum = int(self.gameplay_skill_max_vars[index].get().strip())
                if not 0 <= level <= 15 or not 0 <= maximum <= 15:
                    raise ValueError(f"{TROOP_SKILLS[index]} start and maximum must be between 0 and 15.")
                if level > maximum:
                    raise ValueError(f"{TROOP_SKILLS[index]} starting level cannot exceed its module maximum.")
                levels[index] = level
                maximum_updates[self.gameplay_skill_records[index].line_index] = maximum
            updated_player = replace(player, attributes=attributes, skill_words=rebuild_troop_skill_words(player.skill_words, tuple(levels)))
            validate_troop_record(updated_player, len(records), len(self.item_records) or None)
            updated_troops = apply_troop_updates(troops_text, {player.line_index: updated_player})
            updated_skills = apply_skill_maximums(skills_text, maximum_updates)
            changes: list[tuple[Path, str, str, bool]] = []
            if updated_skills != skills_text:
                changes.append((skill_path, updated_skills, skill_encoding, False))
            if updated_troops != troops_text:
                changes.append((troop_path, updated_troops, troop_encoding, False))
            if not changes:
                self.status_var.set("Player defaults and skill rules already match the requested values.")
                return
            backup_paths = write_config_batch(changes)
            changed_paths = [change[0] for change in changes]
            backups = [backup.name for backup in backup_paths]
            self._load_troop_file(troop_path.parent)
            self._load_gameplay_tweaks(troop_path.parent)
            self._refresh_raw_after_gameplay_save(changed_paths)
            self.status_var.set(f"Saved new-campaign player and skill rules. {len(backups)} backup file{'s' if len(backups) != 1 else ''} created.")
            messagebox.showinfo(APP_TITLE, "Player defaults and module skill caps saved.\n\nBackups created:\n" + "\n".join(backups) + "\n\nPlayer attribute/skill defaults apply to new campaigns. Existing saves keep their current player stats.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _detect_modules(self) -> None:
        install = find_warband_install()
        self.known_modules = discover_modules(install) if install else []
        self.module_combo.configure(values=[str(path) for path in self.known_modules])
        if self.known_modules:
            preferred = next((path for path in self.known_modules if path.name.casefold() == "native"), self.known_modules[0])
            self.module_path_var.set(str(preferred))
            try:
                self._load_module(preferred)
            except Exception as exc:
                self.status_var.set(f"Could not load {preferred.name}: {exc}")
        else:
            self.module_path_var.set("")

    def _load_module(self, module_dir: Path, discard: bool = False, reload_party: bool = True) -> None:
        module_dir = module_dir.expanduser().resolve()
        ini_path = module_dir / "module.ini"
        if not ini_path.is_file():
            raise FileNotFoundError(f"module.ini was not found in:\n{module_dir}")
        if (self.module_pending or self.party_pending or self.item_pending or self.item_additions or self.troop_pending or self.troop_additions or self.raw_dirty) and not discard and not messagebox.askyesno(APP_TITLE, "Discard staged module changes and load another module?"):
            return
        text, encoding = read_config(ini_path)
        self.module_dir = module_dir
        self.module_ini_path = ini_path
        self.module_text = text
        self.module_encoding = encoding
        self.module_entries = parse_config_entries(text)
        self.module_pending = {}
        self.module_selected_line = None
        self.module_path_var.set(str(module_dir))
        if module_dir not in self.known_modules:
            self.known_modules.append(module_dir)
            self.known_modules.sort(key=lambda path: path.name.casefold())
            self.module_combo.configure(values=[str(path) for path in self.known_modules])
        self._refresh_module_tree()
        self._update_module_change_count()
        self._clear_module_editor()
        self._sync_quick_module()
        if reload_party:
            self._load_item_file(module_dir)
            self._load_troop_file(module_dir)
            self._load_gameplay_tweaks(module_dir)
            self._load_party_file(module_dir)
            self._load_battle_continuation(module_dir)
            self._load_raw_files(module_dir)
        self.status_var.set(f"Loaded {len(self.module_entries)} module.ini entries from {module_dir.name}.")

    def _load_module_from_var(self) -> None:
        try:
            self._load_module(Path(os.path.expandvars(self.module_path_var.get().strip())))
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _browse_module(self) -> None:
        initial = self.module_dir.parent if self.module_dir else (find_warband_install() or Path.home())
        selected = filedialog.askdirectory(title="Select a Warband module folder", initialdir=initial)
        if selected:
            try:
                self._load_module(Path(selected))
            except Exception as exc:
                messagebox.showerror(APP_TITLE, str(exc))

    def _clone_current_module(self) -> None:
        if not self.module_dir:
            messagebox.showerror(APP_TITLE, "Load a Warband module first.")
            return
        if (self.module_pending or self.party_pending or self.item_pending or self.item_additions or self.troop_pending or self.troop_additions or self.raw_dirty) and not messagebox.askyesno(APP_TITLE, "The staged module changes are not saved and will not be included in the clone. Continue?"):
            return
        folder_name = simpledialog.askstring(APP_TITLE, "New module folder name:", initialvalue=f"{self.module_dir.name} Tweaked", parent=self)
        if folder_name is None:
            return
        folder_name = folder_name.strip()
        if not folder_name or any(character in folder_name for character in '<>:"/\\|?*'):
            messagebox.showerror(APP_TITLE, "Use a non-empty Windows folder name without < > : \" / \\ | ? * characters.")
            return
        display_name = simpledialog.askstring(APP_TITLE, "Name shown in the Warband launcher:", initialvalue=folder_name, parent=self)
        if display_name is None:
            return
        try:
            source_name = self.module_dir.name
            destination = self.module_dir.parent / folder_name
            clone_module(self.module_dir, destination, display_name)
            self._load_module(destination, discard=True)
            self.status_var.set(f"Cloned {source_name} to {destination.name}.")
            messagebox.showinfo(APP_TITLE, f"Module clone created:\n{destination}\n\nThe clone is now loaded for editing.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, f"Could not clone the module. Warband installations under Program Files may require administrator permission.\n\n{exc}")

    def _module_entry_type(self, entry: ConfigEntry) -> str:
        if entry.key.lower() in MODULE_BOOLEAN_KEYS and entry.value.strip() in {"0", "1"}:
            return "Toggle"
        return self._entry_type(entry)

    def _refresh_module_tree(self, *_args: object) -> None:
        if not hasattr(self, "module_tree"):
            return
        selected = self.module_selected_line
        resources_were_open = self.module_tree.exists("module-resources") and bool(self.module_tree.item("module-resources", "open"))
        self.module_tree.delete(*self.module_tree.get_children())
        query = self.module_search_var.get().strip().lower()
        category_order = {name: index for index, name in enumerate(("Campaign", "Combat", "World Map", "Gameplay Toggles", "Compatibility", "Advanced"))}
        entries = sorted(self.module_entries, key=lambda entry: (category_order.get(module_setting_category(entry.key), 99), entry.line_index))
        visible: list[tuple[ConfigEntry, str, str, bool]] = []
        for entry in entries:
            category = module_setting_category(entry.key)
            shown_value = self.module_pending.get(entry.line_index, entry.value)
            help_text = MODULE_SETTING_HELP.get(entry.key.lower(), "")
            if query and query not in entry.key.lower() and query not in shown_value.lower() and query not in category.lower() and query not in help_text.lower():
                continue
            changed = entry.line_index in self.module_pending
            visible.append((entry, category, shown_value, changed))

        tweakables = [item for item in visible if item[1] != "Resources"]
        resources = [item for item in visible if item[1] == "Resources"]
        if tweakables:
            self.module_tree.insert("", "end", iid="module-tweakables", text=f"Tweakable settings ({len(tweakables)})", open=True)
            for entry, category, shown_value, changed in tweakables:
                iid = f"module-line-{entry.line_index}"
                self.module_tree.insert("module-tweakables", "end", iid=iid, values=(category, entry.key, shown_value, self._module_entry_type(entry), "Modified" if changed else ""))
        if resources:
            self.module_tree.insert("", "end", iid="module-resources", text=f"Resource loading order ({len(resources)})", open=bool(query) or resources_were_open)
            for entry, category, shown_value, changed in resources:
                iid = f"module-line-{entry.line_index}"
                self.module_tree.insert("module-resources", "end", iid=iid, values=(category, entry.key, shown_value, self._module_entry_type(entry), "Modified" if changed else ""))
        if selected is not None and self.module_tree.exists(f"module-line-{selected}"):
            iid = f"module-line-{selected}"
            self.module_tree.selection_set(iid)
            self.module_tree.see(iid)

    def _module_entry_by_line(self, line_index: int) -> ConfigEntry | None:
        return next((entry for entry in self.module_entries if entry.line_index == line_index), None)

    def _select_module_entry(self, _event: object = None) -> None:
        selection = self.module_tree.selection()
        if not selection or not selection[0].startswith("module-line-"):
            return
        self.module_selected_line = int(selection[0].rsplit("-", 1)[1])
        entry = self._module_entry_by_line(self.module_selected_line)
        if not entry:
            return
        count = sum(1 for item in self.module_entries if item.key.lower() == entry.key.lower())
        duplicate_note = f" This key appears {count} times; this is line {entry.line_index + 1}." if count > 1 else ""
        category = module_setting_category(entry.key)
        default_help = "Ordered module resource entry." if category == "Resources" else f"{category} module.ini setting."
        self.module_edit_key_var.set(entry.key)
        self.module_edit_help_var.set(MODULE_SETTING_HELP.get(entry.key.lower(), default_help) + duplicate_note)
        self.module_edit_value_var.set(self.module_pending.get(entry.line_index, entry.value))
        self._show_module_value_editor(self._module_entry_type(entry) == "Toggle")
        self.module_stage_button.state(["!disabled"])
        self.module_revert_button.state(["!disabled"] if entry.line_index in self.module_pending else ["disabled"])

    def _show_module_value_editor(self, toggle: bool) -> None:
        if self.module_value_editor:
            self.module_value_editor.destroy()
        if toggle:
            self.module_value_editor = ttk.Combobox(self.module_value_editor_host, textvariable=self.module_edit_value_var, values=("0", "1"), state="readonly", font=("Consolas", 12))
        else:
            self.module_value_editor = tk.Entry(self.module_value_editor_host, textvariable=self.module_edit_value_var, bg="#f4eddb", fg="#201f1a", insertbackground="#201f1a", relief="flat", font=("Consolas", 13))
        self.module_value_editor.pack(fill="x", ipady=8)

    def _clear_module_editor(self) -> None:
        self.module_edit_key_var.set("Select a game tweak")
        self.module_edit_help_var.set("Choose a module.ini setting to inspect and edit.")
        self.module_edit_value_var.set("")
        self._show_module_value_editor(False)
        self.module_stage_button.state(["disabled"])
        self.module_revert_button.state(["disabled"])

    def _stage_module_selected(self) -> None:
        if self.module_selected_line is None:
            return
        entry = self._module_entry_by_line(self.module_selected_line)
        if not entry:
            return
        try:
            value = validate_config_value(entry.value, self.module_edit_value_var.get())
            if entry.key.lower() in MODULE_BOOLEAN_KEYS and value not in {"0", "1"}:
                raise ValueError("This module toggle must be 0 (off) or 1 (on).")
            if value == entry.value:
                self.module_pending.pop(entry.line_index, None)
            else:
                self.module_pending[entry.line_index] = value
            self._refresh_module_tree()
            self._update_module_change_count()
            self._sync_quick_module()
            self.module_revert_button.state(["!disabled"] if entry.line_index in self.module_pending else ["disabled"])
            self.status_var.set(f"Staged module tweak {entry.key} = {value}.")
        except ValueError as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _revert_module_selected(self) -> None:
        if self.module_selected_line is None:
            return
        entry = self._module_entry_by_line(self.module_selected_line)
        if not entry:
            return
        self.module_pending.pop(entry.line_index, None)
        self.module_edit_value_var.set(entry.value)
        self._refresh_module_tree()
        self._update_module_change_count()
        self._sync_quick_module()
        self.module_revert_button.state(["disabled"])

    def _update_module_change_count(self) -> None:
        count = len(self.module_pending)
        self.module_change_count_var.set("No staged module changes" if not count else f"{count} staged module change{'s' if count != 1 else ''}")
        self.module_save_button.state(["!disabled"] if count else ["disabled"])

    def _save_module_pending(self) -> Path:
        if not self.module_ini_path:
            raise FileNotFoundError("Load a Warband module first.")
        latest, encoding = read_config(self.module_ini_path)
        require_unchanged_text(self.module_text, latest, "module.ini")
        latest_entries = parse_config_entries(latest)
        signature = [(entry.line_index, entry.key, entry.value) for entry in self.module_entries]
        current_signature = [(entry.line_index, entry.key, entry.value) for entry in latest_entries]
        if signature != current_signature:
            raise RuntimeError("module.ini changed outside this app. Reload it before saving so outside changes are not overwritten.")
        updated = apply_config_updates(latest, self.module_pending)
        backup = write_config_text(self.module_ini_path, updated, encoding, False)
        assert self.module_dir is not None
        self._load_module(self.module_dir, discard=True, reload_party=False)
        return backup

    def _save_module_changes(self) -> None:
        if not self.module_pending:
            return
        try:
            count = len(self.module_pending)
            backup = self._save_module_pending()
            self.status_var.set(f"Saved {count} module tweak{'s' if count != 1 else ''}. Backup: {backup.name}")
            messagebox.showinfo(APP_TITLE, f"Saved {count} module tweak{'s' if count != 1 else ''}.\n\nBackup created:\n{backup.name}\n\nStart a new campaign for changes that are baked into saved games.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _reload_module(self) -> None:
        if self.module_dir:
            try:
                self._load_module(self.module_dir)
            except Exception as exc:
                messagebox.showerror(APP_TITLE, str(exc))

    def _load_party_file(self, module_dir: Path) -> None:
        party_path = module_dir / "party_templates.txt"
        troops_path = module_dir / "troops.txt"
        self.party_module_var.set(f"MODULE: {module_dir.name}")
        if not party_path.is_file() or not troops_path.is_file():
            self.party_file_path = None
            self.party_text = ""
            self.troop_text = ""
            self.party_records = []
            self.party_pending = {}
            self.troop_names = []
            self._refresh_party_tree()
            self._clear_party_editor()
            self._update_party_change_count()
            return
        party_text, party_encoding = read_config(party_path)
        troop_text, _troop_encoding = read_config(troops_path)
        records = parse_party_templates(party_text)
        troops = parse_troop_names(troop_text)
        for record in records:
            validate_party_template(record, len(troops))
        self.party_file_path = party_path
        self.party_text = party_text
        self.troop_text = troop_text
        self.party_encoding = party_encoding
        self.party_records = records
        self.party_pending = {}
        self.party_selected_line = None
        self.party_draft_stacks = []
        self.troop_names = troops
        self.party_troop_combo.configure(values=[self._troop_choice(index) for index in range(len(troops))])
        self._refresh_party_tree()
        self._clear_party_editor()
        self._update_party_change_count()

    def _troop_choice(self, index: int) -> str:
        if 0 <= index < len(self.troop_names):
            troop_id, display_name = self.troop_names[index]
            return f"{index}: {troop_id} — {display_name}"
        if 0 <= index < len(self.troop_records):
            record = self.troop_records[index]
            return f"{index}: {record.troop_id} — {record.singular_name.replace('_', ' ')}"
        addition_index = index - len(self.troop_records)
        additions = list(self.troop_additions.values())
        if 0 <= addition_index < len(additions):
            record = additions[addition_index]
            return f"{index}: {record.troop_id} — {record.singular_name.replace('_', ' ')}"
        return f"{index}: unknown troop"

    def _refresh_party_tree(self, *_args: object) -> None:
        if not hasattr(self, "party_tree"):
            return
        selected = self.party_selected_line
        self.party_tree.delete(*self.party_tree.get_children())
        query = self.party_search_var.get().strip().lower()
        for original in self.party_records:
            record = self.party_pending.get(original.line_index, original)
            troop_text = ", ".join(self._troop_choice(stack.troop_index).split(": ", 1)[1].split(" — ", 1)[0] for stack in record.stacks)
            if query and query not in record.template_id.lower() and query not in record.name.lower() and query not in troop_text.lower() and query not in str(record.faction):
                continue
            self.party_tree.insert("", "end", iid=f"party-line-{record.line_index}", values=(record.template_id, record.name.replace("_", " "), record.faction, len(record.stacks), "Modified" if record.line_index in self.party_pending else ""))
        if selected is not None and self.party_tree.exists(f"party-line-{selected}"):
            iid = f"party-line-{selected}"
            self.party_tree.selection_set(iid)
            self.party_tree.see(iid)

    def _party_original_by_line(self, line_index: int) -> PartyTemplateRecord | None:
        return next((record for record in self.party_records if record.line_index == line_index), None)

    def _select_party_record(self, _event: object = None) -> None:
        selection = self.party_tree.selection()
        if not selection:
            return
        self.party_selected_line = int(selection[0].rsplit("-", 1)[1])
        original = self._party_original_by_line(self.party_selected_line)
        if not original:
            return
        self._populate_party_editor(self.party_pending.get(original.line_index, original))

    def _populate_party_editor(self, record: PartyTemplateRecord) -> None:
        self.party_id_var.set(record.template_id)
        self.party_name_var.set(record.name)
        self.party_flags_var.set(str(record.flags))
        self.party_menu_var.set(str(record.menu))
        self.party_faction_var.set(str(record.faction))
        self.party_personality_var.set(str(record.personality))
        self.party_draft_stacks = list(record.stacks)
        self._refresh_party_stack_tree()
        self.party_stage_button.state(["!disabled"])
        self.party_revert_button.state(["!disabled"] if record.line_index in self.party_pending else ["disabled"])

    def _clear_party_editor(self) -> None:
        self.party_id_var.set("Select a party template")
        for variable in (self.party_name_var, self.party_flags_var, self.party_menu_var, self.party_faction_var, self.party_personality_var, self.party_troop_var, self.party_min_var, self.party_max_var, self.party_member_flags_var):
            variable.set("")
        self.party_draft_stacks = []
        if hasattr(self, "party_stack_tree"):
            self.party_stack_tree.delete(*self.party_stack_tree.get_children())
        self.party_stage_button.state(["disabled"])
        self.party_revert_button.state(["disabled"])

    def _refresh_party_stack_tree(self, selected_index: int | None = None) -> None:
        self.party_stack_tree.delete(*self.party_stack_tree.get_children())
        for index, stack in enumerate(self.party_draft_stacks):
            troop_label = self._troop_choice(stack.troop_index).split(": ", 1)[1]
            self.party_stack_tree.insert("", "end", iid=f"stack-{index}", values=(index + 1, troop_label, stack.minimum, stack.maximum, stack.member_flags))
        if selected_index is None and self.party_draft_stacks:
            selected_index = 0
        if selected_index is not None and self.party_stack_tree.exists(f"stack-{selected_index}"):
            iid = f"stack-{selected_index}"
            self.party_stack_tree.selection_set(iid)
            self.party_stack_tree.see(iid)
            self._select_party_stack()
        elif not self.party_draft_stacks:
            for variable in (self.party_troop_var, self.party_min_var, self.party_max_var, self.party_member_flags_var):
                variable.set("")

    def _selected_stack_index(self) -> int | None:
        selection = self.party_stack_tree.selection()
        return int(selection[0].split("-", 1)[1]) if selection else None

    def _select_party_stack(self, _event: object = None) -> None:
        index = self._selected_stack_index()
        if index is None or index >= len(self.party_draft_stacks):
            return
        stack = self.party_draft_stacks[index]
        self.party_troop_var.set(self._troop_choice(stack.troop_index))
        self.party_min_var.set(str(stack.minimum))
        self.party_max_var.set(str(stack.maximum))
        self.party_member_flags_var.set(str(stack.member_flags))

    def _stack_from_editor(self) -> PartyStack:
        match = re.match(r"\s*(\d+)", self.party_troop_var.get())
        if not match:
            raise ValueError("Choose a troop from this module's troops.txt list.")
        try:
            stack = PartyStack(int(match.group(1)), int(self.party_min_var.get().strip()), int(self.party_max_var.get().strip()), int(self.party_member_flags_var.get().strip()))
        except ValueError as exc:
            raise ValueError("Troop minimum, maximum, and flags must be whole numbers.") from exc
        temporary = PartyTemplateRecord(0, "pt_validation", "Validation", 0, 0, 0, 0, (stack,))
        validate_party_template(temporary, len(self.troop_names))
        return stack

    def _apply_party_stack(self) -> None:
        index = self._selected_stack_index()
        if index is None:
            messagebox.showerror(APP_TITLE, "Select a troop stack first.")
            return
        try:
            self.party_draft_stacks[index] = self._stack_from_editor()
            self._refresh_party_stack_tree(index)
            self.status_var.set("Updated the party's draft troop stack. Stage the party to keep it.")
        except ValueError as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _add_party_stack(self) -> None:
        if self.party_selected_line is None:
            messagebox.showerror(APP_TITLE, "Select a party template first.")
            return
        if len(self.party_draft_stacks) >= 6:
            messagebox.showerror(APP_TITLE, "Warband party templates can contain at most six troop stacks.")
            return
        self.party_draft_stacks.append(PartyStack(0, 1, 1, 0))
        self._refresh_party_stack_tree(len(self.party_draft_stacks) - 1)

    def _remove_party_stack(self) -> None:
        index = self._selected_stack_index()
        if index is None:
            messagebox.showerror(APP_TITLE, "Select a troop stack first.")
            return
        self.party_draft_stacks.pop(index)
        self._refresh_party_stack_tree(min(index, len(self.party_draft_stacks) - 1) if self.party_draft_stacks else None)

    def _stage_party_record(self) -> None:
        if self.party_selected_line is None:
            return
        original = self._party_original_by_line(self.party_selected_line)
        if not original:
            return
        try:
            stack_index = self._selected_stack_index()
            if stack_index is not None:
                self.party_draft_stacks[stack_index] = self._stack_from_editor()
            name = self.party_name_var.get().strip().replace(" ", "_")
            record = PartyTemplateRecord(
                original.line_index, original.template_id, name,
                int(self.party_flags_var.get().strip()), int(self.party_menu_var.get().strip()),
                int(self.party_faction_var.get().strip()), int(self.party_personality_var.get().strip()),
                tuple(self.party_draft_stacks),
            )
            validate_party_template(record, len(self.troop_names))
            if record == original:
                self.party_pending.pop(record.line_index, None)
            else:
                self.party_pending[record.line_index] = record
            self.party_name_var.set(name)
            self._refresh_party_tree()
            self._update_party_change_count()
            self.party_revert_button.state(["!disabled"] if record.line_index in self.party_pending else ["disabled"])
            self.status_var.set(f"Staged {record.template_id}. Save Party Templates to write it to disk.")
        except ValueError as exc:
            messagebox.showerror(APP_TITLE, f"Party header values must be whole numbers.\n\n{exc}")

    def _revert_party_record(self) -> None:
        if self.party_selected_line is None:
            return
        original = self._party_original_by_line(self.party_selected_line)
        if not original:
            return
        self.party_pending.pop(original.line_index, None)
        self._populate_party_editor(original)
        self._refresh_party_tree()
        self._update_party_change_count()

    def _update_party_change_count(self) -> None:
        count = len(self.party_pending)
        self.party_change_count_var.set("No staged party changes" if not count else f"{count} staged party change{'s' if count != 1 else ''}")
        self.party_save_button.state(["!disabled"] if count else ["disabled"])

    def _save_party_pending(self) -> Path:
        if not self.party_file_path or not self.module_dir:
            raise FileNotFoundError("The selected module does not contain party_templates.txt and troops.txt.")
        latest, encoding = read_config(self.party_file_path)
        require_unchanged_text(self.party_text, latest, "party_templates.txt")
        latest_troops, _troop_encoding = read_config(self.module_dir / "troops.txt")
        require_unchanged_text(self.troop_text, latest_troops, "troops.txt")
        current_troops = parse_troop_names(latest_troops)
        current_records = parse_party_templates(latest)
        if [(record.line_index, record.template_id) for record in current_records] != [(record.line_index, record.template_id) for record in self.party_records]:
            raise RuntimeError("The party-template structure changed outside this app. Reload before saving.")
        for record in self.party_pending.values():
            validate_party_template(record, len(current_troops))
        updated = apply_party_template_updates(latest, self.party_pending)
        parse_party_templates(updated)
        backup = write_config_text(self.party_file_path, updated, encoding, False)
        self._load_party_file(self.module_dir)
        return backup

    def _save_party_changes(self) -> None:
        if not self.party_pending:
            return
        try:
            count = len(self.party_pending)
            backup = self._save_party_pending()
            self.status_var.set(f"Saved {count} party template{'s' if count != 1 else ''}. Backup: {backup.name}")
            messagebox.showinfo(APP_TITLE, f"Saved {count} party template{'s' if count != 1 else ''}.\n\nBackup created:\n{backup.name}\n\nA new campaign may be required before all changes appear.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _reload_party_file(self) -> None:
        if not self.module_dir:
            return
        if self.party_pending and not messagebox.askyesno(APP_TITLE, "Discard staged party-template changes and reload?"):
            return
        try:
            self._load_party_file(self.module_dir)
            self.status_var.set(f"Reloaded party_templates.txt for {self.module_dir.name}.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _load_item_file(self, module_dir: Path) -> None:
        item_path = module_dir / "item_kinds1.txt"
        self.item_module_var.set(f"MODULE: {module_dir.name}")
        if not item_path.is_file():
            self.item_file_path = None
            self.item_text = ""
            self.item_records = []
            self.item_pending = {}
            self.item_additions = {}
            self.next_item_key = -1
            self.item_selected_line = None
            self.item_end_var.set("End marker: missing")
            self.item_create_button.state(["disabled"])
            self.item_clone_button.state(["disabled"])
            self._refresh_item_tree()
            self._clear_item_editor()
            self._update_item_change_count()
            return
        text, encoding = read_config(item_path)
        self.item_file_path = item_path
        self.item_text = text
        self.item_encoding = encoding
        self.item_records = parse_item_kinds(text)
        self.item_pending = {}
        self.item_additions = {}
        self.next_item_key = -1
        self.item_selected_line = None
        sentinel = find_terminal_item_sentinel(self.item_records)
        self.item_end_var.set(f"End marker: {sentinel.item_id}" if sentinel else "End marker: missing")
        self.item_create_button.state(["!disabled"] if sentinel else ["disabled"])
        self.item_clone_button.state(["disabled"])
        self._refresh_item_tree()
        self._clear_item_editor()
        self._update_item_change_count()

    def _refresh_item_tree(self, *_args: object) -> None:
        if not hasattr(self, "item_tree"):
            return
        selected = self.item_selected_line
        self.item_tree.delete(*self.item_tree.get_children())
        query = self.item_search_var.get().strip().lower()
        selected_type = self.item_filter_var.get()
        index_by_line = {record.line_index: index for index, record in enumerate(self.item_records)}

        def insert_record(record: ItemRecord, state: str) -> None:
            type_name = item_type_name(record.item_flags)
            if selected_type != "All item types" and type_name != selected_type:
                return
            mesh_text = " ".join(mesh.name for mesh in record.meshes)
            if query and query not in record.item_id.lower() and query not in record.singular_name.lower() and query not in record.plural_name.lower() and query not in type_name.lower() and query not in mesh_text.lower():
                return
            iid = self._item_tree_iid(record.line_index)
            self.item_tree.insert("", "end", iid=iid, values=(
                index_by_line.get(record.line_index, "NEW"), record.item_id,
                record.singular_name.replace("_", " "), type_name,
                record.value, f"{record.weight:g}", state,
            ))

        sentinel = find_terminal_item_sentinel(self.item_records)
        for original in self.item_records:
            if sentinel and original.line_index == sentinel.line_index:
                for addition in self.item_additions.values():
                    insert_record(addition.record, "New")
            record = self.item_pending.get(original.line_index, original)
            insert_record(record, "Modified" if original.line_index in self.item_pending else "")
        if not sentinel:
            for addition in self.item_additions.values():
                insert_record(addition.record, "New")
        if selected is not None and self.item_tree.exists(self._item_tree_iid(selected)):
            iid = self._item_tree_iid(selected)
            self.item_tree.selection_set(iid)
            self.item_tree.see(iid)

    @staticmethod
    def _item_tree_iid(line_index: int) -> str:
        return f"item-new-{abs(line_index)}" if line_index < 0 else f"item-line-{line_index}"

    @staticmethod
    def _item_line_from_iid(iid: str) -> int:
        if iid.startswith("item-new-"):
            return -int(iid.rsplit("-", 1)[1])
        return int(iid.rsplit("-", 1)[1])

    def _item_original_by_line(self, line_index: int) -> ItemRecord | None:
        if line_index < 0:
            addition = self.item_additions.get(line_index)
            return addition.record if addition else None
        return next((record for record in self.item_records if record.line_index == line_index), None)

    def _select_item_record(self, _event: object = None) -> None:
        selection = self.item_tree.selection()
        if not selection:
            return
        self.item_selected_line = self._item_line_from_iid(selection[0])
        original = self._item_original_by_line(self.item_selected_line)
        if not original:
            return
        record = original if original.line_index < 0 else self.item_pending.get(original.line_index, original)
        self._populate_item_editor(record)

    def _populate_item_editor(self, record: ItemRecord) -> None:
        self.item_id_var.set(record.item_id)
        type_code = record.item_flags & 0xFF
        self.item_type_edit_var.set(f"{type_code}: {item_type_name(record.item_flags)}")
        mesh_names = ", ".join(mesh.name for mesh in record.meshes)
        factions = ", ".join(map(str, record.factions)) if record.factions else "none"
        self.item_meta_var.set(f"Meshes: {mesh_names}   •   Factions: {factions}   •   Triggers: {record.trigger_count}")
        values = {
            "singular": record.singular_name, "plural": record.plural_name,
            "value": record.value, "weight": f"{record.weight:g}", "abundance": record.abundance,
            "difficulty": record.difficulty, "head_armor": record.head_armor,
            "body_armor": record.body_armor, "leg_armor": record.leg_armor,
            "hit_points": record.hit_points, "speed_rating": record.speed_rating,
            "missile_speed": record.missile_speed, "weapon_length": record.weapon_length,
            "max_ammo": record.max_ammo, "item_flags": record.item_flags,
            "capabilities": record.capabilities, "modifiers": record.modifiers,
        }
        thrust_amount, thrust_type = unpack_damage(record.thrust_damage)
        swing_amount, swing_type = unpack_damage(record.swing_damage)
        values["thrust_amount"] = thrust_amount
        values["swing_amount"] = swing_amount
        for key, value in values.items():
            self.item_fields[key].set(str(value))
        self.item_thrust_type_var.set(f"{thrust_type}: {DAMAGE_TYPES[thrust_type]}")
        self.item_swing_type_var.set(f"{swing_type}: {DAMAGE_TYPES[swing_type]}")
        attachment = record.item_flags & 0xF00
        attachment_name = ITEM_ATTACHMENT_OPTIONS.get(attachment, "Unknown attachment value (preserved)")
        self.item_attachment_var.set(f"{attachment}: {attachment_name}")
        kill_info = (record.item_flags & ITEM_KILL_INFO_MASK) >> 56
        self.item_kill_info_var.set(f"{kill_info}: {'Default' if kill_info == 0 else f'Custom icon {kill_info}'}")
        unknown_flags = record.item_flags & ~ITEM_FLAG_KNOWN_MASK
        self.item_unknown_flags_var.set(f"Unknown bits preserved: 0x{unknown_flags:X}" if unknown_flags else "No unknown item-flag bits")
        for key, _label, bit, _help in ITEM_FLAG_OPTIONS:
            self.item_flag_vars[key].set(bool(record.item_flags & bit))
        shoot = record.capabilities & CAPABILITY_SHOOT_MASK
        carry = record.capabilities & CAPABILITY_CARRY_MASK
        reload_action = record.capabilities & CAPABILITY_RELOAD_MASK
        self.item_shoot_action_var.set(f"{shoot}: {CAPABILITY_SHOOT_OPTIONS.get(shoot, 'Unknown action (preserved)')}")
        self.item_carry_position_var.set(f"{carry}: {CAPABILITY_CARRY_OPTIONS.get(carry, 'Unknown position (preserved)')}")
        self.item_reload_action_var.set(f"{reload_action}: {CAPABILITY_RELOAD_OPTIONS.get(reload_action, 'Unknown action (preserved)')}")
        unknown_caps = record.capabilities & ~CAPABILITY_KNOWN_MASK
        self.item_unknown_caps_var.set(f"Unknown bits preserved: 0x{unknown_caps:X}" if unknown_caps else "No unknown capability bits")
        for key, _label, bit, _help in CAPABILITY_OPTIONS:
            self.item_cap_vars[key].set(bool(record.capabilities & bit))
        self.item_stage_button.state(["!disabled"])
        is_new = record.line_index < 0
        self.item_revert_button.configure(text="Remove New Item" if is_new else "Revert Item")
        self.item_revert_button.state(["!disabled"] if is_new or record.line_index in self.item_pending else ["disabled"])
        self.item_clone_button.state(["disabled"] if find_terminal_item_sentinel([record]) else ["!disabled"])

    def _clear_item_editor(self) -> None:
        self.item_id_var.set("Select an item")
        self.item_type_edit_var.set("")
        self.item_meta_var.set("")
        for variable in self.item_fields.values():
            variable.set("")
        self.item_thrust_type_var.set("")
        self.item_swing_type_var.set("")
        self.item_attachment_var.set("")
        self.item_kill_info_var.set("")
        self.item_unknown_flags_var.set("")
        self.item_shoot_action_var.set("")
        self.item_carry_position_var.set("")
        self.item_reload_action_var.set("")
        self.item_unknown_caps_var.set("")
        for variable in (*self.item_flag_vars.values(), *self.item_cap_vars.values()):
            variable.set(False)
        self.item_stage_button.state(["disabled"])
        self.item_revert_button.state(["disabled"])
        self.item_revert_button.configure(text="Revert Item")
        self.item_clone_button.state(["disabled"])

    @staticmethod
    def _choice_code(value: str, label: str) -> int:
        match = re.match(r"\s*(\d+)\s*:", value)
        if not match:
            raise ValueError(f"Choose a valid {label}.")
        return int(match.group(1))

    def _current_item_record(self) -> ItemRecord | None:
        if self.item_selected_line is None:
            return None
        original = self._item_original_by_line(self.item_selected_line)
        if not original:
            return None
        return original if original.line_index < 0 else self.item_pending.get(original.line_index, original)

    def _prompt_item_identity(self, default_id: str, default_singular: str, default_plural: str) -> tuple[str, str, str] | None:
        raw_id = simpledialog.askstring(APP_TITLE, "New item ID (itm_ prefix is optional):", initialvalue=default_id, parent=self)
        if raw_id is None:
            return None
        item_id = normalize_item_id(raw_id)
        all_ids = {record.item_id.casefold() for record in self.item_records}
        all_ids.update(addition.record.item_id.casefold() for addition in self.item_additions.values())
        if item_id.casefold() in all_ids:
            raise ValueError(f"Item ID already exists: {item_id}")
        if item_id.endswith(("items_end", "end_items")):
            raise ValueError("New items cannot use an Items_End sentinel ID.")
        singular = simpledialog.askstring(APP_TITLE, "Singular display name:", initialvalue=default_singular.replace("_", " "), parent=self)
        if singular is None:
            return None
        plural = simpledialog.askstring(APP_TITLE, "Plural display name:", initialvalue=default_plural.replace("_", " "), parent=self)
        if plural is None:
            return None
        singular = singular.strip().replace(" ", "_")
        plural = plural.strip().replace(" ", "_")
        if not singular or not plural:
            raise ValueError("Item display names cannot be blank.")
        return item_id, singular, plural

    def _add_item_draft(self, record: ItemRecord, source_item_id: str | None, source_line_index: int | None = None) -> None:
        validate_item_record(record)
        self.item_additions[record.line_index] = ItemAddition(record, source_item_id, source_line_index)
        self.item_search_var.set("")
        self.item_filter_var.set("All item types")
        self.item_selected_line = record.line_index
        self._refresh_item_tree()
        iid = self._item_tree_iid(record.line_index)
        if self.item_tree.exists(iid):
            self.item_tree.selection_set(iid)
            self.item_tree.see(iid)
        self._populate_item_editor(record)
        self._update_item_change_count()

    def _create_item(self) -> None:
        if find_terminal_item_sentinel(self.item_records) is None:
            messagebox.showerror(APP_TITLE, "No terminal Items_End marker was found, so a new item cannot be inserted safely.")
            return
        try:
            identity = self._prompt_item_identity("itm_new_item", "New_Item", "New_Items")
            if identity is None:
                return
            item_id, singular, plural = identity
            selected = self._current_item_record()
            default_mesh = selected.meshes[0].name if selected and selected.meshes else "invalid_item"
            mesh_name = simpledialog.askstring(APP_TITLE, "Primary mesh name (must exist in the module's BRF resources):", initialvalue=default_mesh, parent=self)
            if mesh_name is None:
                return
            mesh_name = mesh_name.strip()
            if not mesh_name or any(character.isspace() for character in mesh_name):
                raise ValueError("A mesh name cannot be blank or contain spaces.")
            default_type = (selected.item_flags & 0xFF) if selected else 11
            type_code = simpledialog.askinteger(APP_TITLE, "Item type code (0–20):", initialvalue=default_type, minvalue=0, maxvalue=20, parent=self)
            if type_code is None:
                return
            key = self.next_item_key
            self.next_item_key -= 1
            record = ItemRecord(
                key, item_id, singular, plural, (ItemMesh(mesh_name, 0),), type_code, 0,
                100, 0, 1.0, 100, 0, 0, 0, 0, 0, 0, 0, 0, 0,
                pack_damage(0, 0), pack_damage(0, 0), (), 0,
            )
            self._add_item_draft(record, None)
            sentinel = find_terminal_item_sentinel(self.item_records)
            self.status_var.set(f"Created staged item {item_id}; it will be inserted before {sentinel.item_id}.")
        except ValueError as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _clone_item(self) -> None:
        source = self._current_item_record()
        if source is None:
            messagebox.showerror(APP_TITLE, "Select an item to clone.")
            return
        if find_terminal_item_sentinel([source]) is not None:
            messagebox.showerror(APP_TITLE, "The Items_End marker cannot be cloned.")
            return
        try:
            identity = self._prompt_item_identity(f"{source.item_id}_copy", f"{source.singular_name}_Copy", f"{source.plural_name}_Copies")
            if identity is None:
                return
            item_id, singular, plural = identity
            key = self.next_item_key
            self.next_item_key -= 1
            record = ItemRecord(
                key, item_id, singular, plural, source.meshes, source.item_flags, source.capabilities,
                source.value, source.modifiers, source.weight, source.abundance, source.head_armor,
                source.body_armor, source.leg_armor, source.difficulty, source.hit_points,
                source.speed_rating, source.missile_speed, source.weapon_length, source.max_ammo,
                source.thrust_damage, source.swing_damage, source.factions, source.trigger_count,
            )
            if source.line_index < 0:
                source_addition = self.item_additions[source.line_index]
                source_id = source_addition.source_item_id
                source_line_index = source_addition.source_line_index
            else:
                source_id = source.item_id
                source_line_index = source.line_index
            self._add_item_draft(record, source_id, source_line_index)
            sentinel = find_terminal_item_sentinel(self.item_records)
            self.status_var.set(f"Cloned {source.item_id} as {item_id}; it will be inserted before {sentinel.item_id}.")
        except ValueError as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _stage_item_record(self) -> None:
        if self.item_selected_line is None:
            return
        original = self._item_original_by_line(self.item_selected_line)
        if not original:
            return
        try:
            type_code = self._choice_code(self.item_type_edit_var.get(), "item type")
            thrust_type = self._choice_code(self.item_thrust_type_var.get(), "thrust damage type")
            swing_type = self._choice_code(self.item_swing_type_var.get(), "swing damage type")
            raw_flags = int(self.item_fields["item_flags"].get().strip())
            attachment = self._choice_code(self.item_attachment_var.get(), "attachment")
            kill_info = self._choice_code(self.item_kill_info_var.get(), "custom kill icon")
            enabled_flags = {key for key, variable in self.item_flag_vars.items() if variable.get()}
            item_flags = rebuild_item_flags(raw_flags, type_code, attachment, kill_info, enabled_flags)
            integer_keys = (
                "value", "abundance", "difficulty", "head_armor", "body_armor", "leg_armor",
                "hit_points", "speed_rating", "missile_speed", "weapon_length", "max_ammo",
                "capabilities", "modifiers", "thrust_amount", "swing_amount",
            )
            integers = {key: int(self.item_fields[key].get().strip()) for key in integer_keys}
            shoot_action = self._choice_code(self.item_shoot_action_var.get(), "shoot/throw action")
            carry_position = self._choice_code(self.item_carry_position_var.get(), "carry position")
            reload_action = self._choice_code(self.item_reload_action_var.get(), "reload action")
            enabled_caps = {key for key, variable in self.item_cap_vars.items() if variable.get()}
            capabilities = rebuild_capabilities(integers["capabilities"], shoot_action, carry_position, reload_action, enabled_caps)
            record = ItemRecord(
                original.line_index, original.item_id,
                self.item_fields["singular"].get().strip().replace(" ", "_"),
                self.item_fields["plural"].get().strip().replace(" ", "_"),
                original.meshes, item_flags, capabilities, integers["value"],
                integers["modifiers"], float(self.item_fields["weight"].get().strip()),
                integers["abundance"], integers["head_armor"], integers["body_armor"],
                integers["leg_armor"], integers["difficulty"], integers["hit_points"],
                integers["speed_rating"], integers["missile_speed"], integers["weapon_length"],
                integers["max_ammo"], pack_damage(integers["thrust_amount"], thrust_type),
                pack_damage(integers["swing_amount"], swing_type), original.factions, original.trigger_count,
            )
            validate_item_record(record)
            if record.line_index < 0:
                addition = self.item_additions[record.line_index]
                self.item_additions[record.line_index] = ItemAddition(record, addition.source_item_id, addition.source_line_index)
            elif record == original:
                self.item_pending.pop(record.line_index, None)
            else:
                self.item_pending[record.line_index] = record
            self._populate_item_editor(record)
            self._refresh_item_tree()
            self._update_item_change_count()
            self.status_var.set(f"Staged {record.item_id}. Save Items to write it to disk.")
        except ValueError as exc:
            messagebox.showerror(APP_TITLE, f"Item values are invalid. Whole-number fields cannot contain decimals.\n\n{exc}")

    def _revert_item_record(self) -> None:
        if self.item_selected_line is None:
            return
        original = self._item_original_by_line(self.item_selected_line)
        if not original:
            return
        if original.line_index < 0:
            removed = self.item_additions.pop(original.line_index)
            self.item_selected_line = None
            self._refresh_item_tree()
            self._clear_item_editor()
            self._update_item_change_count()
            self.status_var.set(f"Removed staged new item {removed.record.item_id}.")
            return
        self.item_pending.pop(original.line_index, None)
        self._populate_item_editor(original)
        self._refresh_item_tree()
        self._update_item_change_count()

    def _update_item_change_count(self) -> None:
        count = len(self.item_pending) + len(self.item_additions)
        self.item_change_count_var.set("No staged item changes" if not count else f"{count} staged item change{'s' if count != 1 else ''}")
        self.item_save_button.state(["!disabled"] if count else ["disabled"])

    def _save_item_pending(self) -> Path:
        if not self.item_file_path or not self.module_dir:
            raise FileNotFoundError("The selected module does not contain item_kinds1.txt.")
        if self.raw_dirty and self.raw_path and self.raw_path.resolve() == self.item_file_path.resolve():
            raise RuntimeError("Save or reload the raw item_kinds1.txt edits before saving structured Item Editor changes.")
        latest, encoding = read_config(self.item_file_path)
        require_unchanged_text(self.item_text, latest, "item_kinds1.txt")
        current = parse_item_kinds(latest)
        if [(record.line_index, record.item_id) for record in current] != [(record.line_index, record.item_id) for record in self.item_records]:
            raise RuntimeError("The item structure changed outside this app. Reload before saving.")
        for record in self.item_pending.values():
            validate_item_record(record)
        updated = apply_item_updates(latest, self.item_pending)
        updated = append_item_records(updated, list(self.item_additions.values()))
        parse_item_kinds(updated)
        backup = write_config_text(self.item_file_path, updated, encoding, False)
        self._load_item_file(self.module_dir)
        if hasattr(self, "troop_item_combo"):
            self.troop_item_combo.configure(values=["-1: Empty", *[self._item_choice(index) for index in range(len(self.item_records))]])
        if self.raw_path and self.raw_path.resolve() == self.item_file_path.resolve() and not self.raw_dirty:
            self._load_raw_file(self.raw_path)
        return backup

    def _save_item_changes(self) -> None:
        if not self.item_pending and not self.item_additions:
            return
        try:
            count = len(self.item_pending) + len(self.item_additions)
            backup = self._save_item_pending()
            self.status_var.set(f"Saved {count} item{'s' if count != 1 else ''}. Backup: {backup.name}")
            messagebox.showinfo(APP_TITLE, f"Saved {count} item{'s' if count != 1 else ''}.\n\nBackup created:\n{backup.name}\n\nRestart Warband; a new campaign may be needed for some inventory changes.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _reload_item_file(self) -> None:
        if not self.module_dir:
            return
        if (self.item_pending or self.item_additions) and not messagebox.askyesno(APP_TITLE, "Discard staged item changes and reload?"):
            return
        try:
            self._load_item_file(self.module_dir)
            self.status_var.set(f"Reloaded item_kinds1.txt for {self.module_dir.name}.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    @staticmethod
    def _leading_int(value: str, label: str) -> int:
        token = value.strip().split(":", 1)[0]
        try:
            return int(token)
        except ValueError as exc:
            raise ValueError(f"{label} must begin with a numeric index.") from exc

    def _load_troop_file(self, module_dir: Path) -> None:
        path = module_dir / "troops.txt"
        self.troop_module_var.set(f"MODULE: {module_dir.name}")
        if not path.is_file():
            self.troop_file_path = None
            self.troop_records = []
            self.troop_pending = {}
            self.troop_additions = {}
            self.next_troop_key = -1
            self.faction_names = []
            self._refresh_troop_tree()
            self._clear_troop_editor()
            self._update_troop_change_count()
            self.troop_create_button.state(["disabled"])
            self.troop_clone_button.state(["disabled"])
            return
        text, encoding = read_config(path)
        records = parse_troops(text)
        faction_path = module_dir / "factions.txt"
        factions: list[tuple[str, str]] = []
        if faction_path.is_file():
            faction_text, _ = read_config(faction_path)
            factions = parse_faction_names(faction_text)
        item_count = len(self.item_records) or None
        for record in records:
            validate_troop_record(record, len(records), item_count)
        self.troop_file_path = path
        self.troop_text = text
        self.troop_encoding = encoding
        self.troop_records = records
        self.troop_names = [(record.troop_id, record.singular_name.replace("_", " ")) for record in records]
        self.troop_pending = {}
        self.troop_additions = {}
        self.next_troop_key = -1
        self.troop_selected_line = None
        self.troop_draft_inventory = []
        self.faction_names = factions
        self._refresh_troop_choice_controls()
        self.troop_faction_combo.configure(values=[f"{index}: {fac_id} — {name}" for index, (fac_id, name) in enumerate(factions)])
        self.troop_item_combo.configure(values=["-1: Empty", *[self._item_choice(index) for index in range(len(self.item_records))]])
        self._refresh_troop_tree()
        self._clear_troop_editor()
        self._update_troop_change_count()
        self.troop_create_button.state(["!disabled"])

    def _item_choice(self, index: int) -> str:
        if 0 <= index < len(self.item_records):
            item = self.item_records[index]
            return f"{index}: {item.item_id} — {item.singular_name.replace('_', ' ')}"
        return f"{index}: unknown item"

    def _refresh_troop_tree(self, *_args: object) -> None:
        if not hasattr(self, "troop_tree"):
            return
        selected = self.troop_selected_line
        self.troop_tree.delete(*self.troop_tree.get_children())
        query = self.troop_search_var.get().strip().lower()
        shown_records = [self.troop_pending.get(original.line_index, original) for original in self.troop_records]
        shown_records.extend(self.troop_additions.values())
        for index, record in enumerate(shown_records):
            searchable = f"{record.troop_id} {record.singular_name} {record.plural_name}".lower()
            if query and query not in searchable:
                continue
            state = "New" if record.line_index < 0 else "Modified" if record.line_index in self.troop_pending else ""
            self.troop_tree.insert("", "end", iid=f"troop-line-{record.line_index}", values=(index, record.troop_id, record.singular_name.replace("_", " "), record.attributes[4], state))
        if selected is not None and self.troop_tree.exists(f"troop-line-{selected}"):
            iid = f"troop-line-{selected}"
            self.troop_tree.selection_set(iid)
            self.troop_tree.see(iid)

    def _troop_original_by_line(self, line_index: int) -> TroopRecord | None:
        if line_index < 0:
            return self.troop_additions.get(line_index)
        return next((record for record in self.troop_records if record.line_index == line_index), None)

    def _select_troop_record(self, _event: object = None) -> None:
        selection = self.troop_tree.selection()
        if not selection:
            return
        line_index = int(selection[0].removeprefix("troop-line-"))
        original = self._troop_original_by_line(line_index)
        if original:
            self.troop_selected_line = line_index
            self._populate_troop_editor(original if line_index < 0 else self.troop_pending.get(line_index, original))

    def _populate_troop_editor(self, record: TroopRecord) -> None:
        all_records = [*self.troop_records, *self.troop_additions.values()]
        index = next((i for i, value in enumerate(all_records) if value.line_index == record.line_index), -1)
        self.troop_id_var.set(record.troop_id)
        self.troop_meta_var.set(f"Troop index {index} • faction {record.faction} • 64 fixed inventory slots")
        for key, value in (("singular", record.singular_name), ("plural", record.plural_name), ("image", record.image), ("flags", record.flags), ("scene", record.scene), ("reserved", record.reserved)):
            self.troop_fields[key].set(str(value))
        faction_label = f"{record.faction}"
        if 0 <= record.faction < len(self.faction_names):
            fac_id, name = self.faction_names[record.faction]
            faction_label = f"{record.faction}: {fac_id} — {name}"
        self.troop_fields["faction"].set(faction_label)
        for key, value in (("upgrade_one", record.upgrade_one), ("upgrade_two", record.upgrade_two)):
            self.troop_fields[key].set("0: none" if value == 0 else self._troop_choice(value))
        troop_type = record.flags & TROOP_TYPE_MASK
        self.troop_type_var.set(f"{troop_type}: {TROOP_TYPES.get(troop_type, 'Unknown')}" if troop_type in TROOP_TYPES else str(troop_type))
        for key, _label, bit in TROOP_FLAG_OPTIONS:
            self.troop_flag_vars[key].set(bool(record.flags & bit))
        self.troop_unknown_flags_var.set(f"Unknown flags preserved: 0x{record.flags & ~TROOP_KNOWN_FLAG_MASK:X}")
        for variable, value in zip(self.troop_attribute_vars, record.attributes):
            variable.set(str(value))
        for variable, value in zip(self.troop_proficiency_vars, record.proficiencies):
            variable.set(str(value))
        for variable, value in zip(self.troop_skill_vars, troop_skill_levels(record.skill_words)):
            variable.set(str(value))
        for variable, value in zip(self.troop_face_vars, record.face_words):
            variable.set(str(value))
        pool_size = len(troop_face_preset_pool(self._effective_troop_records(), troop_type))
        self.troop_face_status_var.set(f"{pool_size} valid same-type face preset{'s' if pool_size != 1 else ''} available in {self.module_dir.name if self.module_dir else 'this module'}. Changes are staged with the troop.")
        self.troop_draft_inventory = list(record.inventory)
        self._refresh_troop_inventory_tree()
        self.troop_stage_button.state(["!disabled"])
        is_new = record.line_index < 0
        self.troop_revert_button.configure(text="Remove New Troop" if is_new else "Revert Troop")
        self.troop_revert_button.state(["!disabled"] if is_new or record.line_index in self.troop_pending else ["disabled"])
        self.troop_clone_button.state(["!disabled"])

    def _clear_troop_editor(self) -> None:
        self.troop_id_var.set("Select a troop")
        self.troop_meta_var.set("")
        self.troop_selected_line = None
        self.troop_draft_inventory = []
        for variable in (*self.troop_fields.values(), *self.troop_attribute_vars, *self.troop_proficiency_vars, *self.troop_skill_vars, *self.troop_face_vars):
            variable.set("")
        self.troop_type_var.set("")
        self.troop_unknown_flags_var.set("")
        self.troop_face_status_var.set("Select a troop to inspect its face presets.")
        for variable in self.troop_flag_vars.values():
            variable.set(False)
        if hasattr(self, "troop_inventory_tree"):
            self.troop_inventory_tree.delete(*self.troop_inventory_tree.get_children())
        self.troop_stage_button.state(["disabled"])
        self.troop_revert_button.state(["disabled"])
        self.troop_revert_button.configure(text="Revert Troop")
        self.troop_clone_button.state(["disabled"])

    def _effective_troop_records(self) -> list[TroopRecord]:
        records = [self.troop_pending.get(record.line_index, record) for record in self.troop_records]
        records.extend(self.troop_additions.values())
        return records

    def _troop_face_words_from_editor(self) -> tuple[int, ...]:
        try:
            words = tuple(int(variable.get().strip()) for variable in self.troop_face_vars)
        except ValueError as exc:
            raise ValueError("All eight face words must be whole numbers.") from exc
        if len(words) != 8 or any(not 0 <= word <= 0xFFFFFFFFFFFFFFFF for word in words):
            raise ValueError("Every face word must fit an unsigned 64-bit integer.")
        return words

    def _set_troop_face_words(self, words: tuple[int, ...], status: str) -> None:
        if len(words) != 8:
            raise ValueError("A troop face requires eight words.")
        for variable, value in zip(self.troop_face_vars, words):
            variable.set(str(value))
        self.troop_face_status_var.set(status + " Click Stage Troop Changes to keep it.")

    def _randomize_troop_face(self, fixed: bool) -> None:
        if self.troop_selected_line is None:
            messagebox.showerror(APP_TITLE, "Select a troop first.")
            return
        try:
            troop_type = self._leading_int(self.troop_type_var.get(), "Troop type")
            current = self._troop_face_words_from_editor()
            words, donors, pool_size = randomize_troop_face_words(self._effective_troop_records(), troop_type, current, fixed=fixed)
            self.troop_flag_vars["randomize_face"].set(not fixed)
            if fixed:
                detail = f"Fixed face sampled from {donors[0]} ({pool_size} presets available)."
            else:
                detail = f"Random range sampled from {donors[0]} to {donors[1]} ({pool_size} presets available)."
            self._set_troop_face_words(words, detail)
        except ValueError as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _swap_troop_faces(self) -> None:
        if self.troop_selected_line is None:
            return
        try:
            words = self._troop_face_words_from_editor()
            self._set_troop_face_words(words[4:] + words[:4], "Face 1 and Face 2 were swapped.")
        except ValueError as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _fix_troop_face_one(self) -> None:
        if self.troop_selected_line is None:
            return
        try:
            words = self._troop_face_words_from_editor()
            self.troop_flag_vars["randomize_face"].set(False)
            self._set_troop_face_words(words[:4] + words[:4], "Face 1 was copied to Face 2 and spawn randomization was disabled.")
        except ValueError as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _reset_troop_face(self) -> None:
        if self.troop_selected_line is None:
            return
        original = self._troop_original_by_line(self.troop_selected_line)
        if not original:
            return
        record = self.troop_pending.get(original.line_index, original)
        self.troop_flag_vars["randomize_face"].set(bool(record.flags & 0x00008000))
        self._set_troop_face_words(record.face_words, "Face fields were reset to the current staged troop values.")

    def _refresh_troop_inventory_tree(self, selected: int | None = None) -> None:
        self.troop_inventory_tree.delete(*self.troop_inventory_tree.get_children())
        for index, slot in enumerate(self.troop_draft_inventory):
            item = "Empty" if slot.item_index == -1 else self._item_choice(slot.item_index).split(": ", 1)[-1]
            self.troop_inventory_tree.insert("", "end", iid=f"slot-{index}", values=(index + 1, item, slot.modifier))
        if selected is not None and self.troop_inventory_tree.exists(f"slot-{selected}"):
            self.troop_inventory_tree.selection_set(f"slot-{selected}")
            self.troop_inventory_tree.see(f"slot-{selected}")

    def _selected_troop_inventory_slot(self) -> int | None:
        selection = self.troop_inventory_tree.selection()
        return int(selection[0].split("-", 1)[1]) if selection else None

    def _select_troop_inventory_slot(self, _event: object = None) -> None:
        index = self._selected_troop_inventory_slot()
        if index is None or index >= len(self.troop_draft_inventory):
            return
        slot = self.troop_draft_inventory[index]
        self.troop_item_var.set("-1: Empty" if slot.item_index == -1 else self._item_choice(slot.item_index))
        self.troop_modifier_var.set(str(slot.modifier))

    def _apply_troop_inventory_slot(self) -> None:
        index = self._selected_troop_inventory_slot()
        if index is None:
            messagebox.showerror(APP_TITLE, "Select an inventory slot first.")
            return
        try:
            item_index = self._leading_int(self.troop_item_var.get(), "Item")
            modifier = int(self.troop_modifier_var.get().strip())
            if item_index < -1 or item_index >= len(self.item_records):
                raise ValueError("The selected item index is outside item_kinds1.txt.")
            if not 0 <= modifier <= 0xFFFFFFFF:
                raise ValueError("The modifier must fit an unsigned 32-bit integer.")
            self.troop_draft_inventory[index] = TroopInventorySlot(item_index, modifier if item_index >= 0 else 0)
            self._refresh_troop_inventory_tree(index)
        except ValueError as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _clear_troop_inventory_slot(self) -> None:
        index = self._selected_troop_inventory_slot()
        if index is not None:
            self.troop_draft_inventory[index] = TroopInventorySlot(-1, 0)
            self._refresh_troop_inventory_tree(index)
            self.troop_item_var.set("-1: Empty")
            self.troop_modifier_var.set("0")

    def _refresh_troop_choice_controls(self) -> None:
        choices = [self._troop_choice(index) for index in range(len(self.troop_records) + len(self.troop_additions))]
        if choices:
            choices[0] = f"0: none / {self.troop_records[0].troop_id}" if self.troop_records else "0: none"
        self.troop_upgrade_one_combo.configure(values=choices)
        self.troop_upgrade_two_combo.configure(values=choices)

    def _prompt_troop_identity(self, default_id: str, default_singular: str, default_plural: str) -> tuple[str, str, str] | None:
        raw_id = simpledialog.askstring(APP_TITLE, "New troop ID (trp_ prefix is optional):", initialvalue=default_id, parent=self)
        if raw_id is None:
            return None
        troop_id = normalize_troop_id(raw_id)
        all_ids = {record.troop_id.casefold() for record in self.troop_records}
        all_ids.update(record.troop_id.casefold() for record in self.troop_additions.values())
        if troop_id.casefold() in all_ids:
            raise ValueError(f"Troop ID already exists: {troop_id}")
        singular = simpledialog.askstring(APP_TITLE, "Singular display name:", initialvalue=default_singular.replace("_", " "), parent=self)
        if singular is None:
            return None
        plural = simpledialog.askstring(APP_TITLE, "Plural display name:", initialvalue=default_plural.replace("_", " "), parent=self)
        if plural is None:
            return None
        singular = singular.strip().replace(" ", "_")
        plural = plural.strip().replace(" ", "_")
        if not singular or not plural:
            raise ValueError("Troop display names cannot be blank.")
        return troop_id, singular, plural

    def _add_troop_draft(self, record: TroopRecord) -> None:
        validate_troop_record(record, len(self.troop_records) + len(self.troop_additions) + 1, len(self.item_records) or None)
        self.troop_additions[record.line_index] = record
        self.troop_search_var.set("")
        self.troop_selected_line = record.line_index
        self._refresh_troop_choice_controls()
        self._refresh_troop_tree()
        iid = f"troop-line-{record.line_index}"
        if self.troop_tree.exists(iid):
            self.troop_tree.selection_set(iid)
            self.troop_tree.see(iid)
        self._populate_troop_editor(record)
        self._update_troop_change_count()

    def _create_troop(self) -> None:
        if not self.troop_file_path:
            messagebox.showerror(APP_TITLE, "Load a module with troops.txt first.")
            return
        try:
            identity = self._prompt_troop_identity("trp_new_troop", "New_Troop", "New_Troops")
            if identity is None:
                return
            troop_id, singular, plural = identity
            selected = self._troop_original_by_line(self.troop_selected_line) if self.troop_selected_line is not None else None
            default_type = (selected.flags & TROOP_TYPE_MASK) if selected else 0
            troop_type = simpledialog.askinteger(APP_TITLE, "Troop type: 0 = male, 1 = female, 2 = undead", initialvalue=default_type, minvalue=0, maxvalue=2, parent=self)
            if troop_type is None:
                return
            default_faction = selected.faction if selected and 0 <= selected.faction < len(self.faction_names) else 0
            max_faction = max(0, len(self.faction_names) - 1)
            faction = simpledialog.askinteger(APP_TITLE, f"Faction index (0–{max_faction}):", initialvalue=default_faction, minvalue=0, maxvalue=max_faction, parent=self)
            if faction is None:
                return
            face_words = (0,) * 8
            try:
                face_words, _donors, _pool_size = randomize_troop_face_words(self._effective_troop_records(), troop_type, face_words, fixed=True)
            except ValueError:
                pass
            key = self.next_troop_key
            self.next_troop_key -= 1
            record = TroopRecord(
                key, troop_id, singular, plural, "0", troop_type, 0, 0, faction, 0, 0,
                tuple(TroopInventorySlot(-1, 0) for _ in range(64)),
                (4, 4, 4, 4, 1), (0, 0, 0, 0, 0, 0, 0), (0, 0, 0, 0, 0, 0), face_words,
            )
            self._add_troop_draft(record)
            new_index = len(self.troop_records) + len(self.troop_additions) - 1
            self.status_var.set(f"Created staged troop {troop_id} at new index {new_index}; existing troop indexes stay unchanged.")
        except ValueError as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _clone_troop(self) -> None:
        if self.troop_selected_line is None:
            messagebox.showerror(APP_TITLE, "Select a troop to clone.")
            return
        source = self._troop_original_by_line(self.troop_selected_line)
        if source is None:
            return
        if source.line_index >= 0:
            source = self.troop_pending.get(source.line_index, source)
        try:
            identity = self._prompt_troop_identity(f"{source.troop_id}_copy", f"{source.singular_name}_Copy", f"{source.plural_name}_Copies")
            if identity is None:
                return
            troop_id, singular, plural = identity
            key = self.next_troop_key
            self.next_troop_key -= 1
            record = replace(source, line_index=key, troop_id=troop_id, singular_name=singular, plural_name=plural)
            self._add_troop_draft(record)
            new_index = len(self.troop_records) + len(self.troop_additions) - 1
            self.status_var.set(f"Cloned {source.troop_id} as {troop_id} at new index {new_index}; existing troop indexes stay unchanged.")
        except ValueError as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _stage_troop_record(self) -> None:
        if self.troop_selected_line is None:
            return
        original = self._troop_original_by_line(self.troop_selected_line)
        if not original:
            return
        try:
            base_flags = int(self.troop_fields["flags"].get().strip())
            troop_type = self._leading_int(self.troop_type_var.get(), "Troop type")
            flags = rebuild_troop_flags(base_flags, troop_type, {key for key, variable in self.troop_flag_vars.items() if variable.get()})
            attributes = tuple(int(variable.get().strip()) for variable in self.troop_attribute_vars)
            proficiencies = tuple(int(variable.get().strip()) for variable in self.troop_proficiency_vars)
            levels = tuple(int(variable.get().strip()) for variable in self.troop_skill_vars)
            base = original if original.line_index < 0 else self.troop_pending.get(original.line_index, original)
            record = replace(
                original,
                singular_name=self.troop_fields["singular"].get().strip(),
                plural_name=self.troop_fields["plural"].get().strip(),
                image=self.troop_fields["image"].get().strip(), flags=flags,
                scene=int(self.troop_fields["scene"].get().strip()),
                reserved=int(self.troop_fields["reserved"].get().strip()),
                faction=self._leading_int(self.troop_fields["faction"].get(), "Faction"),
                upgrade_one=self._leading_int(self.troop_fields["upgrade_one"].get(), "Upgrade path 1"),
                upgrade_two=self._leading_int(self.troop_fields["upgrade_two"].get(), "Upgrade path 2"),
                inventory=tuple(self.troop_draft_inventory), attributes=attributes,
                proficiencies=proficiencies, skill_words=rebuild_troop_skill_words(base.skill_words, levels),
                face_words=self._troop_face_words_from_editor(),
            )
            validate_troop_record(record, len(self.troop_records) + len(self.troop_additions), len(self.item_records) or None)
            if record.line_index < 0:
                self.troop_additions[record.line_index] = record
            elif record == original:
                self.troop_pending.pop(original.line_index, None)
            else:
                self.troop_pending[original.line_index] = record
            self._refresh_troop_choice_controls()
            self._populate_troop_editor(record)
            self._refresh_troop_tree()
            self._update_troop_change_count()
            self.status_var.set(f"Staged troop {record.troop_id}. Save Troops to write it to disk.")
        except ValueError as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _revert_troop_record(self) -> None:
        if self.troop_selected_line is None:
            return
        original = self._troop_original_by_line(self.troop_selected_line)
        if original and original.line_index < 0:
            addition_keys = list(self.troop_additions)
            removed_index = len(self.troop_records) + addition_keys.index(original.line_index)
            try:
                remapped_pending = {
                    key: remap_troop_upgrades_after_removal(record, removed_index)
                    for key, record in self.troop_pending.items()
                }
                remapped_additions = {
                    key: remap_troop_upgrades_after_removal(record, removed_index)
                    for key, record in self.troop_additions.items()
                    if key != original.line_index
                }
            except ValueError as exc:
                messagebox.showerror(APP_TITLE, f"Cannot remove {original.troop_id} yet.\n\n{exc}\n\nChange that upgrade path to 0 or another troop, stage it, and try again.")
                return
            removed = self.troop_additions[original.line_index]
            self.troop_pending = remapped_pending
            self.troop_additions = remapped_additions
            self.troop_selected_line = None
            self._refresh_troop_choice_controls()
            self._refresh_troop_tree()
            self._clear_troop_editor()
            self._update_troop_change_count()
            self.status_var.set(f"Removed staged new troop {removed.troop_id}.")
            return
        if original:
            self.troop_pending.pop(original.line_index, None)
            self._populate_troop_editor(original)
            self._refresh_troop_tree()
            self._update_troop_change_count()

    def _update_troop_change_count(self) -> None:
        count = len(self.troop_pending) + len(self.troop_additions)
        self.troop_change_count_var.set("No staged troop changes" if not count else f"{count} staged troop change{'s' if count != 1 else ''}")
        self.troop_save_button.state(["!disabled"] if count else ["disabled"])

    def _save_troop_pending(self) -> Path:
        if not self.troop_file_path:
            raise FileNotFoundError("Load a module with troops.txt first.")
        if self.raw_dirty and self.raw_path and self.raw_path.resolve() == self.troop_file_path.resolve():
            raise RuntimeError("Save or discard the raw troops.txt edit before saving the Troop Editor.")
        latest, encoding = read_config(self.troop_file_path)
        require_unchanged_text(self.troop_text, latest, self.troop_file_path.name)
        updated = apply_troop_updates(latest, self.troop_pending)
        updated = append_troop_records(updated, list(self.troop_additions.values()))
        final_records = parse_troops(updated)
        item_count = len(self.item_records) or None
        for record in final_records:
            validate_troop_record(record, len(final_records), item_count)
        backup = write_config_text(self.troop_file_path, updated, encoding, False)
        module_dir = self.troop_file_path.parent
        self._load_troop_file(module_dir)
        self._load_party_file(module_dir)
        if self.raw_path and self.raw_path.resolve() == self.troop_file_path.resolve() and not self.raw_dirty:
            self._load_raw_file(self.troop_file_path)
        return backup

    def _save_troop_changes(self) -> None:
        if not self.troop_pending and not self.troop_additions:
            return
        try:
            count = len(self.troop_pending) + len(self.troop_additions)
            backup = self._save_troop_pending()
            self.status_var.set(f"Saved {count} troop{'s' if count != 1 else ''}. Backup: {backup.name}")
            messagebox.showinfo(APP_TITLE, f"Saved {count} troop{'s' if count != 1 else ''}.\n\nBackup created:\n{backup.name}\n\nStart a new campaign for troop data changes to apply reliably.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _reload_troop_file(self) -> None:
        if not self.module_dir:
            return
        if (self.troop_pending or self.troop_additions) and not messagebox.askyesno(APP_TITLE, "Discard staged troop changes and reload?"):
            return
        try:
            self._load_troop_file(self.module_dir)
            self.status_var.set(f"Reloaded troops.txt for {self.module_dir.name}.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _load_raw_files(self, module_dir: Path) -> None:
        self.raw_module_var.set(f"MODULE: {module_dir.name}")
        self.raw_files = sorted(
            (path for path in module_dir.glob("*.txt") if path.name.casefold() != "party_templates.txt"),
            key=lambda path: path.name.casefold(),
        )
        self.raw_path = None
        self.raw_original = ""
        self.raw_dirty = False
        self.raw_file_var.set("Select a module text file")
        self.raw_state_var.set(f"{len(self.raw_files)} files available")
        self.raw_text_widget.delete("1.0", "end")
        self.raw_text_widget.edit_modified(False)
        self.raw_save_button.state(["disabled"])
        self._refresh_raw_file_list()

    def _refresh_raw_file_list(self, *_args: object) -> None:
        if not hasattr(self, "raw_file_list"):
            return
        query = self.raw_search_var.get().strip().lower()
        self.raw_visible_files = [path for path in self.raw_files if not query or query in path.name.lower()]
        self.raw_file_list.delete(0, "end")
        for path in self.raw_visible_files:
            self.raw_file_list.insert("end", path.name)
        if self.raw_path in self.raw_visible_files:
            index = self.raw_visible_files.index(self.raw_path)
            self.raw_file_list.selection_set(index)
            self.raw_file_list.see(index)

    def _select_raw_file(self, _event: object = None) -> None:
        selection = self.raw_file_list.curselection()
        if not selection:
            return
        path = self.raw_visible_files[selection[0]]
        if path == self.raw_path:
            return
        if self.raw_dirty and not messagebox.askyesno(APP_TITLE, "Discard unsaved raw-file edits and open another file?"):
            self._refresh_raw_file_list()
            return
        try:
            self._load_raw_file(path)
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _load_raw_file(self, path: Path) -> None:
        if not self.module_dir or path.parent.resolve() != self.module_dir.resolve() or path not in self.raw_files:
            raise ValueError("The raw editor can only open listed files in the selected module.")
        text, encoding = read_config(path)
        self.raw_path = path
        self.raw_original = text
        self.raw_encoding = encoding
        self.raw_newline = "\r\n" if "\r\n" in text else "\r" if "\r" in text else "\n"
        self.raw_file_var.set(path.name)
        self.raw_text_widget.delete("1.0", "end")
        self.raw_text_widget.insert("1.0", normalize_line_endings(text, "\n"))
        self.raw_text_widget.edit_modified(False)
        self.raw_dirty = False
        self.raw_state_var.set(f"Loaded • {encoding} • {repr(self.raw_newline)[1:-1]}")
        self.raw_save_button.state(["disabled"])
        self.status_var.set(f"Loaded raw module file {path.name}.")

    def _raw_text_modified(self, _event: object = None) -> None:
        if not self.raw_text_widget.edit_modified():
            return
        self.raw_text_widget.edit_modified(False)
        if not self.raw_path:
            return
        self.raw_dirty = True
        self.raw_state_var.set("Unsaved raw-file edits")
        self.raw_save_button.state(["!disabled"])

    def _refresh_raw_files(self) -> None:
        if not self.module_dir:
            return
        if self.raw_dirty and not messagebox.askyesno(APP_TITLE, "Discard unsaved raw-file edits and refresh the file list?"):
            return
        self._load_raw_files(self.module_dir)
        self.status_var.set(f"Found {len(self.raw_files)} editable text files in {self.module_dir.name}.")

    def _reload_raw_file(self) -> None:
        if not self.raw_path:
            return
        if self.raw_dirty and not messagebox.askyesno(APP_TITLE, "Discard unsaved raw-file edits and reload from disk?"):
            return
        try:
            self._load_raw_file(self.raw_path)
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _save_raw_file(self) -> None:
        if not self.raw_path or not self.raw_dirty:
            return
        try:
            if self.raw_path.name.casefold() == "troops.txt" and (self.party_pending or self.troop_pending or self.troop_additions):
                raise RuntimeError("Save or revert staged Party Template and Troop Editor changes before changing troops.txt as raw text.")
            if self.raw_path.name.casefold() == "item_kinds1.txt" and (self.item_pending or self.item_additions):
                raise RuntimeError("Save or revert staged Item Editor changes before editing item_kinds1.txt as raw text.")
            if self.raw_path.name.casefold() == "item_kinds1.txt" and (self.troop_pending or self.troop_additions):
                raise RuntimeError("Save or revert staged Troop Editor changes before changing item indexes in raw item_kinds1.txt.")
            latest, encoding = read_config(self.raw_path)
            require_unchanged_text(self.raw_original, latest, self.raw_path.name)
            edited = self.raw_text_widget.get("1.0", "end-1c")
            updated = normalize_line_endings(edited, self.raw_newline)
            if "\x00" in updated:
                raise ValueError("Module text files cannot contain NUL characters.")
            if self.raw_path.name.casefold() == "troops.txt":
                parse_troops(updated)
            if self.raw_path.name.casefold() == "item_kinds1.txt":
                parse_item_kinds(updated)
            if updated == latest:
                self._load_raw_file(self.raw_path)
                self.status_var.set("The raw file already matches the text on disk.")
                return
            path = self.raw_path
            backup = write_config_text(path, updated, encoding, False)
            self._load_raw_file(path)
            if path.name.casefold() == "troops.txt" and self.module_dir:
                self._load_troop_file(self.module_dir)
                self._load_party_file(self.module_dir)
            if path.name.casefold() == "item_kinds1.txt" and self.module_dir:
                self._load_item_file(self.module_dir)
                self._load_troop_file(self.module_dir)
            if path.name.casefold() == "mission_templates.txt" and self.module_dir:
                self._load_battle_continuation(self.module_dir)
            if path.name.casefold() in {"menus.txt", "scripts.txt", "simple_triggers.txt", "conversation.txt", "skills.txt", "troops.txt"} and self.module_dir:
                self._load_gameplay_tweaks(self.module_dir)
            self.status_var.set(f"Saved {path.name}. Backup: {backup.name}")
            messagebox.showinfo(APP_TITLE, f"Saved raw module file:\n{path.name}\n\nBackup created:\n{backup.name}\n\nWarband may require a new campaign for the change to appear.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _path(self) -> Path:
        return Path(os.path.expandvars(self.path_var.get().strip())).expanduser()

    def _detect_config(self) -> None:
        found = find_default_config()
        self.path_var.set(str(found or (Path.home() / "Documents" / "Mount&Blade Warband" / "rgl_config.txt")))
        if found:
            self._load_config(found)
        else:
            self.status_var.set("Warband config was not found automatically. Use Browse to select rgl_config.txt.")

    def _load_config(self, path: Path, discard: bool = False) -> None:
        if self.pending and not discard and not messagebox.askyesno(APP_TITLE, "Discard staged changes and load this file?"):
            return
        text, encoding = read_config(path)
        self.config_path, self.config_text, self.config_encoding = path, text, encoding
        self.entries, self.pending, self.selected_line = parse_config_entries(text), {}, None
        self.path_var.set(str(path))
        self.lock_var.set(not bool(path.stat().st_mode & stat.S_IWRITE))
        battle = next((entry for entry in self.entries if entry.key.lower() == "battle_size"), None)
        if battle:
            try:
                self.size_var.set(str(value_to_battle_size(float(battle.value))))
            except ValueError:
                pass
        self._refresh_tree()
        self._update_change_count()
        self._clear_editor()
        self._sync_quick_config()
        self.status_var.set(f"Loaded {len(self.entries)} config entries from {path.name}.")

    def _load_from_path(self) -> None:
        try:
            self._load_config(self._path())
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _browse(self) -> None:
        initial = self._path().parent
        selected = filedialog.askopenfilename(title="Select Warband rgl_config.txt", initialdir=initial if initial.exists() else Path.home(), filetypes=[("Warband config", "rgl_config.txt"), ("Text files", "*.txt"), ("All files", "*.*")])
        if selected:
            try:
                self._load_config(Path(selected))
            except Exception as exc:
                messagebox.showerror(APP_TITLE, str(exc))

    def _entry_type(self, entry: ConfigEntry) -> str:
        if entry.key.lower() in BOOLEAN_KEYS and entry.value.strip() in {"0", "1"}:
            return "Toggle"
        if re.fullmatch(r"[-+]?\d+", entry.value.strip()):
            return "Integer"
        if re.fullmatch(r"[-+]?(?:\d+\.?\d*|\.\d+)", entry.value.strip()):
            return "Decimal"
        return "Text"

    def _refresh_tree(self, *_args: object) -> None:
        if not hasattr(self, "tree"):
            return
        selected = self.selected_line
        self.tree.delete(*self.tree.get_children())
        query = self.search_var.get().strip().lower()
        for entry in self.entries:
            shown_value = self.pending.get(entry.line_index, entry.value)
            if query and query not in entry.key.lower() and query not in shown_value.lower() and query not in SETTING_HELP.get(entry.key.lower(), "").lower():
                continue
            changed = entry.line_index in self.pending
            iid = f"line-{entry.line_index}"
            self.tree.insert("", "end", iid=iid, values=(entry.key, shown_value, self._entry_type(entry), "Modified" if changed else ""))
        if selected is not None and self.tree.exists(f"line-{selected}"):
            self.tree.selection_set(f"line-{selected}")
            self.tree.see(f"line-{selected}")

    def _entry_by_line(self, line_index: int) -> ConfigEntry | None:
        return next((entry for entry in self.entries if entry.line_index == line_index), None)

    def _select_entry(self, _event: object = None) -> None:
        selection = self.tree.selection()
        if not selection:
            return
        self.selected_line = int(selection[0].split("-", 1)[1])
        entry = self._entry_by_line(self.selected_line)
        if not entry:
            return
        count = sum(1 for item in self.entries if item.key.lower() == entry.key.lower())
        duplicate_note = f" This key appears {count} times; you are editing line {entry.line_index + 1}." if count > 1 else ""
        self.edit_key_var.set(entry.key)
        self.edit_help_var.set(SETTING_HELP.get(entry.key.lower(), "Raw Warband configuration variable.") + duplicate_note)
        self.edit_value_var.set(self.pending.get(entry.line_index, entry.value))
        self._show_value_editor(self._entry_type(entry) == "Toggle")
        self.stage_button.state(["!disabled"])
        self.revert_button.state(["!disabled"] if entry.line_index in self.pending else ["disabled"])

    def _show_value_editor(self, toggle: bool) -> None:
        if self.value_editor:
            self.value_editor.destroy()
        if toggle:
            self.value_editor = ttk.Combobox(self.value_editor_host, textvariable=self.edit_value_var, values=("0", "1"), state="readonly", font=("Consolas", 12))
        else:
            self.value_editor = tk.Entry(self.value_editor_host, textvariable=self.edit_value_var, bg="#f4eddb", fg="#201f1a", insertbackground="#201f1a", relief="flat", font=("Consolas", 13))
        self.value_editor.pack(fill="x", ipady=8)

    def _clear_editor(self) -> None:
        self.edit_key_var.set("Select a variable")
        self.edit_help_var.set("Choose a row to inspect and edit its raw value.")
        self.edit_value_var.set("")
        self._show_value_editor(False)
        self.stage_button.state(["disabled"])
        self.revert_button.state(["disabled"])

    def _stage_selected(self) -> None:
        if self.selected_line is None:
            return
        entry = self._entry_by_line(self.selected_line)
        if not entry:
            return
        try:
            value = validate_config_value(entry.value, self.edit_value_var.get())
            if value == entry.value:
                self.pending.pop(entry.line_index, None)
            else:
                self.pending[entry.line_index] = value
            self._refresh_tree()
            self._update_change_count()
            self._sync_quick_config()
            self.revert_button.state(["!disabled"] if entry.line_index in self.pending else ["disabled"])
            self.status_var.set(f"Staged {entry.key} = {value}. Save All Changes to write it to disk.")
        except ValueError as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _revert_selected(self) -> None:
        if self.selected_line is None:
            return
        entry = self._entry_by_line(self.selected_line)
        if not entry:
            return
        self.pending.pop(entry.line_index, None)
        self.edit_value_var.set(entry.value)
        self._refresh_tree()
        self._update_change_count()
        self._sync_quick_config()
        self.revert_button.state(["disabled"])

    def _update_change_count(self) -> None:
        count = len(self.pending)
        self.change_count_var.set("No staged changes" if not count else f"{count} staged change{'s' if count != 1 else ''}")
        self.save_all_button.state(["!disabled"] if count else ["disabled"])

    def _save_pending(self) -> Path:
        if not self.config_path:
            raise FileNotFoundError("Load a Warband rgl_config.txt file first.")
        latest, encoding = read_config(self.config_path)
        require_unchanged_text(self.config_text, latest, self.config_path.name)
        latest_entries = parse_config_entries(latest)
        signature = [(entry.line_index, entry.key, entry.value) for entry in self.entries]
        current_signature = [(entry.line_index, entry.key, entry.value) for entry in latest_entries]
        if signature != current_signature:
            raise RuntimeError("The config file changed outside this app. Reload it before saving so no outside changes are overwritten.")
        updated = apply_config_updates(latest, self.pending)
        backup = write_config_text(self.config_path, updated, encoding, self.lock_var.get())
        self._load_config(self.config_path, discard=True)
        return backup

    def _save_all_changes(self) -> None:
        if not self.pending:
            return
        try:
            count = len(self.pending)
            backup = self._save_pending()
            self.status_var.set(f"Saved {count} change{'s' if count != 1 else ''}. Backup: {backup.name}")
            messagebox.showinfo(APP_TITLE, f"Saved {count} config change{'s' if count != 1 else ''}.\n\nBackup created:\n{backup.name}\n\nRestart Warband for all settings to take effect.")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _reload_config(self) -> None:
        if self.config_path:
            try:
                self._load_config(self.config_path)
            except Exception as exc:
                messagebox.showerror(APP_TITLE, str(exc))

    def _update_battle_preview(self, *_args: object) -> None:
        try:
            troops = int(self.size_var.get().replace(",", "").strip())
            value = battle_size_to_value(troops)
            self.value_var.set(f"battle_size = {value:.4f}")
            if troops <= 150:
                load = "Native — Warband’s normal range"
            elif troops <= 300:
                load = "Elevated — usually comfortable on modern hardware"
            elif troops <= 500:
                load = "Heavy — lower corpses and shadows if needed"
            elif troops <= 1000:
                load = "Extreme — expect major CPU load and crowded scenes"
            else:
                load = "Unbound — engine instability or crashes are possible"
            self.load_var.set(load)
            self.apply_button.state(["!disabled"])
        except (ValueError, TypeError):
            self.value_var.set("Enter a whole number of 30 or more")
            self.load_var.set("")
            self.apply_button.state(["disabled"])

    def _apply_battle_size(self) -> None:
        try:
            if not self.config_path:
                raise FileNotFoundError("Load a Warband rgl_config.txt file first.")
            troops = int(self.size_var.get().replace(",", "").strip())
            formatted = f"{battle_size_to_value(troops):.4f}"
            if troops > 1000 and not messagebox.askyesno(APP_TITLE, f"{troops:,} troops is extremely demanding and may make Warband unstable.\n\nApply it anyway?", icon="warning"):
                return
            entry = next((item for item in self.entries if item.key.lower() == "battle_size"), None)
            if entry:
                self.pending[entry.line_index] = formatted
                backup = self._save_pending()
            else:
                text, encoding = read_config(self.config_path)
                require_unchanged_text(self.config_text, text, self.config_path.name)
                updated = apply_config_updates(text, self.pending)
                updated, _ = replace_battle_size(updated, troops)
                backup = write_config_text(self.config_path, updated, encoding, self.lock_var.get())
                self._load_config(self.config_path, discard=True)
            self.status_var.set(f"Applied {troops:,} troops. Backup: {backup.name}")
            messagebox.showinfo(APP_TITLE, f"Battle size set to {troops:,} troops.\n\nAny staged config changes were saved at the same time.\nBackup: {backup.name}")
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _open_folder(self) -> None:
        folder = self._path().parent
        if not folder.exists():
            messagebox.showerror(APP_TITLE, f"Folder not found:\n{folder}")
            return
        try:
            os.startfile(folder)  # type: ignore[attr-defined]
        except Exception as exc:
            messagebox.showerror(APP_TITLE, str(exc))

    def _on_close(self) -> None:
        if (self.pending or self.module_pending or self.party_pending or self.item_pending or self.item_additions or self.troop_pending or self.troop_additions or self.raw_dirty) and not messagebox.askyesno(APP_TITLE, "Discard staged changes and close the app?"):
            return
        self.destroy()


if __name__ == "__main__":
    BattleSizerApp().mainloop()
