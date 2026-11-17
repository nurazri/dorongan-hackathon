# Hackathon-aligned external validation

Validation match: J03WPY. Candidate frozen before its tracking and labels were downloaded.
Primary criterion: unchanged official possession spellF1. macroF1 is secondary. No parameters are fit or selected by this evaluator.

| Input | Model | spellF1 | macroF1 | D F1 | Matched spells @ IoU .5 | False spells | Missed spells |
|---|---|---:|---:|---:|---:|---:|---:|
| native | baseline_smooth50 | 0.3171 | 0.3954 | 0.0000 | 123 | 252 | 298 |
| native | experimental_control_v2 | 0.5341 | 0.8823 | 0.9471 | 197 | 101 | 224 |
| native | possession_control_v5 | 0.5408 | 0.8871 | 0.9529 | 200 | 98 | 221 |
| masked35 | baseline_smooth50 | 0.2392 | 0.3930 | 0.0228 | 123 | 456 | 298 |
| masked35 | experimental_control_v2 | 0.4337 | 0.7966 | 0.8631 | 151 | 93 | 270 |
| masked35 | possession_control_v5 | 0.4403 | 0.8065 | 0.8765 | 152 | 92 | 269 |

## Decision

Small validation-supported candidate; further match-level confirmation required.

- One validation match, with a team also present in development.
- DFL reference and corrected tracking differ from competition data; scores are not comparable across datasets.
- Masked35 is a synthetic corruption condition, not a second independent match.
- Small gains on a single match do not establish statistical significance or competition improvement.

The sequence-emission v3 candidate and learned gap-fill v4 experiment remain research artifacts; neither is presented as a gain over v2 in the hackathon ranking metric.
The v5 calibration changes only the settled-far-ball confirmation duration. It was selected from a fixed, bounded set of single-parameter alternatives on a different development match.
Final held-out matches remain untouched. No competition public labels were used for training, calibration or selection.
