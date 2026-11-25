# ParcelCheck spend ledger

**Total spent: about $0.17 of the $10 credit, meter side.** Meta Billing
is the authority for the credit. The reconciliation, stated plainly
because the two records do not fully close: the Billing page already
showed $0.10 spent at 20:26 ET on 2026-11-24, before the first
ParcelCheck call at 20:39, so that $0.10 is not ours and is
unattributed. At 07:34 ET on 2026-11-25 the meter read $0.11. Our
logged runs itemize to about $0.56 at list rates; the dated entries
below itemize them, including the Muse Ember code build and the demo
video phase. The
meter's movement is smaller than the itemization; caching and metering
sit on Meta's side and cannot be reconciled from here. The meter
governs the credit; this log governs what ran.

Credit allocation: $10.00.

## Allocation table

| Bucket | Allocated (USD) | Spent (USD) | Remaining (USD) |
|---|---|---|---|
| Development | 3.00 | 0.16 | 2.84 |
| Verification | 2.00 | 0.11 | 1.89 |
| Demo video | 1.00 | 0.00 | 1.00 |
| Live judge demo reserve (never spent on development) | 2.00 | 0.00 | 2.00 |
| Final submission day | 1.00 | 0.00 | 1.00 |
| Unallocated buffer | 1.00 | 0.00 | 1.00 |
| **Total** | **10.00** | **0.56** | **9.44** |

## Rules

- **Stop rule:** at $8.00 total spent, experimentation stops and only the frozen prompt runs.
- The live judge demo reserve of $2.00 is never spent on development, verification, or experimentation.
- Every model call gets one line in the run log below, with the cost taken from the API usage record (the cost field in prompt-draft.md), not estimated.

## Run log

Per-call trace for every checker run: `runs.jsonl` (prompt version,
input and output tokens, cost, errors). Calls that do not go through
checker.py (smoke tests, shape tests, page and Worker runs, records
runs) are itemized in the dated entries below.

2026-11-24: day-one prep. No API calls, no model calls, no spend.

2026-11-24, about 18:12 ET: sealed key re-sealed on main chat adjudication, before any model run. L03 and L04 utilities problem to missing (gas alone does not state utilities generally, gas fact kept in the note). L05 survey problem to missing (no survey status stated). L07 note fixed from five missing to six missing, matching its table. L04 perc/septic and water kept clean on "Water and Sewer available", thin basis noted. New hash 688099684502282a3e8805e7caaabeb7ad3b1d611f01479ee3f7a8d78c70e507, verified on Flash and on this VM. New tally counted from the tables: 13 problems stated, 18 clean, 77 missing across 108 rows. That count also corrects the day-one report, which said 17 clean and 75 missing; the tables themselves were right, the count was off by one in each direction. Still $0.00 spent, still no model run.

2026-11-24, 18:11 ET: Vinay confirmed the $10 credits claim is done (his word "done" in the side chat, right after the claim steps). Credits land in batches around 10 AM and 3 PM ET, so the expected landing is the Wed Nov 25 morning batch. Spend stays locked until Billing shows the $10 and the main chat confirms.

2026-11-24, 20:26 ET: Vinay confirmed the $10 credits landed ("we got the $10") and said he is adding the Meta Model API key to Flash OmniRoute himself, with his go to use it after. First spend, once he confirms the key is in: one smoke call on Muse Ember, the Ember rate recorded from Billing, both written into this ledger before any build run. Submission also needs a prompt and token trace as proof of Ember usage and amount spent (event waiver), so every run from the smoke call on gets logged with its prompt version and token counts.

2026-11-24, 20:26 ET: Vinay's Billing screenshot verifies it: "Free credits in use $10.00" on the correct team account (1579961457492318), monthly spend limit set to $10. The same page shows $0.10 spent (1% used) already metered this month, source not yet identified, before any logged ParcelCheck run; and a pre-existing outstanding balance of $0.09 (the October restriction), which the page says will not increase while free credits are in use. An OmniRoute catalog check from here at 20:27 ET returned 401, consistent with Vinay being mid edit on the router; no spend attempted.

