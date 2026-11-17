# Control v2 — sustained control and observed stoppages

This is a second experimental candidate, not a demonstrated competitive improvement. It is available as **Control v2 · experimental** in Angular. The published baseline remains the default.

## Changes from v1

The new algorithm is a state machine with explicit confirmation periods instead of per-frame proximity emissions plus a generic transition penalty. It uses the supplied automatic tactical tracking and the presence of automatic set-piece intervals. It does not read human annotations, ground truth, external event data, or trained-model output.

Control requires a ball within 2.5 m, at least a 0.75 m advantage over the nearest opposing track, and a continuous 0.4 s run of supporting observations. Fast balls above 12 m/s require closer contact (within 1.2 m). Confirmed changes are backdated only to the start of that observed candidate run. Contested or loose balls retain the last controlled team, and gaps interrupt pending confirmation.

Stoppage hypotheses use three independent cues:

- Ball observed at least 0.3 m beyond the pitch for 0.2 s.
- Settled ball far from visible players for 1.5 s.
- Settled ball within an automatic set-piece interval for 0.6 s.

Ball motion is endpoint displacement across a fully observed 0.48 s window. The algorithm never interpolates across missing observations. A single outside-pitch outlier is insufficient to create a stoppage. A stationary ball beside a player during otherwise live play is insufficient without additional set-piece context.

After a confirmed stoppage, an inbounds ball moving at least 1.5 m/s near a player for 0.12 s supports a restart. The restart boundary is estimated from observed motion, not the tag's boundary. An unambiguous nearest-team advantage establishes restart ownership; otherwise the system abstains. Tags with N/A team do not invent an owner.

Missing observations alone never establish D. After two seconds of missing ball observations the system emits X while retaining its internal last-known state. X is an explicit uncertainty output, not a claim of correct possession: the competition scorer forward-fills it for spellF1 and counts it as a miss on graded frames for macroF1.

Half state resets and ungraded ranges follow published metadata. The organizer-published second-half pre-kickoff interval is D. All other thresholds above are physical/duration assumptions fixed before running the candidate on the match. The public five-minute labels were not read or scored during this work.

## Inspect and reproduce

```powershell
cd C:\dev\possession-lab
npm run rebuild-data
npm test
npm start
```

Select **Control v2 · experimental** in ACTIVE MODEL. The frame inspector shows the instantaneous close-control candidate, measured motion, confirmed stoppage cue, set-piece context, and restart confirmation evidence. A candidate is evidence rather than proof of a team change; confirmation requires a continuous run.

Outputs:

- `evaluation/results/experimental_control_v2.csv`: 199,319 ordered rows.
- `.local/control_v2_diagnostics.json`: algorithm decision log, parameters, output counts and hash.
- `.local/tracking.npz`: local evidence arrays for the frame inspector.

These generated outputs remain excluded from Git. The log records inference decisions; it is not ground truth and is not a complete label-transition listing, because abstentions and published metadata overrides also affect final labels.

Reproduction SHA-256: `fa34aa00363a28b193cad34e82b63eabd8063a9881cc6ef968214af14b133356`.

## Verification and limits

Fifteen synthetic scenarios cover brief opponent touches, sustained changes, loose and contested balls, missing observations, interrupted confirmation, stationary live control, tracking outliers, persistent stoppages, measured restarts, misleading set-piece context, absent teams, unknown scenes and half resets. Nine existing/expanded algorithm and HTTP tests cover earlier temporal behavior, server contracts, export identity, local-only Host handling and JSON-safe v2 evidence. All 24 tests pass; the Angular production build and official CSV validator pass. Rebuilding produces the same v2 bytes and preserves the original v1 hash.

V2 abstains on 49.5% of the full recording, including the ungraded portions. This is a conservative research model and has not been scored against the public sample or private full-match labels. Coverage, segment count and apparent plausibility do not establish accuracy.

Automatic tracking cannot observe a referee's permission or reliably distinguish a controlled reception from every rebound. Noisy set-piece tags can create false stationary-ball stoppages. Ball repositioning near a player can resemble a restart. Camera-plane ball positions do not reliably resolve aerial duels, and strict control thresholds can miss genuine possession. Long tracking gaps may hide both a stoppage and a restart.

The next useful step is an independent labeled match or synthetic benchmark with these ambiguous cases and a documented validation protocol. Competition-match human annotations and public-sample parameter selection remain prohibited.
