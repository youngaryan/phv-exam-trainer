# Release validation and packaging

The release checker and packager use Python's standard library only. They are developer tools; users opening the supplied HTML or launcher do not need Python, Node, Git or any installation.

## Read-only audit

```powershell
python tools/validate_release.py --check-only
python tools/validate_release.py --check-only --json
python tools/package_release.py --check-only
```

These commands do not create an archive or change any source files. A missing file, missing map image or tile, oversized distribution, prohibited runtime network construction or external script/style asset fails the check with a nonzero exit code. The report lists the current measured bytes and all failures; an interim run is not labelled as a finished release.

The measured source/distribution contains the app, launchers, documentation, attribution and licences, and developer source files. It excludes research downloads, installed dependencies (`node_modules` and `.venv`), caches, user imports, archives and `.git`. Limits use decimal bytes: 400,000,000 for the distribution and 50,000,000 for any individual distributed file. This is stricter than the equivalent MiB interpretation.

When Git is available, its tracked working-file inventory is checked separately, including files accidentally tracked from otherwise excluded locations. Git's object database size is reported separately, and the portable source plus the current Git metadata must also fit within 400 MB. Neither an ignored download folder nor installed developer dependencies are advertised as part of the portable app. The check is for current source contents, not a complete audit of every historical Git object.

Static checks include:

- Required release files, the four classic data globals, and minimum bank counts (350/150/40 SERU, 140 routes and 400 static-map items).
- Existing local assets for every HTML script and stylesheet, CSS `url()`/import, static question-map reference and per-route graph.
- Every tile within the data's declared bounds at every declared zoom level.
- No module script tags, dynamic module imports, fetch/XHR, WebSocket/EventSource, beacon or service-worker registration in application, data and vendor JavaScript. Ordinary object methods named `import` are distinguished from dynamic module imports.
- No remote runtime script/style/image URLs, and an index Content Security Policy with `connect-src 'none'`.

The large question/graph globals and route files are checked as strict JSON inside their exact classic assignments, with executable prefixes or suffixes rejected. JavaScript code in the remaining files is scanned for network or module constructions. This avoids treating text inside a source citation as executable code.

Ordinary study citations and clickable external links are allowed. URLs appearing as provenance or SVG namespace identifiers are not treated as network requests. These static checks complement the file-URL browser tests; they cannot substitute for observing browser requests or a launcher working on a fresh machine.

## Create a release ZIP

Only run this once the data build and tests have finished. The check-only mode is available when disk space is limited.

```powershell
python tools/package_release.py --output "PHV Exam Trainer v1.0.0.zip"
```

Without `--output`, the same filename is created in the source root. Existing archives are preserved unless `--overwrite` is supplied. The ZIP contains one `PHV Exam Trainer/` directory and exactly the files selected by the shared distribution policy. It carries the tools' source and lockfiles, not installed developer packages. Shell-launcher executable permissions are recorded in the archive for Mac/Linux extraction.

Packaging validates first, writes a private temporary file, checks that source files have not changed, tests every ZIP member's CRC, then moves the completed archive into place. Failed partial archives created by this process are removed. The report includes the archive path, size, source-file count and SHA-256. This does not push or publish anything.

## Audit an extracted copy

```powershell
python tools/validate_release.py --root "C:\path with spaces\PHV Exam Trainer" --check-only
```

Use that copy's `Start PHV Trainer.bat` for the separate offline launcher test. A source audit alone cannot claim that the computer was disconnected, that an app-mode window opened, or that no administrative permissions were required. Record those observations with the browser/launcher test results. A copy without `.git` receives a Git-inventory warning, not an app-integrity failure.

## Execution status

On 18 November 2026, the source audit passed after the final browser run: 5,370 distributed files, approximately 211.67 MB; largest file 29.72 MB. All 400 map references, 140 route graphs and 4,733 declared-coverage tiles existed. After the map release commit and removal of an incomplete automatic-repack temporary file, source plus Git metadata measured 368.87 MB. The final verification commit adds the latest screenshots and documentation; its exact current measurement is printed by the read-only checker and must remain below 400 MB. These are measured snapshots, not a permanent size guarantee.

Both the release validator and `package_release.py --check-only` passed. The packager has not been run in archive-creation mode during this check. No release ZIP is claimed. Any subsequent missing-file, unfinished-render or size failure must be resolved before packaging.
