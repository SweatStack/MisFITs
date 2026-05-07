# MisFITs

> Here's to the crazy ones. The misfits. The ones with rides that finish before they start, power meters reporting 65,535 watts, and timestamps from December 31st, 1989.

A curated collection of FIT files for testing your activity data parsers. Malformed, corrupted, and edge-case files alongside known-good ones, so you can validate both failure modes and happy paths.
Because the files crazy enough to break your parser are the ones that will make it unbreakable.

## Using the corpus

Each fixture lives in `files/{slug}/` and contains exactly one `.fit` file plus a `metadata.json` describing it:

- Point your parser at the `.fit` file.
- Read `metadata.json` to see what defects the file contains, and — where the contributor wrote one — what a robust parser should do.
- A fixture with `"defects": []` is a known-good control. Your parser should handle these without complaint.

Programmatic consumers can also use `index.json` at the repo root, which aggregates every fixture's metadata into a single fetch.

## Repository structure

```
misfits/
├── files/{slug}/            # one directory per fixture
│   ├── *.fit                # exactly one .fit
│   └── metadata.json        # validated against schema/fixture.schema.json
├── schema/fixture.schema.json
├── index.json               # generated; aggregate of every metadata.json
├── TAXONOMY.md              # the defect ontology
├── SCHEMA.md                # human-readable metadata reference
└── CONTRIBUTING.md
```

Slugs are short, descriptive, kebab-case (e.g. `wrist-hr-locks-onto-cadence-fenix7`). They're stable handles, not classifiers — the metadata carries the taxonomy, so directory layout stays flat.

## Fixture metadata

Every fixture's `metadata.json` follows a small schema: a `title`, a `description`, and a list of `defects`. Each defect names where in the FIT stack the wrongness lives (`layer`) and what kind of wrongness it is (`nature`), and may optionally carry `cause` tags and free-form `notes`. An optional `expected_behavior` field captures what a robust parser should do.

A file with multiple defects has multiple entries. A known-good file has an empty list.

Field-by-field reference and a worked example: [SCHEMA.md](SCHEMA.md). Machine-readable validator: [`schema/fixture.schema.json`](schema/fixture.schema.json).

## Defect taxonomy

Defects live on two orthogonal axes.

**Layer** — where in the FIT stack the defect lives, ordered from "closest to the bytes" to "closest to the athlete's intent":

| # | Layer | Example |
|---|---|---|
| 1 | Container integrity | Missing EOF CRC, truncated upload |
| 2 | Schema conformance | Undeclared developer field, illegal enum |
| 3 | Record-level validity | Heart rate of 300 bpm in a single sample |
| 4 | Temporal coherence | Power spike, dropped samples, time going backwards |
| 5 | Cross-signal coherence | Wrist HR locking onto cadence |
| 6 | Calibration / systematic bias | Uncalibrated barometer reading 50 m low all day |
| 7 | Activity semantics | Forgot to stop recording during the drive home |
| 8 | Derived / aggregate fields | Wrong session totals, miscalculated normalized power |

**Nature** — what kind of wrongness: `missing`, `malformed`, `implausible`, `biased`, or `mislabeled`.

Every defect is a `(layer, nature)` pair. The full reasoning — including the cause axis, edge cases, and where the model strains — is in [TAXONOMY.md](TAXONOMY.md).

## Contributing

Contributions are welcome, especially wild-caught weird files. See [CONTRIBUTING.md](CONTRIBUTING.md) for how to add a fixture, the license attestation contributors agree to in the PR template, and what to consider before publishing a file that may contain personal data.

## Status

Early. The corpus is being seeded; the schema is intentionally minimal and will grow as patterns emerge. Feedback on the taxonomy and schema is as welcome as fixture contributions — easier to change shape now than after a hundred fixtures are committed to it.

## License

`.fit` data: [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Code: MIT.
