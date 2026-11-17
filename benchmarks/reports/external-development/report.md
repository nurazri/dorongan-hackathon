# External development evaluation: possession recovery

Match J03WOH, other than the competition match. The objective is official spellF1; macroF1 is secondary.
The first half supplies training/tuning for v3. Its second half was withheld from fitting and transition-penalty selection.
This is a within-development-match temporal diagnostic, not independent match-level confirmation.

## Second-half diagnostic

| Input | Model | spellF1 | macroF1 | D F1 | Coverage | Matched spells / true @ IoU .5 | False spells | Missed spells |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| native | baseline_raw | 0.0876 | 0.3482 | 0.0000 | 100.0% | 43 / 174 | 897 | 131 |
| native | baseline_smooth25 | 0.2964 | 0.3696 | 0.0000 | 100.0% | 69 / 174 | 201 | 105 |
| native | baseline_smooth50 | 0.3391 | 0.3820 | 0.0000 | 100.0% | 62 / 174 | 112 | 112 |
| native | baseline_smooth125 | 0.2273 | 0.3740 | 0.0000 | 100.0% | 29 / 174 | 61 | 145 |
| native | experimental_temporal | 0.1644 | 0.6356 | 0.6601 | 100.0% | 61 / 174 | 568 | 113 |
| native | experimental_control_v2 | 0.5453 | 0.8574 | 0.9222 | 99.8% | 90 / 174 | 58 | 84 |
| native | possession_sequence_v3 | 0.5153 | 0.8881 | 0.9846 | 100.0% | 77 / 174 | 44 | 97 |
| masked35 | baseline_raw | 0.0469 | 0.4267 | 0.4019 | 100.0% | 26 / 174 | 1027 | 148 |
| masked35 | baseline_smooth25 | 0.1858 | 0.3988 | 0.1412 | 100.0% | 61 / 174 | 443 | 113 |
| masked35 | baseline_smooth50 | 0.2652 | 0.3773 | 0.0274 | 100.0% | 61 / 174 | 207 | 113 |
| masked35 | baseline_smooth125 | 0.2068 | 0.3631 | 0.0000 | 100.0% | 30 / 174 | 92 | 144 |
| masked35 | experimental_temporal | 0.1987 | 0.6263 | 0.6505 | 100.0% | 60 / 174 | 390 | 114 |
| masked35 | experimental_control_v2 | 0.4532 | 0.7644 | 0.8298 | 90.9% | 67 / 174 | 52 | 107 |
| masked35 | possession_sequence_v3 | 0.4258 | 0.8485 | 0.9662 | 100.0% | 61 / 174 | 44 | 113 |

## Alignment with the hackathon

- Predictions concern H/A/D possession states. The metric implementation is the unchanged official scorer.
- Training inputs are ball/player geometry and temporal context only. BallStatus and BallPossession are reference-only fields.
- Candidate transition scales were fixed before scoring and selected by first-half tuning spellF1, with macroF1 as a tie-break.
- No competition public/private ground truth is loaded, and no labels or corrections are written by hand.
- Competition CSV generation remains deterministic and goes through the official file validator.

## Interpretation limits

- One external development match; not the predeclared match-level validation or held-out split.
- Corrected external tracking and label semantics differ from automatic competition tracking.
- Masked35 is label-independent synthetic observation corruption, not proof of competition robustness.
- V3 is a candidate until confirmed on predeclared validation matches. The published baseline remains the application default.
- Masked35 removes blocks of ball observations without changing the external reference labels. Native and corrupted results must not be conflated.

Frozen model SHA-256: `79562534b316bdef0917625eb95c3b01f111ed0daf65d382098ce9f59b86d406`.

Reproduce: `npm run external:fetch`, `npm run external:prepare`, `npm run external:train`, `npm run external:evaluate`.
Raw downloads and prepared arrays remain in ignored .local/. Weights and attributed provenance are in models/possession_sequence_v3.json.
