# Verification round 3 results (2026-11-25)

Method, the same as rounds 1 and 2: ten real listings (L23 to L32)
collected from public listing pages on 2026-11-25, an answer key sealed
by hash before any checker run, the frozen prompt v1, one scored pass,
failed runs standing. Round 3 ran under the hardened checker (24,000
token output cap, one bounded retry on an empty, unparseable, or
invalid reply), the same checker the production Worker now runs.

The key (answer-key-round3.md) was drafted by Muse Ember from the
listing texts and checklist.md in ten logged calls ($0.0174), every
quote verified by script as an exact substring of its listing file, and
every status hand-reviewed against checklist.md before sealing. No
draft status needed a hand correction. The review did catch a round 2
key error, disclosed inside the round 3 key: checklist point 4 lists
"Well Needed" as problem wording, and round 3 follows that to the
letter; the sealed round 2 key had keyed the same shape on L18 as
clean. The checker read it clean too, so no published score changes.

Key SHA-256 (sealed before the runs):
d1b99a93df88abede6ad05d1d508744e2ddcb15730ff155bf7407d694c588def
(answer-key-round3.sha256).

Key tally: 10 problem stated, 25 clean, 55 missing across 90 points.

## Scored result: 85 of 90

| Measure | Result |
|---|---|
| Points exact | 85 of 90 |
| Stated problems caught | 7 of 10 |
| False problem flags | 2 |
| Missing points named | 55 of 55 |
| Clean points called clean | 23 of 25 |
| Clean points flagged as a problem | 2 |
| Cost of the ten scored runs | $0.0394 |

Per listing, exact of 9: L23 9, L24 9, L25 9, L26 9, L27 7, L28 9,
L29 8, L30 8, L31 9, L32 8. Six listings scored perfectly. The retry
fired on two runs in this pass (L26 and L30); both produced valid
reports that would previously have been at risk of scoring zero.

The five misses, in plain words:

- L27 flood: the listing states the property "also has wetlands"; the
  checker named flood missing instead of a problem. (In round 2 the
  same seam ran the other way: stated wetlands with "FLOODPLAIN: none"
  were keyed a problem and read clean.)
- L27 water: a well "installed however needs a pump" was flagged a
  problem; the key reads an installed well as a stated water source,
  clean.
- L29 utilities: "Electric: At Street" with "Gas: None" was flagged a
  problem; the key reads electricity at the street as clean.
- L30 water: "Water Source: Need Well" was read clean; checklist
  point 4 lists "Well Needed" as problem wording.
- L32 water: "Will require well water" was named missing instead of a
  problem, the same point 4 wording seam as L30, in the other
  direction.

One handling disclosure, the same shape as the re-verification pass:
L32's batch output file was corrupted by overlapping writes from a
still-finishing process. Three L32 traces from this round are in
runs.jsonl; the scored result is the final clean run ($0.0040 of the
cost above), and the two surplus runs ($0.0102) are counted in the
ledger, not in the scored cost.

Full per-point detail: verification-round3-detail.json. Combined with
the re-verified rounds 1 and 2, the current checker stands at 246 of
270 points exact across thirty listings (30 of 40 stated problems
caught, 8 false problem flags, 158 of 166 missing points named, 58 of
64 clean points called clean), $0.0982 for the thirty scored runs.
