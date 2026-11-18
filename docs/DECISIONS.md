# Decisions

## 2026-11-18 — Local-only delivery

Use the provided empty workspace as the repository root. Build plain HTML/CSS/classic JavaScript with local data and vendored Leaflet, opened through `file://`. No hosting, telemetry, account, runtime package install or network dependency. Do not push a repository.

## Evidence and unresolved formats

TfL sources take precedence. Conflicting or unpublished counts, scoring details and UI behaviours remain labelled as simulator defaults. The 37-question/45-minute preset is the provisional default pending research. A 60-minute/36-question preset is retained as an explicitly unverified alternative. A true 60% threshold on 36 equally weighted questions is 22, not 23; never reproduce the arithmetic error in the supplied third-party claim.

## Evidence excerpts

Question evidence should be original paraphrases linked to the handbook page. Avoid accumulating copied handbook excerpts into a redistributed derivative question bank. Explain this schema deviation in the content audit.

## User work isolation

The workspace was empty and had no existing Git history. Developer dependencies and source downloads are ignored. The distributable consists of the app, launchers and project documentation; dependencies are developer-only.
