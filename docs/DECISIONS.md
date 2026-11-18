# Decisions

## 2026-11-18 — Local-only delivery

Use the provided empty workspace as the repository root. Build plain HTML/CSS/classic JavaScript with local data and vendored Leaflet, opened through `file://`. No hosting, telemetry, account, runtime package install or network dependency. Do not push a repository.

## Evidence and unresolved formats

TfL sources take precedence. Conflicting or unpublished counts, scoring details and UI behaviours remain labelled as simulator defaults. The 37-question/45-minute preset is the provisional default: official public PHV material does not settle its current count/time. A 60-minute/36-question preset is retained as an explicitly unverified alternative; some reporting confuses taxi and PHV assessments. A true 60% threshold on 36 equally weighted questions is 22, not 23; never reproduce the arithmetic error in the supplied third-party claim. The displayed score uses actual fractional marks, not the rounded percentage, when deciding pass/fail.

The official May 2026 Topographical video confirms 24 questions and 70 minutes. The official guidelines confirm 3 routes, 66 route marks plus 34 other marks, and a 60% pass mark. The app assigns 22 marks to each route and selects 8 single-answer plus 13 two-answer questions to total 34. Those individual weights, the section distribution and section order are simulator defaults, not claimed official details.

## Evidence excerpts

Question evidence should be original paraphrases linked to the handbook page. Avoid accumulating copied handbook excerpts into a redistributed derivative question bank. Explain this schema deviation in the content audit.

## User work isolation

The workspace was empty and had no existing Git history. Developer dependencies and source downloads are ignored. The distributable consists of the app, launchers and project documentation; dependencies are developer-only.

## Smaller reproducible atlas build

The local disk filled during tool setup. The map build therefore uses pyosmium, Shapely and Pillow rather than Planetiler/OpenMapTiles/MapLibre, and limits coverage to a central-London rectangle (51.475–51.565 N, −0.225–−0.045 E). It produces buffered 8×8 metatiles and slices local WebP tiles at all zooms 12–17. Unused task-installed MapLibre, OSMnx, GeoPandas, Pandas, PyOgrio and PyProj were removed; required developer libraries remain under `tools/.venv`. No unrelated user files were removed. Fonts are vendored Noto Sans under OFL. See `MAP_BUILD.md` for source hashes and all cartographic limits.

Route subgraph files hold compact references into the shared graph instead of duplicating the same geometry 140 times. All required graph data is loaded through local classic scripts. POIs are snapped within 100 m to real drivable vertices; the marker is the exact exercise endpoint, not a verified entrance/frontage. Conditional/via-way restrictions not represented by the build are disclosed and cannot create hidden penalties.

## Route matching and pixel precision

The routing graph retains all geometry shape points at runtime by subdividing source edges. This avoids falsely treating a click in the middle of a curved road as off-road. Consecutive clicks are matched through a physical graph constrained to a 25 m corridor; backwards-only graph movements retain their illegal-direction flag. Full source-edge IDs preserve turn restrictions across shape segments.

Screen rounding can place a click slightly either side of closely spaced junctions. A separate bounded recogniser accepts a drawing that continuously and monotonically follows the entire legal optimal/acceptable reference geometry within 3 m, sampled at intervals no greater than 2 m. Endpoints alone are insufficient. The reference is checked again for connectivity, closures and prohibited turns before acceptance. Arbitrary drawings still go through physical graph marking. Tests cover both ideal coordinates and real mouse clicks, wrong-way detours and closure violations.

## Exam fidelity and review

Raw official SERU screenshots establish blue `#0018A9`, white content, plain radio choices, right-side pink discard box and grey tiles. The simulator uses a neutral PH mark. The timer, review grid, finish dialog and instant post-mock results are documented simulator implementations where an exact current PHV reference was unavailable. Practice feedback is kept out of mocks. Click-to-place support supplements drag-and-drop for accessibility. Unplaced words warn; the user can deliberately skip a question and return, preserving flexible navigation.

Full 2 fps video extraction and OCR would have produced excessive files on the constrained disk. A bounded sample of official video frames and the original Rise screenshots were inspected instead. This is a documented deviation, not a completed exhaustive OCR pass.

## Persistence and revision

Settings, active attempt, seen questions and the latest 100 completed sessions are stored locally with every storage operation guarded. A monotonic wall-clock deadline survives refresh and closing the app; leaving a timed attempt does not pause its timer. Question selection avoids repeats within each eligible pool until it is exhausted, with a shared seen list across drills and mocks. Missed questions are due immediately; successive correct reviews return after 1 and 3 days, then leave the queue on the third success. Due items take priority. Progress JSON imports are strictly validated and explicitly replace existing progress; no uploaded file leaves the computer.
