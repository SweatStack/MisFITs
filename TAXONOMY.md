## What I think you're asking for

You want a principled taxonomy of FIT file errors — not just a list, but a structure where every error has a natural home, the categories are mutually exclusive (or close to it), and the dimensions of categorization are explicit. The kind of thing you could hand to someone writing a FIT validator/repair tool and they'd know where a new error type belongs.

Looking at your examples, I notice they live on very different axes:
- *"FIT file not properly closed"* is about the **file as a container** — bytes on disk, structure, encoding
- *"Power spike"* is about a **single data point being wrong**
- *"Forgot to stop the device in the car"* is about the **activity boundaries** being wrong, even though every individual sample is technically correct
- *"Wrist HR locking onto cadence"* is about a **sensor failure mode** — the data is internally consistent but measuring the wrong thing
- *"Erroneous developer field data"* is about **schema/semantic correctness** of an extension mechanism

So a flat list won't work well. You need at least two dimensions: *where in the stack the error lives* (file format → record → signal → activity-level semantics) and *what kind of wrongness it is* (missing, malformed, implausible, miscalibrated, mislabeled).

Below is my attempt. I'll give you the primary axis (a layered model), then a secondary axis (error nature), then show how your examples slot in, and finally flag the hard cases where the taxonomy strains.

---

## Primary axis: layers of the FIT stack

I'll order these from "closest to the bytes" to "closest to the athlete's intent." An error at layer N generally assumes layers 1..N−1 are intact.

**Layer 1 — Container integrity.** The file as a sequence of bytes conforming to the FIT format spec. Header present and valid, CRC matches, definition messages precede their data messages, file properly terminated. Failures here mean a parser may not even get to the data.

**Layer 2 — Schema conformance.** Given that the bytes parse, do the messages conform to the FIT profile? Required fields present, field types correct, enum values within declared ranges, developer fields properly declared before use. This is "is the data well-formed?" rather than "is the data right?"

**Layer 3 — Record-level validity.** A single record (e.g. one `record` message at one timestamp) considered in isolation. Are the values within physically possible ranges? Heart rate of 300 bpm, power of 50000 W, latitude of 200°. No cross-record reasoning yet.

