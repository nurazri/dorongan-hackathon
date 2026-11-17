# What this project is trying to improve

The Phase 1 deliverable is a reproducible `frame,label` CSV with 199,319 tactical video frames, using H/A/D/X. The competition ranks **whole possessions through spellF1**; macroF1 is the first tie-break. Dead-ball classification matters because stoppages define possession boundaries, not because D accuracy alone is the objective. [Challenge](https://github.com/metrica-sports/more-than-a-hack-2027/blob/main/CHALLENGE.md) · [Evaluation](https://github.com/metrica-sports/more-than-a-hack-2027/blob/main/EVALUATION.md)

The organizer's published full-match baseline floor is spellF1 0.2433. Scores on other datasets cannot be compared to that number to claim a competition gain. Public five-minute labels are for pipeline checks, not model selection. [Evaluation rules](https://github.com/metrica-sports/more-than-a-hack-2027/blob/main/EVALUATION.md)

## Decision rules for further work

1. Use official spellF1 to evaluate candidate changes on permitted external data. Check macroF1, false/missed possessions and boundary timing as supporting diagnostics.
2. Preserve possession through loose/contested balls and distinguish controlled opposition possession from a brief touch. Do not optimize tracking identity or unrelated player statistics.
3. Keep human ownership/status fields out of model inputs. External labels may supervise training, but labels and corrections on the supplied competition match are prohibited.
4. Preserve the exact tactical frame contract, deterministic regeneration, pinned dependencies and technical documentation.
5. Avoid changing the default merely because an experiment improves per-frame accuracy, D F1, coverage or synthetic scores. Require evidence on separately declared match-level validation data.
6. Keep final held-out matches separate. A validation gain on one match is provisional, especially when teams overlap across splits.

External data from other matches is allowed when organizers can inspect it and the technical document explains it. Match assets remain local; source and reproduction instructions must be public for submission. [Rules](https://github.com/metrica-sports/more-than-a-hack-2027/blob/main/RULES.md) · [Submission](https://github.com/metrica-sports/more-than-a-hack-2027/blob/main/SUBMISSION.md)

## This development step

- Audit and stream a checksum-verified Sportec development match into geometry-only observations and separately mapped H/A/D reference labels.
- Compare the current models on real tracking using the unchanged official metric code.
- Train an interpretable geometry/sequence candidate on the first 70% of the development match's first half; select its temporal penalty on the remaining 30% using spellF1.
- Reject the learned candidate as a replacement when higher macroF1 fails to improve possession recovery over v2. A constrained learned gap-fill experiment also includes unchanged v2 as a required no-change control.
- Calibrate only a bounded set of single-parameter v2 variants on the first-half development tuning segment. Freeze the selected configuration before acquiring a separate predeclared validation match.
- Report the untouched-match comparison honestly; a small or mixed result is not a confirmed improvement.

No competition ground truth is used by these development commands. Published metadata such as graded frame windows is used only for alignment/export, never to hand-label possession changes.
