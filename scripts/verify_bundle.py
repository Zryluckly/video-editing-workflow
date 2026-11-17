"""Verify distributed media and third-party document fingerprints without networking."""

import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile


ROOT = Path(__file__).resolve().parents[1]


def checked_file(base, relative):
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()) or not path.is_file():
        raise ValueError(f"Missing or out-of-scope file: {relative}")
    return path


def asset_bytes(item):
    if "storage" not in item:
        data = checked_file(ROOT, item["path"]).read_bytes()
    else:
        if item["storage"]["type"] != "split":
            raise ValueError(f"Unknown storage type: {item['path']}")
        parts = []
        for part in item["storage"]["parts"]:
            chunk = checked_file(ROOT, part["path"]).read_bytes()
            if len(chunk) != part["bytes"] or hashlib.sha256(chunk).hexdigest() != part["sha256"]:
                raise ValueError(f"Part fingerprint mismatch: {part['path']}")
            parts.append(chunk)
        data = b"".join(parts)
    if len(data) != item["bytes"] or hashlib.sha256(data).hexdigest() != item["sha256"]:
        raise ValueError(f"Asset fingerprint mismatch: {item['path']}")
    return data


def verify():
    manifest = json.loads((ROOT / "ASSET_SOURCES.json").read_text(encoding="utf-8"))
    media = documents = 0
    for item in manifest["assets"]:
        data = asset_bytes(item)
        checked_file(ROOT, item["licenseNotice"])
        if Path(item["path"]).suffix == ".motion":
            with zipfile.ZipFile(io.BytesIO(data)) as archive:
                damaged = archive.testzip()
                if damaged is not None:
                    raise ValueError(f"Damaged template entry: {damaged}")
        media += 1
    for manifest_path in sorted((ROOT / "integrations").glob("*/SOURCE_FILES.json")):
        source = json.loads(manifest_path.read_text(encoding="utf-8"))
        checked_file(manifest_path.parent, "LICENSE")
        for item in source["files"]:
            path = checked_file(manifest_path.parent, item["file"])
            if hashlib.sha256(path.read_bytes()).hexdigest() != item["distributed_sha256"]:
                raise ValueError(f"Document fingerprint mismatch: {path.relative_to(ROOT)}")
            documents += 1
    print(f"Verified {media} media assets and {documents} reference documents")
    print("Fingerprints and archive CRC only; not a rendering or listening test")


if __name__ == "__main__":
    try:
        verify()
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        sys.exit(f"Bundle verification failed: {error}")