2026-11-24, 20:26 to 20:30 ET: Ember access attempts through OmniRoute. Model id found: muse-code/muse-ember-1.0. Every call failed with HTTP 400 from the upstream (unknown parameter max_tokens, then unknown parameter messages), 0 tokens in and out on each, so $0.00 spent by this chat. The failures match Vinay's own OmniRoute test at 20:30 ET: Ember appears to be off until the hackathon start. Vinay's instruction: do not use anything until the start. One OmniRoute model metadata edit made during diagnosis (Ember apiFormat) was reverted from backup the same evening, router left as found. Build spend stays locked until the hackathon start and Ember answers.

2026-11-24, 20:39 ET: EMBER IS LIVE. Smoke call through Muse Code on Flash (muse exec, model muse-ember-1.0, Vinay's own login on the credits team) answered READY. Usage: 32,402 input tokens (that is Muse Code's own system prompt overhead, not ParcelCheck prompt), 13 output, 3 reasoning, 1 call. Ember direct API list rate (Meta pricing, as of 2026-11-12): input $0.10 per million up to 200K input, cached input $0.004 per million, output $0.50 per million; over 200K input the rates triple. Smoke call cost at those rates: about $0.0033. A ParcelCheck run on the direct API (about 1,500 tokens in, 800 out) costs about $0.0006, so the $10 covers on the order of 15,000 checks; the budget is not tight, the trace still gets kept for every run. Route findings, final: OmniRoute cannot carry Ember (its muse-code route posts to the Responses endpoint but never converts the body for imported models, Meta rejects it); this VM's network path to api.meta.ai is refused (tunnel 403) even with the new key in the connector, so the connector route is out too. Working route: direct API calls from Flash, which needs the new key in a file on Flash (Vinay to place it; the key never goes in chat).

2026-11-24, 20:42 to 20:52 ET: DIRECT API LIVE and CALL SHAPE DECIDED. Vinay placed the key at ~/parcelcheck-prep/meta-api-key.txt on Flash (mode 600). Direct smoke (Responses API): 200, READY, 15 in / 15 out, 0.7 s, about $0.000009. Dev/test split set: L01 and L07 are development listings; the verification set is the other ten, untouched. Shape test on L01+L07: (A) one structured pass with the v0.1 draft prompt as written scored 0/9 on both, because the draft references the JSON schema but never pastes it in, so Ember invented its own shape (its statuses were visibly right, the shape was wrong); (B) per-check calls scored 4/9 and 7/9 with five parse failures on L01, at about twice the cost and time. (A2) one structured pass with the exact schema pasted into the prompt: 9/9 on L01 and 9/9 on L07, zero fabricated quotes, $0.0040 and $0.0030 per check (output runs 6 to 8 thousand tokens including reasoning, so a check costs about $0.0035, not the $0.0006 estimated earlier; the $10 still covers roughly 2,800 checks). DECISION: one structured pass, prompt v1 is the draft system prompt plus the full schema pasted in. Spend tonight, all logged: Muse Code smoke $0.0033, direct smoke $0.000009, shape A $0.0048, shape B $0.0094, shape A2 $0.0070. Total about $0.025 of the $10. The $0.10 on the Billing page predates these runs.

2026-11-24, 20:55 ET: CHECKER CORE BUILT. prompt-v1.md and prompt-v1.json frozen on Flash (v1 = draft system prompt plus full schema). checker.py runs one Ember pass, validates the output (nine points, statuses, quote substring check, red flag and missing consistency, seller question coverage), fills the cost from usage, and appends a trace line to runs.jsonl for every run. First core runs: L01 clean, no errors or warnings, $0.0022; L07 clean, no errors or warnings, $0.0024. Cached outputs saved as cached-L01.json and cached-L07.json for the page examples. Running total about $0.030 of $10.

