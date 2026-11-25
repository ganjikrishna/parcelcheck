# Records mode verification (2026-11-25)

Public records mode was verified the same way as listing mode: expectations
sealed before the scored run, one pass, no retries inside the pass, misses
published.

## Protocol

- Ten addresses chosen for variety: two in Special Flood Hazard Areas,
  eight outside them; septic ratings spanning Very limited, Somewhat
  limited, Not limited, and Not rated (most urban soils).
- The answer key (`records-answer-key.md`, sealed before the run at
  SHA-256 c3e44ae65d5aa38434bc58cbd7a283a448a7dbe8c8de2d33682b234a7db6da73,
  with a wording-only amendment recorded inside it before publication)
  was built
  from an independent spike (`records-spike.py`): direct calls to the US
  Census geocoder, FEMA NFHL, and USDA Soil Data Access from a separate
  code path, with the expectation rules fixed in writing before the run.
- The scored run went through the production Worker, the same code path a
  visitor uses. Two points scored per address (flood, perc/septic), 20 in
  total. Two development addresses (a residential address in Georgia and
  a Miami Beach address used while building the mode) were excluded from
  the set.

## Scored result: 14 of 20

| Address | Flood expected | Flood got | Septic expected | Septic got |
|---|---|---|---|---|
| 1632 S School Ave, Fayetteville, AR | problem (Zone AE) | problem | problem (Very limited) | problem |
| 55 Dora Bush Hill Rd, Carlton, GA | clean (Zone X) | clean | problem (Somewhat limited) | problem |
| 1600 Pennsylvania Ave NW, Washington, DC | clean (Zone X) | clean | missing (Not rated) | problem |
| 350 Fifth Ave, New York, NY | clean (Zone X) | clean | problem (Very limited) | problem |
| 2217 Strand St, Galveston, TX | problem (Zone AE) | problem | problem (Very limited) | problem |
| 400 Broad St, Seattle, WA | clean (Zone X) | clean | missing (Not rated) | problem |
| 1415 Tulane Ave, New Orleans, LA | clean (Zone X) | missing | missing (Not rated) | problem |
| 1 E Edenton St, Raleigh, NC | clean (Zone X) | clean | missing (Not rated) | problem |
| 1 Dr Carlton B Goodlett Pl, San Francisco, CA | clean (Zone X) | clean | clean (Not limited) | clean |
| 206 Washington St SW, Atlanta, GA | clean (Zone X) | clean | missing (Not rated) | problem |

Flood: 9 of 10. Perc/septic: 5 of 10. Cost of the scored pass: $0.0175.

## The two findings, and the fixes

1. **"Not rated" read as a problem, 5 times out of 5.** The records text
   carried the USDA sentence "rated for septic tank absorption fields as:
   Not rated" for urban soils, and Ember flagged every one as a septic
   problem. No information was read as bad information. Fix, in the
   records text assembly (the prompt is unchanged): the septic sentence
   is now omitted when the rating is Not rated, so the point stays an
   honest seller question.
2. **FEMA dropped one run in ten.** FEMA's gateway resets connections
   intermittently; the New Orleans run lost its flood answer and the
   point went missing. Fix: the Worker now pauses and retries FEMA once,
   then falls back to FEMA's FIRMette mirror of the same layer.

## Confirmation run (post-fix, reported separately)

The five addresses that missed were re-run once after the fixes: **10 of
10**, all four sources answering on every run, cost $0.0071. The sealed
14 of 20 stands as the first-pass result; the confirmation shows the two
failure patterns are gone, on the same addresses that produced them.
