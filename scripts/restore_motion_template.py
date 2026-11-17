"""Restore the unchanged .motion archive from bundled parts, after hash verification."""

import argparse
import hashlib
import json
from pathlib import Path
import sys

from verify_bundle import ROOT, asset_bytes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, help="Optional new output .motion path")
    args = parser.parse_args()
    manifest = json.loads((ROOT / "ASSET_SOURCES.json").read_text(encoding="utf-8"))
    item = next(x for x in manifest["assets"] if x["kind"] == "motion-template")
    data = asset_bytes(item)
    output = args.output or ROOT / item["path"]
    if output.exists():
        if output.is_file() and hashlib.sha256(output.read_bytes()).hexdigest() == item["sha256"]:
            print(f"Already restored and verified: {output}")
            return
        parser.error("output exists with different content; choose a new path")
    if not output.parent.is_dir():
        parser.error("output directory must already exist")
    with output.open("xb") as stream:
        stream.write(data)
    print(f"Restored {len(data)} bytes: {output}")
    print(f"SHA256: {item['sha256']}")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, KeyError, StopIteration) as error:
        sys.exit(f"Restore failed: {error}")
