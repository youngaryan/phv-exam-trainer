# Visual comparison and fidelity limits

Research baseline inspected 18 November 2026: four original TfL Rise example screenshots, retained in ignored `research/official/`; filenames and source URLs are in [UI_SPEC.md](UI_SPEC.md). The current public guide shows MCQ, reading, empty cloze and cloze while dragging. It does not show the review/flag grid, final confirmation, timer or immediate results screen.

## Deliberate differences

| Area | Reference | Trainer |
|---|---|---|
| Emblem | TfL roundel | Neutral icon; trademarks are not branding |
| Questions | Official demonstration content | Original, traceable practice questions |
| Count/date/name | Example data, including134-item demonstration | Actual attempt length, current date and configured candidate name |
| SERU timer | Not shown in inspected screenshots | Visible countdown for requested timed practice |
| Typography/hit areas | Fixed screenshot controls | Responsive native controls; exact original font is unverified |
| Results | Real routes marked by two humans and results later | Immediate approximate educational feedback, explicitly labelled |
| Maps | Proprietary atlas-like reference | Original OSM-based styling and attribution |
| Review/confirmation | No authoritative reference captured | Consistent original implementation |
| Home/settings/progress | Not part of inspected exam software | Trainer-only workflow |

Raw screenshot frame colour is #0018A9; the scaled Rise page itself fades it to approximately #3346BA. The trainer matches the raw reference. White panel, simple lower buttons, plain radio options and red word-disposal box are the core observed layout features. Exact official fonts and interactive hover/disabled colours cannot be verified from bitmap references.

## Observed app comparison

The 18 November 2026 offline Edge smoke run captured and visually inspected the following trainer images. These contain original practice content and can be distributed; the TfL reference images remain research-only.

- [Home](screenshots/qa-home.png), 1440×900.
- [Mock MCQ](screenshots/qa-seru-mcq.png), 1440×900.
- [Mock reading](screenshots/qa-seru-reading.png), 1440×900.
- [Mock cloze](screenshots/qa-seru-cloze.png), 1440×900.
- [Settings, review, finish confirmation, results and practice feedback](screenshots/qa-other-states.png), a contact sheet of five viewport captures.

The reference and trainer have different viewport aspect ratios. The following measurements report original pixels, not a claim of pixel equivalence. Reference measurements are approximate bitmap measurements; trainer values come from browser geometry and computed styles in `research/official/ui-smoke-report.json`.

| Element | Public reference, about 1650×890 | Trainer, 1440×900 | Assessment |
|---|---|---|---|
| Blue frame / white panel | #0018A9 / #FFFFFF | Same colours | Matched |
| Panel start / header height | x≈37, y≈36 | x22, y46 | Responsive margin and taller header remain |
| Header text | ≈18px | 11px | Smaller; countdown occupies extra header space |
| Question counter | ≈26px | 25px | Close |
| MCQ option presentation | Plain native radios; no A/B/C prefixes or cards | Same in mock | Matched pattern |
| Option type / vertical pitch | ≈23px / ≈84px | 17px / ≈46.5px | Trainer is more compact |
| Reading passage | Black text on plain white | Plain white, 16px text | Matched structure; text size differs |
| Cloze blanks | Empty, dark rectangular border | Empty white 120×35px, 1px dark border | Matched pattern; dynamic width/content differ |
| Disposal area | ≈395×285px, pink, at right below passage | 402×270px, #FEC8CF, at right of passage | Close size/palette; exact position differs with content |
| Word tiles | Grey bordered/bevelled rectangles | Grey bordered rectangles | Similar; not an exact bevel reproduction |
| Navigation | Same flag/review/previous/next wording | Same wording; actual disabled first Previous | Matched labels; disabled reference state unavailable |

The first implementation used answer cards, letter prefixes, a grey reading block, labelled dashed blanks and a shallow full-width disposal box. These visible mismatches were corrected before the linked captures. The trainer retains a larger modern card style in **practice feedback**, settings and the home screen, where there is no official equivalent to reproduce.

No clipping or overlap was observed in the inspected 1440×900 captures. The 1280×720 practice screen had no document-level horizontal overflow. This is a bounded visual review, not certification of every question at every viewport or a formal accessibility audit.

## Functional smoke evidence

The smoke script opens `app/index.html` through `file://` in a fresh Edge context with networking disabled. It uses UI clicks, radio selection and actual drag-and-drop; reading the in-memory question IDs/answer key is used only to drive deterministic verification. It does not mutate the app state directly.

The completed run verified:

- Preset A composition: 18 MCQ, 17 cloze and 2 reading questions.
- All 37 answers selected through the UI; every cloze correct word dragged into its blank and every distractor into the disposal box.
- Leaving a partially disposed cloze triggers the red-box navigation guard.
- Flagging appears on review; previous/next works; reload preserves position, flag and the submitted answer.
- Review shows all 37 answered and one flagged; finish confirmation works; results give 37/37 and an expandable answer review.
- Practice displays correct-answer feedback with an explanation and handbook reference.
- No page errors, console errors or app HTTP(S) requests were recorded.

A separate read-only validator audit initially found acceptance of malformed imported progress. After the fix it rejected all five regression cases: missing marks, negative marks, an out-of-range MCQ answer, a non-array cloze discard value and invalid saved attempt settings. This exercises the validation function; it is not a substitute for the integration suite's import/export round-trip checks.

## Verification limits

The official topographical video was downloaded and inspected with 15 sparse frames and 6 selected full-resolution frames. This verifies 24 questions, 70 minutes, static-map behaviour and mouse controls. The route toolbar and exact drawing-line appearance remain unverified. A full 2fps/Tesseract pass was not performed: automatic approval review rejected broad frame extraction under disk pressure, and bounded sampling was used instead.

This SERU-focused smoke run does not certify route scoring, static-map content, timer expiry, every import/export path or the complete question bank. Those require their separate integration/data checks. Exact official review, confirmation and result screens were unavailable, so the matching colours and controls on those trainer screens are consistent design defaults, not a claim that TfL uses the same screens.
