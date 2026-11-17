# Synthetic benchmark and external validation plan

## Run the synthetic suite

```powershell
cd C:\dev\possession-lab
npm run benchmark
```

This creates `benchmarks/reports/synthetic-v1/report.md`, `scores.csv`, `summary.json` and `cases.json`. It runs without the enrolled match bundle: the benchmark imports only model inference and metric code, and generates all observations and reference labels locally. No competition ground truth is loaded. No new package installation is needed beyond the pinned numerical dependencies.

Commands for focused work:

```powershell
npm run benchmark -- --split development
npm run benchmark -- --case clean_control --seed 105
npm run benchmark -- --output benchmarks/reports/reproduction
npm test
```

## What it measures

The frozen suite contains 180 generated 50-second cases across 15 families: control changes, passes, deflections, contested/loose balls, aerial duels, short and long occlusions, boundary stoppages, outliers, sparse tracks, noisy tagging, stationary live play, an ambiguous referee pair, and combined corruption.

Development and validation use disjoint seed sets (0–5 and 100–105). Models receive only ball positions, nearest-team distances and simulated automatic tags. Synthetic reference labels remain in the evaluator. The deliberately indistinguishable referee pair has identical observations but different reference states, so no deterministic model can correctly resolve both from these inputs.

Four unchanged official baseline rules and both research models run on the same observations. The benchmark reuses the unchanged official metric implementation for spellF1, macroF1, dead-ball F1 and transition matching. Coverage and matched-boundary timing are reported alongside missed-transition counts. Per-case predictions and references are stored as segments for diagnosis.

These are feature-level traces with simplified trajectories and discontinuities. They do not establish physically valid ball dynamics or predict competition scores. All cases use a small set of generated schedules. Tags are simulated and often correct by construction; the noisy-tag family probes errors. With only six seeds per family/split, a few geometric configurations can strongly affect the mean. Validation seed results are now visible; further iteration against them makes them regression cases, not an untouched final test.

## First-run findings

On the synthetic validation split:

| Model | spellF1 | macroF1 | Dead-ball F1 | Coverage |
|---|---:|---:|---:|---:|
| Official smooth50 rule | 0.885 | 0.591 | 0.000 | 100.0% |
| Temporal v1 | 0.784 | 0.638 | 0.137 | 100.0% |
| Control v2 | 0.636 | 0.698 | 0.877 | 79.1% |

The numbers show a tradeoff on this suite: v2 identifies generated stoppages better, but its possession-spell score is lower and it abstains more. They do not justify changing the competition default. Long smoothing is favored by these long generated possessions; high spellF1 alone conceals poor dead-ball detection here.

`clean_control` seed 105 produces no matched possessions under the synthetic labels. Its median prescribed-owning-team distance is 3.777 m, beyond v2's 2.5 m eligibility radius. Here "clean" means uncorrupted observations; it does not guarantee physical contact. This exposes a generator/model assumption mismatch, not proof that the threshold should be loosened. Use independent labeled matches to decide which assumption is realistic. No model threshold was changed during benchmark construction or scoring.

## External source recommendation

**Sportec Open DFL / IDSSE** is the strongest candidate found. The [paper by Bassek, Rein, Weber and Memmert (2025)](https://doi.org/10.1038/s41597-025-04505-y) documents seven matches, synchronized position/event data, and ball fields for team possession and active/dead state. The [original Figshare record](https://doi.org/10.6084/m9.figshare.28196177.v1) declares CC BY 4.0. The checked manifest contains 21 XML files totaling approximately 2.63 GB. The initial benchmark task fetched metadata only; subsequent acquisition/evaluation is documented in EXTERNAL-VALIDATION.md.

Use `benchmarks/external/sportec/protocol.json` for fixed match splits, file URLs/checksums, source attribution and the proposed label mapping. `BallStatus=0` maps to D; active frames with possession 1/2 map to H/A. Unsupported reference values stay ungraded. Mapping is proposed from documentation and still needs a raw-file audit.

[Kloppy's Sportec loader documentation](https://kloppy.pysport.org/user-guide/loading-data/sportec/) exposes ball state/owning team and lists the seven match IDs. These reference fields must be separated from input features. Avoid relying on a loader's default alive-only filtering when measuring stoppages.

**Alternatives:** [Metrica sample data](https://github.com/metrica-sports/sample-data) provides anonymized synchronized tracking/events and asks for source acknowledgement. Its README does not establish a continuous H/A/D reference, so event-to-possession conversion would need separate validation. [SkillCorner Open Data](https://github.com/SkillCorner/opendata) documents 10 Hz broadcast tracking with possession fields and derived phases. Their automatic origin, timebase and dead-ball semantics need auditing; treat those as proxy references unless validated. Its software MIT license should not be assumed to settle every data-use question.

## Predeclared external protocol

| Split | Match IDs |
|---|---|
| Development | J03WOH, J03WQQ, J03WMX |
| Validation | J03WPY, J03WR9 |
| Held out | J03WN1, J03WOY |

This split is recorded before reading match observations or references. It separates matches, not necessarily teams. This is the initial pre-data split. Current development and validation results are in EXTERNAL-VALIDATION.md; the final held-out split is still unopened.

The subsequent implementation downloads checksummed development/validation inputs and uses a tested streaming adapter with observations separated from references. See EXTERNAL-VALIDATION.md for the current results. Keep label fields and human event XML out of the prediction path. Native-label definitions still need comparison to this challenge's rules for loose balls, aerial touches and stoppages. Higher-quality external tracking also differs from noisy automatic competition tracking, so native and deliberately corrupted evaluations should be reported separately.

Refresh only the public metadata with `npm run external:manifest`. This command neither downloads match files nor evaluates them. Preserve the dataset authors' attribution and license in any future derived benchmark.
