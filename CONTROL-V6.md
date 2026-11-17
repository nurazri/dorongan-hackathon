# Control v6 experiment

Decision: retain Control v5 in the app and export pipeline. V6 failed the predeclared promotion gate; no v6 competition CSV was generated.

## Implementation

V6 retains the v5 physical parameters and forks the control algorithm into a separate research module. It tests two changes independently and together:
- Median-filtered path-length speed over the observed 0.48-second window, rather than endpoint displacement. Missing observations and post-filter steps above 45 m/s invalidate motion. Motion cannot cross half/window boundaries.
- Up to 0.08 seconds of neutral evidence can interrupt confirmation. Neutral frames never count toward the ten supporting control observations; a contrary team resets confirmation. Longer gaps still reset it.

The selected development candidate includes both changes. It does not implement learned touch detection, long-gap inference, new restart states, or local video processing.

## Development selection

Three fixed ablations plus frozen v5 were evaluated on the existing 20,828-frame first-half J03WOH tuning region. Selection used mean official spellF1 across native and seeded masked35 observations; macroF1 broke ties. V5 was not refit.

| Candidate | Mean spellF1 |
|---|---:|
| v5 | 0.5082 |
| motion_only | 0.5275 |
| tolerant_only | 0.5082 |
| combined | 0.5294 |

The candidate and inference-source hash were frozen before v6 validation scores were computed. No changes were selected after those scores became available.

## External evaluation

| Match | Condition | v5 spellF1 | v6 spellF1 | Change |
|---|---|---:|---:|---:|
| J03WOH (second half) | native | 0.5533 | 0.5082 | -0.0451 |
| J03WOH (second half) | masked35 | 0.4366 | 0.4068 | -0.0298 |
| J03WOH (second half) | dropout10 | 0.3765 | 0.3944 | 0.0179 |
| J03WOH (second half) | spikes005 | 0.5333 | 0.4988 | -0.0346 |
| J03WPY | native | 0.5408 | 0.4931 | -0.0477 |
| J03WPY | masked35 | 0.4403 | 0.4243 | -0.0160 |
| J03WPY | dropout10 | 0.3625 | 0.4019 | 0.0394 |
| J03WPY | spikes005 | 0.5385 | 0.4907 | -0.0478 |
| J03WR9 | native | 0.5644 | 0.5089 | -0.0556 |
| J03WR9 | masked35 | 0.4831 | 0.4501 | -0.0331 |
| J03WR9 | dropout10 | 0.4092 | 0.4105 | 0.0012 |
| J03WR9 | spikes005 | 0.5681 | 0.5111 | -0.0569 |

Promotion required positive development gain, no spellF1 regression in either validation match under native/masked35 observations, and at least one positive validation gain. V6 regressed in all four primary validation conditions and on the development second half. Improvements with scattered dropouts do not justify switching.

The 90 existing synthetic validation cases averaged spellF1 0.6330 for v5 and 0.6876 for v6. Synthetic improvement did not transfer to real native/block-masked matches.

## Interpretation and limits

The combined change is not a validated upgrade. Development ablations show that the path-motion change contributed most of the tuning gain; they do not establish which change caused the separate-match regressions. Isolate motion evidence for control versus stoppage/restart detection in a future development-only experiment, rather than assuming all decisions benefit from the same estimator.

The validation matches were already used for v5 and their old summary results were known before v6 design. This is reused validation, not fresh held-out confirmation. Both matches share a team with development. Corruptions are alternate observations of the same games, not independent samples. Sportec tracking and label conventions differ from the competition. Final held-out matches remain unopened. No competition assets, public labels or private labels were read by this experiment.

dropout10 independently hides approximately 10% of ball/distance observations. spikes005 perturbs approximately 0.5% of normalized ball positions and marks associated nearest-player distances unavailable; it is a limited feature-level corruption rather than a simulation of re-tracking. Native/masked35 are the promotion conditions; added corruptions are diagnostics.

## Reproduce

From the project root, with the existing pinned runtime/dependencies and prepared external caches:
```powershell
python lab/external_control_v6.py select
python lab/external_control_v6.py evaluate
python lab/external_control_v6.py synthetic
python -m unittest discover -s lab -p "test_*.py" -v
```

Machine-readable reports retain macroF1, dead-ball F1, transition timing, matched/spurious/missed spells at IoU 0.5, coverage, frozen configuration, and the inference-source hash. The selection command intentionally regenerates only the experimental v6 configuration; it never changes the active app model.
