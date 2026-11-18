"""Read-only checks for the portable source/distribution, using only Python stdlib.

Ignored research, installed developer dependencies, caches and Git's object
database are not distributable source. Their exclusion does not hide large
tracked files: Git-tracked source is measured separately when Git is available.
This check does not replace answer validators or browser tests.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
REPO_LIMIT = 400_000_000  # Decimal MB: deliberately stricter than 400 MiB.
FILE_LIMIT = 50_000_000
ROOT_FILES = {"README.md", "LICENSE", "ATTRIBUTION.md", "Start PHV Trainer.bat",
              "start.sh", ".gitignore", ".gitattributes"}
SOURCE_DIRS = {"app", "docs", "tools"}
EXCLUDED_DIRS = {".git", "research", "node_modules", ".venv", "venv", "__pycache__",
                 ".cache", ".pytest_cache", "test-results", "playwright-report", "user-imports"}
EXCLUDED_SUFFIXES = {".zip", ".7z", ".pbf", ".pdf", ".mp4", ".webm", ".mkv", ".mov",
                     ".avi", ".pyc", ".log", ".whl", ".jar", ".exe", ".dll", ".pyd",
                     ".partial", ".tmp"}
REQUIRED = [
    "README.md", "LICENSE", "ATTRIBUTION.md", ".gitignore", "Start PHV Trainer.bat", "start.sh",
    "app/index.html", "app/css/app.css", "app/js/app.js", "app/js/core.js", "app/js/routing.js",
    "app/data/config.js", "app/data/seru_bank.js", "app/data/topo_bank.js", "app/data/map_data.js",
    "app/data/map_manifest.json", "app/maps/legend.webp", "app/vendor/leaflet/leaflet.js",
    "app/vendor/leaflet/leaflet.css", "app/vendor/leaflet/LICENSE", "app/vendor/fonts/OFL.txt",
    "tools/launch.ps1", "tools/requirements.txt", "tools/package.json", "tools/package-lock.json",
    "tools/build_seru.py", "tools/build_maps.py", "tools/validate_seru.py", "tools/validate_topo.py",
    "tools/tests/e2e.cjs", "tools/tests/marking.cjs", "tools/validate_release.py", "tools/package_release.py",
    "docs/RESEARCH.md", "docs/UI_SPEC.md", "docs/UI_DIFF.md", "docs/DECISIONS.md", "docs/PROGRESS.md",
    "docs/MARKING.md", "docs/MAP_BUILD.md", "docs/SERU_AUDIT.md", "docs/rejected_items.md",
    "docs/RELEASE_CHECKS.md",
]
GLOBALS = {"app/data/config.js": "PHV_CONFIG", "app/data/seru_bank.js": "SERU_BANK",
           "app/data/topo_bank.js": "TOPO_BANK", "app/data/map_data.js": "PHV_MAP"}


def excluded(relative: Path) -> bool:
    return (any(part in EXCLUDED_DIRS for part in relative.parts)
            or relative.suffix.lower() in EXCLUDED_SUFFIXES
            or relative.name in {".DS_Store", "Thumbs.db"})


def collect_release_files(root: Path) -> list[Path]:
    """The packager imports this exact inclusion policy; no hidden extra files."""
    root = root.resolve()
    files = [root / name for name in ROOT_FILES if (root / name).is_file()]
    for folder in sorted(SOURCE_DIRS):
        base = root / folder
        if not base.is_dir():
            continue
        for current, directories, names in os.walk(base, followlinks=False):
            directories[:] = sorted(d for d in directories if d not in EXCLUDED_DIRS
                                      and not (Path(current) / d).is_symlink())
            for name in sorted(names):
                path = Path(current) / name
                if not excluded(path.relative_to(root)) and path.is_file():
                    files.append(path)
    return sorted(files, key=lambda p: p.relative_to(root).as_posix())


def read_global_json(path: Path, name: str):
    text = path.read_text(encoding="utf-8")
    match = re.search(r"window\." + re.escape(name) + r"\s*=\s*", text)
    if not match:
        raise ValueError(f"Missing window.{name} assignment")
    prefix = re.sub(r"/\*.*?\*/|//[^\n]*(?:\n|$)", "", text[:match.start()], flags=re.S).strip()
    if prefix:
        raise ValueError(f"Unexpected executable prefix in {name} data")
    value, end = json.JSONDecoder().raw_decode(text[match.end():])
    if text[match.end() + end:].strip() not in ("", ";"):
        raise ValueError(f"Unexpected executable suffix in {name} data")
    return value


def validate_route_data(path: Path):
    text = path.read_text(encoding="utf-8")
    match = re.match(r'^\s*window\.TOPO_ROUTES\s*=\s*window\.TOPO_ROUTES\s*\|\|\s*\{\s*\}\s*;'
                     r'\s*window\.TOPO_ROUTES\["([^"\\]+)"\]\s*=\s*', text)
    if not match:
        raise ValueError("Route file does not use the expected classic global data assignment")
    value, end = json.JSONDecoder().raw_decode(text[match.end():])
    if text[match.end() + end:].strip() not in ("", ";"):
        raise ValueError("Unexpected executable suffix in route data")
    if match.group(1) != path.stem or value.get("id") != path.stem:
        raise ValueError("Route data ID does not match its filename")


class AssetParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.assets, self.errors, self.csp = [], [], ""

    def handle_starttag(self, tag, attributes):
        attrs = dict(attributes)
        if tag == "script":
            if attrs.get("type", "").lower() == "module":
                self.errors.append("ES-module script tag is not permitted for the file:// runtime")
            if attrs.get("src"):
                self.assets.append(("script", attrs["src"]))
        elif tag == "link" and any(word in attrs.get("rel", "").lower().split()
                                    for word in ("stylesheet", "preload", "modulepreload", "icon")):
            if attrs.get("rel") == "modulepreload":
                self.errors.append("Module preload is not permitted")
            if attrs.get("href"):
                self.assets.append(("link", attrs["href"]))
        elif tag in ("img", "iframe", "audio", "video", "source", "embed", "input"):
            for key in ("src", "poster"):
                if attrs.get(key):
                    self.assets.append((tag, attrs[key]))
            if attrs.get("srcset"):
                for candidate in attrs["srcset"].split(","):
                    self.assets.append((tag, candidate.strip().split()[0]))
        elif tag == "object" and attrs.get("data"):
            self.assets.append((tag, attrs["data"]))
        elif tag == "meta":
            if attrs.get("http-equiv", "").lower() == "content-security-policy":
                self.csp = attrs.get("content", "")
            if attrs.get("http-equiv", "").lower() == "refresh":
                self.errors.append("Automatic meta refresh is not permitted")


def check_local_asset(root: Path, owner: Path, reference: str, errors: list[str]):
    reference = reference.strip().strip("\"'")
    if not reference or reference.startswith(("data:", "blob:", "#")):
        return
    parsed = urlsplit(reference)
    relative_owner = owner.relative_to(root).as_posix()
    if parsed.scheme or parsed.netloc or reference.startswith("//"):
        errors.append(f"External/non-portable runtime asset in {relative_owner}: {reference}")
        return
    if parsed.path.startswith(("/", "\\")):
        errors.append(f"Absolute asset path in {relative_owner}: {reference}")
        return
    target = (owner.parent / unquote(parsed.path)).resolve()
    if not target.is_relative_to((root / "app").resolve()):
        errors.append(f"Runtime asset escapes app directory in {relative_owner}: {reference}")
    elif not target.is_file():
        errors.append(f"Missing runtime asset in {relative_owner}: {reference}")


def tree_bytes(path: Path):
    if not path.is_dir():
        return 0
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file() and not p.is_symlink())


def git_inventory(root: Path, errors: list[str], warnings: list[str]):
    try:
        result = subprocess.run(["git", "-C", str(root), "ls-files", "-z"], check=False,
                                capture_output=True, timeout=20)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        warnings.append("Git inventory unavailable; distribution size is still checked")
        return {"available": False}
    if result.returncode:
        warnings.append("This copy has no usable Git metadata; distribution size is still checked")
        return {"available": False}
    total, count, missing = 0, 0, []
    for raw in result.stdout.split(b"\0"):
        if not raw:
            continue
        relative = Path(os.fsdecode(raw))
        path = root / relative
        if excluded(relative):
            errors.append(f"Ignored/dependency/research material is tracked by Git: {relative.as_posix()}")
        if not path.is_file():
            missing.append(relative.as_posix())
            continue
        count += 1
        size = path.stat().st_size
        total += size
        if size > FILE_LIMIT:
            errors.append(f"Tracked file exceeds 50 MB: {relative.as_posix()} ({size} bytes)")
    if total > REPO_LIMIT:
        errors.append(f"Git-tracked working files exceed 400 MB: {total} bytes")
    if missing:
        warnings.append(f"{len(missing)} tracked paths are absent from the working tree")
    return {"available": True, "trackedFiles": count, "trackedWorkingBytes": total,
            "metadataBytes": tree_bytes(root / ".git"), "note": "Current tracked contents, not every historical Git object."}


def validate(root: Path = ROOT):
    root = root.resolve()
    errors, warnings = [], []
    files = collect_release_files(root)
    by_directory = defaultdict(int)
    sizes = []
    for path in files:
        relative = path.relative_to(root)
        if path.is_symlink() or not path.resolve().is_relative_to(root):
            errors.append(f"Symlink/nonportable path in distribution: {relative.as_posix()}")
            continue
        size = path.stat().st_size
        sizes.append((relative.as_posix(), size))
        by_directory[relative.parts[0]] += size
        if size > FILE_LIMIT:
            errors.append(f"Distribution file exceeds 50 MB: {relative.as_posix()} ({size} bytes)")
    total = sum(size for _, size in sizes)
    if total > REPO_LIMIT:
        errors.append(f"Distribution exceeds 400 MB: {total} bytes")
    for name in REQUIRED:
        if not (root / name).is_file():
            errors.append("Missing required file: " + name)
    for name, global_name in GLOBALS.items():
        if (root / name).is_file():
            with (root / name).open(encoding="utf-8") as stream:
                prefix = stream.read(4096)
            if not re.search(r"window\." + global_name + r"\s*=", prefix):
                errors.append(f"Missing classic global window.{global_name}: {name}")
    html_count = css_count = 0
    for path in files:
        if not path.is_relative_to(root / "app"):
            continue
        if path.suffix == ".html":
            html_count += 1
            parser = AssetParser()
            parser.feed(path.read_text(encoding="utf-8"))
            errors.extend(f"{path.relative_to(root).as_posix()}: {error}" for error in parser.errors)
            for _, reference in parser.assets:
                check_local_asset(root, path, reference, errors)
            if path == root / "app/index.html":
                if not re.search(r"(?:^|;)\s*connect-src\s+'none'\s*(?:;|$)", parser.csp):
                    errors.append("Index CSP must declare connect-src 'none'")
                if re.search(r"https?:|(?<!\S)\*(?!\S)", parser.csp):
                    errors.append("Index CSP permits remote network origins")
        elif path.suffix == ".css":
            css_count += 1
            text = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
            for reference in re.findall(r"url\(\s*([^)]*?)\s*\)", text, re.I):
                check_local_asset(root, path, reference, errors)
            for reference in re.findall(r"@import\s+['\"]([^'\"]+)['\"]", text, re.I):
                check_local_asset(root, path, reference, errors)
    network_patterns = [r"\bfetch\s*\(", r"\bXMLHttpRequest\b", r"\bWebSocket\b", r"\bEventSource\b",
                        r"\bsendBeacon\s*\(", r"\bimport\s*\([^)]*\)\s*(?!\s*\{)", r"\bserviceWorker\s*\.\s*register\s*\(",
                        r"^\s*(?:import|export)\s", r"\btileLayer\s*\(\s*['\"]https?://",
                        r"\.src\s*=\s*['\"]https?://", r"<(?:script|img|iframe)\b[^>]*\bsrc\s*=\s*['\"]https?://"]
    scanned_js = 0
    # These files are parsed as a single strict JSON assignment below. Searching
    # tens of MB of quoted map values for JavaScript keywords adds no protection.
    pure_global_files = {root / "app/data" / name for name in ("seru_bank.js", "topo_bank.js", "map_data.js")}
    for directory in (root / "app",):
        if not directory.is_dir():
            continue
        for path in sorted(directory.rglob("*.js")):
            scanned_js += 1
            if path in pure_global_files:
                continue
            if path.parent == root / "app/data/topo_routes":
                try:
                    validate_route_data(path)
                except (ValueError, KeyError, TypeError) as exc:
                    errors.append(f"Invalid classic route data {path.relative_to(root).as_posix()}: {exc}")
                continue
            text = path.read_text(encoding="utf-8")
            for pattern in network_patterns:
                if re.search(pattern, text, re.I | re.M):
                    errors.append(f"Network/module construction in {path.relative_to(root).as_posix()}: {pattern}")
    image_refs = subgraphs = expected_tiles = 0
    bank_path, graph_path = root / "app/data/topo_bank.js", root / "app/data/map_data.js"
    if bank_path.is_file():
        try:
            bank = read_global_json(bank_path, "TOPO_BANK")
            route_count = sum(q.get("type") == "route" for q in bank)
            static_count = sum(q.get("type") != "route" for q in bank)
            if route_count < 140 or static_count < 400:
                errors.append(f"Incomplete Topographical bank: {route_count}/140 routes and {static_count}/400 static-map items")
            for question in bank:
                if question.get("map"):
                    image_refs += 1
                    check_local_asset(root, root / "app/index.html", question["map"], errors)
                if question.get("type") == "route":
                    subgraphs += 1
                    graph_file = root / "app/data/topo_routes" / (question["id"] + ".js")
                    if not graph_file.is_file():
                        errors.append("Missing route subgraph: " + graph_file.relative_to(root).as_posix())
        except (ValueError, KeyError, TypeError) as exc:
            errors.append("Cannot inspect topographical asset references: " + str(exc))
    seru_path = root / "app/data/seru_bank.js"
    if seru_path.is_file():
        try:
            seru = read_global_json(seru_path, "SERU_BANK")
            for kind, minimum in (("mcq", 350), ("cloze", 150), ("reading", 40)):
                count = sum(q.get("type") == kind for q in seru)
                if count < minimum:
                    errors.append(f"Incomplete SERU bank: {count}/{minimum} {kind} items")
        except (ValueError, KeyError, TypeError) as exc:
            errors.append("Cannot inspect SERU bank completeness: " + str(exc))
    if graph_path.is_file():
        try:
            graph = read_global_json(graph_path, "PHV_MAP")
            (south, west), (north, east) = graph["bounds"]
            for z in range(graph["minZoom"], graph["maxZoom"] + 1):
                def tile(lon, lat):
                    return (int((lon + 180) / 360 * 2**z),
                            int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * 2**z))
                x0, y0 = tile(west, north)
                x1, y1 = tile(east, south)
                for x in range(x0, x1 + 1):
                    for y in range(y0, y1 + 1):
                        expected_tiles += 1
                        name = f"app/tiles/{z}/{x}/{y}.webp"
                        if not (root / name).is_file():
                            errors.append("Missing declared-coverage tile: " + name)
            del graph
        except (ValueError, KeyError, TypeError, OverflowError) as exc:
            errors.append("Cannot inspect tile coverage: " + str(exc))
    git = git_inventory(root, errors, warnings)
    checkout_with_git = total + git.get("metadataBytes", 0)
    if checkout_with_git > REPO_LIMIT:
        errors.append(f"Portable source plus current Git metadata exceeds 400 MB: {checkout_with_git} bytes")
    return {"status": "PASS" if not errors else "FAIL", "root": str(root),
            "scope": "Portable source/distribution; ignored research/dependencies/caches/Git metadata excluded",
            "distributionFiles": len(files), "distributionBytes": total,
            "limitsBytes": {"distribution": REPO_LIMIT, "singleFile": FILE_LIMIT},
            "byDirectoryBytes": dict(sorted(by_directory.items())),
            "largestFiles": [{"path": name, "bytes": size} for name, size in sorted(sizes, key=lambda v: v[1], reverse=True)[:10]],
            "assetChecks": {"htmlFiles": html_count, "stylesheets": css_count, "runtimeJavaScriptFiles": scanned_js,
                            "staticMapReferences": image_refs, "routeSubgraphs": subgraphs, "declaredCoverageTiles": expected_tiles},
            "git": git, "portableSourcePlusGitBytes": checkout_with_git,
            "freeDiskBytes": shutil.disk_usage(root).free, "warnings": warnings,
            "errorCount": len(errors), "errors": errors,
            "limitsOfCheck": "Static inspection; file:// browser tests and real launcher testing are separate. Clicked study links may open online pages."}


def print_report(report, as_json=False):
    if as_json:
        print(json.dumps(report, indent=2))
        return
    print(f"Release checks {report['status']}: {report['distributionFiles']} files, "
          f"{report['distributionBytes'] / 1_000_000:.2f} MB / 400 MB")
    for entry in report["largestFiles"][:3]:
        print(f"  {entry['path']}: {entry['bytes'] / 1_000_000:.2f} MB / 50 MB")
    assets = report["assetChecks"]
    print(f"Assets: {assets['staticMapReferences']} map references; {assets['routeSubgraphs']} route graphs; "
          f"{assets['declaredCoverageTiles']} tiles checked")
    if report["git"]["available"]:
        print(f"Git-tracked working files: {report['git']['trackedWorkingBytes'] / 1_000_000:.2f} MB; "
              f"Git metadata separately: {report['git']['metadataBytes'] / 1_000_000:.2f} MB")
        print(f"Portable source plus current Git metadata: {report['portableSourcePlusGitBytes'] / 1_000_000:.2f} MB / 400 MB")
    for warning in report["warnings"]:
        print("WARNING:", warning)
    for error in report["errors"][:30]:
        print("ERROR:", error)
    if report["errorCount"] > 30:
        print(f"... {report['errorCount'] - 30} further errors (use --json)")
    print("Read-only: no archive created. Browser/launcher checks are separate.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT, help="Also supports an extracted copy in a path containing spaces")
    parser.add_argument("--check-only", action="store_true", help="Explicit read-only mode; this is already the default")
    parser.add_argument("--json", action="store_true", help="Print the full machine-readable report")
    args = parser.parse_args()
    report = validate(args.root)
    print_report(report, args.json)
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
