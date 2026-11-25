# Records verification answer key, round 2 (sealed before the scored run)

Built 2026-11-25 from an independent spike (records-spike2.py, run on Flash,
direct calls to the US Census geocoder, FEMA NFHL layer 28, and USDA Soil
Data Access), a separate code path from the production Worker. Ten fresh
addresses, none of them in the round 1 records set or the development set.
One first-choice address (1 Public Sq, Nashville, TN) returned no geocode
match in the spike and was replaced before sealing with 350 Deaderick St,
Nashville, TN, which was spiked the same way.

Expectation rules, the same as round 1, fixed before the scored run:
- Flood: problem_stated if the FEMA point is in a Special Flood Hazard Area
  (SFHA_TF = T); clean if a flood zone feature exists and SFHA_TF = F;
  missing if FEMA publishes no feature at the point.
- Perc/septic: problem_stated if the USDA septic absorption rating is Very
  limited or Somewhat limited; clean if Not limited; missing if Not rated
  or no soil data.

| # | Address (as entered) | FEMA zone | SFHA | Expected flood | USDA septic rating | Expected perc/septic |
|---|---|---|---|---|---|---|
| 1 | 1000 Ocean Dr, Miami Beach, FL 33139 | AE | T | problem_stated | Not rated | missing |
| 2 | 200 Ocean Ave, Santa Monica, CA 90402 | X | F | clean | Not rated | missing |
| 3 | 600 Travis St, Houston, TX 77002 | X | F | clean | Not limited | clean |
| 4 | 301 W 2nd St, Austin, TX 78701 | X | F | clean | Very limited | problem_stated |
| 5 | 100 W Washington St, Phoenix, AZ 85003 | X | F | clean | Somewhat limited | problem_stated |
| 6 | 200 E Colfax Ave, Denver, CO 80203 | X | F | clean | Not rated | missing |
| 7 | 400 W Church St, Orlando, FL 32801 | X | F | clean | Somewhat limited | problem_stated |
| 8 | 350 Deaderick St, Nashville, TN 37219 | X | F | clean | Somewhat limited | problem_stated |
| 9 | 100 Main St, Madison, GA 30650 | X | F | clean | Somewhat limited | problem_stated |
| 10 | 301 King St, Charleston, SC 29401 | X | F | clean | Very limited | problem_stated |
