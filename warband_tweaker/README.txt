PVN'S WARBAND TWEAKER v1.0.0

Unofficial Mount & Blade: Warband configuration and compiled-module editor.
This utility is not affiliated with or endorsed by TaleWorlds Entertainment.

Native 1.174 is the canonical compatibility baseline. General structured editors
also work with other modules when their compiled layouts are valid. Gameplay
formula controls are signature-guarded and show Unsupported rather than guessing
when a module has changed the expected Native record structure.

The standalone executable is not digitally signed. Windows SmartScreen may
show an Unknown Publisher warning when it is downloaded onto another computer.
Use the included SHA256SUMS.txt when distributing the release ZIP if recipients
need to verify that their files match this build.

1. Close Mount & Blade: Warband.
2. Double-click PVN's Warband Tweaker v1.0.0.exe.
3. The app will try to locate Documents\Mount&Blade Warband\rgl_config.txt.
4. Use Quick Edit for any whole-number battle size of 30 or more, common player
   and performance settings, relevant module toggles, and battle continuation.
5. Use Player Config to search every key/value entry in the file.
6. Select a variable, edit its raw value, and click Stage Change.
7. Stage as many variables as needed, then click Save All Changes.

Quick Edit changes only settings present in the selected config/module. Battle
continuation is offered only when all eight known Warband player-fall triggers
are recognized in mission_templates.txt. It is a reversible, targeted condition
edit; mixed or unfamiliar layouts are refused instead of replacing the whole file.

GAME TWEAKS (MODULE.INI)

1. Open the Game Tweaks tab.
2. The app detects installed Warband modules and loads Native by default.
3. Use Clone Module before changing Native or another original module.
4. Search settings by name, value, description, or category.
5. Select a setting, enter its value, and click Stage Change.
6. Click Save Module Tweaks to write every staged change together.

Game tweaks are grouped into Campaign, Combat, World Map, Gameplay Toggles,
Compatibility, and Advanced under an open Tweakable Settings section. Ordered
load_resource/load_mod_resource rows live in their own collapsed Resource Loading
Order section below the tweaks; searching for one opens that section. The editor
preserves comments, spacing, line endings, duplicate resource entries, and
Warband's misspelled engine keys.
It blocks saving if module.ini changes outside the app and creates a timestamped
module.ini backup before every save.

GAMEPLAY TWEAKS

The Gameplay Tweaks tab provides guarded controls for values normally buried in
compiled module records. Unsupported or heavily customized layouts are shown as
unsupported instead of being edited by guesswork.

Tournament Betting & Rewards
- Set every tournament bet choice as a comma-separated list.
- Set the winner's guaranteed denar prize, renown award, and XP award.

Siege Construction Times
- Set the ladder and siege-tower Engineer-skill bases and time multipliers.
- Set the ladder divisor. The displayed estimate and actual build duration are
  always patched together so the menu cannot show a false completion time.

Fief Income & Campaign Clocks
- Set weekly village, castle, and town rents; prosperity base; and the income
  divisor used as the fief tax/income scale.
- Set the fief-income interval, food-consumption interval, troops per food unit,
  and shared mercenary/village-volunteer refresh interval in game hours.
- Global campaign speed remains in Game Tweaks (module.ini) and is not duplicated.

Party Size & Wages
- Set base party size, renown required per extra party slot, and the garrison
  wage divisor. Charisma remains an automatic +1 per point.
- Leadership and Prisoner Management bonuses remain in Game Tweaks (module.ini).

Post-Battle Gold & XP
- Set the defeated-troop level bonus and base reward divisor.
- Set battle-gold share multiplier, cap, random percentage range, and percent
  divisor, plus the corresponding XP random range and divisor.
- Native's maximum random-range values are exclusive. Lower percent divisors
  increase rewards (100 = stock 1x; 50 is approximately 2x).

Recruitment, Mercenaries & Prisoners
- Set the village base recruit pool, relation bonus, final amount multiplier,
  and price per recruited troop.
- Set the minimum and maximum mercenary group offered in town taverns.
- Set the prisoner-price level bonus, divisor, and special-troop minimum.
- Enable every tavern keeper to buy regular prisoners, without removing the
  normal ransom-broker dialogue.

