# SERU source audit

Date: 18 November 2026. Reviewer: Codex, by reading the source pages and inspecting the answer options; this is not independent human or TfL certification.

## Source and scope

The source is the [official PHV Driver's Handbook v1.0](https://content.tfl.gov.uk/phv-driver-handbook-v1.pdf), dated 30 September 2021, 52 pages. Page references are one-based printed PDF pages: section 1 begins on page 6. The research pass found TfL still linking this edition. Questions test that edition, not a promise that every historical licensing or charging statement remains current operational law.

The evidence field contains an original paraphrase of at most 25 words, explicitly marked `evidenceKind: "paraphrase"`. It is not represented as a quotation. The handbook and full extracted text stay in ignored `research/`; they are not part of the published app.

## Authoring and verification

- 350 MCQs were individually authored from the source pages, with a stem and two incorrect alternatives. They are not name-swapped template clones or copied mock-test questions.
- 150 cloze exercises reuse 150 of those source facts in a different task format. Each has two independently scored blanks, two unused distractors, and original wording. Commonly confused word forms are used for language practice. This intentionally revisits handbook facts; it is not a claim of 150 additional independent rules.
- 40 reading passages each draw from a single cited page. Their 60–150 words combine an original scenario introduction and original fact paraphrases. All 40 sets of answer statements were separately authored and reviewed after rejecting an initial mechanical distractor approach.
- Authoring covered all ten sections and 84 subsection labels, including subheadings. Each source fact was checked against its cited page while authored. Explanations restate the relevant rule and link to the page.
- A separate reproducible random 10% sample of 54 final items was re-read against its source page. The sample was selected without filtering using Python `random.Random(20261118).sample(bank, 54)`. Correct answers, page attribution and competing options were checked. No factual-key or page-reference errors were found in this sample.
- The earlier sample exposed poor-quality reading distractors, not wrong answer keys. Review was widened to every reading item and all 40 distractor sets were replaced with plausible misunderstandings. The cloze alternatives were also revised to use grammatical near misses. One very similar ULEZ MCQ stem was rewritten, and one cloze about an exception was made explicit about hand-held phones. See [rejected_items.md](rejected_items.md).

A separate research-agent check independently re-extracted pages 8, 9, 29 and 40 and confirmed the medical age intervals, 21-day address notification, overnight cashpoint exception and its prohibited stopping places, and assistance-dog footwell/no-extra-charge duties. This corroborates the cited v1.0 text, not current operational policy.

A structural validator cannot prove factual accuracy. These checks are useful quality controls, not an empirical guarantee of exam performance or a substitute for review by a trained human editor. Difficulty tags are editorial: direct recall is level 1, application is level 2 and exceptions or interacting conditions are level 3; reading is level 2. They have not been psychometrically calibrated on candidates.

## Reproduction

```powershell
tools/.venv/Scripts/python.exe tools/seru_extract.py research/official/phv-driver-handbook-v1.pdf
tools/.venv/Scripts/python.exe tools/build_seru.py
tools/.venv/Scripts/python.exe tools/validate_seru.py
```

`tools/seru_extract.py` extracts each page and groups complete referenced pages into subsection review packets. It preserves surrounding context rather than pretending that automatic heading extraction can reliably isolate every subsection. The packets are ignored research files. The committed authoring records contain original material only.

The validator checks counts, exact schema, distinct IDs and options, answer balance, section/page bounds, source links, evidence length and type, British spellings, subsection coverage, cloze completion, reading lengths and RapidFuzz similarity above 85. MCQ stems are compared against MCQ stems; cloze and reading passages are compared within their own type. Shared standard instructions are excluded from similarity comparison. Cross-format reuse of a source fact is intentional and disclosed above.

Source PDF SHA-256: `d2d8410305f29c26484a3293833681c028ff4dff9ebc93378121417872783e53`.

Final bank SHA-256: `4ca7e73c9e1d53ae8da53f291e9c7de6631f0b2901cd1c181ddb1fade913a5c7`.

## Final counts

| Section | MCQ | Cloze | Reading | Total |
|---|---:|---:|---:|---:|
| 1 | 49 | 21 | 6 | 76 |
| 2 | 16 | 7 | 2 | 25 |
| 3 | 32 | 14 | 4 | 50 |
| 4 | 37 | 16 | 5 | 58 |
| 5 | 20 | 9 | 3 | 32 |
| 6 | 40 | 17 | 4 | 61 |
| 7 | 69 | 30 | 7 | 106 |
| 8 | 45 | 19 | 5 | 69 |
| 9 | 29 | 12 | 3 | 44 |
| 10 | 13 | 5 | 1 | 19 |
| **All** | **350** | **150** | **40** | **540** |

MCQ answer positions A/B/C: 117/117/116. Reading answer positions: 14/13/13. No within-type near-duplicate pair exceeds 85.

## Random sample log

Each row was checked against the complete referenced source page. Outcome: supported answer and page; alternatives do not correctly answer the question under the cited handbook rule. For cloze, the completed statement and grammatical word alternatives were checked.

Sample types: 16 cloze, 35 mcq, 3 reading.

| Item | Page | Check |
|---|---:|---|
| `SERU-01-LICENSINGREQUIREMENTS-CLOZE-001` | 6 | Supported: Applicants need the right to live and work in the UK. |
| `SERU-01-LICENSINGREQUIREMENTS-MCQ-004` | 6 | Supported: The qualifying licence must be full and held for at least three years. |
| `SERU-01-LICENSINGREQUIREMENTS-MCQ-007` | 6 | Supported: The examining doctor needs access to the applicant's complete medical records. |
| `SERU-01-YOURPHVDRIVERSBADGE-CLOZE-015` | 7 | Supported: A driver with a badge exemption must carry the relevant notice while working. |
| `SERU-01-YOURPHVDRIVERSBADGE-CLOZE-017` | 7 | Supported: The badge must be visible while working, including travelling to collect passengers. |
| `SERU-01-YOURPHVDRIVERSBADGE-MCQ-019` | 8 | Supported: Passengers may inspect the badge to note the driver's licence number. |
| `SERU-01-RIGHTTOLIVEANDWORKINTHEUNITE-CLOZE-002` | 10 | Supported: Drivers must meet right-to-work conditions and retain a continuing right to work. |
| `SERU-01-DISCLOSUREANDBARRINGSERVICE-READING-006` | 11 | Supported: Applicants must use TfL's specified company for the DBS check. |
| `SERU-01-REVOKINGADRIVERSPRIVATEHIREV-MCQ-047` | 11 | Supported: TfL may revoke the owner's vehicle licence where public safety is at risk. |
| `SERU-02-LICENCESANDLICENCEDISCS-MCQ-053` | 12 | Supported: Damaged discs prevent PHV use; the owner should contact TfL. |
| `SERU-02-LICENCESANDLICENCEDISCS-MCQ-055` | 12 | Supported: A disc exemption requires the driver to carry its notice while using the PHV. |
| `SERU-02-LICENCESANDLICENCEDISCS-READING-007` | 12 | Supported: Discs must remain attached during private use because removing them causes damage. |
| `SERU-02-INFORMATIONABOUTVEHICLES-MCQ-065` | 13 | Supported: Read and follow recall instructions, including any restriction on use. |
| `SERU-02-INSURANCE-MCQ-059` | 13 | Supported: Insurance must be valid at licensing and throughout private hire use. |
| `SERU-03-BOOKINGS-CLOZE-041` | 14 | Supported: TfL's public licence checker can verify an operator's number. |
| `SERU-03-BOOKINGS-MCQ-068` | 14 | Supported: The driver must receive the booking before the passenger enters. |
| `SERU-03-BOOKINGDETAILS-CLOZE-036` | 15 | Supported: For multiple pickups, record the first passenger's agreed time and place. |
| `SERU-03-OPERATINGCENTRESINLATENIGHTV-MCQ-077` | 15 | Supported: People requesting rides outside a venue should be directed to a licensed operator for a booking. |
| `SERU-03-FARES-CLOZE-035` | 16 | Supported: Tell the operator about changes when it is safe so the fare can be updated. |
| `SERU-03-LOSTPROPERTY-CLOZE-029` | 16 | Supported: Found property goes to the operator, who must keep a record. |
| `SERU-04-DRIVERSAFETY-CLOZE-058` | 18 | Supported: Drivers may reject abusive behaviour and ask passengers to leave when safe. |
| `SERU-04-DRIVERSAFETY-MCQ-099` | 18 | Supported: Hate crime should be reported to police as soon as possible. |
| `SERU-04-DRUGSANDALCOHOL-MCQ-110` | 19 | Supported: Inability to confirm a destination or walk may justify refusal for safety. |
| `SERU-04-AFTERANINCIDENT-CLOZE-050` | 20 | Supported: Talking with a trusted person and seeking support can help after an incident. |
| `SERU-04-DRUGSANDALCOHOL-MCQ-114` | 20 | Supported: Keep yourself safe while maintaining sight of the person awaiting help. |
| `SERU-05-COMPLAINTS-CLOZE-062` | 23 | Supported: TfL provides complaint details and seeks the driver's comments before making its decision. |
| `SERU-05-UNACCEPTABLESEXUALBEHAVIOUR-MCQ-148` | 24 | Supported: Sexual activity must never replace a fare and cannot be accepted as payment. |
| `SERU-05-UNACCEPTABLESEXUALBEHAVIOUR-MCQ-152` | 24 | Supported: Unsuitable sexual behaviour towards a passenger can result in loss of the licence. |
| `SERU-06-DRIVINGANDPARKINGINLONDON-MCQ-155` | 26 | Supported: Taxi access signs do not grant the same permission to PHVs. |
| `SERU-06-STOPPINGANDWAITING-MCQ-157` | 26 | Supported: PHVs must not stop on zig-zag markings near crossings. |
| `SERU-06-STOPPINGANDWAITING-MCQ-160` | 27 | Supported: The issuing council decides whether assistance evidence justifies cancelling the PCN. |
| `SERU-06-STOPPINGANDWAITING-MCQ-170` | 27 | Supported: Helping a passenger does not create a general parking exemption. |
| `SERU-06-PENALTYCHARGENOTICES-CLOZE-084` | 28 | Supported: Blocking a yellow box junction is a traffic offence that can lead to a PCN. |
| `SERU-06-ULTRALOWEMISSIONZONE-MCQ-185` | 29 | Supported: For petrol PHVs, the handbook specifies Euro 4 emissions standards. |
| `SERU-07-CONCENTRATION-MCQ-202` | 31 | Supported: Distractions can reduce awareness and impair judgement. |
| `SERU-07-CONCENTRATION-CLOZE-088` | 32 | Supported: The hand-held phone exception concerns emergency services when stopping is unsafe or impractical. |
| `SERU-07-FOLLOWINGTRAFFICLAWSBEFOREAJ-MCQ-209` | 32 | Supported: Adults must wear seatbelts and drivers should encourage their use for safety. |
| `SERU-07-FOLLOWINGTRAFFICLAWSBEFOREAJ-MCQ-214` | 32 | Supported: Traffic breaches may lead to a driving ban and PHV licence loss. |
| `SERU-07-BECRADLECAREFUL-MCQ-222` | 33 | Supported: Before each journey, check that devices and signs do not obstruct vision. |
| `SERU-07-BEINGAWAREOFOTHERROADUSERS-CLOZE-095` | 33 | Supported: Anticipate pedestrians stepping into the road and take care near side roads. |
| `SERU-07-INCLEARSIGHT-MCQ-220` | 33 | Supported: Windscreens and windows must be clean and free from visual obstruction. |
| `SERU-07-WINDSCREENVISION-MCQ-223` | 34 | Supported: Devices must be positioned without reducing visibility or causing distraction. |
| `SERU-07-DRIVERSCOMPARTMENT-MCQ-238` | 35 | Supported: Check that the steering wheel is secure and in good condition. |
| `SERU-07-TOPTIPS-MCQ-231` | 35 | Supported: Use indicators even when nobody seems nearby. |
| `SERU-07-TOPTIPS-MCQ-235` | 35 | Supported: Wait until there is enough room to overtake a cyclist safely. |
| `SERU-07-OUTSIDETHEVEHICLE-MCQ-262` | 37 | Supported: Serious rust causing sharp edges is an external safety defect. |
| `SERU-07-WHEELSANDTYRES-READING-031` | 37 | Supported: When tread reaches wear indicators, the tyre must be replaced. |
| `SERU-08-ASSISTINGPASSENGERS-MCQ-277` | 39 | Supported: State the fare clearly and count change into the passenger's hand. |
| `SERU-08-EQUALITYACT2010-MCQ-283` | 39 | Supported: Age and disability are protected characteristics. |
| `SERU-08-ASSISTANCEDOGS-CLOZE-127` | 41 | Supported: Assistance dogs can be different breeds and need not match the pictures. |
| `SERU-08-EXEMPTIONSFROMASSISTANCEDOGD-MCQ-303` | 41 | Supported: Assistance-dog exemptions are available only on medical grounds. |
| `SERU-08-EXEMPTIONSFROMASSISTANCEDOGD-CLOZE-133` | 42 | Supported: A medical condition may support an application; TfL must grant the exemption. |
| `SERU-09-SIGNSTHATACHILDORVULNERABLEP-MCQ-324` | 44 | Supported: A frightened child in adults' company can signal a safeguarding concern, requiring attention. |
| `SERU-10-RIDESHARING-MCQ-345` | 46 | Supported: Inform passengers about route changes and additional pickups. |

## Exclusions and limits

No glossary-definition questions, linked-website facts, leaked material, copied third-party mock questions or English speaking/listening module were used. The old wheelchair ULEZ exemption statement was deliberately not turned into a current-rules question. Current policy may differ from v1.0; licence holders must consult current TfL material. The age and notification periods included here are expressly handbook-study content. Source-page paraphrases should be checked again whenever TfL changes the assessed handbook version.
