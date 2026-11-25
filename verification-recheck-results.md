# Re-verification under the hardened checker (2026-11-25)

After rounds 1 and 2 were published, the checker was hardened against the
one failure shape both rounds had shown: a run that returns no usable
result and scores zero. The two causes were found in failed-runs.log.
L10's model reply echoed the JSON schema instead of a result. L15's reply
was empty: the model spent the whole 12,000-token output cap on hidden
reasoning and returned no text.

The fix, written by Muse Ember from a written spec and verified by
running it (five offline stub tests covering empty reply, unparseable
reply, schema echo, validation error, and the unchanged first-try path):
the output cap is 24,000 tokens, and a run whose reply is empty,
unparseable, or fails validation is retried once with the identical
prompt. Both attempts are traced and their costs summed. The frozen
prompt v1 did not change. The same hardening was then mirrored into the
production Worker and re-verified live.

Both sealed sets were then re-run, one pass per listing, same keys
(round 1 key SHA-256 in answer-key.sha256, round 2 key SHA-256 in
answer-key-round2.sha256, both re-verified against their files before
the runs). Per-point detail in verification-recheck-detail.json.

## Results

| Set | Exact | Problems caught | False problem flags | Missing named | Clean called clean | Cost |
|---|---|---|---|---|---|---|
| Round 1 listings (10) | 84 of 90 (was 78) | 9 of 11 | 3 | 62 of 65 (was 55) | 13 of 14 (was 14) | $0.0226 |
| Round 2 listings (10) | 77 of 90 (was 69) | 14 of 19 | 3 (was 4) | 41 of 46 (was 34) | 22 of 25 (was 21) | $0.0363 |
| Combined | 161 of 180 (was 147) | 23 of 30 | 6 (was 7) | 103 of 111 (was 89) | 35 of 39 | $0.0588 |

What moved and why, stated plainly:

- L10 went from 0 to 8 of 9 and L15 from 0 to 7 of 9. Neither needed the
  retry in this pass; the higher output cap alone kept both replies
  inside the budget. The retry is proven by the offline tests and by
  round 3, where it fired twice in the scored pass.
- The rest of the movement is ordinary sampling variance on a fresh
  pass: missing points named rose sharply (89 to 103 of 111 across both
  sets), and one clean point in round 1 was read as missing this time
  (clean 14 of 14 became 13 of 14). No number from the earlier passes
  was edited; the original results files stand as the record of those
  passes, and this file is the record of the current checker.
- No run in this pass needed the retry (all 20 harness blocks show
  attempts: 1).

One handling disclosure: L22's first output file in this pass was
corrupted by overlapping writes when a re-run was started while the
batch's final process was still finishing. Three L22 traces from this
pass are in runs.jsonl; the scored result is the final clean run
($0.0079 of the round 2 cost above), and the two surplus runs ($0.0129)
are counted in the ledger, not in the scored cost.
