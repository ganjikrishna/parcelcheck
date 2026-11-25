# ParcelCheck listing verification, round 2

Round 2 widens the round 1 verification from ten listings to twenty. Ten new real listings (L13 to L22) were collected on 2026-11-25 from public listing pages, with the source and URL recorded at the head of each file in `listings/`. A second answer key (`answer-key-round2.md`) was sealed by SHA-256 before any checker run over these listings: **1ab2d2e7405861ec2b0f4d897d1fe7975d8250fc066a260bc8f4573cf0cc95b7**. The key was drafted by Muse Ember from the listing texts and the rules in `checklist.md` (ten logged calls, see `ember-build/build-runs.jsonl`), every quote in it was checked by script to be an exact substring of its listing file, and every status was reviewed by hand against `checklist.md` before sealing; two draft statuses on L13 were corrected by hand to follow the letter of the checklist, each noted in its row.

Method: the same frozen prompt v1, the same checker, one pass per listing, no retries in the scored pass, scored after the runs against the sealed key. The checker never saw the key. A failed run stands as scored, the same rule as round 1.

## Round 2 results (L13 to L22, 90 points)

- Exact status matches: **69 of 90**
- Stated problems caught: **14 of 19**
- False problem flags: **4**
- Missing points named missing: **34 of 46**
- Clean points called clean: **21 of 25**
- Clean points flagged as problems: **0**
- Cost of the ten scored runs: **$0.0368**, the failed run included

Per listing (exact of 9): L13 7, L14 9, L15 failed run (0), L16 9, L17 9, L18 6, L19 8, L20 7, L21 8, L22 6. Full detail in `verification-round2-detail.json`.

## What missed, plainly

- **L15's scored run failed to parse.** The model's reply was not parseable JSON, so the run produced no report and scores zero, at $0.0062, the most expensive run of the round. Two later re-runs, reported here as an addendum and not counted in the score, each scored 7 of 9 with the same two misses (water and zoning below). This is the same failure shape as round 1's L10.
- **Wetlands read as flood-clean (L18, L22).** Both AcreTown listings state "FLOODPLAIN: none" and also state wetlands acreage (7.06 and 14.65 acres). Point 2 covers flood zone and wetlands together, so the key scores the stated wetlands as a problem. The checker keyed on the floodplain line and called the point clean, both times.
- **Perc flagged where the key says missing (L13, L20, L21).** The checker flags a problem when a listing says a soil test was never done (L13), or carries a "Sewer Not Available" or "Sewer: None" field (L20, L21). The key follows `checklist.md`: those statements say no test or no public sewer, not that the soil failed, so they score missing. These are the round's four false problem flags together with L13's liens row.
- **Tax auction history flagged (L13).** The checker flagged liens because the seller bought the parcel at a county tax auction and the deed is a quit claim. The key scores it missing: no current tax status or lien is stated, and a deed type is not a lien statement.
- **Stated clean points called missing (L18, L22).** On both AcreTown listings the checker called liens and mineral rights missing even though the listings state "clean - no back taxes, no liens" and that the mineral rights the seller owns will convey. No clean point was flagged as a problem in this round.
- **Erratum on the liens half of that miss (added after an independent review, 2026-11-25).** The run outputs show the harness rule liens_tax_clean_requires_both_halves fired on both listings in this pass, and again in the re-verification pass: the model read the stated words as clean, and the harness downgraded the point to missing because "no back taxes" does not satisfy the rule's taxes-paid-or-current wording. The liens misses are the harness rule's wording strictness, not the checker misreading the listings. The mineral rights half of the miss stands as written above.
- **Key judgment note (L19 water).** This key scores "There is no public water or sewer" as a stated water problem, while scoring "no public sewer" statements as missing for perc. The water reading follows checklist point 4 (a stated absence of any water source is a problem); the seam is recorded here so it is visible.
- **Zoning called clean on a non-designation (L19, L20).** "No known zoning restrictions" (L19) and "unrestricted" (L20) state no designation, so the key scores missing; the checker called both clean. On the L15 re-runs the same pattern ran the other way: "Unbuildable" is problem wording in `checklist.md`, the key scores zoning a problem, and the checker called it clean from the A-2 designation.

## Combined listing verification (rounds 1 and 2, twenty listings, 180 points)

- Exact status matches: **147 of 180**
- Stated problems caught: **23 of 30**
- False problem flags: **7**
- Missing points named missing: **89 of 111**
- Clean points called clean: **35 of 39**
- Cost of the twenty scored runs: **$0.0626**, failed runs included

Round 1 stands as published in `verification-results.md` (78 of 90); nothing in round 1 was re-run or re-scored for this round.
