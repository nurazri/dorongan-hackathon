# Dorongan — Possession Lab, Control v5

## Final method

The submitted method is frozen Control v5: an offline, deterministic state machine that predicts Barcelona possession (H), Athletic Club possession (A), dead ball (D), or abstention (X) for each of the 199,319 tactical-video frames. The primary development objective is the organiser's whole-possession spellF1; macroF1 is secondary. No manual corrections are applied to the output. Control v6 was evaluated and rejected; it does not participate in submission inference.

## Inputs and alignment

Inference reads only the supplied tactical automatic-tracking TXT, tactical tracking/team metadata XML, and automatic tactical Smart Tagging XML. Tracking records are indexed at video frame = record ID minus one. Player/ball coordinates are retained as float32 and converted to pitch metres (105.3 × 68.0) for nearest-team distances. Half windows come from the organiser's published metadata, and state resets between halves. The organiser-published second-half pre-kickoff range [110808, 113742) is exported as D. Other ungraded ranges remain X.

Only automatic set-piece intervals are used from Smart Tagging, as contextual evidence. Team ownership is never copied from event tags. Tactical video supports local inspection only. Neither video, homography, broadcast tracking nor broadcast video is used by inference. Broadcast has a separate, unsynchronised timeline and an unresolved one-frame discrepancy between video and tracking. No competition assets or extracts are sent to hosted model APIs.

## Possession and stoppage rules

Team control requires a ball within 2.5 m of a tracked player, a distance advantage of at least 0.75 m over the nearest opponent, and 0.4 s of consecutive supporting observations. When measured ball speed exceeds 12 m/s, proximity must be within 1.2 m. If the opposing team's tracks are absent, control is not established from that absence. Confirmed control is backdated to the beginning of the supporting run. Brief contacts, loose balls and contested observations retain the previous controlled team. Missing or ambiguous evidence interrupts pending confirmation.

Ball speed is endpoint displacement over a fully observed 0.48 s window; missing observations are never interpolated. A stoppage is supported by a ball at least 0.3 m outside the pitch for 0.2 s, a settled ball at least 3 m from visible players for 0.75 s, or a settled ball in automatic set-piece context for 0.6 s. Settled means measured speed at most 0.6 m/s. Missing ball observations alone never imply D.

A confirmed D state persists until an observed inbounds ball moves at least 1.5 m/s within 4 m of a player for 0.12 s. Restart ownership requires the measured nearest-team advantage; otherwise the model abstains. Restart boundaries come from observations, not event-interval boundaries. After two seconds of missing ball observations, output is X while the internal state is retained. Under the official scorer, X is a miss for graded-frame macroF1 and is forward-filled within the half for spellF1; abstention is not an accuracy claim.

## External calibration, datasets and rejected experiments

The external source is Sportec/IDSSE: Bassek, Rein, Weber & Memmert (2025), *An integrated dataset of spatiotemporal and event data in elite soccer*, dataset DOI [10.6084/m9.figshare.28196177.v1](https://doi.org/10.6084/m9.figshare.28196177.v1), CC BY 4.0. Reference labels are supplied DFL/Sportec BallStatus and BallPossession fields mapped mechanically to D and H/A. The source does not identify individual annotators. Our team did not create or correct labels on the competition match. Position/team observations and reference labels are loaded through separate paths; event XML is not used.

V5 requires no learned weights. Eleven predefined alternatives, including unchanged v2, were compared on 20,828 first-half frames from external development match J03WOH. Selection maximised mean official spellF1 over native observations and seeded 35% block occlusion, using macroF1 to break ties. The selected change was settled-far-ball confirmation from 1.5 s to 0.75 s. Other control parameters were retained. The frozen values and provenance are in models/possession_control_v5.json. Competition public/private labels were not used for parameter selection.

The earlier v3 learned experiment used 48,596 distinct J03WOH first-half frames, duplicated once with synthetic occlusion to form 97,192 training rows. Its temporal penalty used the remaining 20,828 first-half frames. It improved some per-frame scores but did not beat v2 on the development second-half possession metric, so it was rejected. A constrained gap-fill v4 experiment selected its unchanged-v2 control and was also rejected. Neither model supplies features or weights to v5.

V5 was frozen before two predeclared validation matches were acquired: J03WPY (146,211 cached rows including the period separator) and J03WR9 (146,810 rows). Both final held-out matches, J03WN1 and J03WOY, remain unopened.

| External validation | v2 spellF1 | Final v5 spellF1 |
|---|---:|---:|
| J03WPY, native | 0.5341 | 0.5408 |
| J03WPY, 35% block-missing | 0.4337 | 0.4403 |
| J03WR9, native | 0.5604 | 0.5644 |
| J03WR9, 35% block-missing | 0.4745 | 0.4831 |

After these results, v6 tested path-based motion estimation and tolerance of 0.08 s neutral interruptions. Three fixed ablations were selected on the same development tuning slice. The combined candidate improved development and synthetic scores but regressed in all four native/block-missing validation comparisons: 0.4931, 0.4243, 0.5089 and 0.4501 respectively. V6 was rejected without retuning on validation results. Those validation matches were reused, not fresh held-out evidence. CONTROL-V6.md documents the experiment.

## Limitations

Planar proximity cannot reliably distinguish controlled reception from every rebound or aerial duel. Tracking gaps can conceal a turnover, stoppage and restart. Stationary balls and repositioning can resemble stoppages or restarts; automatic set-piece tags can be wrong. Endpoint displacement can understate movement that returns toward its starting location. Track fragmentation and absent opposing tracks limit control evidence. A high abstention rate does not establish quality.

External reference conventions and tracking quality differ from this competition. Both validation games share a team with development; synthetic corruption is not an independent game and does not reproduce every tracking failure. The small v5 proxy-data gains do not establish statistical significance or performance on the competition's private full-match labels. No competition score is claimed.

## Reproduction and exact file identity

Use Python 3.12 (verified with 3.12.14), NumPy 2.3.5 and pandas 3.0.1. The submission path needs no Node, browser, external dataset, model training or UI cache. From the source repository root:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-lab.txt
.venv\Scripts\python.exe lab/export_submission.py --data-dir "C:\path\to\data" --output "submission.csv"
.venv\Scripts\python.exe evaluation/validate_submission.py submission.csv
```

The data directory must contain tactical/BAR-ATH_tactical_atd.xml, tactical/BAR-ATH_tactical_atd.txt and tactical/BAR-ATH_tactical_smart_tagging.xml. On macOS/Linux use .venv/bin/python. The filename may be changed to the registered team name without changing the bytes. Export performs official format validation and refuses to write an output whose SHA-256 differs from the frozen submission:

`0c9d0d83918031d97ba8d557ce863145b585e80894163c6a569c23f234d8969d`

The CSV contains exactly 199,319 ordered rows, frames 0–199318, with only H/A/D/X labels. The full test suite runs with `python -m unittest discover -s lab -p "test_*.py" -v` after preparing local viewer caches; HTTP integration tests require those caches and the tactical video. Exporter parsing tests alone run without match assets: `python -m unittest discover -s lab -p "test_submission_export.py" -v`. START-HERE.md covers the optional Angular viewer. The unchanged official scorer/validator and MIT licence are retained. Source releases exclude match assets, local paths, videos, screenshots, tracking caches, private ground truth and the final competition CSV; upload that CSV only through the organiser's submission form.
