# PHV Exam Trainer progress

Started 18 November 2026. This file records completed work and verification limits; unchecked items are not claimed as done.

- [x] Read the supplied specification and inspect the empty workspace.
- [x] Initialise Git and assign bounded research, SERU content and map-data workstreams.
- [x] Research assessment formats, official material, candidate experiences and 40 useful sources. Register: 53 sources; official video confirms 24 Topographical questions/70 minutes.
- [x] Record UI evidence, unknowns, defaults and differences. Raw screenshots and bounded video frames inspected; exhaustive OCR remains a documented deviation.
- [x] Build the offline shared shell, launcher, review, timer and persistence.
- [x] Build and validate SERU banks, both presets and both blank styles. 540 items; 54-item source audit; both complete mocks passed offline.
- [x] Build OSM maps, routing data, route bank and computed map questions. 140 routes + 400 MCQs; 43-item map audit completed.
- [x] Implement route plotting and configurable approximation of route marking. All 140 optimal geometries and actual browser wrong-way/closure cases passed.
- [x] Add practice, mistakes, statistics, settings and JSON export/import. Final suite includes transfer round trip.
- [x] Run validators, browser tests, answer audits and visual review. Both bank validators passed; all 140 optimal routes passed; final offline mocks scored 100%; browser logs recorded zero errors/network requests. See `TESTING.md` and JSON reports.
- [x] Verify launcher in a path with spaces and offline browser operation. The real batch file exited 0 and Edge exposed the trainer window. A clean offline browser profile loaded the copied app, tiles and legend with zero errors/HTTP requests.
- [ ] Package licences, attribution, README, Git milestones and release tag.

## Evidence policy

Officially confirmed facts are distinguished from third-party reports and simulator defaults. Tests are recorded only after execution. Any unmet requested acceptance criterion must remain explicit in this file and the final report.

## Explicit scope differences

- Current PHV SERU composition remains unresolved in official public guidance; A and B are labelled reported/unverified formats.
- Central-London coverage replaces complete Zones 1–2/wider-London coverage; real named POIs are snapped to exercise points, not individually verified frontages.
- Pyosmium/Shapely/Pillow replace Planetiler/MapLibre after local disk exhaustion; the required local raster output and offline runtime are retained.
- 172 conditional/via-way restrictions are not represented; only shown graph restrictions are marked.
- The 2 fps/Tesseract video pass and exhaustive nested Rise question inventory were not completed. Original screenshot analysis and bounded official-video frame inspection were used.
- Answer audits are documented agent source/map reviews, not human or TfL certification.
- A separate clean physical PC is unavailable. Checks used a clean browser context, disabled browser networking, a spaced/ampersand path and the actual Windows launcher on this PC. Large immutable assets in the test copy were hardlinked to conserve disk space.
- Native-window visual inspection was stopped by Computer Use because it could not determine the local browser URL confidently enough to enforce its policy. No further UI automation was attempted. Launcher exit status/window title and the independent offline Playwright screenshots are the available evidence; a native-window screenshot is not claimed.