**Layer 4 — Temporal/sequential coherence.** Records considered as a time series. Gaps, duplicates, out-of-order timestamps, impossible rates of change (the "spike" category — a single sample where the *value* is plausible but the *delta* from neighbors isn't). This is where most signal-quality issues live.

**Layer 5 — Cross-signal coherence.** Multiple channels considered together. HR tracking cadence too perfectly. GPS speed disagreeing with wheel speed. Altitude derivative not matching grade × distance. Power present but cadence zero for an extended period on a bike. The individual signals may each look fine; their *relationship* is wrong.

**Layer 6 — Sensor calibration / systematic bias.** The signal is internally coherent and cross-coherent, but offset or scaled wrong. Uncalibrated barometer, stale power meter zero offset, magnetometer needing declination correction, tire circumference wrong. Distinguished from layer 4/5 errors by being *constant or slowly drifting* rather than transient.

**Layer 7 — Activity semantics.** The data is correct as recorded, but doesn't match what the user did. Forgot to stop recording during the drive home. Wrong sport selected. Auto-pause failed and recorded a 20-minute coffee stop as cycling. Activity split incorrectly across files. The error is in the *labeling and boundaries*, not the samples.

**Layer 8 — Derived/aggregate fields.** Session totals, laps, training load, normalized power, TSS — values computed from the underlying records. Can be wrong because the inputs were wrong (downstream of errors above) or because the computation itself is wrong (Garmin firmware bug, third-party tool miscalculation).

A useful property of this layering: a repair tool generally has to fix errors bottom-up. You can't validate a power spike (layer 4) until you've parsed the records (layer 1) and confirmed the field is even a power field (layer 2).

---

## Secondary axis: nature of the error

Orthogonal to *where* the error lives is *what kind* of error it is. Five kinds cover almost everything:

- **Missing** — expected data is absent (dropped sample, missing required field, no GPS fix yet)
- **Malformed** — data is present but doesn't conform to its schema/format (bad CRC, illegal enum value, developer field with no prior definition)
- **Implausible** — data conforms but violates physics/physiology (300 bpm, 200° latitude, −50 m/s² acceleration)
- **Biased** — data is plausible but systematically offset (uncalibrated altimeter reading 50 m low all day)
- **Mislabeled** — data is correct but attributed to the wrong context (driving recorded as cycling, wrong sport, wrong lap boundary)

Every concrete error is a (layer, nature) pair. This is the part that makes the ontology actually useful: when you encounter a new error, you ask both questions and you get a cell in the matrix.

---

## Tertiary axis (optional but useful): cause / origin

Not every taxonomy needs this, but for a repair tool it helps to know *why* the error happened, because that often determines whether it's fixable:

- **Sensor** — hardware limitation or failure (HR strap dropout, GPS multipath, optical HR cross-talk with cadence)
- **Firmware/algorithm** — device software produced bad output from good input (bad smoothing, bad auto-pause logic, bad altitude fusion)
- **User** — operator error (forgot to stop, wrong sport, didn't calibrate)
- **Environment** — conditions exceeded sensor capability (urban canyon for GPS, cold for battery/LCD, water for optical HR)
- **Transmission/storage** — file corruption during transfer, interrupted write, truncation
- **Schema/extension** — mismatch between writer and reader, developer field schema bugs

This axis is messier (a single error often has multiple causes — wrist HR locking onto cadence is sensor *and* algorithm *and* environment) so I'd treat it as tags rather than a partition.

---

## Your examples mapped in

| Example | Layer | Nature | Likely cause |
|---|---|---|---|
| FIT file not properly closed/ended | 1 Container | Malformed | Transmission/storage |
| Erroneous developer field data | 2 Schema (if undeclared/wrong type) or 3 Record (if value wrong) | Malformed or Implausible | Schema/extension |
| Missing data (occasional gap) | 4 Temporal | Missing | Sensor / transmission |
| Power or speed spikes | 4 Temporal | Implausible | Sensor / firmware |
| Wrist HR locking onto cadence | 5 Cross-signal | Implausible (in context) | Sensor + environment |
| Forgot to stop in the car | 7 Activity semantics | Mislabeled | User |
| No GPS fix at start → big jump | 4 Temporal | Implausible (jump) caused by Missing (fix) | Environment / sensor |
| Incorrect altitude from GPS | 6 Calibration | Biased | Sensor (intrinsic GPS-Z noise) |
| Uncalibrated barometer | 6 Calibration | Biased | User / sensor |

Notice how cleanly they spread across layers 1, 2, 4, 5, 6, 7. That's a good sign the layering reflects real structure rather than being arbitrary.

---

## Where the taxonomy strains (worth being honest about)

A few cases don't fit cleanly, and I think it's worth flagging them rather than pretending the scheme is airtight:

The **GPS-jump-at-start** case is really *two* errors: a layer-4 "missing fix" that becomes a layer-4 "implausible jump" the moment a fix arrives. You have to decide whether to record it as one event or two.

**Wrist HR locking onto cadence** is layer 5 (cross-signal) when cadence is also recorded, but layer 3 (just an implausible HR trace) on a run with no cadence sensor. The same underlying physical failure shows up at different layers depending on what else was recorded. This isn't a bug in the taxonomy, but it means error *detection* depends on context in ways the taxonomy hides.

**Auto-pause failures** straddle layer 7 (mislabeled — should have been paused) and layer 4 (a long run of identical positions/zero speed is itself a temporal anomaly). You'd want to detect it at layer 4 and reclassify it as layer 7.

**Developer fields** are awkward because they're an extension mechanism — a malformed developer field is a layer 2 problem, but the *content* of a well-formed developer field can have errors at any layer 3–8. So "developer field error" isn't really one category; it's a flag that can attach to errors at multiple layers.

---

## Suggested deliverable shape

If you're going to operationalize this — say, as an error code namespace for a validator — I'd recommend a structure like:

`<layer>.<nature>.<specific_code>`

e.g. `4.implausible.power_spike`, `7.mislabeled.recording_continued_after_activity`, `1.malformed.missing_eof_crc`, `6.biased.altimeter_uncalibrated`. The first two segments give you the taxonomy; the third is the specific failure mode. This lets you write rules like "auto-fix anything in layer 4 with confidence > X" or "always surface layer 7 errors to the user because we can't disambiguate intent."

Want me to push further on any of these? The places I'd naturally go next are: (a) enumerating the specific codes under each (layer, nature) cell, (b) thinking about *detectability* — which errors can be caught from the file alone vs. needing reference data like a route or another device's recording, or (c) thinking about *repair strategies* per cell (drop / interpolate / flag / split / require user input).
