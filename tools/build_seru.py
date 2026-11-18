"""Build the original, page-linked SERU bank. No handbook text is redistributed.

The pipe-separated authoring files contain manually written questions, distractors
and short evidence paraphrases. Brackets mark authored cloze alternatives, not
verbatim handbook text. Run with tools/.venv/Scripts/python tools/build_seru.py.
"""
from __future__ import annotations

import hashlib
import json
import random
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = "https://content.tfl.gov.uk/phv-driver-handbook-v1.pdf"
SECTIONS = {
    1: "London PHV Driver Licensing", 2: "Licensing Requirements for PHVs",
    3: "Carrying out Private Hire Journeys", 4: "Staying Safe",
    5: "Driver Behaviour", 6: "Driving and Parking in London",
    7: "Safer Driving", 8: "Being Aware of Equality and Disability",
    9: "Safeguarding Children and Adults at Risk", 10: "Ridesharing",
}
STARTS = {1: 6, 2: 12, 3: 14, 4: 18, 5: 23, 6: 26, 7: 31, 8: 38, 9: 43, 10: 46}
SLOT = re.compile(r"\[([^\]~]+)~([^\]]+)\]")


def section_for(page):
    return max(s for s, start in STARTS.items() if page >= start)


def plain(value):
    return SLOT.sub(lambda m: m.group(1), value)


def read_records():
    records = []
    for path in sorted((ROOT / "tools").glob("seru_items_*.txt")):
        for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not raw or raw.startswith("#"):
                continue
            parts = raw.split("|")
            if len(parts) != 7:
                raise ValueError(f"{path.name}:{line_number}: expected seven fields")
            page, subsection, question, correct, wrong1, wrong2, annotated = parts
            record = dict(page=int(page), subsection=subsection, question=question,
                          correct=correct, wrong=[wrong1, wrong2], annotated=annotated,
                          authoredAt=f"tools/{path.name}:{line_number}")
            record["section"] = section_for(record["page"])
            record["evidence"] = plain(annotated)
            records.append(record)
    return sorted(records, key=lambda r: (r["page"], r["authoredAt"]))


def difficulty_for(record, kind):
    if kind == "reading":
        return 2
    if kind == "cloze":
        return 2 if any(char.isdigit() for char in record["evidence"]) else 1
    text = record["question"].lower()
    if any(term in text for term in ("exception", "unless", "exemption", "but ", "in addition", "no correct child seat")):
        return 3
    return 2 if any(term in text for term in ("passenger", "what should", "after ", "before ", "may ", "when ", "why ")) else 1


def base(record, kind, number):
    slug = re.sub(r"[^A-Z0-9]+", "", record["subsection"].upper())[:28]
    return {
        "id": f"SERU-{record['section']:02}-{slug}-{kind.upper()}-{number:03}",
        "type": kind, "section": record["section"],
        "sectionName": SECTIONS[record["section"]], "subsection": record["subsection"],
        "handbook": {"version": "1.0", "page": record["page"]},
        "evidence": record["evidence"], "evidenceKind": "paraphrase",
        "sourceURL": SOURCE + "#page=" + str(record["page"]),
        "explanation": record["evidence"] + " This is the rule described in the cited handbook passage.",
        "difficulty": difficulty_for(record, kind),
        "tags": [re.sub(r"[^a-z0-9]+", "-", record["subsection"].lower()).strip("-")],
        "provenance": {"source": "TfL PHV Driver's Handbook v1.0", "authoring": record["authoredAt"],
                       "scope": "Handbook knowledge; not a statement of current law or operational charging exemptions."},
    }


def rotated_options(correct, wrong, position):
    options = list(wrong)
    options.insert(position, correct)
    return options


def build_mcq(records):
    result = []
    for i, record in enumerate(records, 1):
        q = base(record, "mcq", i)
        q.update(question=record["question"], options=rotated_options(record["correct"], record["wrong"], (i - 1) % 3),
                 answer=(i - 1) % 3)
        result.append(q)
    return result


