# Dorongan — Possession Lab

**Team:** Dorongan  
**Selected algorithm:** Control v5  
**Possession file:** `dorongan.csv` (in the same folder as this document)

## Project description

Possession Lab analyses football tracking data to identify which team controls the ball in each video frame. It produces a CSV with home possession (`H`), away possession (`A`), dead ball (`D`), or abstention (`X`). A local Angular interface synchronises tactical video, player and ball positions, possession states, and a shared timeline so users can inspect the algorithm's decisions and export the final predictions.

The submission contains 199,319 predictions for the Barcelona–Athletic Club match. Control v5 generates the labels automatically using a deterministic state machine, with no manual label edits.

## Required software and dependencies

Install the following software before starting. Commands below assume Windows PowerShell and are run from the repository root (the folder containing `package.json` and `requirements-lab.txt`).

| Software | Project version | Purpose |
|---|---|---|
| Python | 3.12; verified project runtime 3.12.14 | Prediction algorithm, CSV export, validation, local HTTP server |
| pip and venv | Included with a standard Python installation | Install dependencies in an isolated environment |
| NumPy | 2.3.5 | Numerical processing of tracking observations |
| pandas | 3.0.1 | CSV processing and official validation |
| Node.js | 24.15.0 | Build and launch the Angular viewer |
| npm | 11.12.1 | Install the viewer's locked JavaScript dependencies |
| Web browser | A modern browser | Open the local viewer |

Python, NumPy and pandas are sufficient to reproduce and validate the submission. Node.js, npm, Angular and a browser are needed for the viewer. Install Python and Node.js on the machine; the commands below install the project libraries. Git is optional for cloning the source; an extracted source archive also works.

The Angular application uses these versions from `ui/package-lock.json`:

| Package | Locked version |
|---|---|
| `@angular/core` | 22.2.4 |
| `@angular/cli` | 22.2.5 |
| `@angular/build` | 22.2.5 |
| `typescript` | 6.0.3 |
| `rxjs` | 7.8.2 |
| `tslib` | 2.9.1 |


`npm --prefix ui ci` installs Angular, its local CLI/compiler/build tools, TypeScript, RxJS, tslib and the remaining dependencies from the lockfile. A global Angular CLI installation is unnecessary. Use `requirements-lab.txt` for the pinned Python dependencies.

## Install and reproduce the CSV

1. Obtain the project source and the organiser's authorised match-data bundle.
2. Open PowerShell in the repository root.
3. Create the Python environment and install the pinned dependencies:

```powershell
python --version
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lab.txt
```

If Windows does not recognise `python`, use `py -3.12` for the first two commands. The remaining commands call the virtual environment directly and do not require activation.

For direct CSV generation, the data folder must have this structure:

```text
<data-folder>/
  tactical/
    BAR-ATH_tactical_atd.xml
    BAR-ATH_tactical_atd.txt
    BAR-ATH_tactical_smart_tagging.xml
```

Replace `C:\path\to\data` below with the folder containing `tactical`:

```powershell
.\.venv\Scripts\python.exe lab/export_submission.py --data-dir "C:\path\to\data" --output "dorongan.csv"
.\.venv\Scripts\python.exe evaluation/validate_submission.py dorongan.csv
```

The exporter uses the frozen configuration in `models/possession_control_v5.json`. It checks the official CSV format and expected checksum before writing the output. No UI build, training run, external dataset, video or viewer cache is required for this route.

## Install and run the Angular viewer

First complete the Python installation above. The viewer setup requires the complete nine-file participant bundle: tactical and broadcast MP4 video, ATD XML metadata, ATD TXT tracking and homography CSV for both cameras, plus tactical Smart Tagging XML. Keep the original filenames. The setup script searches the supplied directory recursively.

```powershell
node --version
npm --version
npm --prefix ui ci
$env:PYTHON = (Resolve-Path .\.venv\Scripts\python.exe).Path
& $env:PYTHON lab/setup_data.py "C:\path\to\hackathon-resources"
& $env:PYTHON starter/baseline.py
& $env:PYTHON lab/build.py
npm start
```

`npm start` builds the Angular application automatically through `prestart`, then starts the Python server. Open **http://127.0.0.1:8765** in the browser. Use Ctrl+C in the terminal to stop it. When starting from a new terminal, set `PYTHON` again before `npm start` so the launcher uses the installed virtual environment. Restart the server after changes to Python server code or generated data, then refresh the browser.

The viewer offers play/pause, playback speed, frame search, fullscreen, a draggable timeline, possession inspection and **Export CSV**. Export downloads the existing Control v5 predictions as **`dorongan.csv`**. Internal research filenames such as `experimental_control_v5.csv` remain in `evaluation/results/`.

For a build without launching the server, run `npm run build`. The local server serves both the built Angular interface and its API; no separate `ng serve` process is needed.

Viewer setup creates `.local/` caches and `local_paths.json`. It may hard-link source data to avoid duplicating large files, so leave the original inputs unmodified. Match data and these local files are excluded from the public source release.

On macOS/Linux, use `.venv/bin/python` instead of `.\.venv\Scripts\python.exe`, and set the launcher variable with `export PYTHON="$PWD/.venv/bin/python"`.

## Submission file and verification

`dorongan.csv` sits beside `Dorongan.md` in the project root. It has the header `frame,label`, followed by 199,319 ordered rows for frames 0–199318, using only H/A/D/X labels. The supplied CSV was copied byte-for-byte from the team's Downloads export.

Expected SHA-256:

```text
0c9d0d83918031d97ba8d557ce863145b585e80894163c6a569c23f234d8969d
```

Check the exact file before upload:

```powershell
.\.venv\Scripts\python.exe evaluation/validate_submission.py dorongan.csv
Get-FileHash .\dorongan.csv -Algorithm SHA256
```

Run exporter parsing tests without match assets:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s lab -p "test_submission_export.py" -v
```

After preparing the full viewer data and caches, run all lab tests:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s lab -p "test_*.py" -v
```

The technical method, assets, external calibration and limitations follow below. The CSV and this document are separate submission uploads; the public repository provides the implementation, frozen parameters and installation instructions. The repository must exclude the restricted match assets, local configuration, caches and generated competition predictions. Preserve the MIT licence and external dataset attribution.

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

After these results, v6 tested path-based motion estimation and tolerance of 0.08 s neutral interruptions. Three fixed ablations were selected on the same development tuning slice. The combined candidate improved development and synthetic scores but regressed in all four native/block-missing validation comparisons: 0.4931, 0.4243, 0.5089 and 0.4501 respectively. V6 was rejected without retuning on validation results. Those validation matches were reused, not fresh held-out evidence. The research implementation remains in `lab/control_v6.py` and `lab/external_control_v6.py`, with machine-readable results in `benchmarks/reports/control-v6/`.

## Limitations

Planar proximity cannot reliably distinguish controlled reception from every rebound or aerial duel. Tracking gaps can conceal a turnover, stoppage and restart. Stationary balls and repositioning can resemble stoppages or restarts; automatic set-piece tags can be wrong. Endpoint displacement can understate movement that returns toward its starting location. Track fragmentation and absent opposing tracks limit control evidence. A high abstention rate does not establish quality.

External reference conventions and tracking quality differ from this competition. Both validation games share a team with development; synthetic corruption is not an independent game and does not reproduce every tracking failure. The small v5 proxy-data gains do not establish statistical significance or performance on the competition's private full-match labels. No competition score is claimed.

