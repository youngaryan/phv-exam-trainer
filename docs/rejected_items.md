# Rejected and revised SERU candidates

18 November 2026. This records actual authoring and review decisions. None of the rejected wording is presented as a live exam question.

| Candidate | Issue discovered | Resolution |
|---|---|---|
| Initial 40 reading distractor sets | Mechanically replacing a cloze word produced implausible statements, such as unrelated objects in a road-safety sentence. Correct keys were source-supported, but the distractors were not realistic. | Rejected the entire approach. Individually authored all 40 sets in `tools/seru_reading_options.json` using plausible misunderstandings; reviewed each against the same page as the passage. |
| Diesel ULEZ MCQ, current ID `SERU-06-ULTRALOWEMISSIONZONE-MCQ-186` | Stem similarity to the petrol question was 94.59 under RapidFuzz ratio. | Rewrote the diesel item as a vehicle-check scenario. It still tests the diesel standard, rather than merely changing a name. Final similarity validation passes. |
| Cloze about the hand-held-phone emergency exception | The sentence began with an unexplained reference to an exception. | Added the hand-held-phone subject to the original evidence and cloze passage. The same page 32 supports the clarified wording. |
| Initial cloze distractor vocabulary | Several alternatives were unrelated nouns, making exercises less like the official language-style task. | Replaced applicable distractors with authored grammatical near misses. Correct answers and cited source facts did not change. Exact word-tile uniqueness and completion remain validated. |
| Historical wheelchair ULEZ exemption as a current rule | The 2021 handbook describes a historical exemption; publishing it as timeless driving advice risks misleading learners. | Omitted this candidate. The bank's other rules are clearly scoped to handbook v1.0, and current charging rules must be checked with TfL. |
| Engine-start warning-light question | The handbook's compressed wording does not distinguish normal bulb checks from a warning that remains illuminated. | Did not create an item from this ambiguous wording. Other vehicle-check items cover the subsection. |

The original 350 source facts are reused across some question types for practice. That reuse is disclosed in `SERU_AUDIT.md`; it is not hidden by random names or superficial rephrasing. No rejected item was replaced with a copy of a real or third-party exam question.
