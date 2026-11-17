# Dorongan — final submission, Control v5

The selected algorithm is Control v5. Control v6 remains a rejected research experiment and must not replace the final CSV or active viewer model.

## Files to provide

1. The team-named CSV, containing the unchanged frozen v5 output.
2. A public repository URL containing the supplied clean source release.
3. The team-named technical document (Markdown is explicitly accepted by SUBMISSION.md).

The possession CSV SHA-256 is:

`0c9d0d83918031d97ba8d557ce863145b585e80894163c6a569c23f234d8969d`

It must validate as 199,319 frames, numbered 0–199318. Rename the CSV and document to the registered team name if they have provisional filenames; renaming does not change the CSV hash. Do not substitute another research CSV.

## Reproduce

Install requirements-lab.txt in Python 3.12, then run:

```powershell
python lab/export_submission.py --data-dir "C:\path\to\data" --output "submission.csv"
python evaluation/validate_submission.py submission.csv
```

Only the tactical ATD metadata, raw tracking and Smart Tagging files are needed. See START-HERE.md for directory layout. The exporter checks the expected hash and official CSV contract before writing the destination.

## Publishing the source

Extract the clean source ZIP into a new directory and publish that directory as the team's public source repository. The ZIP contains source, frozen parameters, dependency lock, licence, technical documentation and external-validation reports. It excludes competition assets and extracts, video/image previews, generated predictions, local paths, private ground truth, installed dependencies and Git history. The organiser's starter repository URL is not a substitute for the team's modified implementation.

The source ZIP itself is not one of the form's public-URL fields; publish the source and supply its URL. Final CSV and technical document are separate uploads. The full preparation ZIP is a private handoff bundle, not material to publish wholesale.

## Submission status

Preparing files does not submit the Google Form or publish a repository. The registered team name is Dorongan. Source publication and form submission are deferred to the team; no commit or push is requested. Use Dorongan.csv and Dorongan.md for the uploads. Use one form response per team and upload the exact validated CSV. The repository's organiser instructions list November 17, 2026 as the deadline; consult the emailed form for the applicable time.
