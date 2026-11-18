# Assessment interface specification

Research date:18 November2026. Scope: reproduce publicly demonstrated interaction patterns with original questions and a neutral emblem. This is a practice interface, not TfL software. Sources and uncertainties are in RESEARCH.md (R03,R05,R06,R15).

## Measured official SERU references

The Rise “what to expect” lesson was opened in headless Edge and its CONTINUE button activated. Four publicly embedded PNGs were downloaded only into ignored `research/official/` and visually inspected:

| Reference | Original image URL | Dimensions |
|---|---|---|
| MCQ | https://articulateusercontent.com/rise/courses/qIklurV6jC01UnOkAqUviEbCTFssrR2l/FQ3ubLx7FmpALYIS.png |1650×890|
| Reading | https://articulateusercontent.com/rise/courses/qIklurV6jC01UnOkAqUviEbCTFssrR2l/KpNwgBWPWRaitdXC.png |1649×887|
| Cloze before answer | https://articulateusercontent.com/rise/courses/qIklurV6jC01UnOkAqUviEbCTFssrR2l/rfJTCMd6kXBCaIWd.png |1649×891|
| Cloze during dragging | https://articulateusercontent.com/rise/courses/qIklurV6jC01UnOkAqUviEbCTFssrR2l/RDiv1EXm6rs8GovT.png |1348×716|

Raw PNG dominant frame colour is **RGB(0,24,169),#0018A9** (130,685 exactly matching pixels in the MCQ source). The browser-displayed scaled/faded image measured #3346BA; that is not the original colour and must not be used as the authoritative sample. Panel is #FFFFFF; text black. Red box contains near-identical compression colours #FEC8CF/#FFC9CF, so use #FEC8CF. Tiles are approximately #D8D8D6 with a thin dark outer border and inner bevel. These are measurements, not guesses.

At original MCQ dimensions, white content starts about x37,y36 and ends x1637,y853. Border widths are asymmetric (left~37,right~13), header~36 high, footer~37 high. White panel corner radius~15px. Text starts at x77 (~40px content inset), counter baseline~85; question follows immediately; options are widely spaced vertically (~84px). Header text is about18px, question/options about23px, counter about26px. The face appears Arial/Helvetica; font identity is not embedded proof. Default to Arial,sans-serif.

## Shell and controls

- Full viewport blue frame; white rounded panel with a scrollable interior if content exceeds a small screen.
- Header left: neutral circular compass/letter icon, date as `Mon DD YYYY`, separator, `Logged in as : <candidate name>`.
- Header right: `Assessment progress:` and a narrow white-outlined bar. Original bar is about245×10px. Width follows answered fraction in simulator; the official definition of progress is unknown.
- Requested countdown `Time remaining: HH:MM:SS` is added on blue. It is **not present in the four source SERU screenshots**; record this as a simulator deviation. It is essential for timed practice.
- Content counter `N of M` at top left. Demonstration counters132–134/134 must never determine mock composition.
- Bottom left: `Click here to flag this question`, `Click here to review assessment`.
- Bottom right: `< Previous Question`, `Next Question >`. Last official reading example has no Next. First question previous is disabled in simulator (official disabled state unknown).
- Source controls have white faces, blue labels, square corners and compact height. Enlarge hit areas modestly for accessibility without changing labels.

## Question layouts

MCQ: question above three native radio buttons, left aligned. No hint, score feedback or explanation inside strict mock. Topographical multi-answer variants use checkboxes with explicit select-two instruction.

Reading: bold instruction, passage, question, then three options. Preserve this order. Source's title line is `Please read the following information carefully and answer the question below:` and its question line is `Question: Which one of the following statements is correct?`. Content must be original paraphrase; source example is not copied into the bank.

Cloze: instruction at top, inline empty bordered slots, then a conspicuous pink disposal area labelled `Incorrect words here`; word tiles below. Original disposal area is approximately395×285px at x731,y449 in the 1649px source. Use a proportionally scaled, minimum accessible target. Drag tile into slot or disposal area. A tile can occupy one place only and be moved back. All unused tiles must go in disposal area before onward navigation when strict validation is enabled. Exact warning wording/behaviour is unknown; use a plain notice and configurable block/warn rule. Dropdown option uses same passage and six-word pool but is a reported alternate format, not a visual claim about the current official software.

## Topographical layouts

Route map uses a narrow white question/instruction panel at left (~25% width by simulator choice), toolbar above map, green start and red end. The official video confirms click/release plotting, dragging to pan and wheel zoom. Map and routes are created from open map data, not copied atlas imagery. Default tools: `Undo last point`, `Clear route`, `Centre on start`, `Map key`. These toolbar labels/proportions remain fallbacks: a legible full route toolbar is not shown in the inspected video sample.

Straight-segment route is blue5px; assisted mode uses graph paths. Green dashed optimal route/red violations appear only in practice feedback or result review. Exact official line colour/width and snapping algorithm are unknown. Map must show attributed OSM data and restrictions used by marking. Static MCQ maps are fixed images at roughly900×600; no pan or zoom controls. The official video at103s verifies the static behaviour and shows map on left, question/options on right, with roughly a60:40 split. Reference legend opens separately and closes without losing answers. Atlas-inspired palette: warm pink built-up land, green parks, blue water, white local roads and yellow/orange main roads with dark casing. This is original styling, not licensed A–Z reproduction.

The official video title card around13–23s verifies70 minutes and24 questions. Its timer is white text in a blue rectangle at top right. The75s frame prohibits pen/notes. The130s sequence permits any question order and confirms autosaving. These are observed facts; they no longer rely solely on provider reports. Research captures are sparse bounded JPEGs because the full2fps extraction was rejected for disk-space risk; no Tesseract run is claimed.

## States and flows

| State | Behaviour | Fidelity status |
|---|---|---|
| Normal | Native radios/checkboxes; square navigation controls | Basic source pattern observed |
| Hover | Slight grey/blue change; pointer cursor | Default; not documented in static images |
| Keyboard focus | Visible high-contrast outline; logical tab order | Accessibility addition |
| Selected | Native selected mark or placed word; unique tile location | Selection pattern observed; exact hover style unknown |
| Flagged | Distinct flag state on button/review entry; answering does not remove flag | Flow requested; official flagged appearance unknown |
| Disabled | Reduced contrast and actual disabled attribute | Simulator choice |
| Instructions | Explain mouse, types, time, no notes, navigation, saving and practice pass mark; Start begins timer | Original paraphrase, not copied official instruction pages |
| Review | Every item and answered/unanswered/flagged status; click returns | Official exact screen unavailable |
| Finish | Confirmation with unanswered count, cancel returns | Official exact dialog unavailable |
| Timeout | Submit once; persist result; announce time expired | Simulator behaviour, exact official messaging unknown |
| Results | Immediate educational marks, section breakdown, review/source links | Practice-only; real routes require human marking |
| Resume | Refresh restores question, answers, flags, absolute deadline | Added local persistence, not claimed as official |

Home, statistics, settings, practice feedback, mistake queue and import/export use a clean modern visual style distinct from the sparse exam panel. They are trainer features, not replicas of centre screens.

## Required visual QA

Capture home, instructions, each question type, route map, static map, legend, review, finish confirmation, results and settings at1440×900 (and a smaller1280×720 check). Compare MCQ/reading/cloze with the research-only reference PNGs at equivalent scale. Log deviations honestly in UI_DIFF.md. Do not redistribute reference screenshots or claim pixel equivalence where fonts, aspect ratios, responsive sizing or unobserved states differ.