New-Campaign Player Stats & Skill Rules
- Set trp_player's Strength, Agility, Intelligence, Charisma, and starting level.
- Set starting levels for all 24 named Warband skills, including Leadership,
  Prisoner Management, Trade, Surgery, Riding, and combat skills.
- Set the module-wide maximum level for every named skill from skills.txt.

Player attributes and skill levels are stored inside a save game after campaign
creation. The player-default controls therefore apply to new campaigns; they do
not rewrite an existing save. Siege, economy, party, battle-reward, tournament,
recruitment, prisoner, and skill-cap rules are module data and should be tested
after fully restarting Warband.

The tab checks the complete source text before saving, validates each compiled
operation block, reparses the result, and creates timestamped backups for every
changed file.

PARTY TEMPLATES

1. Load the desired module in the Game Tweaks tab.
2. Open Party Templates; it follows the currently loaded module.
3. Search by party ID, display name, faction number, or troop ID.
4. Edit the party name, flags, menu, faction, or personality values.
5. Select a troop stack to edit its troop, minimum, maximum, and member flags.
6. Use Add Stack or Remove Stack; Warband supports up to six stacks per template.
7. Click Stage Party Changes, then Save Party Templates.

Troop choices are resolved from the selected module's own troops.txt, so Native
and total-conversion modules can use different troop indexes safely. The editor
validates troop references, non-negative stack sizes, minimum <= maximum, record
counts, and the six-stack engine limit. Unedited records remain byte-for-byte
unchanged, and every save creates a timestamped party_templates.txt backup.

ITEM EDITOR

1. Load a module, then open Item Editor.
2. Search by item ID, display name, item type, or mesh name.
3. Optionally filter the list by weapon, armor, ammunition, horse, goods, or
   another item type.
4. General controls edit singular/plural names, item type, denar value, weight,
   abundance, and difficulty.
5. Stats & Damage controls edit armor, hit points, speed, missile speed, weapon
   length, ammunition, and decoded thrust/swing damage amounts and types.
6. Item Flags gives named checkboxes for every documented Warband 1.174 flag,
   plus item type, attachment position, and kill-info controls.
7. Capabilities gives named attack/parry/mounted checkboxes and dropdowns for
   the packed shoot action, carry position, and reload action fields.
8. Raw / Modifiers retains the exact integer fields and modifier-bit editor.
9. Stage any number of items, then click Save Items.

Item Flags and Capabilities can be scrolled with the normal mouse wheel while
the pointer is anywhere over the tab, as well as with the visible scrollbar.

Some item-flag bits have different meanings depending on the item type. These
are labeled together in the GUI (for example Covers Legs / Doesn't Cover Hair /
Penetrates Shield) so the same stored bit is never represented by conflicting
checkboxes. Explanatory help text is shown beside each named control.

The raw flag and capability integers remain editable for custom modules. Bits
not documented by Warband 1.174 are displayed as Unknown / mod-defined and are
preserved when named controls are changed. This lets module-specific extensions
round-trip without silently losing data.

CREATE AND CLONE ITEMS

- Create opens a guided dialog for a unique item ID, names, primary mesh, and
  item type, then adds a safe blank item that can be finished in the editor.
- Clone duplicates the selected item's meshes, factions, triggers, flags, and
  stats under a new ID. The clone can be adjusted before saving.
- The item list shows each compiled numeric index. This keeps Native's known
  duplicate tutorial/voulge IDs distinguishable, and cloning follows the exact
  selected record instead of guessing by ID.
- Newly created and cloned rows are marked New. Select one and use Remove New
  Item to discard it before saving.
- Item IDs are normalized to lowercase with an itm_ prefix and must be unique.

Warband modules use a terminal Items_End record. The editor detects the LAST
valid end marker, which matters for modules such as this Native installation
that contain both itm_items_end and a later itm_ccoop_new_items_end. New items
are inserted immediately before the final marker, and the file's declared item
count is increased. This leaves every pre-existing item index unchanged; only
the terminal marker moves down. Saving is refused if no safe end marker exists.

The editor reads all meshes, faction restrictions, and item trigger blocks and
preserves them unchanged. Packed Warband damage values are decoded into normal
amount plus Cut/Pierce/Blunt controls and safely repacked on save. Item IDs stay
fixed so troop inventories and scripts cannot be orphaned accidentally. Every
save is reparsed, checks for outside file changes, and creates a timestamped
item_kinds1.txt backup.

