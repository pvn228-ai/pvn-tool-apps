# Module compatibility and integrity notes

PVN's Warband Tweaker v1.0.0 is an all-in-one editor for Mount & Blade:
Warband's player configuration and compiled module data.

## Product scope

- Stock Native 1.174 is the canonical gameplay-tweak baseline.
- The module manager, `module.ini`, party-template, item, troop, face, and raw
  text editors are module-oriented features and are not tied to a personally
  installed custom module.
- Other modules are accepted when their file structures parse correctly.
- Compiled gameplay formulas are enabled only when their named records and
  surrounding operation signatures match. An unfamiliar layout is reported as
  unsupported and is not patched by guesswork.

## Structured editors

| Area | Main guarantees |
|---|---|
| `module.ini` | Preserves comments, order, spacing, duplicate resource rows, encoding, line endings, and Warband's original misspelled keys. |
| `party_templates.txt` | Validates record count, troop indexes, stack ranges, and the six-stack engine limit. |
| `item_kinds1.txt` | Preserves meshes, faction blocks, triggers, unknown bits, packed damage, existing indexes, and the final item sentinel. |
| `troops.txt` | Validates the six-line compiled layout, 64 inventory slots, item/troop references, packed skills, flags, upgrades, and both 256-bit face codes. |
| Gameplay Tweaks | Uses exact Native 1.174 record/operation signatures and reparses every result before saving. |
| Module Files | Provides advanced raw access with encoding, line-ending, outside-change, and backup protection. |

New items are inserted immediately before the final valid Items_End marker. New
troops are appended. These rules keep every existing numeric index stable.

Native contains 15 known duplicated item IDs (mainly tutorial items plus
`itm_voulge`). The Item Editor displays the compiled numeric index and stores the
exact source line when cloning, so duplicate IDs remain distinguishable and the
correct meshes, factions, and trigger block are copied.

## Guarded Native gameplay controls

The current release includes reversible controls for:

- tournament bet choices, denar prize, renown, and XP;
- ladder and siege-tower construction formulas;
- village, castle, and town income, prosperity scaling, and campaign clocks;
- base party size, renown scaling, garrison wages, food consumption, and refresh timing;
- post-battle gold and XP formulas;
- village recruitment, tavern mercenary groups, prisoner prices, and tavern sales;
- new-campaign player attributes/skills and all module-wide skill caps;
- battle continuation after player knock-out.

Global campaign speed and Leadership/Prisoner Management bonuses remain in the
typed `module.ini` editor so the same setting is not exposed twice.

## Save integrity

1. The app compares the complete current file with the originally loaded text
   and refuses to overwrite outside edits, including comment or whitespace changes.
2. Structured results are validated and reparsed before disk writes.
3. Every target receives a unique timestamped backup beside the source file.
4. New content is encoded and flushed into a temporary sibling before replacement.
5. The target is replaced atomically and its prior read-only state is preserved.
6. Multi-file gameplay changes prepare every file before committing. If a later
   replacement fails, all earlier replacements are restored byte-for-byte and to
   their original access modes.
7. Unknown packed item/troop bits are retained instead of silently discarded.

Clone an original module before routine editing. Backups protect individual
saves, while a clone gives the user a clean module-level recovery point.

## Saved-game behavior

Warband copies substantial module state into a campaign save. Existing troops,
the player character, parties, faction relations, and other spawned state may
therefore keep old values after the source text changes. Start a new campaign
when validating troop definitions or player defaults. Formula-driven module
rules should be tested after fully restarting Warband.

## Release audit

Run the automated suite and the read-only Native audit from the source folder:

```powershell
python -m unittest -v test_warband_battle_sizer.py
python verify_native_release.py
python verify_release_archive.py path\to\PVNs-Warband-Tweaker-v1.0.0.zip
```

The v1.0.0 Native 1.174 baseline contains 1,078 troops, 63 party templates, 624
items, 34 factions, 42 skills, and 35 compiled text files. The audit validates
those records, known Native duplicate IDs, references, terminal item marker,
structured serializer semantics, all eight battle-continuation signatures, and
every guarded gameplay formula without writing to the module.
