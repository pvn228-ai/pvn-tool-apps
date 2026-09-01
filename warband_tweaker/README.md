# PVN's Warband Tweaker v1.0.0

PVN's Warband Tweaker is an unofficial Windows desktop utility for Mount & Blade:
Warband. Native 1.174 is the canonical baseline for guarded gameplay formulas;
general structured editors also support other modules whose compiled layouts are
valid. Unfamiliar gameplay signatures are reported as unsupported instead of
being changed by guesswork.

## Downloads

- [Standalone EXE](<../PVN's Warband Tweaker v1.0.0.exe?raw=1>)
- [Complete release ZIP](PVNs-Warband-Tweaker-v1.0.0.zip?raw=1)
- [ZIP checksum](PVNs-Warband-Tweaker-v1.0.0.zip.sha256.txt)
- [Release notes](RELEASE-NOTES.txt)

ZIP SHA-256:
`E35EDD8690F3E0DC1F936E1B94A371442B6D2B77FA50300FE529CEA825FF3493`

Standalone EXE SHA-256:
`A068B8AE575A780B5098F9C41822B06E780A0FC4927D02D19037CAC3A97942DB`

## Highlights

- Any whole-number battle size of 30 or more.
- Searchable player config and typed `module.ini` editors.
- Guarded tournament, siege, economy, party, wage, recruitment, prisoner,
  battle-reward, player-default, and skill-cap controls.
- Structured party-template, item, and troop editors with create/clone support.
- Full troop stats, skills, inventory, upgrades, flags, and face workshop.
- Exact outside-change detection, timestamped backups, atomic replacements, and
  rollback-protected multi-file gameplay saves.
- Advanced raw module-file access for experienced module authors.

Close Warband before saving. Clone original modules before routine editing, and
start a new campaign when testing definitions that are copied into save games.

## Verified release

- 50 automated tests pass.
- Stock Native 1.174 read-only audit passes across 1,078 troops, 63 party
  templates, 624 items, 34 factions, 42 skills, and all guarded formulas.
- Frozen Windows GUI startup and responsiveness smoke test passes.
- The release archive and every internal payload checksum pass verification.

## Source

The dependency-free Tkinter source and verification tools are in [`src/`](src/).
The [compatibility and integrity notes](docs/module-compatibility-and-integrity.md)
describe the save model and Native baseline in detail.

```powershell
cd warband_tweaker\src
python -m unittest -v test_warband_battle_sizer.py
python verify_native_release.py
python verify_release_archive.py
python -m pip install pyinstaller
pyinstaller --noconfirm PVNsWarbandTweaker.spec
powershell -ExecutionPolicy Bypass -File .\smoke_frozen_app.ps1
```

This utility is not affiliated with or endorsed by TaleWorlds Entertainment.
