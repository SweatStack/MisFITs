# Contributing to MisFITs

Thanks for considering a contribution. The corpus only works if it's curated, so PRs go through review.

## Adding a fixture

1. Create `files/{slug}/` with a short, descriptive, kebab-case slug (e.g. `wrist-hr-locks-onto-cadence-fenix7`).
2. Drop the `.fit` file inside. One `.fit` per directory.
3. Write `metadata.json` next to it. See `SCHEMA.md` for fields and `schema/fixture.schema.json` for the validator.
4. Open a PR. The PR template includes the license attestation — please read it carefully.

A known-good control fixture is just a fixture with `"defects": []`. We need these too.

## License attestation

All `.fit` data in this repo is published under **CC BY 4.0**. All code under **MIT**. By submitting a PR you attest, via the PR-template checkboxes, that you have the right to grant these licenses for the content you're submitting.

If you're unsure whether you have the right to release a file (e.g. it was given to you privately by someone else, or it was downloaded from a service whose terms restrict redistribution), don't submit it.

## A note on personal data in FIT files

FIT files can contain GPS tracks, timestamps, heart rate, user profile, and device serial numbers. Some of this is identifying. We do **not** scrub files: scrubbing would mutate bytes and undermine the corpus's value as a parser test set. Instead:

- **Review the file before submitting.** Open it in a viewer (e.g. fitfileviewer.com, or your preferred parser) and look at what's in it.
- **Don't submit files you wouldn't be comfortable publishing as-is.** Once it's merged, assume it's permanent and public.
- If a defect can be reproduced on a synthetic or non-residential trace, prefer that.

## Style

- Keep `description` concrete. "Power spike" is less useful than "Single sample reads 65535 W between two ~280 W samples on a 6% climb."
- `expected_behavior` is optional. If you have a clear view of what a robust parser should do, write it down while the file is fresh in your mind. If you don't, leave it out.