# Authored grammatical near-misses make the language exercises resemble sentence
# completion instead of relying on implausible unrelated nouns.
NEAR_MISS = {
    "live": "living", "work": "working", "full": "fully", "licensed": "licensing",
    "doctor": "doctors", "complete": "completed", "enhanced": "enhancement",
    "suitable": "suitability", "map": "maps", "route": "routes", "conditions": "conditional",
    "letter": "letters", "revocation": "revoked", "safely": "safe", "copies": "copying",
    "driving": "driven", "immediately": "immediate", "respond": "response", "contact": "contacted",
    "visible": "visibly", "travelling": "travel", "number": "numbering", "exemption": "exempt",
    "notice": "notices", "badge": "badges", "personal": "personally", "lent": "lending",
    "reference": "referred", "returned": "returning", "replacement": "replaced",
    "expiry": "expired", "renewal": "renewed", "annual": "annually", "driver": "drivers",
    "form": "forms", "promptly": "prompt", "drive": "driving", "report": "reporting",
    "advice": "advise", "home": "homes", "address": "addressing", "notification": "notified",
    "return": "returning", "orders": "ordering", "authority": "authorised", "arrest": "arrested",
    "conviction": "convicted", "offences": "offending", "points": "pointed", "reported": "reporting",
    "behaviour": "behave", "action": "acting", "continuing": "continued", "account": "accounting",
    "decision": "decisive", "vehicle": "vehicles", "safety": "safely", "specified": "specify",
    "check": "checking", "barred": "barring", "status": "stated", "inspection": "inspected",
    "private": "privately", "damage": "damaged", "use": "using", "keeper": "keeping",
    "licence": "licensing", "carry": "carrying", "permanent": "permanently", "removed": "removal",
    "rent": "rented", "own": "owned", "hire": "hiring", "reward": "rewarding",
    "covered": "covering", "requested": "requesting", "collision": "colliding", "person": "persons",
    "hours": "hourly", "read": "reading", "recall": "recalled", "operator": "operators",
    "checker": "checking", "booking": "booked", "enters": "entering", "before": "after",
    "words": "wording", "journey": "journeys", "destination": "destinations", "change": "changing",
    "agreed": "agreeing", "estimate": "estimated", "first": "firstly", "place": "placing",
    "parking": "parked", "noise": "noisy", "idling": "idled", "official": "officially",
    "legality": "legal", "agrees": "agreeing", "safe": "safely", "changes": "changing",
    "record": "recording", "instructions": "instructed", "significance": "significant",
    "confidentially": "confidential", "polite": "politely", "cancellation": "cancelled",
    "disability": "disabled", "refuse": "refusal", "fulfilled": "fulfilling", "good": "well",
    "abusive": "abusively", "possible": "possibly", "name": "naming", "duration": "durations",
    "fare": "fares", "aggression": "aggressive", "assistance": "assisting", "alone": "lonely",
    "identity": "identify", "fists": "fisted", "voice": "voicing", "early": "earlier",
    "escalation": "escalating", "ignore": "ignoring", "communication": "communicating",
    "unpredictable": "unpredictably", "pickup": "picked up", "walk": "walking", "refusal": "refused",
    "friend": "friendly", "arrive": "arrival", "sight": "sighted", "calmly": "calm",
    "interrupting": "interrupted", "concerns": "concerning", "explanations": "explained",
    "arguments": "arguing", "exit": "exiting", "situation": "situated", "stopping": "stopped",
    "help": "helping", "leave": "leaving", "keys": "keyed", "calm": "calmly",
    "support": "supporting", "incident": "incidental", "time": "timely", "location": "located",
    "witness": "witnessing", "description": "described", "clothing": "clothed", "type": "typed",
    "actions": "acting", "evidence": "evident", "dispute": "disputed", "signage": "signed",
    "see": "seeing", "blocking": "blocked", "entry": "entered", "details": "detailed",
    "complaints": "complaining", "crimes": "criminal", "comments": "commenting", "professional": "professionally",
    "ease": "easily", "emergency": "emergencies", "discomfort": "uncomfortable", "necessary": "necessarily",
    "unacceptable": "unacceptably", "agreement": "agreeing", "accepted": "accepting", "sexual": "sexually",
    "staring": "stared", "uncomfortable": "uncomfortably", "touching": "touched", "assault": "assaulted",
    "appropriate": "appropriately", "inappropriate": "inappropriately", "permission": "permitted",
    "obstruction": "obstructing", "danger": "dangerous", "signs": "signed", "restrictions": "restricted",
    "boarding": "boarded", "wheelchair": "wheelchairs", "securing": "secured", "council": "councils",
    "shopping": "shopped", "illegal": "illegally", "kerb": "kerbs", "directly": "direct",
    "cyclists": "cycling", "line": "lined", "obstruct": "obstructing", "delay": "delayed",
    "empty": "emptied", "fine": "fined", "points": "pointed", "postal": "posted",
    "offence": "offending", "turns": "turning", "charge": "charging", "times": "timing",
    "air": "aired", "standards": "standardised", "date": "dated", "waiting": "waited",
    "minutes": "minute", "prohibitions": "prohibited", "limits": "limited", "obey": "obeying",
    "road": "roads", "causes": "caused", "react": "reaction", "severity": "severe",
    "carefully": "careful", "awareness": "aware", "judgement": "judging", "impaired": "impairing",
    "maintenance": "maintained", "standard": "standardised", "encourage": "encouragement",
    "age": "aged", "seatbelt": "seatbelts", "rear": "rearing", "seats": "seated",
    "ban": "banned", "loss": "lost", "stepping": "stepped", "care": "caring",
    "turning": "turned", "traffic": "trafficked", "clean": "cleanly", "vision": "visual",
    "visibility": "visible", "distraction": "distracted", "tired": "tiring", "breaks": "breaking",
    "speed": "speeding", "attention": "attentive", "moving": "moved", "direction": "directed",
    "indicators": "indicating", "advance": "advanced", "confusion": "confused", "enough": "many",
    "clearance": "clear", "secure": "securely", "condition": "conditional", "adjustable": "adjusted",
    "covers": "covering", "correctly": "correct", "working": "worked", "functional": "functioning",
    "locking": "locked", "installed": "installing", "available": "availability", "weight": "weighted",
    "present": "presently", "bulges": "bulging", "cuts": "cutting", "uneven": "unevenly",
    "replaced": "replacing", "leaks": "leaking", "undamaged": "damage", "repairs": "repairing",
    "defect": "defective", "advertising": "advertised", "acceptance": "accepted", "respond": "response",
    "arm": "arms", "push": "pushing", "patient": "patiently", "fastened": "fastening",
    "departure": "departed", "speak": "speaking", "information": "informed", "difficulties": "difficult",
    "requests": "requested", "differ": "different", "hazards": "hazardous", "slopes": "sloping",
    "belongings": "belonging", "arrival": "arrived", "delays": "delaying", "difficulty": "difficult",
    "assist": "assistance", "respectfully": "respectful", "assumptions": "assumed", "extra": "extremely",
    "securely": "secure", "comfort": "comfortable", "reasonably": "reasonable", "designation": "designated",
    "medical": "medically", "approval": "approved", "displayed": "displaying", "feed": "feeding",
    "distract": "distraction", "lack": "lacking", "role": "roles", "breeds": "breeding",
    "pictures": "pictured", "accompany": "accompanying", "grounds": "grounded", "application": "applied",
    "investigates": "investigating", "duties": "dutiful", "sufficient": "sufficiently", "interest": "interested",
    "suitability": "suitable", "harm": "harmful", "abuse": "abusive", "adults": "adult",
    "exploitation": "exploited", "protection": "protected", "illness": "ill", "notice": "notices",
    "exploiting": "exploited", "counties": "county", "transport": "transporting", "warning": "warned",
    "unknown": "knowing", "decisions": "deciding", "neglect": "neglected", "risk": "risky",
    "concern": "concerned", "money": "monies", "kindness": "kind", "professionalism": "professional",
    "controller": "controlled", "crime": "criminal", "unfamiliar": "unfamiliarly", "separate": "separately",
    "training": "trained", "service": "servicing", "routines": "routinely", "strangers": "strange",
    "mistaken": "mistakenly", "numbers": "numbered", "pickups": "picked up", "cost": "costing",
    "clear": "clearly", "recurring": "recurred", "closing": "closed", "order": "ordered"
}


