# Verification record

Completed on 31 October 2026 using Python 3.12.14, NumPy 2.3.5, pandas 3.0.1, Node 24.15.0 and npm 11.12.1.

- All nine expected match assets located locally; original downloads preserved.
- Tactical video metadata: 1920×1080, 25 fps, 199,319 frames.
- Tactical tracking: 199,319 sequential records; 113,488 ball observations.
- Tactical homography: 199,319 sequential rows, all marked valid.
- Broadcast tracking/homography: 164,488 rows. Broadcast video metadata: 164,487 frames. Discrepancy unresolved; broadcast excluded from inference.
- All four official baselines regenerated; their files match the original repository (no Git diff).
- Experimental and default baseline CSVs pass the official validator.
- Official public evaluation reproduces documented baseline scores. The experiment is weaker on the public sample; no parameter tuning followed this check.
- Experimental CSV independently rebuilt with identical SHA-256: `e75e7e65ea62445496f436e834fd77b1d5c1d5bbaf5ede01b3fdcd23d12ef2f2`.
- Eight Python unit/integration tests pass: synthetic temporal behavior, bounded tracking windows, exact video byte ranges, CSV export identity, unsafe export path rejection, external Host rejection.
- Angular production build passes with strict template/type checking.
- Browser verification: video ready at 1920×1080 without a media error, one-frame stepping, second-half kickoff seek, model selection and matching export link.
- Desktop visual review and 390-pixel responsive check completed with restricted match content hidden. No horizontal page overflow found at the mobile breakpoint.
- Restricted input files, local path configuration, derived caches and experimental prediction output are ignored by Git. No remote repository publication or competition submission occurred.

These checks establish a functioning local pipeline and viewer. They do not establish competitive full-match model quality. Dead-ball inference and controlled-possession transitions remain the main research work.


## Control v2 follow-up — 31 October 2026

- Added 15 synthetic control/stoppage scenarios and a v2 export/evidence API check; all 24 tests pass.
- Full-match v2 CSV passes the unchanged official validator.
- Independently regenerated v2 with SHA-256 `fa34aa00363a28b193cad34e82b63eabd8063a9881cc6ef968214af14b133356`. V1 output remains byte-identical.
- Angular production compilation passes with the new evidence inspector.
- Browser check confirms Control v2 selection, five evidence fields and matching export URL. Restricted match assets are hidden in the saved interface preview.
- The public ground truth was not read, scored, or used to choose parameters during this follow-up.
- Full-match competitive improvement remains unverified. See CONTROL-V2.md.


## Synthetic benchmark follow-up — 31 October 2026

- Built 180 deterministic scenarios across 15 families, yielding 1,080 scores for the four baseline rules and two frozen research models.
- All 33 unit/integration tests pass, including oracle scores, all-abstention scoring, known transition delays, prediction-path isolation from files/labels, seed separation and ambiguous paired observations.
- Reused the unchanged official metric implementation. No competition ground truth was read or scored.
- Factored v1 inference into a shared module so benchmark and match processing execute the same model implementation.
- The first benchmark records a whole-possession weakness in Control v2 despite better generated-stoppage detection. No thresholds were changed based on these results.
- Selected Sportec/IDSSE for the next external validation stage and fetched public metadata only; match-level splits and feature/label separation are predeclared.

- Final report.md, summary.json, cases.json and scores.csv were regenerated independently with identical bytes. Existing v1/v2 match CSV hashes remain unchanged after the shared-inference refactor.
- Clarified that the uncorrupted synthetic family can prescribe ownership beyond physical close-contact assumptions; this is not evidence to loosen thresholds. No model parameters were changed.


## Hackathon goal recheck and external validation — 31 October 2026

- Rechecked current CHALLENGE, EVALUATION, RULES and SUBMISSION: whole-possession spellF1 is primary; macroF1 is secondary; no competition public-label tuning. See HACKATHON-ALIGNMENT.md.
- Checksummed and streamed J03WOH (development, 137,214 frames) and J03WPY (separate validation, 146,211 frames). Geometry and label paths are separate; both periods remain isolated.
- Rejected v3 as a replacement despite higher macroF1; constrained v4 selection retained its unchanged-v2 control.
- A fixed 11-alternative, single-parameter calibration selected settled-far-ball confirmation 0.75 s using first-half external development spellF1. Configuration frozen before validation acquisition.
- On J03WPY, v2→v5 spellF1 is 0.5341→0.5408 native and 0.4337→0.4403 masked35. These small single-match gains are provisional, not claimed competition gains.
- Generated and officially validated experimental_control_v5.csv (199,319 rows). Original v1/v2 files remain available.
- No competition ground truth scored; final held-out matches remain unopened. External reproduction commands and provenance are retained.

- Final 47 tests pass, Angular production compilation passes, and the new selector/export were verified in the browser with restricted assets hidden.
- Repeated calibration JSON and competition CSV are byte-identical. V5 CSV SHA-256: 0c9d0d83918031d97ba8d557ce863145b585e80894163c6a569c23f234d8969d. Original v1/v2 hashes remain unchanged.
- Fixed an observed preview/rebuild race by atomically replacing generated tracking and summary caches; reran affected checks successfully.

## Final Control v5 release — 16 November 2026

- Selected Control v5; rejected the separately preserved v6 experiment after four native/block-masked external-validation regressions. No retuning followed those results.
- Added lab/export_submission.py for a cache-independent, v5-only reproduction path from the three tactical tracking/tagging inputs. It never opens reference labels or external datasets.
- Regenerated all 199,319 rows with the exact frozen SHA-256: 0c9d0d83918031d97ba8d557ce863145b585e80894163c6a569c23f234d8969d.
- All 75 Python model, parsing and HTTP integration tests passed. The Angular production build passed.
- Final viewer retains v5 with combined tactical/tracking player and shared draggable timeline, playback controls and frame search. Older interface verification entries above are historical, not descriptions of the current controls.
- Updated TECHNICAL.md, START-HERE.md, README.md and FINAL-SUBMISSION.md. Clean source release excludes local assets, image previews, caches, generated competition CSVs and Git history.
- Exact upload validation, clean-source extraction/reproduction and artifact checksums are recorded in the handoff package's manifest. Those checks establish format and reproducibility, not competitive accuracy.
- No competition public/private ground truth was used for this finalisation. No repository publication or competition form submission was performed.
