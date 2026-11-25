# ParcelCheck

ParcelCheck reads a land listing and tells you what the listing is not telling you, for pennies.

**Live: https://parcelcheck.ganjikrishna.workers.dev** (paste a listing, or open a cached example for free)

Paste a listing and ParcelCheck checks nine things land buyers get burned on:

1. Legal road access
2. Flood zone
3. Perc test and septic feasibility
4. Water source and well depth
5. Liens and tax status
6. Zoning
7. Utilities
8. Mineral and timber rights
9. Survey status

For each point it reports one of three things: a problem the listing itself states (with the listing's own words quoted as evidence), a point the listing affirmatively covers, or a point the listing does not say anything about. Every point the listing leaves silent becomes an exact question to ask the seller. The checker never invents a value the text does not state. If it cannot quote the listing, it does not make the claim.

## Why

Land listings are written to sell. The expensive facts, a parcel that is landlocked, a flood zone that forces elevated construction, no perc test, no water, are often present only as silence, or buried in field codes at the bottom of the page. A buyer who does not already know the diligence list does not know what to look for. ParcelCheck hands them the list, the evidence, and the questions, for about a fifth of a cent per check.

## How it works

One structured call to Muse Ember (Meta Model API) per listing, using the frozen prompt in `prompt-v1.md`. A small harness around the call validates the output before anything is shown: exactly nine points, every problem or clean claim backed by a quote that must appear word for word in the listing text, red flags and missing items consistent with the per point statuses, and a seller question for every missing point. The harness fills in the real cost of the run from the API token counts. Every run is logged in `runs.jsonl` with its prompt version and token counts.

Listings go stale, so the live page (a Cloudflare Worker, source in `worker.js`) also checks public records. One box, nothing to configure: type just an address and the check runs on records alone; paste a listing that contains an address and the records are checked too and merged into the same report. The sources are all free and need no keys: the US Census geocoder finds the point, FEMA's National Flood Hazard Layer gives the flood zone, the USDA soil survey gives the soil, its drainage class, and its septic absorption rating, and the US Fish and Wildlife Service wetlands inventory reports mapped wetlands. The records are compiled into sourced sentences and go through the same Ember pass and the same quote-or-drop validation, so a record can fill a listing's silence but can never be invented. A source that fails adds nothing, and that point stays a seller question.

## Verification

The checker was tested against 12 real listings. Two (L01, L07) were development listings used to settle the prompt. The other ten were scored against an answer key written by hand from the listing text and sealed with a SHA-256 hash before any of the ten was run (`answer-key.md`, `answer-key.sha256`). Results, including the misses, are in `verification-results.md`:

- 78 of 90 points matched the key exactly
- 9 of 11 stated problems caught
- 3 false problem flags, all from one pattern: a statement about a single utility (natural gas) read as a statement about utilities in general
- 55 of 65 missing points correctly named as missing
- 14 of 14 clean points correctly called clean
- One listing (L10) produced output that did not parse and scored zero. It is reported, not hidden.
- Total cost of the ten verification runs: $0.0236

Records mode was verified the same way (`records-verification.md`, key in `records-answer-key.md`, sealed by hash): ten addresses, flood and septic scored, 20 points. First pass: **14 of 20** (flood 9 of 10, septic 5 of 10), $0.0175. The misses had two causes, both fixed in the harness and records assembly with the prompt unchanged: a USDA "Not rated" sentence that read as a septic problem (5 of the misses), and one FEMA gateway drop. A post-fix confirmation run on the five missed addresses scored 10 of 10.

The L10 parse failure was also revisited (addendum in `verification-results.md`): the parser now recovers a result object surrounded by prose or a schema echo, the validator rejects a schema-only reply, and L10 re-ran at 9 of 9 twice. The original scored zero stands in the table above.

## Budget

Built for the Muse Ember Hackathon (Cerebral Valley), category Scale the Real World. The entire budget was $10 in Meta Model API credits. Every dollar is accounted for in `ledger.md`: development, the call shape test that chose one structured pass over per point calls, the verification runs, and the reserve kept for live judging. Total spent at the time of the verification run: about $0.08.

## Run it

```
python3 server.py     # serves the page at http://127.0.0.1:8931
python3 checker.py listings/L01.txt L01   # one check from the command line
python3 verify.py     # re-run the verification set against the sealed key
```

The API key is read from `meta-api-key.txt` in the working folder. It is listed in `.gitignore` and is never committed.

## Files

- `index.html` the one page app: examples with cached results, paste box, live run, cost counter
- `worker.js` the production Cloudflare Worker: serves the page, runs the same checker, and adds the live public records check (Census, FEMA, USDA, USFWS). The frozen prompt is injected at deploy time from `prompt-v1.json`; the API key is a Worker secret
- `server.py` local server with an explicit path allowlist (the answer key and the API key are never served) and a daily live run cap
- `checker.py` the checker core: one Ember pass, harness validation, quote check, cost fill, trace log
- `prompt-v1.md`, `prompt-v1.json` the frozen prompt, schema included
- `checklist.md` the nine point diligence list the prompt is built from
- `listings/` the 12 real listings used for development and verification
- `answer-key.md`, `answer-key.sha256` the sealed scoring key
- `verification-results.md`, `verification-detail.json` the scored results, with the L10 addendum
- `records-answer-key.md`, `records-answer-key.sha256`, `records-verification.md` the sealed key and scored results for records mode
- `cached-L01.json`, `cached-L07.json` recorded live results used as page examples
- `runs.jsonl` the prompt and token trace for every run
- `ledger.md` the spend ledger

## Builder

Solo build by Vinay K Ganji Krishna. The diligence list comes from real use: a Georgia tax deed auction watch and a family farmland purchase in India, where access, flood zone, perc, well depth, and liens are the questions that decide whether land is worth anything.
