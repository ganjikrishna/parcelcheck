# Records mode verification, round 2 (2026-11-25)

Round 1 of records verification scored 14 of 20 on its first pass
(flood 9 of 10, septic 5 of 10); the fixes were confirmed 10 of 10 on
the five missed addresses. Round 2 asks the same question on ten fresh
addresses the fixes had never seen, with the septic side weighted
heavily on purpose: six of the ten carry a limited septic rating.

## Protocol

- Ten addresses chosen for variety and spiked independently
  (records-spike2.py: US Census geocoder, FEMA NFHL layer 28, USDA
  Soil Data Access), the same separate code path as round 1.
- The answer key (records-answer-key-round2.md) was sealed before the
  scored run at SHA-256
  260e8e29eb92839ca0441bb9e3aaa8f213769ad20d689161c7731c50d4025210,
  with the same expectation rules as round 1, fixed in writing inside
  the key. One first-choice address returned no geocode match in the
  spike and was replaced before sealing; the replacement is named in
  the key.
- The scored run went through the production Worker, one pass per
  address, after the Worker received the same output-cap and retry
  hardening as the checker. Two points scored per address (flood,
  perc/septic), 20 in total. One driver note: the first attempt to
  drive the pass used a script user agent that Cloudflare refused
  with 403 before any request reached the Worker; the pass was then
  driven with a browser user agent. No run reached the model before
  the scored pass.

## Scored result: 20 of 20

| Address | Flood expected | Flood got | Septic expected | Septic got |
|---|---|---|---|---|
| 1000 Ocean Dr, Miami Beach, FL 33139 | problem_stated | problem_stated | missing | missing |
| 200 Ocean Ave, Santa Monica, CA 90402 | clean | clean | missing | missing |
| 600 Travis St, Houston, TX 77002 | clean | clean | clean | clean |
| 301 W 2nd St, Austin, TX 78701 | clean | clean | problem_stated | problem_stated |
| 100 W Washington St, Phoenix, AZ 85003 | clean | clean | problem_stated | problem_stated |
| 200 E Colfax Ave, Denver, CO 80203 | clean | clean | missing | missing |
| 400 W Church St, Orlando, FL 32801 | clean | clean | problem_stated | problem_stated |
| 350 Deaderick St, Nashville, TN 37219 | clean | clean | problem_stated | problem_stated |
| 100 Main St, Madison, GA 30650 | clean | clean | problem_stated | problem_stated |
| 301 King St, Charleston, SC 29401 | clean | clean | problem_stated | problem_stated |

Flood 10 of 10, septic 10 of 10. Cost of the ten runs: $0.0172.
