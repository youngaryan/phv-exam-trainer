"""Extract a locally downloaded handbook into ignored review material.

The handbook is intentionally not redistributed. Download the source linked in
the README, then run this script. Page numbers are one-based printed PDF pages.
Subsection review packets retain complete referenced pages for context; headings
which cross a page are therefore not truncated by a brittle automatic splitter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

import pdfplumber

from build_seru import ROOT, SOURCE, read_records


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("pdf", nargs="?", type=Path, default=ROOT / "research/official/phv-driver-handbook-v1.pdf")
    args = parser.parse_args()
    with pdfplumber.open(args.pdf) as pdf:
        pages = [page.extract_text() or "" for page in pdf.pages]
    if len(pages) != 52 or "30 September 2021" not in pages[1]:
        raise ValueError("This builder is scoped to the 52-page handbook v1.0 dated 30 September 2021")
    output = ROOT / "research/seru"
    output.mkdir(parents=True, exist_ok=True)
    (output / "pages.json").write_text(json.dumps(pages, ensure_ascii=False, indent=2), encoding="utf-8")
    groups = defaultdict(set)
    for record in read_records():
        groups[(record["section"], record["subsection"])].add(record["page"])
    chunks = [{"section": section, "subsection": subsection,
               "pageContext": [{"page": p, "text": pages[p - 1]} for p in sorted(page_numbers)]}
              for (section, subsection), page_numbers in sorted(groups.items())]
    (output / "subsection_review_packets.json").write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    metadata = {"source": SOURCE, "version": "1.0", "pages": len(pages),
                "pdfSha256": hashlib.sha256(args.pdf.read_bytes()).hexdigest(),
                "subsections": len(chunks), "note": "Complete referenced page contexts, not isolated sentence excerpts."}
    (output / "source_metadata.json").write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
