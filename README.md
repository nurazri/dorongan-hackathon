# Dorongan — Possession Lab

Football possession analysis for the More than a Hack 2027 challenge. The frozen Control v5 algorithm predicts home possession, away possession, dead ball or abstention for every tactical-video frame. An optional Angular viewer synchronises video, tracking and possession inspection, and exports `dorongan.csv`.

**Start with [Dorongan.md](Dorongan.md)** for the project description, required software, pinned dependencies, installation, CSV reproduction, viewer setup, technical approach, external calibration and limitations.

## Reference documentation

- [Challenge](CHALLENGE.md): label meanings and possession semantics.
- [Data](DATA.md): organiser asset formats and frame alignment.
- [Evaluation](EVALUATION.md): official scoring and validation.
- [Rules](RULES.md): competition and data-use requirements.
- [Licence](LICENSE): MIT licence for the code.

The organiser's [submission instructions](https://github.com/metrica-sports/more-than-a-hack-2027/blob/main/SUBMISSION.md) describe the form and deliverables. Upload the team CSV and technical document separately and supply this repository's public URL.

Match assets, local caches, exported predictions and generated baseline CSVs stay local. The baseline generator is retained in `starter/baseline.py`; see [evaluation/results](evaluation/results/README.md) for commands. Machine-readable research results remain in `benchmarks/reports/`.