2026-11-24, 21:00 to 21:20 ET: PAGE WIRED AND VERIFICATION RUN COMPLETE. server.py serves the page on Flash at 127.0.0.1:8931 with an explicit path allowlist (answer key and API key return 404, verified) and a 200 runs per day cap; live run through the server on L07 returned the exact six missing items from the key, $0.0022. Page examples are L01 and L07 only, with cached results labeled by date; the L05 example button from the skeleton was removed so no verification listing is spent as an example. VERIFICATION, one clean pass, key hash verified before the run (688099684502282a3e8805e7caaabeb7ad3b1d611f01479ee3f7a8d78c70e507): 78 of 90 points exact matches; problems caught 9 of 11; false problem flags 3; missing items named 55 of 65; clean points called clean 14 of 14; seven listings scored a perfect 9 of 9. The misses, published as they stand in verification-results.md: L03 and L04 each had utilities over-flagged from a gas-only statement, and L03 perc from "Sewer: None"; L10 (Hermitage TN) failed to parse because the model added extra text after the JSON, so its two problems went uncaught and the listing scored zero. Cost of the ten verification runs: $0.0236. Two earlier verification passes aborted on output shape failures and are logged in runs.jsonl; nothing was retried per listing inside the scored pass. runs.jsonl total after 20 logged runs: $0.0509. All-in hackathon spend including the shape tests and smoke calls: about $0.08 of the $10.