def cloze_from(record, number):
    q = base(record, "cloze", number)
    matches = list(SLOT.finditer(record["annotated"]))
    if not 2 <= len(matches) <= 4:
        raise ValueError(f"Expected 2-4 authored blanks: {record['question']}")
    blanks, words = {}, []
    for i, match in enumerate(matches, 1):
        blanks[str(i)] = match.group(1)
        words.extend([match.group(1), NEAR_MISS.get(match.group(1), match.group(2))])
    if len(set(words)) != len(words):
        return None
    counter = iter(range(1, len(matches) + 1))
    passage = SLOT.sub(lambda m: "{{" + str(next(counter)) + "}}", record["annotated"])
    random.Random(909 + number).shuffle(words)
    q.update(question="Complete the passage.", passage=passage, blanks=blanks, wordBank=words)
    return q


def build_cloze(records):
    from rapidfuzz.fuzz import ratio
    by_section = defaultdict(list)
    for record in records:
        by_section[record["section"]].append(record)
    rng = random.Random(20261118)
    for values in by_section.values():
        rng.shuffle(values)
    # Proportional to authored coverage, with all ten sections represented.
    quotas = {s: int(150 * len(values) / len(records)) for s, values in by_section.items()}
    for s in sorted(quotas, key=lambda s: (150 * len(by_section[s]) / len(records)) % 1, reverse=True)[:150 - sum(quotas.values())]:
        quotas[s] += 1
    result = []
    for section in sorted(by_section):
        selected = 0
        for record in by_section[section]:
            q = cloze_from(record, len(result) + 1)
            if q is None:
                continue
            if any(ratio(q["passage"].lower(), old["passage"].lower()) > 85 for old in result):
                continue
            result.append(q)
            selected += 1
            if selected == quotas[section]:
                break
        if selected != quotas[section]:
            raise ValueError(f"Not enough distinct cloze records in section {section}")
    return result