TROOP EDITOR

1. Load a module, then open Troop Editor beside Item Editor.
2. Search and select any compiled troop, or use Create / Clone in the toolbar.
3. General & Flags edits names, gender/type, hero/equipment flags, faction, scene,
   reserved field, conversation image, and both upgrade paths.
4. Stats & Skills edits attributes, level, all seven weapon proficiencies, and all
   42 Warband skill slots, including reserved slots used by some mods.
5. Inventory edits all 64 fixed item slots and their exact compiled modifier values.
6. Face Workshop exposes both 256-bit face codes, safely randomizes fixed faces
   or spawn ranges from same-type presets already in the module, swaps presets,
   resets them, and controls the Randomize Face spawn flag.
7. Stage any number of troops, then click Save Troops.

CREATE AND CLONE TROOPS

- Create guides you through a unique troop ID, display names, troop type, and
  faction, then opens a safe blank troop for full editing.
- Clone copies the selected troop's flags, stats, skills, equipment, upgrades,
  faction, and face data under a new unique ID.
- New rows are marked New and can be removed before saving. If later new troops
  use higher upgrade indexes, those indexes are safely remapped on removal.
- New troops are always appended to troops.txt. No existing numeric troop index
  moves, which protects party templates, scripts, menus, and other references.
- Troop IDs are normalized to lowercase with a trp_ prefix and must be unique.

Unknown flag and skill bits are preserved, unedited troop records remain unchanged,
and every save validates the complete file, checks for outside changes, and creates
a timestamped troops.txt backup. Start a new campaign for troop changes to apply
reliably.

The face randomizer never generates arbitrary bit patterns. It builds new faces
only from valid, non-empty male/female/undead presets found in the selected
module, and reports the size of the available same-type preset pool.

MODULE FILES (ADVANCED)

The Module Files tab lists every remaining .txt file in the selected module,
including troops, items, factions, scripts, menus, conversations, triggers,
quests, scenes, skills, music, strings, and other compiled module data.

1. Clone and load the desired module first.
2. Open Module Files and select a file from the left.
3. Edit the raw text, then click Save Raw Text File.
4. Use Reload File to discard local edits and reread the disk copy.

The raw editor preserves the original encoding, final newline, and CRLF/LF line
endings. It refuses to overwrite a file changed by another program and creates
a timestamped backup before every save. troops.txt also receives a record-count
check, and its troop mapping is reloaded into Party Templates after saving.

This tab is intentionally marked Advanced. Files such as scripts.txt, menus.txt,
conversation.txt, triggers.txt, and mission_templates.txt contain compiled
operation blocks. Incorrect token edits can keep a module from loading, so use a
cloned module and change only values whose exact version-specific meaning is known.

Warband may need to be run as administrator when its Modules folder is under
Program Files. Some module definition changes only take effect in a new campaign.

The app creates a timestamped backup of rgl_config.txt before every change.
It preserves the file's line endings, blank lines, encoding, spacing, and
duplicate keys. If another program changes the file while it is open, the app
will stop and ask you to reload instead of overwriting those outside changes.

INTEGRITY SAFEGUARDS

- Structured editors refuse to save if their source file changed after loading,
  including comment-only and whitespace-only changes.
- Party Templates also refuses to save if troops.txt changed after loading.
- Saves first create a timestamped backup, write a temporary file beside the
  target, and atomically replace the target only after the new text is complete.
- Gameplay operations that change two files prepare both first and roll back the
  first file byte-for-byte if the second replacement fails, preventing half-saves.
- A failed save restores the target's original read-only state.
- Item, troop, and party files are reparsed and record counts validated before writing.
- Unknown item and troop flag/capability/skill bits are preserved rather than discarded.

Optional: enable "Lock config as read-only" to stop Warband's in-game slider
from resetting the custom value. Turn it off if you want Warband to update
other settings in the same config file.

Very large battles can cause low frame rates, crowded scenes, instability,
or crashes. Sizes above 1,000 require an extra confirmation.

PVNsWarbandTweaker.pyw is the editable Python source version. The original
battle-size and complete rgl_config.txt tools remain available. The public source
repository includes verify_native_release.py for the read-only Native 1.174 audit.
