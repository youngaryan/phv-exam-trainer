# Verification record

All checks below were performed on 18 November 2026. Reports record actual executed checks rather than intended coverage.

## Application regression suite

`npm.cmd --prefix tools test` runs state tests, all-route marking tests, full offline exam tests, and real mouse route regressions in Microsoft Edge. The browser uses `file://` with its network disabled, without a local server.

- Complete SERU A: 37 questions (18 MCQ/17 drag cloze/2 reading), 45-minute deadline, 100% for correct answers.
- Complete SERU B: 36 questions (22 MCQ/12 dropdown cloze/2 reading), 60-minute deadline, 100% for correct answers.
- Flag/review/jump/previous/next and last-question navigation; saved answers and flags after refresh.
- The red-box rule prevents accidental departure with unused words; explicit skip remains available.
- Timer expiry submits the stored answers automatically.
- Complete Topographical mock: 3 mouse-plotted optimal routes plus 21 static-map questions, 100/100.
- Real mouse-plotted wrong-way and closed-street routes lose marks; undo/clear and map reference work.
- Progress export/import round trip, compact viewport and zero horizontal overflow.
- Zero browser page/console errors and zero HTTP(S) requests in the tested app flows.

Machine-readable evidence: `e2e-report.json`, `route-ui-report.json`. Screenshots are in `screenshots/`. An additional independent UI smoke pass covered SERU practice feedback and screenshot comparison; see `UI_DIFF.md`.

## Route matcher regressions

`node tools/tests/marking.cjs --bank` checks empty/reversed drawings, closed roads, one-way movements, prohibited turns and off-road diagonal shortcuts. Every one of the 140 map-derived optimum geometries must receive full marks.

Testing found and fixed two integration errors: matching intermediate road geometry only to junction endpoints, and Leaflet marker click propagation substituting a nearby marker's coordinate for the actual click. The runtime now retains shape vertices, recognises continuous legal reference geometry within a small screen tolerance, and uses actual mouse coordinates even over a marker. Reference acceptance still verifies every edge's connectivity, closure and turn legality.

## State, content and packaging

`node tools/tests/state.cjs` checks malformed imported marks/settings/answers, cloze partial credit, cross-pool non-repetition and blocked local storage. The separate UI audit also confirmed rejection of five malformed progress snapshots.

`tools/validate_seru.py` checks all 540 items; a reproducible 54-item source review is recorded in `SERU_AUDIT.md`. `tools/validate_topo.py` recomputes map answers and route legality/shortest distances; the visual sample is recorded in `MAP_AUDIT.md`. These are agent audits, not external human certification.

`tools/validate_release.py --check-only` checks all local runtime references, bank minimums, complete declared tile coverage, classic scripts, network construction and the 400 MB / 50 MB size limits. It measures portable files plus Git metadata separately from ignored developer/research folders. `package_release.py --check-only` uses the same inventory. No archive is needed for the launcher or GitHub's automatically generated ZIP.

## Portable and launcher checks

`node tools/tests/portable.cjs` opens an extracted-style copy under `research/Fresh machine test & spaces` in a new offline browser context, with no copied developer packages. Home, map tiles, graph, route bank and legend loaded with zero errors/HTTP requests. Large immutable assets use hardlinks to avoid redundant disk use; this is a clean-profile/path check on this PC, not a test on another physical PC.

The actual copied `Start PHV Trainer.bat` was launched through Windows. It exited with code 0 and the app inventory reported an Edge window titled **PHV Exam Trainer · Offline practice**. Native visual capture was stopped by Computer Use because it could not reliably establish the local browser URL for policy enforcement. No further UI automation was attempted. A native-window screenshot and a physically disconnected second-PC test are therefore not claimed. The Playwright tests provide the offline rendering and interaction evidence.

The missing-Edge fallback was also exercised with `Test-Path` and `Start-Process` substituted in a child PowerShell process: it selected the correctly resolved spaced/ampersand HTML path for the default browser. Optional Program Files locations are filtered before path construction, including the missing `ProgramFiles(x86)` case on 32-bit Windows.

## Remaining limits

Tests establish consistency with the shipped exercise data, not complete real-world map restrictions or unpublished TfL scoring. Exact current PHV SERU composition, some screen details, full atlas coverage and unsupported conditional/via-way relations remain documented in `RESEARCH.md`, `DECISIONS.md` and `MAP_BUILD.md`.
