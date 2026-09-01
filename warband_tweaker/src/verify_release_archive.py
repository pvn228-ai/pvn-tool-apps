"""Verify the v1.0.0 release ZIP without extracting or executing it."""

from __future__ import annotations

import argparse
import hashlib
import re
from pathlib import Path
from zipfile import ZipFile


ARCHIVE_NAME = "PVNs-Warband-Tweaker-v1.0.0.zip"
EXPECTED_ENTRIES = {
    "PVN's Warband Tweaker v1.0.0.exe",
    "PVNsWarbandTweaker.pyw",
    "README.txt",
    "RELEASE-NOTES.txt",
    "SHA256SUMS.txt",
    "warband-module-tweakables.md",
}
STALE_SCOPE_TERMS = (f"{2008:,} troops", f"{1251:,} items", f"{47} automated tests", "both installed " + "modules")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest().upper()


def default_archive() -> Path:
    source_dir = Path(__file__).resolve().parent
    candidates = (
        source_dir.parent / ARCHIVE_NAME,
        source_dir.parent / "releases" / ARCHIVE_NAME,
        source_dir.parents[1] / "outputs" / ARCHIVE_NAME,
    )
    return next((path for path in candidates if path.is_file()), candidates[0])


def verify_archive(path: Path) -> str:
    path = path.expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"Release ZIP not found: {path}")
    with ZipFile(path) as archive:
        names = set(archive.namelist())
        if names != EXPECTED_ENTRIES:
            raise RuntimeError(f"Unexpected archive contents: {sorted(names)}")
        corrupt = archive.testzip()
        if corrupt:
            raise RuntimeError(f"ZIP CRC check failed for: {corrupt}")
        manifest_text = archive.read("SHA256SUMS.txt").decode("ascii")
        manifest: dict[str, str] = {}
        for line in manifest_text.splitlines():
            match = re.fullmatch(r"([0-9A-F]{64}) \*(.+)", line)
            if not match:
                raise RuntimeError(f"Malformed SHA256SUMS.txt line: {line!r}")
            manifest[match.group(2)] = match.group(1)
        expected_manifest_names = EXPECTED_ENTRIES - {"SHA256SUMS.txt"}
        if set(manifest) != expected_manifest_names:
            raise RuntimeError("SHA256SUMS.txt does not cover exactly the expected payload files.")
        for name, expected_hash in manifest.items():
            actual_hash = sha256(archive.read(name))
            if actual_hash != expected_hash:
                raise RuntimeError(f"Internal SHA-256 mismatch for {name}: {actual_hash}")

        packaged_source = archive.read("PVNsWarbandTweaker.pyw")
        local_source = Path(__file__).with_name("warband_battle_sizer.py").read_bytes()
        if packaged_source != local_source:
            raise RuntimeError("The source inside the ZIP differs from warband_battle_sizer.py.")
        release_text = (archive.read("README.txt") + archive.read("RELEASE-NOTES.txt") + archive.read("warband-module-tweakables.md")).decode("utf-8").casefold()
        stale = [term for term in STALE_SCOPE_TERMS if term in release_text]
        if stale:
            raise RuntimeError(f"Release documentation contains stale scope claims: {stale}")
    return sha256(path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the PVN's Warband Tweaker release ZIP and internal hash manifest.")
    parser.add_argument("archive", nargs="?", type=Path, default=default_archive())
    args = parser.parse_args()
    digest = verify_archive(args.archive)
    print(f"Release archive audit passed: {args.archive}")
    print(f"SHA-256: {digest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
