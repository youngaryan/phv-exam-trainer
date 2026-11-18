"""Validate SERU data structure, provenance, coverage and textual quality.

This is not an automatic proof that a factual answer is correct. The separate
source audit in docs/SERU_AUDIT.md records the source-reading work and limitations.
Run from any directory. Requires rapidfuzz from requirements-seru.txt.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter
from pathlib import Path

from rapidfuzz.fuzz import ratio

ROOT = Path(__file__).resolve().parents[1]
BOUNDARIES = {1: (6, 11), 2: (12, 13), 3: (14, 17), 4: (18, 22), 5: (23, 25),
              6: (26, 30), 7: (31, 37), 8: (38, 42), 9: (43, 45), 10: (46, 46)}
REQUIRED_SUBSECTIONS = {
    1: ["Licensing requirements", "Private hire driver's licence", "Your PHV driver's badge",
        "Lost PHV driver's badge and licence", "Medical conditions", "Change of address",
        "Other changes in personal circumstances", "Convictions, cautions and arrests",
        "Other fixed penalties, parking tickets and PCNs", "Right to live and work in the United Kingdom",
        "Complaints", "Suspending or revoking a PHV driver's licence",
        "Revoking a driver's private hire vehicle licence", "Disclosure and Barring Service"],
    2: ["Licences and licence discs", "Insurance", "Collision damage", "Information about vehicles"],
    3: ["Bookings", "Booking details", "Operating centres in late night venues", "Airports",
        "Journeys outside Greater London", "Fares", "Lost property", "Suspicious items and behaviour",
        "When a booking cannot be carried out"],
    4: ["Driver safety", "Protecting yourself", "Warning signs of possible aggressive behaviour",
        "Drugs and alcohol", "Reducing the risk of violence in a difficult situation",
        "If you cannot reduce the risk of violence", "After an incident",
        "What to do if you are attacked or assaulted", "CCTV cameras"],
    5: ["Complaints", "Unacceptable behaviour", "Entering the back of your vehicle", "Unacceptable sexual behaviour"],
    6: ["Stopping and waiting", "Bus lanes and bus stops", "Taxi ranks", "Electric taxi charging points",
        "Penalty Charge Notices", "Congestion Charging", "Ultra Low Emission Zone", "Red routes"],
    7: ["Obey the law", "Safe speeds", "Safe manoeuvres", "Concentration", "Use of alcohol or drugs",
        "Prescription medicine", "Following traffic laws before a journey begins", "Being aware of other road users",
        "In clear sight", "Be cradle careful", "Other things to consider", "Cycle safety", "Top tips",
        "Driver's compartment", "Passenger compartment", "Wheels and tyres", "Outside the vehicle"],
    8: ["Assisting passengers", "Equality Act 2010", "Designated wheelchair accessible PHVs",
        "Exemptions from wheelchair duties", "Assistance dogs", "Dogs and Islamic law",
        "Exemptions from assistance-dog duties", "Complaints about equality duties"],
    9: ["Safeguarding Children and Adults at Risk", "Who is a child or an adult at risk?",
        "Carrying unaccompanied children in your vehicle", "Carrying children and adults at risk in your vehicle",
        "County lines", "Signs that a child or vulnerable person is at risk", "Reporting safeguarding concerns", "Other support"],
    10: ["Ridesharing"],
}


def load_bank(path=None):
    text = (path or ROOT / "app/data/seru_bank.js").read_text(encoding="utf-8")
    return json.loads(text.split("window.SERU_BANK = ", 1)[1].rstrip(";\n\r "))


def normalise(text):
    return re.sub(r"\s+", " ", text.casefold()).strip()


def validate(bank):
    errors, near = [], []
    ids = set()
    counts = Counter(q.get("type") for q in bank)
    for kind, minimum in [("mcq", 350), ("cloze", 150), ("reading", 40)]:
        if counts[kind] < minimum:
            errors.append(f"{kind}: {counts[kind]} < {minimum}")
    for q in bank:
        label = q.get("id", "<missing id>")
        def require(condition, message):
            if not condition:
                errors.append(f"{label}: {message}")
        require(bool(re.match(r"^SERU-\d{2}-[A-Z0-9]+-(MCQ|READING|CLOZE)-\d{3}$", label)), "invalid ID")
        require(label not in ids, "duplicate ID")
        ids.add(label)
        kind, section = q.get("type"), q.get("section")
        require(kind in ("mcq", "reading", "cloze"), "invalid type")
        require(section in BOUNDARIES, "invalid section")
        ref = q.get("handbook", {})
        page = ref.get("page", 0)
        require(ref.get("version") == "1.0", "wrong or missing version")
        lo, hi = BOUNDARIES.get(section, (1, 0))
        require(isinstance(page, int) and lo <= page <= hi, "page outside section")
        require(q.get("difficulty") in (1, 2, 3), "difficulty must be 1-3")
        require(bool(q.get("tags")) and all(isinstance(t, str) for t in q["tags"]), "missing tags")
        require(bool(q.get("subsection")), "missing subsection")
        require(bool(q.get("question")), "missing question")
        require(bool(q.get("explanation")), "missing explanation")
        require(q.get("evidenceKind") == "paraphrase", "evidence must be explicitly identified as paraphrase")
        require(1 <= len(q.get("evidence", "").split()) <= 25, "evidence paraphrase must have at most 25 words")
        require(q.get("sourceURL") == f"https://content.tfl.gov.uk/phv-driver-handbook-v1.pdf#page={page}", "missing exact source link")
        require(bool(q.get("provenance", {}).get("authoring")), "missing authoring provenance")
        content = " ".join(str(q.get(k, "")) for k in ("question", "options", "passage", "explanation", "evidence"))
        require("all of the above" not in content.casefold(), "all-of-the-above option")
        require(not re.search(r"\b(behavior|color|center|analyze|license|maneuver)\b", content, re.I), "non-British spelling")
        if kind in ("mcq", "reading"):
            options = q.get("options", [])
            require(len(options) == 3 and len(set(map(normalise, options))) == 3, "need three distinct options")
            require(type(q.get("answer")) is int and 0 <= q["answer"] < 3, "invalid single answer")
        if kind == "reading":
            require(60 <= len(q.get("passage", "").split()) <= 150, "reading passage outside 60-150 words")
            require(q["question"] == "Question: Which one of the following statements is correct?", "reading instruction wording")
        if kind == "cloze":
            blanks, word_bank = q.get("blanks", {}), q.get("wordBank", [])
            require(2 <= len(blanks) <= 4, "need 2-4 blanks")
            require(set(re.findall(r"\{\{(\d+)\}\}", q.get("passage", ""))) == set(blanks), "blank placeholders mismatch")
            require(len(set(word_bank)) == len(word_bank), "duplicate word tiles")
            require(set(blanks.values()) <= set(word_bank), "missing correct word")
            require(len(word_bank) > len(blanks), "no distractors for red box")
            require(len(set(blanks.values())) == len(blanks), "identical answers need multiple indistinguishable tiles")
            completed = re.sub(r"\{\{(\d+)\}\}", lambda m: blanks[m.group(1)], q.get("passage", ""))
            require(completed == q["evidence"], "completed cloze differs from authored fact")
    for section, names in REQUIRED_SUBSECTIONS.items():
        present = {q["subsection"] for q in bank if q["section"] == section}
        errors.extend(f"Section {section}: missing subsection {name}" for name in names if name not in present)
    for kind in ("mcq", "reading"):
        positions = Counter(q["answer"] for q in bank if q["type"] == kind)
        if max(positions.values()) - min(positions.values()) > 1 or len(positions) != 3:
            errors.append(f"{kind}: unbalanced answer positions {dict(positions)}")
    for kind in ("mcq", "reading", "cloze"):
        questions = [q for q in bank if q["type"] == kind]
        # Reading instructions and cloze instructions are necessarily identical;
        # compare the actual passage for these types, the stem for MCQ.
        key = "question" if kind == "mcq" else "passage"
        for i, q in enumerate(questions):
            for other in questions[:i]:
                score = ratio(normalise(q[key]), normalise(other[key]))
                if score > 85:
                    near.append({"first": other["id"], "second": q["id"], "similarity": round(score, 2)})
    for pair in near:
        errors.append("Near duplicate >85: " + json.dumps(pair))
    return errors, near


def main():
    bank = load_bank()
    errors, near = validate(bank)
    report = {"status": "PASS" if not errors else "FAIL", "items": len(bank),
              "types": dict(Counter(q["type"] for q in bank)),
              "sections": dict(Counter(q["section"] for q in bank)),
              "mcqAnswerPositions": dict(Counter(q["answer"] for q in bank if q["type"] == "mcq")),
              "readingAnswerPositions": dict(Counter(q["answer"] for q in bank if q["type"] == "reading")),
              "nearDuplicateThreshold": 85, "nearDuplicates": near, "errors": errors,
              "limitation": "Structural validation does not prove factual correctness; see docs/SERU_AUDIT.md."}
    (ROOT / "tools/seru_validation.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
