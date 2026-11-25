# ParcelCheck verification results

Answer key sha256 verified before the run: 688099684502282a3e8805e7caaabeb7ad3b1d611f01479ee3f7a8d78c70e507

**Totals across 90 points: 78 exact matches. Problems in key: 11, caught: 9. False problem flags: 3. Missing in key: 65, named missing: 55. Clean in key: 14, called clean: 14. Total cost of the ten runs: $0.0258, including the L10 run that failed to parse ($0.0022).**
Prompt: v1 (frozen). Model: muse-ember-1.0. One structured pass per listing.

Two earlier passes over parts of the set (L02 to L06) aborted on output
shape failures before this scored pass; their runs and costs are in
runs.jsonl and the ledger, and nothing from them was reused. Inside the
scored pass, no listing was retried. The seal claim for the answer key
rests on the timestamps in ledger.md; the git history of this repo
begins after these runs.

## L02: 9/9 points match, cost $0.0018

## L03: 7/9 points match, cost $0.0039
- MISS: perc_septic: key missing, got problem_stated
- MISS: utilities: key missing, got problem_stated

## L04: 8/9 points match, cost $0.0036
- MISS: utilities: key missing, got problem_stated

## L05: 9/9 points match, cost $0.0042

## L06: 9/9 points match, cost $0.0021

## L08: 9/9 points match, cost $0.0019

## L09: 9/9 points match, cost $0.0031

## L10: RUN FAILED (Extra data: line 1 column 2058 (char 2057)). Tokens logged in runs.jsonl. Scored as no points matched.

## L11: 9/9 points match, cost $0.0013

## L12: 9/9 points match, cost $0.0016


## Addendum, 2026-11-25: the L10 failure, revisited

The scored result above stands as run. After it, the harness (not the
prompt; prompt v1 is unchanged) was hardened against the failure shapes
L10 produces, and L10 was re-run five times, all logged in runs.jsonl
($0.0096 total):

- One run returned a clean result with no errors.
- One run added prose and the schema before its result; the original
  parser rejected it. The parser now scans for the first complete object
  carrying a top level "checks" key.
- One run returned the schema alone; the validator rejected it
  ("checks must be a list of exactly 9") and, in the production Worker,
  such a run now returns an error to the visitor instead of an empty
  report.
- The last two runs scored **9 of 9** against the sealed key: both
  problems caught (landlocked access, zoning with no permitted use) and
  all seven missing points named. Cost $0.0018 each.

L10 remains the listing where Ember is least stable; the harness now
recovers the recoverable shapes and refuses the rest, instead of
scoring a silent zero.