INTRO = {
    6: "A prospective driver is organising an application and checking which requirements must be satisfied before private hire work can begin.",
    7: "A newly licensed driver prepares for work and checks the documents, identification and communications that need attention during the licence period.",
    8: "A driver reviews what to do when identification is lost and how medical requirements affect continued private hire work.",
    9: "A driver has moved home and is reviewing which changes in personal circumstances must be brought to the licensing authority's attention.",
    10: "An experienced driver checks the reporting duties that continue throughout a licence, including offences, complaints and changes affecting permission to work.",
    11: "An applicant reviews the background-check process and the connection between driver suitability, vehicle licensing and the protection of the travelling public.",
    12: "A driver is about to use a licensed vehicle and checks how its licence and identification discs should be managed.",
    13: "An owner-driver reviews insurance documents and considers what must happen if the vehicle is damaged or recalled for a safety repair.",
    14: "A driver receives several enquiries about journeys and wants to distinguish lawful operator bookings from requests made directly on the street.",
    15: "A driver is preparing for evening work, including journeys from entertainment venues and an airport, and reviews booking and collection arrangements.",
    16: "After completing a journey, a driver reviews the operator's fare procedures and checks the vehicle for possessions a passenger may have forgotten.",
    17: "A driver considers how to respond when a journey presents a safety concern, including suspicious items or a passenger whose behaviour prevents carriage.",
    18: "Before a late shift, a driver discusses personal safety with the operator and reviews steps that can prevent misunderstandings with passengers.",
    19: "At pickup, a driver notices that a passenger is struggling to communicate and considers both early warning signs and emergency assistance.",
    20: "During an uncomfortable encounter, a driver thinks about calming the discussion, leaving safely if necessary and obtaining support after the incident.",
    21: "Following a difficult shift, a driver reviews incident-reporting procedures and the role of records and in-vehicle CCTV in supporting an investigation.",
    22: "A vehicle owner is deciding where to place a CCTV notice. The decision must consider both passenger awareness and the driver's view of the road.",
    23: "A driver reviews professional conduct after the operator discusses complaints and the importance of making every passenger feel safe during a booking.",
    24: "A driver is considering the boundaries of passenger assistance, emergency help and professional behaviour, including situations in which physical contact might be misunderstood.",
    25: "A driver considers whether apparently harmless behaviour could make a passenger uncomfortable. Professional boundaries apply throughout the journey, whatever the driver's personal intentions.",
    26: "A driver plans a collection on a busy London street and reads the signs before deciding where the vehicle can stop safely.",
    27: "A passenger is not ready at the agreed pickup time. The driver must distinguish permitted boarding from waiting and consider any necessary assistance.",
    28: "A driver reviews restrictions around bus stops, taxi ranks and charging points, together with the way traffic offences can be enforced.",
    29: "A driver studies the handbook's description of charging requirements and red-route rules before deciding whether a proposed stop falls within the stated restrictions.",
    31: "A driver is preparing for a journey in changing conditions and reviews speed choice, concentration and the need to keep manoeuvres safe.",
    32: "Before setting off, a driver checks the rules concerning phones, fitness to drive and passenger restraints, including the special situations described for children.",
    33: "A driver checks visibility and thinks about cyclists, pedestrians and motorcyclists who may be close to the vehicle when it moves or a door opens.",
    34: "A driver expects a long shift with possible rain and darkness. Preparation includes rest breaks, clear vision and extra attention to vulnerable road users.",
    35: "Approaching a junction used by cyclists, a driver reviews signalling, observation and space requirements before moving on to the vehicle's safety checks.",
    36: "A driver performs a vehicle check before accepting bookings, looking at the controls, passenger equipment, wheels and tyres rather than relying on appearance alone.",
    37: "During an external inspection, a driver checks for damage and fluid leaks and examines the tyres, lights and windows before using the vehicle.",
    38: "A driver is collecting a passenger who may need help. The driver wants to communicate clearly, respect individual needs and avoid unwanted physical assistance.",
    39: "A driver considers how to explain a changed journey to a passenger and how practical assistance can support equal access to transport.",
    40: "A driver of a designated wheelchair-accessible vehicle reviews passenger assistance and the duties applying to wheelchairs and working assistance dogs.",
    41: "A driver reads the assistance-dog guidance and considers why neither an animal's breed nor a driver's personal assumptions should decide whether carriage is offered.",
    42: "A driver considering a medical exemption checks the application and notice requirements, and also reviews how breaches of equality duties can affect licensing.",
    43: "A driver prepares to carry an unaccompanied child and reviews who may be vulnerable, what information is needed and how drivers contribute to safeguarding.",
    44: "During a journey, a driver notices behaviour that may suggest a vulnerable passenger is being controlled. The driver considers recording and reporting the concern.",
    45: "A driver reviews reporting channels for safeguarding concerns, distinguishing emergency assistance from ordinary police reports and the other support services listed in the handbook.",
    46: "A driver begins a shared journey with passengers who do not know each other and wants everyone to understand the arrangements and privacy boundaries.",
}


