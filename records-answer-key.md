# Records verification answer key (sealed before the scored run)

Built 2026-11-25 from an independent spike (records-spike.py, run on Flash,
direct calls to the US Census geocoder, FEMA NFHL layer 28, and USDA Soil
Data Access), a separate code path from the production Worker.

Expectation rules, fixed before the scored run:
- Flood: problem_stated if the FEMA point is in a Special Flood Hazard Area
  (SFHA_TF = T); clean if a flood zone feature exists and SFHA_TF = F;
  missing if FEMA publishes no feature at the point.
- Perc/septic: problem_stated if the USDA septic absorption rating is Very
  limited or Somewhat limited; clean if Not limited; missing if Not rated
  or no soil data.

| # | Address (as entered) | FEMA zone | SFHA | Expected flood | USDA septic rating | Expected perc/septic |
|---|---|---|---|---|---|---|
| 1 | 1632 S School Ave, Fayetteville, AR 72701 | AE | T | problem_stated | Very limited | problem_stated |
| 2 | 55 Dora Bush Hill Road, Carlton, GA 30627 | X | F | clean | Somewhat limited | problem_stated |
| 3 | 1600 Pennsylvania Ave NW, Washington, DC 20500 | X | F | clean | Not rated | missing |
| 4 | 350 Fifth Ave, New York, NY 10118 | X | F | clean | Very limited | problem_stated |
| 5 | 2217 Strand St, Galveston, TX 77550 | AE | T | problem_stated | Very limited | problem_stated |
| 6 | 400 Broad St, Seattle, WA 98109 | X | F | clean | Not rated | missing |
| 7 | 1415 Tulane Ave, New Orleans, LA 70112 | X | F | clean | Not rated | missing |
| 8 | 1 E Edenton St, Raleigh, NC 27601 | X | F | clean | Not rated | missing |
| 9 | 1 Dr Carlton B Goodlett Pl, San Francisco, CA 94102 | X | F | clean | Not limited | clean |
| 10 | 206 Washington St SW, Atlanta, GA 30334 | X | F | clean | Not rated | missing |

Development addresses, excluded from the scored set: a residential
address in Georgia (spike: Zone X, septic Somewhat limited) and 1700
Convention Center Dr, Miami Beach, FL (Zone AE), both used while building
records mode.
L07's flood outcome (clean, Zone X) was also seen once in a combined mode
test before this key was sealed; its address is in the scored set as row 2
with that prior observation disclosed here.

Amendment, 2026-11-25 (after the scored run, before publication): the
development note above originally named the residential address as the
builder's home. That wording, and only that wording, was changed at the
builder's direction so the published key carries no personal reference.
No address, rule, expectation, or result in this key was changed. The
key as sealed before the scored run had SHA-256
c3e44ae65d5aa38434bc58cbd7a283a448a7dbe8c8de2d33682b234a7db6da73; the
scored run was run against that version.
