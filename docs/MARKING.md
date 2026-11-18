# Topographical marking model

TfL's real routes are marked by human assessors. This app's automatic route marking is a practice approximation; no claim is made that these deductions reproduce unpublished TfL rubrics.

## Data and optimum

Every route is computed on the same OpenStreetMap-derived graph used to draw the local map. Edge weights are road distance in metres, including geometry bends. Edges are directed; two-way streets have an explicit reverse edge. Supported turn restrictions are pairs of incoming/outgoing edge IDs. Dijkstra's state includes the incoming edge so a prohibited turn cannot be bypassed by visiting the same junction without turn history.

The graph excludes non-drivable and restricted-access ways. A closure removes all retained edges with the named street. Each closure exercise first proves that the closed street lies on its unclosed optimum, then computes the new shortest legal route. Short and closure routes must be 1–3 km; long routes 5–12 km. Up to three distinct legal alternatives are retained only if their unpenalised length is no more than 105% of the optimum.

The marker defines the precise start or destination. Source POI names, IDs, coordinates and snap distances remain available for audit. The route's `optimalGeometry` includes every shape vertex; joining these coordinates exactly is the reference full-mark drawing.

## Default deductions

All values are configurable in the app configuration. They are practice defaults, not verified TfL mark allocations.

| Condition | Deduction |
| --- | --- |
| Start over 40 m from marker | 3 |
| Finish over 40 m from marker | 3 |
| Reversed start and destination | Question score becomes zero |
| Visible illegal movement, wrong-way travel, closed edge or prohibited turn | 4 per movement |
| Drawn segment leaves the road corridor | 4 per segment |
| Length / optimum ≤1.05 | 0 |
| Ratio >1.05 and ≤1.15 | 3 |
| Ratio >1.15 and ≤1.30 | 7 |
| Ratio >1.30 | 12 |

Scores are clamped to 0–22. A recognised acceptable alternative receives no directness deduction. A blank route receives zero. The default road-matching corridor is 25 m; start/end tolerance is 40 m.

## Visibility and feedback

Only represented restrictions may incur penalties. One-way arrows are drawn on the atlas. Restricted-turn nodes have red symbols; the interactive map must expose the precise prohibited from/via/to movement. Closure geometry is drawn in red with a closed-road annotation. Practice/results show the user's blue route, the green dashed optimum, red violations, ordered street lists and the deduction breakdown. The route layer should show the restriction markers even at overview zooms where raster symbols are too small.

Real-exam drawing connects clicks by straight lines and requires clicks at bends. Assisted drawing snaps to nearby graph positions and follows graph edges. Assisted routes remain subject to closure and one-way rules. Both modes are marked against the actual drawn/traversed path, never simply against the shortest path between start and finish.

The runtime matcher expands each retained road edge into its geometry segments so that clicks at bends are not incorrectly treated as distant junction clicks. Known optimal/acceptable reference traces may be recognised through continuous, monotonic comparison: samples are no more than 2 m apart and must remain within 3 m of the reference. These references are revalidated against current closure and turn data before recognition. This preserves full marks for the actual reference geometry while arbitrary lines still undergo corridor matching and deductions. JavaScript scorer tests exercised all 140 optimal geometries; browser tests exercised all three route types and actual mouse-drawn wrong-way and closure examples. See the main test report for executed results.

## Multiple choice

Single-answer questions are exact match. Two-answer questions require exactly the two correct answers and default to two marks. The default mock composition is three 22-mark route exercises and 21 other questions totalling 34 marks. Individual MCQ allocation remains an explicitly configurable approximation where TfL has not published its precise weighting.

## Verification

`tools/validate_topo.py` independently recomputes shortest distances, route legality, closure intersections, alternatives, POI identities, symbols, source street/road labels, compass bearings and grid arithmetic. It also checks all route tiles and static images. Runtime scoring additionally requires browser tests of optimal, reversed, one-way and closure examples; a passed data validator alone is not evidence of a correct interactive scorer.