def build_reading(records):
    by_page = defaultdict(list)
    for record in records:
        by_page[record["page"]].append(record)
    result = []
    authored_options = json.loads((ROOT / "tools/seru_reading_options.json").read_text(encoding="utf-8"))
    for number, page in enumerate(sorted(INTRO), 1):
        records_on_page = by_page[page]
        # The answer and every factual sentence are supported by this same page.
        specification = authored_options[str(page)]
        target = next(r for r in records_on_page if specification["fact"].casefold() in r["evidence"].casefold())
        selected = [target] + [r for r in records_on_page if r is not target]
        passage = INTRO[page]
        for record in selected:
            candidate = passage + " " + record["evidence"]
            if len(candidate.split()) > 135:
                break
            passage = candidate
            if len(passage.split()) >= 90:
                break
        if len(passage.split()) < 60:
            passage += " The driver considers these points together when deciding how to act, because a professional service depends on understanding the guidance and applying it consistently."
        assert 60 <= len(passage.split()) <= 150, (page, len(passage.split()))
        q = base(target, "reading", number)
        correct, *wrong = specification["options"]
        position = (number - 1) % 3
        q.update(question="Question: Which one of the following statements is correct?",
                 passage=passage, options=rotated_options(correct, wrong, position), answer=position,
                 difficulty=2)
        result.append(q)
    return result


def main():
    records = read_records()
    if len(records) != 350:
        raise ValueError(f"Expected 350 authored MCQs, found {len(records)}")
    bank = build_mcq(records) + build_cloze(records) + build_reading(records)
    out = ROOT / "app/data/seru_bank.js"
    out.parent.mkdir(parents=True, exist_ok=True)
    header = "// Original practice material; source evidence is paraphrased, not quoted.\n"
    out.write_text(header + "window.SERU_BANK = " + json.dumps(bank, ensure_ascii=False, indent=2) + ";\n", encoding="utf-8")
    summary = {"total": len(bank), "byType": dict(Counter(q["type"] for q in bank)),
               "bySection": {str(s): dict(Counter(q["type"] for q in bank if q["section"] == s)) for s in SECTIONS},
               "source": SOURCE, "sourceVersion": "1.0", "evidenceKind": "paraphrase",
               "bankSha256": hashlib.sha256(out.read_bytes()).hexdigest()}
    (ROOT / "tools/seru_manifest.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
