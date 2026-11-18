# Map build and provenance

Source: [Geofabrik Greater London](https://download.geofabrik.de/europe/united-kingdom/england/greater-london.html), accessed 18 November 2026. The page states that the downloaded extract contains OpenStreetMap data through 17 November 2026 21:24:30 UTC. Source PBF size: 130,412,950 bytes. Its SHA-256 is recorded in `app/data/map_manifest.json` after the build.

The map database, route data and geographic question metadata are derived from OpenStreetMap and are distributed under ODbL-1.0. Original cartography is rendered locally; no third-party map tiles or proprietary atlas imagery are bundled. All map screens must retain the OpenStreetMap attribution.

## Rebuild

1. Install `tools/requirements-maps.txt` into `tools/.venv`.
2. Download the linked `greater-london-latest.osm.pbf` into `research/maps/`.
3. Run `tools/.venv/Scripts/python.exe tools/build_maps.py --extract --areas --tiles --bank`.
4. Run `tools/.venv/Scripts/python.exe tools/validate_topo.py`.

`research/maps/` is ignored. It contains the source and intermediate extraction caches. Generated JavaScript, tiles and static maps are release assets. The full runtime graph is in `map_data.js`; each route's `topo_routes/*.js` holds the compact node/edge reference subset for its bounds plus 800 metres. Reference subsets avoid duplicating geometry across 140 exercises.

The original PBF was removed after successful extraction, multipolygon assembly, checksum recording and cache verification to recover disk space. Compressed source/extraction caches are retained locally. For a partial image rebuild, `--bank --only ESSENTIALS,COMPASS` retains other existing images and deterministically regenerates the full metadata. `--areas` is necessary for relation-based water and park polygons, including the Thames. The exact source SHA-256 is `0f02b29482e441a579da5a2c2e35b30745cbf8001e6433edc8838d0689151265`.

## Deliberate implementation differences

- The renderer uses pyosmium, Shapely and Pillow rather than Planetiler/OpenMapTiles/MapLibre. The user allowed documented changes when necessary; a disk-space exhaustion during dependency installation required a smaller reproducible toolchain. There is no Java runtime dependency. The output is still standard 256-pixel WebP raster tiles at zooms 12–17, rendered in buffered 8×8 metatiles.
- Coverage is a central-London rectangle: latitude 51.475–51.565, longitude −0.225–−0.045. It includes meaningful 5–12 km driving exercises but is not a complete Zones 1–2 atlas or Greater London map. Coverage reduction is an explicit size/disk-budget choice.
- The custom atlas appearance uses pink buildings, green parks, blue water, white minor roads, cased yellow main roads, road references, street labels and original generic symbols. It does not copy Collins A–Z artwork. It is an educational snapshot, not a road-navigation product.
- Noto Sans Regular and Bold are bundled under the SIL Open Font License in `app/vendor/fonts/`; no proprietary font file is redistributed.
- Endpoints are named OSM places snapped to a real drivable graph vertex within 100 m. The green/red marker is the precise exercise start/set-down position. A marker is not a verified building entrance; the source POI position and snap distance are retained in the dataset.
- Static question images are 900×600 pixels. Compass grids are original abstract illustrations with arithmetic answer keys, not invented London streets.
- Conditional access roads, private/customer/delivery/destination roads, pedestrian ways, bus-only ways and parking aisles are excluded from the drivable graph. The graph retains explicit one-way direction and supported node-via turn restrictions. Conditional/via-way turn restrictions require additional handling; the build manifest discloses the count rather than claiming complete real-world navigation coverage.

## Source references

Read 18 November 2026; these are primary project documentation rather than TfL examination claims:

- [OSM copyright and ODbL](https://www.openstreetmap.org/copyright): credit, licence and derived database obligations.
- [OSM tile policy](https://operations.osmfoundation.org/policies/tiles/): bulk downloading public OSM raster tiles is prohibited; this build does not do it.
- [OSM restriction relations](https://wiki.openstreetmap.org/wiki/Relation:restriction): from/via/to members and no/only movement semantics.
- [OSM access](https://wiki.openstreetmap.org/wiki/Key:access): mode-specific access tags and their hierarchy.

## Limits

Source data can contain errors and later changes. The validator proves internal consistency with the released exercise graph, not that every street remains legally driveable in November 2026. Unsupported restrictions and rendering limitations remain explicit in the release documentation. Do not use this atlas for actual driving.
