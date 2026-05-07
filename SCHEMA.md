# Fixture Metadata Schema

Each fixture has a `metadata.json` validated against [`schema/fixture.schema.json`](schema/fixture.schema.json) (JSON Schema 2020-12). This document is the human-readable companion.

## Shape

```json
{
  "$schema": "../../schema/fixture.schema.json",
  "title": "Power spike on Edge 530 climb",
  "description": "Mid-ride spike to 65535 W on a Garmin Edge 530 paired with a Stages LR power meter. Single sample; neighboring samples are physiologically plausible. Captured 2024-08, climb in the Pyrenees.",
  "defects": [
    {
      "layer": 4,
      "nature": "implausible",
      "cause": ["sensor"],
      "notes": "Single sample reads 65535 W between two ~280 W neighbors; likely uint16 sentinel leaking through."
    }
  ],
  "expected_behavior": "Parser must not crash. Robust parsers should flag the spike (e.g. value >> physiological max) and either drop or interpolate. Aggregate fields (avg/max power) computed downstream should exclude the spike."
}
```

## Fields

| Field | Required | Type | Notes |
|---|---|---|---|
| `title` | yes | string | One-line summary. Used in indexes and PR titles. |
| `description` | yes | string | Paragraph. Include device/firmware/sport here if relevant — these are not separate fields. |
| `defects` | yes | array | Possibly empty. `[]` means a known-good control fixture. |
| `expected_behavior` | no | string | What a robust parser should do. Optional — write it if you have a clear view; skip it if the file speaks for itself. Prose for now; may become structured later. |

`title`, `description`, and `expected_behavior` are deliberately prose. Structured fields (sport, device, firmware, severity) can be added later if real query workflows demand them — easier to add than to remove.

## Defect entries

Each entry in `defects` is a `(layer, nature)` pair from `TAXONOMY.md`, optionally with a specific code and cause tags.

| Field | Required | Type | Notes |
|---|---|---|---|
| `layer` | yes | integer 1–8 | See `TAXONOMY.md` §"Primary axis". |
| `nature` | yes | enum | `missing` \| `malformed` \| `implausible` \| `biased` \| `mislabeled`. |
| `cause` | no | array | Zero or more of: `sensor`, `firmware`, `user`, `environment`, `transmission`, `schema`. Tags, not a partition — a single defect often has multiple causes. |
| `notes` | no | string | Specifics about this defect in this file. In multi-defect files, this is what disambiguates which detail applies to which defect. |

A file with multiple defects gets multiple entries. A known-good file has `defects: []`.

There is intentionally no per-defect `code` field yet. Once the corpus is large enough to reveal stable categories below `(layer, nature)`, we'll add a registry-backed code and backfill in one pass.
