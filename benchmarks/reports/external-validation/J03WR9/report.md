# Hackathon-aligned external validation

Validation match: J03WR9. Candidate frozen before its tracking and labels were downloaded.
Primary criterion: unchanged official possession spellF1. macroF1 is secondary. No parameters are fit or selected by this evaluator.

| Input | Model | spellF1 | macroF1 | D F1 | Matched spells @ IoU .5 | False spells | Missed spells |
|---|---|---:|---:|---:|---:|---:|---:|
| native | baseline_smooth50 | 0.3152 | 0.4095 | 0.0000 | 108 | 206 | 262 |
| native | experimental_control_v2 | 0.5604 | 0.8772 | 0.9242 | 191 | 110 | 179 |
| native | possession_control_v5 | 0.5644 | 0.8819 | 0.9304 | 192 | 107 | 178 |
| masked35 | baseline_smooth50 | 0.2557 | 0.4087 | 0.0280 | 110 | 396 | 260 |
| masked35 | experimental_control_v2 | 0.4745 | 0.7974 | 0.8359 | 146 | 96 | 224 |
| masked35 | possession_control_v5 | 0.4831 | 0.8085 | 0.8536 | 148 | 93 | 222 |

## Decision

Small validation-supported candidate; further match-level confirmation required.

- One validation match, with a team also present in development.
- DFL reference and corrected tracking differ from competition data; scores are not comparable across datasets.
- Masked35 is a synthetic corruption condition, not a second independent match.
- Small gains on a single match do not establish statistical significance or competition improvement.

The sequence-emission v3 candidate and learned gap-fill v4 experiment remain research artifacts; neither is presented as a gain over v2 in the hackathon ranking metric.
The v5 calibration changes only the settled-far-ball confirmation duration. It was selected from a fixed, bounded set of single-parameter alternatives on a different development match.
Final held-out matches remain untouched. No competition public labels were used for training, calibration or selection.