2026-11-25, 06:35 ET: REPO PUSHED. Vinay created ganjikrishna/parcelcheck (public) and approved the push after seeing the file list. Package validated two ways before the push: Ember's own secret scan over all 30 files (no key value anywhere; the key file is not in the package and is named in .gitignore) and an independent validator pass (Nemotron Ultra, live probed, substituted because Glimmer was not in the day's router catalog): verdict PUSH OK, every README number matched verification-results.md. Pushed via the GitHub connector snapshot (30 files, commit a13c82176c6278ba8a24922640aaddad513af684 on main, on top of Vinay's initial commit) and verified live: head commit and README content read back from GitHub. Note: a plain git clone of the repo earlier tripped an execution-risk check on this VM; Vinay gave an explicit go before the push proceeded through the connector instead.

2026-11-25, 07:12 ET: LIVE PAGE DEPLOYED AND VERIFIED. Cloudflare Worker at https://parcelcheck.ganjikrishna.workers.dev (workers.dev subdomain ganjikrishna, picked by Ember at Vinay's word). The Worker serves the redesigned page (Vinay's brief: unslop; diligence report styling) and the cached examples, and runs live checks with the same frozen prompt v1 and the same harness validation as the local checker; the API key is a Worker secret, set from the key file on Flash, never in code. Live runs capped at 200 per day by a Durable Object counter. Verified end to end through Vinay's own Chrome: page loads, the Florida example renders 2 red flags with quoted evidence, 6 not addressed, 1 in order; a live run on the same text returned identical counts at $0.0027 with no errors. First tab hit a TLS error while the new subdomain's certificate was still provisioning; a fresh tab loaded clean. Public live runs do not append to the local runs.jsonl; their cost shows on the page itself and in Meta Billing.

2026-11-25, 07:15 to 07:35 ET: PUBLIC RECORDS MODE ADDED (Vinay's direction: one box; an address gets an online check, and records run for every paste that contains an address, because listings go stale and records are current). All sources free, no keys: US Census geocoder, FEMA National Flood Hazard Layer, USDA soil survey (map unit, drainage class, septic absorption rating), US Fish and Wildlife Service wetlands inventory. The records text goes through the same frozen prompt v1 and the same quote-or-drop validation; a source that fails adds no sentence and the point stays a seller question. Spike on Vinay's own address returned: Zone X, area of minimal flood hazard; no wetlands mapped; Madison sandy clay loam, septic rated Somewhat limited. One quirk found and fixed: FEMA's gateway drops calls from the Worker until the request carries browser headers; with them, all four sources answer. Live tests through the deployed Worker: address only, records mode, flood clean on the FEMA quote, septic flagged, $0.0017; listing paste with the address inside, combined mode, the listing's landlocked sentence and the USDA septic rating both flagged; a Miami Beach address in Zone AE flagged as a flood problem; the L07 listing (its own address parsed from the text, 55 Dora Bush Hill Road, Carlton GA) gained a records-backed flood clean. Six test runs, about $0.01 total. Page copy and result headings updated for the three modes; listing-only behavior unchanged when no address is found.

2026-11-25, 07:36 to 08:05 ET: BOTH FOLLOW-UPS DONE (Vinay's call, after his Billing screenshot showed $9.89 of the $10 still unused). (1) HARNESS PARSE FIX: the output parser in checker.py and the Worker now scans for the first complete object carrying a top level "checks" key, recovering results surrounded by prose or a schema echo; a schema-only reply is rejected by the validator, and the Worker now returns an error instead of an empty report. Prompt v1 unchanged. L10 re-run five times ($0.0096): one clean, one rejected parse, one rejected schema echo, then 9 of 9 twice at $0.0018 each. Addendum published in verification-results.md; the original scored zero stands. (2) RECORDS VERIFICATION: ten addresses, key built from an independent spike (records-spike.py, direct Census/FEMA/USDA calls, separate code path), sealed at c3e44ae65d5aa38434bc58cbd7a283a448a7dbe8c8de2d33682b234a7db6da73 before the scored run. Scored pass through the production Worker: 14 of 20 (flood 9 of 10, septic 5 of 10), $0.0175. Findings: a USDA "Not rated" sentence read as a septic problem 5 of 5 times (fix: the sentence is omitted when the rating is Not rated), and FEMA's gateway dropped 1 run in 10 (fix: pause, retry, FIRMette mirror fallback). Post-fix confirmation on the five missed addresses: 10 of 10, $0.0071. Full record in records-verification.md. Also this session: the records report's question section is retitled "Still to verify" in records mode, at Vinay's question about why seller questions appear on an address check. All-in hackathon spend now about $0.15 of the $10 (Meta's meter read $0.11 at 07:34 ET, before today's verification runs).

2026-11-25, 09:00 ET: RECORDS KEY AMENDED AND RE-SEALED at Vinay's direction. The independent push validator blocked the verification round on one line: the sealed records key named the Georgia development address as the builder's home, publishing its flood zone and septic categories under his name (no street address anywhere). Vinay chose rewording. The key now says "a residential address in Georgia", with an amendment note inside the key recording the change, that nothing else was touched, and the original sealed hash (c3e44ae65d5aa38434bc58cbd7a283a448a7dbe8c8de2d33682b234a7db6da73, the version the scored run used). The matching line in records-verification.md was reworded the same way. New key hash is in records-answer-key.sha256.

2026-11-25, 09:49 ET: OUTSIDE REVIEW, SIX GAPS, ALL FIXED. A fresh Claude review of the public repo (run under Vinay's outside-validation rule) confirmed the headline numbers and both key hashes, and found six gaps. Checked one by one against the files, all six were real: (1) runs.jsonl in the repo stopped at 20 lines; the five L10 re-runs were only on Flash. Synced; the repo trace now has all 25 checker runs, and records-verification.md states plainly that Worker runs are not in runs.jsonl and where their costs live. (2) The two earlier aborted passes over L02 to L06 were disclosed only here; the disclosure now sits in verification-results.md and the README, with the note that the key seal rests on these ledger timestamps since git history begins after the runs. (3) The published verification cost, $0.0236, was the sum of the nine parsed runs only; with L10's failed run the ten runs cost $0.0258. Corrected in verification-results.md, the README, and the submission draft (description re-trimmed to 1,982 characters). (4) This ledger's header still said $0.00; fixed above with the meter as authority. (5) checker.py, verify.py, and server.py hardcoded ~/parcelcheck-prep; they now use the folder holding the script, with a PARCELCHECK_DIR override, so a clone runs as the README says. (6) records-spike.py, named as the records key's independent source, was missing from the repo; added (it contains only the ten scored public addresses). Spend this round: $0.00.

2026-11-25, 10:02 to 10:20 ET: OUTSIDE REVIEW ROUND 2, SEVEN FIXES. The fresh Claude re-checked round 1's six fixes (all confirmed in the files, and it re-summed the scored pass itself: $0.025807) and then tested the live site. Findings and what was done: (1) verify.py CRASHED on startup: the round 1 path fix's import edit silently missed verify.py's import line, so os was never imported; a syntax compile could not catch it, running it could. Fixed, and this time proven by running it on a keyless copy, where it verifies the key hash and stops at the first missing file instead of NameError. (2) Ledger reconciliation: the header implied logged runs of about $0.01 by 07:34, but they itemize to about $0.09; the header now states the facts and the open gap plainly (see top of this file), and the stub run-log table is replaced by a pointer to runs.jsonl. (3) The first aborted pass: the trace records no error for it, so the docs no longer claim a shape failure for it; verification-results.md and the README now say the second pass stopped on the recorded L06 shape error and the first stopped after two clean runs for a reason the trace does not record. (4) A taxes-only statement was scored clean on liens/tax, against checklist section 5, which requires both halves. The harness now enforces that rule in checker.py and the Worker, openly: a one-half clean is downgraded to not addressed, the standard question is added, and the rule is recorded in the run's harness block. Proven offline on three fabricated cases and live on the reviewer's pattern. The scored verification predates the rule and stands as measured. (5) Junk input ("asdf qwerty 123") was charged $0.0008 and produced a report; inputs under eight words now return a clear 400 and cost nothing, and the empty-input message is fixed. (6) A non-US address silently fell back to listing mode; the report now carries a plain note when an address was not found in US records or records could not be checked. (7) Both cached examples predated records mode, and the Georgia one showed a well-depth question under a clean water point. All three examples were re-recorded through the production Worker (a Miami Beach address-only example added), questions on stated points now render under their own follow-up heading, and the recorded date reads Nov 25. One FEMA drop hit the first Georgia refresh (sources list showed three of four, flood honestly missing); a second run answered with all four sources and flood clean, and that run is the cache. The reviewer's own live tests cost about $0.0064 on our credits, logged here as reported. Round spend: about $0.023. All-in: about $0.17 of the $10.

## 2026-11-25, outside review round 3 (afternoon)

A third fresh-eyes review (the reviewer's live tests cost about $0.010
on the credit). Confirmed real and fixed:

- verify.py, run without the API key in a tree that HAS the listings,
  overwrote the published verification results with zeros and exited 0.
  Round 2's ledger line said it "stops at the first missing file"; that
  was wrong, and this entry corrects it. The keyless test in round 2
  lacked the listings folder, so it stopped earlier and masked the
  overwrite. Fix: a key preflight that exits 2 before anything runs,
  plus a guard that refuses to write results when no listing produced a
  run. Proven on a keyless copy with listings present: exit 2, results
  file untouched.
- Liens loophole: "No tax liens on record." stayed clean under the
  keyword rule while saying nothing about taxes paid. The rule now
  requires both halves with the right words (taxes stated paid or
  current; liens stated clear) in checker.py and the Worker. Eight
  offline cases pass, including the loophole, and a live run of the
  loophole listing now downgrades the point with the rule recorded.
- Short real addresses ("1600 Pennsylvania Ave NW, Washington, DC
  20500", seven words) were rejected as too short while nine junk words
  passed. Addresses now bypass the word minimum, and non-address input
  also needs a digit or a listing keyword. Live: both addresses return
  reports, the nine junk words return 400 at no cost.
- The Georgia catch: a listing's approved perc test silently overrode
  the USDA "Somewhat limited" septic rating in the merged pass. A
  records override now runs in the Worker (see the addendum in
  records-verification.md), and points backed only by records are
  tagged "Public records" on the page. Live on the Carlton listing:
  the perc point flags with both quotes shown, rule recorded.
- Smaller fixes: the unmatched-address note wording, a cache-busting
  query on the example files, and mode-aware wording when no red flags
  are found.
- Utilities was flagged and deliberately NOT changed: checklist.md
  section 7 counts a single stated utility ("Electricity Available",
  "Cable Available") as covered, so the live clean calls follow the
  checklist. The seam the reviewer found is between the checklist's
  wording and the answer key's gas cases, already published in the
  verification results as false flags.
- One process catch worth recording: the first deploy of this round
  silently redeployed the previous Worker, because deploy.sh builds
  from worker.src.js and the edits had landed in the generated
  worker.js. The stranger retest caught it (every new behavior was
  absent live), the edited source was promoted to worker.src.js, and
  the redeploy was verified behavior by behavior.
- The submission and README now state plainly that the entry is solo,
  directed by Vinay, and built with AI assistance, with every product
  check running on Muse Ember (Vinay's call).

Round 3 fix-round live runs: the Carlton combined run $0.0040, the
re-recorded page examples $0.0073 (L01 $0.0025, L07 $0.0034, Miami
Beach $0.0014), and about $0.008 of address, junk, and loophole test
calls, several of which returned 400 at no cost.

## 2026-11-25, the code rewritten by Muse Ember (Vinay's call)

At Vinay's direction ("use it build", "we should have done this from
start"), the implementation was recreated by Muse Ember itself.
Written specifications (behavior only, no existing code) were given to
Ember through the same Meta Model API, one file at a time, by the
runner in ember-build/gen.py. Every call is traced in
ember-build/build-runs.jsonl: 11 calls, $0.111 total, including two
calls that spent their whole budget on hidden reasoning and returned
no code (retried with a larger cap) and three fix rounds.

Validation of the Ember-written code, all by running it:
- checker.py: the eight offline liens cases pass; a fabricated quote
  is caught by its validate.
- verify.py: the keyless preflight stops at exit 2 with results
  untouched. First full run scored 0 because of a truthiness bug
  (the harness dict tested as the errors); second run crashed on a
  cost dict added to a number. Both were pinned in the spec and fixed
  by Ember in logged calls (verify-fix1, verify-fix2). Third run,
  sandboxed with the sealed key: the full verification completed,
  86 of 90 exact on that fresh pass, $0.0237. That run validates the
  code; the published 78 of 90 remains the scored pass and was not
  overwritten with a luckier re-roll.
- worker.js: first live battery failed the Georgia case (the soil
  query used a column name that does not exist, c.name for compname,
  and an inner join); the fix regeneration then broke the geocoder
  (read data.addressMatches instead of data.result.addressMatches).
  Both pinned and fixed by Ember (worker-fix1, worker-fix2). Final
  battery, all live: Pennsylvania Ave records report; nine junk words
  400; the liens loophole downgraded with the rule recorded; Carlton
  combined run flags perc through records_override_perc_septic with
  all four records sources answering; Miami Beach flood flag. The
  Ember-written Worker is the production Worker.
- index.html: Ember-written, deployed; the page and example cards
  verified live.
- server.py: Ember-written, compiles and matches its spec on review;
  a live run was NOT claimed, because port 8931 on Flash is held by
  the long-running original server and the test requests landed on
  it. It is a local development artifact only.

A twelfth Ember call ($0.0017, also in build-runs.jsonl) drafted
the demo recording checklist; the eleven-call, $0.111 figure covers
the code build only. Sandbox verification $0.0237 and about $0.02 of live battery runs
bring this phase to about $0.16. The backups of the previous
implementation sit on Flash as worker.src.js.bak-pre-ember and
index.html.bak-pre-ember.

2026-11-25, 13:35 ET: DEMO VIDEO PUBLISHED. The demo was produced with
the same process as Vinay's previous hackathon video: a real screen
recording of the live site (the Florida example, the L11 live run, the
Miami Beach address-only run, the repo verification page), narration in
Vinay's cloned voice (Chatterbox on Flash, disclosed on the closing
card and in the video description), 1080p, 2 minutes. First cut was
reviewed by Vinay: too fast, explained too much. The main chat rewrote
the script simpler (286 words), the narration was re-recorded slower,
and Vinay approved the second cut. Muse Ember was asked directly
whether it can create voice: it cannot (the API rejects audio
parameters and has no speech endpoint; a voice transcribe model exists,
speech to text only), so the cloned voice stayed, at Vinay's choice.
Published public on the Hackathon YT channel:
https://www.youtube.com/watch?v=LKc1XeZ-5VM
Video phase Ember calls, all in ember-build/build-runs.jsonl (now 15
rows, $0.131 total): YouTube title and description draft, two calls,
$0.0080 (first call returned empty after spending its budget on hidden
reasoning; retried larger) and $0.0097; the README and form link lines,
$0.0005. Demo pre-runs and the runs filmed in the recording: about
$0.008. Itemized logged total is now about $0.31 of the $10. One
disclosure: the recorded narration says the build ran on "under thirty
cents", which was the logged figure when it was recorded; the final
$0.31 includes the video phase drafting calls above.
Thumbnail art was generated by muse-image-1.0 on the same Meta API
(27,460 input and 2,168 output tokens; no list rate for it in our
rate card, so the meter governs its cost), with the thumbnail text
set locally.

2026-11-25, about 13:45 to 13:55 ET: VERIFICATION ROUND 2. At Vinay's
word (ten listings was too few), ten more real listings (L13 to L22)
were collected from public listing pages. Muse Ember drafted the
round 2 answer key from the listing texts and checklist.md in ten
logged calls, $0.0257 total (ember-build/build-runs.jsonl, tasks
key-L13 to key-L22); every quote was script-checked as an exact
substring and every status hand-reviewed, with two L13 statuses
corrected to the letter of the checklist before the key was sealed
(SHA-256 1ab2d2e7405861ec2b0f4d897d1fe7975d8250fc066a260bc8f4573
cf0cc95b7). The scored pass, one run per listing under the frozen
prompt v1, cost $0.0368 including L15's failed parse run at $0.0062,
and scored 69 of 90 (problems 14 of 19, missing 34 of 46, clean 21
of 25, no clean point flagged). Two L15 re-runs at $0.0048 and
$0.0041 scored 7 of 9 each and are reported as an addendum only.
Combined with round 1: 147 of 180 exact, 23 of 30 problems caught,
89 of 111 missing named, 35 of 39 clean called clean, $0.0626 for
the twenty scored runs. Results in verification-round2-results.md.
Itemized logged total is now about $0.38 of the $10.

2026-11-25, about 14:05 to 15:00 ET: IMPROVEMENTS PASS, at Vinay's
word, funded from the remaining credit with $2 held back as the live
judging reserve. (1) Parse-failure hardening: failed-runs.log showed
the two zero-score causes, a schema echo (L10) and an empty reply
after the model spent the whole 12,000-token output cap on hidden
reasoning (L15). Muse Ember rewrote checker.py's run path from a
written spec (one logged call, $0.0103): cap raised to 24,000, one
bounded retry on an empty, unparseable, or invalid reply, both
attempts traced with costs summed. Five offline stub tests passed;
L15 then completed on the first attempt ($0.0037). The same hardening
was mirrored into the production Worker by Ember (one call, $0.0054),
deployed, and passed a live battery (junk still 400, L15 full report,
Austin records correct). (2) Re-verification of both sealed rounds
under the hardened checker: 161 of 180 combined (round 1: 84 of 90,
round 2: 77 of 90), $0.0588; no run needed the retry. Two surplus L22
runs from an output-file collision cost $0.0129 and are counted here,
not in the scored cost. (3) Verification round 3: ten fresh listings
(L23 to L32), Ember-drafted sealed key ($0.0174, hash d1b99a93...),
scored 85 of 90 with the retry firing on two runs, $0.0394; two
surplus L32 runs from the same file collision cost $0.0102, counted
here. (4) Records round 2: ten fresh addresses, sealed key
(260e8e29...), scored 20 of 20 through the production Worker,
$0.0172. (5) Live battery after the Worker deploy, about $0.007.
Itemized logged total is now about $0.56 of the $10.
