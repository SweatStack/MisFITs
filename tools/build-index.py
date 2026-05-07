#!/usr/bin/env python3
"""Build index.json from per-fixture metadata.json sidecars.

Walks files/{slug}/, validates each metadata.json against the constraints
in schema/fixture.schema.json, and writes the aggregate to index.json at
the repo root.

Run with --check to validate and verify index.json is up-to-date without
writing — intended for CI.

Pure stdlib; no third-party dependencies.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
FILES_DIR = REPO_ROOT / "files"
INDEX_PATH = REPO_ROOT / "index.json"

VALID_NATURES = {"missing", "malformed", "implausible", "biased", "mislabeled"}
VALID_CAUSES = {"sensor", "firmware", "user", "environment", "transmission", "schema"}


def validate(slug: str, meta: dict, fit_files: list[Path]) -> list[str]:
    errors: list[str] = []

    if len(fit_files) == 0:
        errors.append(f"{slug}: no .fit file found")
    elif len(fit_files) > 1:
        names = ", ".join(p.name for p in fit_files)
        errors.append(f"{slug}: expected exactly one .fit, found {len(fit_files)}: {names}")

    for field in ("title", "description", "defects"):
        if field not in meta:
            errors.append(f"{slug}: missing required field '{field}'")

    for field in ("title", "description", "expected_behavior"):
        if field in meta and not (isinstance(meta[field], str) and meta[field]):
            errors.append(f"{slug}: '{field}' must be a non-empty string")

    defects = meta.get("defects")
    if not isinstance(defects, list):
        errors.append(f"{slug}: 'defects' must be a list")
        return errors

    for i, d in enumerate(defects):
        loc = f"{slug}.defects[{i}]"
        if not isinstance(d, dict):
            errors.append(f"{loc}: must be an object")
            continue
        layer = d.get("layer")
        if not isinstance(layer, int) or isinstance(layer, bool) or not 1 <= layer <= 8:
            errors.append(f"{loc}: 'layer' must be an integer 1-8")
        nature = d.get("nature")
        if nature not in VALID_NATURES:
            errors.append(f"{loc}: 'nature' must be one of {sorted(VALID_NATURES)}")
        if "cause" in d:
            cause = d["cause"]
            if not isinstance(cause, list) or not all(c in VALID_CAUSES for c in cause):
                errors.append(f"{loc}: 'cause' must be a list of {sorted(VALID_CAUSES)}")
            elif len(set(cause)) != len(cause):
                errors.append(f"{loc}: 'cause' entries must be unique")
        if "notes" in d and not isinstance(d["notes"], str):
            errors.append(f"{loc}: 'notes' must be a string")

        allowed = {"layer", "nature", "cause", "notes"}
        unknown = set(d) - allowed
        if unknown:
            errors.append(f"{loc}: unknown fields: {sorted(unknown)}")

    allowed_top = {"$schema", "title", "description", "defects", "expected_behavior"}
    unknown_top = set(meta) - allowed_top
    if unknown_top:
        errors.append(f"{slug}: unknown top-level fields: {sorted(unknown_top)}")

    return errors


def build() -> tuple[dict, list[str]]:
    fixtures: list[dict] = []
    errors: list[str] = []

    if not FILES_DIR.exists():
        return {"fixtures": fixtures}, [f"{FILES_DIR.relative_to(REPO_ROOT)} does not exist"]

    for fixture_dir in sorted(p for p in FILES_DIR.iterdir() if p.is_dir()):
        slug = fixture_dir.name
        meta_path = fixture_dir / "metadata.json"
        if not meta_path.exists():
            errors.append(f"{slug}: missing metadata.json")
            continue
        try:
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            errors.append(f"{slug}: invalid JSON in metadata.json: {e}")
            continue
        if not isinstance(meta, dict):
            errors.append(f"{slug}: metadata.json must contain a JSON object")
            continue

        fit_files = sorted(fixture_dir.glob("*.fit"))
        errors.extend(validate(slug, meta, fit_files))

        if not fit_files or not isinstance(meta.get("defects"), list):
            continue

        entry = {
            "slug": slug,
            "path": fit_files[0].relative_to(REPO_ROOT).as_posix(),
            "title": meta.get("title"),
            "description": meta.get("description"),
            "defects": meta["defects"],
        }
        if "expected_behavior" in meta:
            entry["expected_behavior"] = meta["expected_behavior"]
        fixtures.append(entry)

    return {"fixtures": fixtures}, errors


def serialize(index: dict) -> str:
    return json.dumps(index, indent=2, ensure_ascii=False) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Build index.json from fixture metadata.")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate and verify index.json is up-to-date; do not write.",
    )
    args = parser.parse_args()

    index, errors = build()
    for err in errors:
        print(f"error: {err}", file=sys.stderr)
    if errors:
        return 1

    output = serialize(index)
    count = len(index["fixtures"])

    if args.check:
        existing = INDEX_PATH.read_text(encoding="utf-8") if INDEX_PATH.exists() else ""
        if existing != output:
            print(
                "error: index.json is out of date; run tools/build-index.py",
                file=sys.stderr,
            )
            return 1
        print(f"ok: {count} fixture(s), index.json up to date")
        return 0

    INDEX_PATH.write_text(output, encoding="utf-8")
    print(f"wrote index.json: {count} fixture(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
