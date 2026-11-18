"""Package the offline app and source files; no downloads or dependencies.

Use --check-only for a read-only audit. Without that flag, validation must pass
before a ZIP is written. The default output is ignored by Git. An existing ZIP
is never overwritten unless --overwrite is explicitly supplied.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import tempfile
import zipfile
from pathlib import Path

sys.dont_write_bytecode = True
from validate_release import ROOT, collect_release_files, print_report, validate


def package(root: Path, output: Path, overwrite=False):
    root, output = root.resolve(), output.resolve()
    report = validate(root)
    if report["status"] != "PASS":
        print_report(report)
        raise ValueError("Release validation failed; no ZIP was created")
    if output.suffix.lower() != ".zip":
        raise ValueError("Output must have a .zip extension")
    if output.exists() and not overwrite:
        raise ValueError(f"Output already exists; choose another name or pass --overwrite: {output}")
    if not output.parent.is_dir():
        raise ValueError(f"Output directory does not exist: {output.parent}")
    files = collect_release_files(root)
    snapshot = {p: (p.stat().st_size, p.stat().st_mtime_ns) for p in files}
    handle, temporary = tempfile.mkstemp(prefix="." + output.stem + "-", suffix=".partial", dir=output.parent)
    os.close(handle)
    temporary_path = Path(temporary)
    try:
        with zipfile.ZipFile(temporary_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
            for path in files:
                relative = path.relative_to(root).as_posix()
                archive_name = "PHV Exam Trainer/" + relative
                # WebP/fonts/screenshots already compress well; avoid redundant CPU work.
                compression = zipfile.ZIP_STORED if path.suffix.lower() in {".webp", ".png", ".jpg", ".jpeg", ".woff2"} else zipfile.ZIP_DEFLATED
                archive.write(path, archive_name, compress_type=compression)
                archive.getinfo(archive_name).external_attr = (0o100755 if path.suffix == ".sh" else 0o100644) << 16
            if any((p.stat().st_size, p.stat().st_mtime_ns) != snapshot[p] for p in files):
                raise ValueError("Source files changed while packaging; retry after builds finish")
        with zipfile.ZipFile(temporary_path) as archive:
            if len(archive.infolist()) != len(files):
                raise ValueError("Archive inventory does not match the validated source list")
            bad_file = archive.testzip()
            if bad_file:
                raise ValueError("Archive integrity check failed: " + bad_file)
        # Atomic publication of our own completed temporary file; no extraction or deletion of user folders.
        if output.exists() and not overwrite:
            raise ValueError(f"Output was created by another process: {output}")
        os.replace(temporary_path, output)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise
    sha = hashlib.sha256()
    with output.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    result = {"status": "PASS", "archive": str(output), "archiveBytes": output.stat().st_size,
              "sourceFiles": len(files), "uncompressedBytes": report["distributionBytes"],
              "sha256": sha.hexdigest(), "crcIntegrityCheck": "PASS",
              "excluded": "Research downloads, installed dependencies, caches, Git metadata, user imports and existing archives"}
    print(json.dumps(result, indent=2))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--output", type=Path, help="Defaults to PHV Exam Trainer v1.0.0.zip in the source root")
    parser.add_argument("--check-only", action="store_true", help="Print file/size/asset audit without creating an archive")
    parser.add_argument("--json", action="store_true", help="Machine-readable output in check-only mode")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing output archive after the new archive verifies")
    args = parser.parse_args()
    if args.check_only:
        report = validate(args.root)
        print_report(report, args.json)
        return 0 if report["status"] == "PASS" else 1
    output = args.output or args.root / "PHV Exam Trainer v1.0.0.zip"
    try:
        package(args.root, output, args.overwrite)
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print("Packaging failed:", exc, file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
