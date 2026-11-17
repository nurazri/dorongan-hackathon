# Possession Lab interface

The Angular interface is optional for submission generation. It displays the frozen Control v5 output; it does not edit labels.

From the repository root, after preparing the local assets and caches as described in START-HERE.md:

```powershell
npm --prefix ui ci
npm run build
npm start
```

Open http://127.0.0.1:8765. The root launcher serves the built UI, Python API and local tactical video together. Running the UI development server alone does not start the API.

The single Angular component uses src/app/app.html for layout, src/app/app.css for styling and src/app/app.ts for playback, timeline seeking, frame search and API state. Global styles are in src/styles.css. The shared player combines tactical video and tracking with a draggable seek bar, play/pause, playback speed, fullscreen and frame entry. The sidebar shows current possession and distances; CSV export downloads v5.

Node 24.15.0 and npm 11.12.1 were used for verification. package-lock.json fixes the installed dependency tree; use npm ci. Run root npm test for Python model/server integration tests after preparing caches. The production Angular build performs strict template/type checks.
