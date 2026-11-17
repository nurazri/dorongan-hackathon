# Generated predictions

This directory holds locally generated CSVs. All CSVs here are ignored by Git; the public repository includes their generators.

After preparing the match data as described in [Dorongan.md](../../Dorongan.md), run these commands from the repository root using the project's Python environment:

```powershell
python starter/baseline.py
python evaluation/run_evaluation.py
```

The first command generates the four nearest-player baselines; the second scores available CSVs in this directory against the public reference labels. [EVALUATION.md](../../EVALUATION.md) defines the metrics. Public labels are for pipeline checks, not model tuning.

To reproduce and validate the final Control v5 submission, follow [Dorongan.md](../../Dorongan.md#install-and-reproduce-the-csv). The team file `dorongan.csv` is kept in the project root beside that document for the separate submission upload.
