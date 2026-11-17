# Real-data progress against the hackathon objective

The decision criterion is **whole-possession spellF1**, followed by macroF1. See HACKATHON-ALIGNMENT.md for the checked organizer requirements. The goal is a reproducible 199,319-frame possession CSV; the Angular app supports inspection rather than competition scoring.

## Data and separation

We acquired checksummed Sportec/IDSSE source metadata and raw observed positions for development match **J03WOH** and predeclared validation matches **J03WPY** and **J03WR9**. All are external to the competition game. The adapter streams XML twice, reduces player geometry to nearest-team distances, checks native 25 fps alignment and resets between halves. No event XML is used.

BallStatus and BallPossession produce reference H/A/D labels in a separate path. Model observations contain positions, team membership, frame/period alignment and pitch dimensions. Tests verify that changing reference ownership/status leaves the inference features unchanged. Unknown references remain ungraded rather than being guessed.

Source: Bassek, Rein, Weber & Memmert (2025), [dataset DOI](https://doi.org/10.6084/m9.figshare.28196177.v1), CC BY 4.0. Labels are supplied DFL/Sportec reference fields; no labels were created or corrected by our team. The source does not provide individual annotator identities. Attribution and input checksums are retained in the public protocol/model metadata.

The two final held-out matches J03WN1 and J03WOY remain unopened; loaders reject them. J03WPY and J03WR9 were acquired only after freezing the calibrated configuration. No competition public/private reference labels were used for model fitting, calibration or selection.

## Experiments and selection

1. **Unchanged v2:** evaluated against the official baseline on development tracking and label-independent 35% block occlusion. It improves spellF1 on this external match despite its weaker earlier synthetic result, demonstrating why synthetic ordering cannot select the submission.
2. **Sequence v3 research model:** trained position-only emissions on the first 48,596 frames of J03WOH's first half. Native plus synthetically occluded observations provide 97,192 training rows, without introducing additional distinct reference frames. Four fixed transition scales were selected on the remaining 20,828 first-half frames, using mean spellF1 over native and masked observations. Better per-frame scores did not beat v2's second-half spellF1, so it was rejected as a replacement.
3. **Gap-fill v4 research experiment:** permitted learned evidence to fill observed v2 abstentions while preserving known decisions. The development selection included an unchanged-v2 control and selected that no-change option. It is not presented as an improvement or exposed as a new competition candidate.
4. **Control v5 candidate:** evaluated 11 predefined alternatives, each changing at most one v2 parameter. Selection used the same 20,828 external development tuning frames and official spellF1, with macroF1 as tie-break. The selected change is settled-far-ball confirmation **1.5 s → 0.75 s**. All other v2 parameters remain unchanged. Its configuration was frozen before reading J03WPY.

Research code and model artifacts are inspectable. V3 weights are not part of v5 inference. V5 needs only its frozen parameter JSON and the original control algorithm to regenerate predictions.

## Separate validation-match results

The frozen candidate was also tested on the second predeclared validation match, **J03WR9**, with no parameter changes. On native observations, spellF1 was 0.3152 for the baseline, 0.5604 for v2, and **0.5644 for v5**. With 35% block masking, it was 0.2557, 0.4745, and **0.4831** respectively. Dead-ball F1 for v5 was 0.9304 native and 0.8536 masked. The small spellF1 gain repeated, but these matches still do not establish a competition full-match score.

### J03WPY

| Input condition | Published baseline rule | Control v2 | Calibrated v5 |
|---|---:|---:|---:|
| Native tracking spellF1 | 0.3171 | 0.5341 | **0.5408** |
| 35% block-missing observations spellF1 | 0.2392 | 0.4337 | **0.4403** |

On J03WPY native observations, matched possessions at IoU 0.5 increase from 197 to 200; false and missed possessions each decrease by three. Both validation matches have a team shared with development and do not establish significance or competition performance. Each masked condition is a corruption test on the same game, not another independent match.

DFL's label conventions and high-quality tracking differ from the competition's automatic tracking. These scores cannot be compared to the organizer's published 0.2433 full-match baseline number to claim a competition win. Competition full-match quality remains unknown.

## Inspect the candidate

```powershell
cd C:\dev\possession-lab
npm start
```

The Angular interface displays Control v5 only. Export downloads the existing `experimental_control_v5.csv` produced by the algorithm. The reference baselines remain available in the research code and reports.

For the competition input, this calibration changes 45 frames relative to v2. This is a mechanical output difference, not a statement that those frames became correct. The new file passes official format validation and must remain excluded from the public source repository.

## Reproduction

The existing project includes verified caches and frozen model JSON files. Competition CSV rebuilding does not require downloading external data again:

```powershell
npm run rebuild-data
npm test
```

To reproduce external development and validation from public source:

```powershell
npm run external:fetch
npm run external:prepare
npm run external:train
npm run external:evaluate
npm run external:gapfill
npm run external:tune
npm run external:fetch -- --match J03WPY --allow-validation
npm run external:prepare -- --match J03WPY --allow-validation
npm run external:validate
npm run external:fetch -- --match J03WR9 --allow-validation
npm run external:prepare -- --match J03WR9 --allow-validation
npm run external:validate -- --match J03WR9
```

`external:train` is the retained v3 experiment; `external:tune` recreates the actual v5 candidate. Network acquisition verifies original MD5 values and keeps all raw data under ignored `.local/external/`. Training, calibration and validation commands are separated so evaluation does not silently refit a model.

Detailed reports: `benchmarks/reports/external-development/` and `benchmarks/reports/external-validation/J03WPY/` and `benchmarks/reports/external-validation/J03WR9/`. The original pre-data split manifest remains in `benchmarks/external/sportec/protocol.json`; its initial status string is historical, not live acquisition state.

## What remains relevant

The frozen candidate showed a small spellF1 gain on both predeclared validation matches. The poor dead-ball recall on the competition public window did not repeat on either external match, so that window does not justify a parameter change. Larger future changes should target missed or falsely split possessions through observation gaps and uncertain restarts. Do not pursue higher dead-ball F1 or coverage alone, expand the UI for its own sake, or tune using the competition public sample.
