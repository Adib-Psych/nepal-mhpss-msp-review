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
4. Visual identity (23 Nov 2026): colours and fonts follow the MSP palette (www.mhpssmsp.org; sector colours from the colour guide on page 2 of the MSP manual). No MSP or IASC logo and no look-alike of it: the MSP licence asks that no use suggests IASC endorsement, and this site holds unofficial drafts. A logo can be added only with written permission from the IASC MHPSS Reference Group.

## Reviewer checks
Until the review round opens, `SEND_ENABLED` in `index.html` is `false` and checks stay in the reviewer's browser. Opening the round (storage of checks for the review team) is a separate change recorded with a checkpoint.

## Review round (built 24 November 2026)
- **Design (owner decisions, 24 Nov 2026).** Each of the 90 sections is a review package. Every package needs two stages by two different people: language (professional translator) and MHPSS technical. Packages with safety rows (77) also have a clinical stage, which covers their safety rows. Stages run at the same time on the draft; rows where they disagree go to reconciliation.
- **Where it runs.** Firestore of project `mhpss-nepal-iec-review`, collections `msp*`, beside the IEC and form proofreading collections. The page talks to it through the REST API, as the IEC review site does.
- **Identity.** Each reviewer gets a personal link with a secret key (`#k=…`). The page stores the key in the browser and removes it from the address bar. The database holds the reviewer code, roles and an active flag; names and emails stay in the review team's local register.
- **Enforced by the server rules, not by the page:** one person one stage per package; a stage only for a reviewer holding that role; a claim holds the package stage for 3 days, then lapses; checks only while holding a live claim; completed stages cannot be reopened from the page.
- **Tests.** `tests/round_check.py` (end to end against a local emulator; the page honours `?emu=` only on localhost). The rules have their own emulator suite with the IEC and form collections as regression checks. Run both before any change to the round.
- **Opening the round** is still a separate change with a checkpoint: set `SEND_ENABLED` to `true`, issue reviewer links from the CMC-Nepal list, and confirm how reviewer details are stored.
