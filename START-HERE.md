# Possession Lab — final Control v5

Control v5 is the selected submission and the app's active model. V6 was tested and rejected after external-match spellF1 regressions. The final inference parameters are frozen; no further tuning is needed.

## Reproduce the submission

Use Python 3.12 with the pinned numerical dependencies. No UI build, external training data, video or local cache is required for CSV generation.

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements-lab.txt
.venv\Scripts\python.exe lab/export_submission.py --data-dir "C:\path\to\data" --output "submission.csv"
.venv\Scripts\python.exe evaluation/validate_submission.py submission.csv
```

`--data-dir` is the folder containing `tactical/`. Required files within that subfolder are `BAR-ATH_tactical_atd.xml`, `BAR-ATH_tactical_atd.txt`, and `BAR-ATH_tactical_smart_tagging.xml`. Alternatively omit the option and put the assets under `data/` or set `MTAH_DATA_DIR`. On macOS/Linux replace `.venv\Scripts\python.exe` with `.venv/bin/python`.

Export verifies official format and exact SHA-256 before writing the final file:

`0c9d0d83918031d97ba8d557ce863145b585e80894163c6a569c23f234d8969d`

Name the final CSV and technical document after the registered team. See TECHNICAL.md for the method and provenance, FINAL-SUBMISSION.md for packaging, and SUBMISSION.md for the organiser's file contract.

## Optional local viewer

The Angular app combines tactical video and the tracking pitch in one player, with a shared draggable timeline, play/pause, speed, fullscreen and frame search. The inspector shows possession and distances. Export downloads the existing v5 CSV; there is no manual label editor.

From a fresh checkout, with the complete nine-file enrolled-participant download:

```powershell
python lab/setup_data.py "C:\path\to\hackathon-resources"
python starter/baseline.py
python lab/build.py
npm --prefix ui ci
npm run build
npm start
```

Use Node 24.15.0/npm 11.12.1, the versions used by the existing project. Open http://127.0.0.1:8765. The server binds to this computer only. Run commands from the repository root. If needed, set `PYTHON` to the installed Python executable before using npm launch commands. Stop with Ctrl+C; restart after rebuilding data so the server reloads its cache.

Setup may hard-link match files to avoid copying large videos. Do not modify linked inputs. Local absolute paths are kept in ignored `local_paths.json`. Missing videos do not affect the direct submission exporter.

## Verification and research

```powershell
python -m unittest discover -s lab -p "test_*.py" -v
npm run build
```

The full suite includes HTTP integration tests requiring local viewer caches and video. Exporter parsing tests alone run without match assets: `python -m unittest discover -s lab -p "test_submission_export.py" -v`. The official scorer is retained, but the competition public five minutes must not be used for fitting, calibration or model selection. Submission export never reads public/private ground truth or external labels. EXTERNAL-VALIDATION.md and CONTROL-V6.md describe the development decisions; the final held-out matches remain unopened.

## Public source

Use the clean source release when publishing. It excludes match assets, prediction CSVs, local configuration, video, image previews, caches, installed dependencies, build output and Git history. Preserve LICENSE and dataset attributions. Do not upload the local checkout or its history wholesale: old tracked preview images are not included in the clean release.

No competition form submission or remote publication is performed by these commands.
