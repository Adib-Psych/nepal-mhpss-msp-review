# Publishing rules · MSP Nepali translation review space

Set 23 November 2026. Read before any change.

## What goes on this site
1. **Units that passed both checks.** A unit file goes into `data/units/` only when the automatic gate (`msp_qc.py`, contract `msp-unit/v1`) passes for its phase and Claude's review QC is done. The file is byte-identical to the file in the working folder on Luna (compare SHA-256). Its unit ID is then added to that document's `units` list in `data/site.json`.
2. **Drafts are shown as drafts.** "Not yet proofread" is never a reason to keep a draft off this site or to take it down: this site is where native proofreading happens. Proofreading and clinical clearance are the gate for any later official use, not for this site.
3. **Layout previews** (`data/preview/`) are earlier drafts shown only to preview the layout, labelled as such. A preview is removed when the document's new draft is published.

## Who does what
| Who | Does |
|---|---|
| Hermes | Produces drafts in the working folder only. Never publishes to this repository. |
| Claude | QC, publication, page structure, tests. |
| Adib | Decides on content, reviewers, the review round and anything sent in his name. |

## Taking content down
Removing anything that is live needs Adib's own words naming that item or group. One question per group, never bundled.

## Before every push
1. `python3 tests/site_check.py` passes against a local server (data integrity, no JavaScript errors, no horizontal scroll at 390 and 768 px, running text fills its container at 1440 px).
2. Partner-facing text only: no internal paths, agent names or working notes.
3. Licence conditions of the MSP are kept: no organisational or donor logo; the IASC disclaimer stays on the About page; the final translation will carry it in Nepali.

## Reviewer checks
Until the review round opens, `SEND_ENABLED` in `index.html` is `false` and checks stay in the reviewer's browser. Opening the round (storage of checks for the review team) is a separate change recorded with a checkpoint.
