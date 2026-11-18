# Topographical data and visual audit

Completed 18 November 2026. This audit verifies the released exercise data and images; it does not certify current real-world driving legality or unpublished TfL marking rules.

## Automated verification

`tools/validate_topo.py` independently recomputes every geographic answer and every route optimum. The release contains:

| Section | Items |
| --- | ---: |
| Route planning essentials | 70 |
| Map symbols | 60 |
| Places of interest | 70 |
| Specific streets | 70 |
| Road numbers | 60 |
| Compass points and directions | 70 |
| Short routes, 1–3 km | 60 |
| Closure routes, 1–3 km | 40 |
| Long routes, 5–12 km | 40 |

There are 400 MCQ items, including 100 two-answer items, and 140 route items. Short routes span 1,119.78–2,964.37 m; closure routes 1,321.22–2,990.92 m; long routes 5,296.25–9,931.04 m. Of the route questions, 114 have one or more legal alternatives within 5% of the optimum (54 have one, 49 have two, 11 have three).

The graph contains 50,026 junction/shape nodes, 99,520 directed edges, 1,219 represented prohibited turns and 2,855 named POIs. The validation checks edge continuity, direction, closures, turn restrictions, distance bands, independently shortest distances, alternatives, source names/references, grid arithmetic, bearings and all referenced images/tiles. The first full run passed with zero errors; the final run was repeated after visual/wording corrections.

The final strengthened validator passed with zero errors and writes `docs/TOPO_VALIDATION.json`. It rejects repeated geographic target/scenario identities and identical image-plus-question combinations. It detected one repeated street pair (STREET-007/STREET-042); STREET-042 was replaced with Lyons Place/Orchardson Street, rerendered and manually rechecked. Final semantic duplicate count: zero. Final identical image/question duplicate count: zero. RapidFuzz identified 4,679 stem pairs above 85% similarity; these are explicitly reported map-context variants, not falsely described as zero near-similar wording. The source identity checks distinguish repeated instructions on different maps from repeated tasks.

Displayed single-answer positions are balanced exactly within one item: two-option questions 35/35; four-option questions 58/58/57/57. Each of the four positions is used exactly 50 times across the two-answer questions. Correct answer text remains unchanged by this deterministic permutation.

The atlas has 4,733 native raster tiles at zooms 12–17, plus an explicit outside-coverage fallback, and 400 static question images of 900×600 pixels. Tile size is 256×256. The native tiles occupy 73,745,204 bytes before the small fallback. Static images occupy approximately 55.5 MB. The largest released map file is the approximately 29.7 MB graph JavaScript.

## Manual sample

A seeded, stratified random sample selected five items in each of the six MCQ sections: `random.Random(20261118)`, then `sample(range(1, section_count + 1), 5)` in the table order below. Each correct response was compared with the actual rendered image and its source/evidence record. Labels were inspected at their native pixel size or as lossless crops of the final image. The three sampled grids have identical image SHA-256 values; the common north-up numbered grid was visually inspected once and each movement was separately worked through.

| Item IDs (TOPO- prefix) | Manual check |
| --- | --- |
| ESSENTIALS-003, 006, 010, 027, 044 | Missing destination, visible Kingsway closure crossing, legal reference route, missing destination, reversed arrow direction respectively. The shortest-route claim was additionally checked by the independent graph validator. |
| SYMBOL-015, 021, 025, 032, 046 | Circled T = theatre; Ho = hotel; Ho = hotel; + = place of worship; Ho = hotel. Checked against the map key and OSM category. |
| POI-001, 022, 028, 030, 055 | Labels read Spiritist Society of London; Egerton House Hotel; Our Lady and St Vincent's; National Crime Agency; The Ampersand Hotel. Circled targets and names are legible. |
| STREET-001, 007, 027, 048, 070 | Westbourne Grove/Ledbury Mews North; Aberdeen Place/Lyons Place; St James's Road/Clements Road; Charlotte Street/Store Street; Commercial Road. All requested labels are visible. |
| ROADNO-007, 018, 023, 037, 048 | Park Square West A4201/Marylebone Road A501; Holborn Circus A40/Charterhouse Street B500; Hunter Street B504/Bernard Street B502; St Martin's Lane B404; Thurloe Place A4. |
| COMPASS-019, 027, 028, 050, 067 | Grid answers 20, 12, 17 worked through by hand; Charles II Street arrow points south-west (239.76°); Lofting Road points east (78.85°). |

## Findings, corrections and widened sample

Two presentation/wording issues were found. Small blue arrowheads were difficult to distinguish from the scenario route line, especially in reversed-route questions. All 70 scenario images and all 30 geographic bearing images were rebuilt with larger navy arrowheads and a white outline. The OSM `amenity=police` category includes enforcement offices, so “Police station” was broadened to **Police facility**, including the National Crime Agency item and the legend. The geographic identity and selected answer position did not change.

These findings were treated conservatively as exceeding the 2% audit trigger. Twelve additional affected items were manually inspected after correction, making 42 inspected items in total:

- ESSENTIALS-002, 008, 014, 020, 032: the larger arrowheads visibly run from the red end towards the green start, as the false answer requires.
- COMPASS-041, 045, 055, 060, 065, 070: visible bearings respectively north-west (321.87°), west (262.11°), north (0.85°), north (351.58°), north-east (47.86°) and west (255.33°). All lie within 15° of their selected compass point.
- SYMBOL-030: the dark-blue P at the National Crime Agency is consistently described as a police facility; the source category remains `police`.

The subsequent semantic-duplicate correction added a thirteenth targeted visual check: STREET-042 clearly displays **LYONS PLACE** and **ORCHARDSON STREET**, both independently present in the retained OSM graph. Total manually inspected items after this additional correction: **43** (30 seeded samples plus 13 targeted checks).

No remaining wrong answer was found in this sample. This is a bounded audit, not a claim that every image has been manually checked or that OSM is error-free. Duplicate wording for map-reading tasks is intentional when the map and source targets differ; exact item IDs and geographic identities are distinct.

## Known limits

- 172 conditional or via-way restriction relations are not represented. Only constraints actually shown in the exercise map are scored. These routes must not be used for real-world navigation.
- Coverage is a central-London rectangle rather than all Zones 1–2 or wider Greater London. Some static crops touch its edge.
- POI markers are graph vertices within 100 m of the named feature, not independently surveyed entrances or guaranteed frontages.
- Source-data inference, automated correctness checks and manual image inspection are distinct. No TfL endorsement, leaked questions or proprietary map artwork is involved.
