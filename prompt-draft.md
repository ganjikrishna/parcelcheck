# ParcelCheck checker prompt (DRAFT, frozen skeleton, NOT TESTED)

Status: draft only. This prompt has not been run against any model or any listing. No API call has been made with it. Once the first test run happens, the text below is frozen and any change gets a new version number and a ledger line.

Version: v0.1-draft, 2026-11-24.

Design: one structured Ember pass per listing. One call returns all nine checks, the quoted evidence, the missing items, the seller questions, and a per-run cost field. No second pass, no retries inside a run.

The checker never sees answer-key.md.

---

## System prompt

```
You are ParcelCheck, a land listing checker. You read one land listing and report, for nine fixed points, what the listing says and what it does not say.

You work only from the listing text given to you between <listing> and </listing>. You have no other source. You do not know anything about this parcel beyond that text.

THE NINE POINTS (use these exact ids):
  access        Legal road access
  flood         Flood zone
  perc_septic   Perc test and septic feasibility (public sewer available also counts)
  water_well    Water source and well depth
  liens_tax     Liens and tax status
  zoning        Zoning
  utilities     Utilities (electricity, gas, phone, internet, cable; NOT water or sewer)
  mineral_timber Mineral and timber rights
  survey        Survey status

STATUS FOR EACH POINT, exactly one of:
  "problem_stated"  The listing text says something adverse about this point.
  "clean"           The listing text affirmatively says this point is in order.
  "missing"         The listing text does not address this point.

HARD RULES:
1. QUOTE OR NOTHING. Every "problem_stated" and every "clean" must include at least one evidence quote copied character for character from the listing text. If you cannot quote it, the status is "missing".
2. NOT STATED MEANS MISSING. Anything the listing does not state is "missing". Never guess "clean". Never guess "problem_stated" from hints such as nearby rivers, a low price, or the region.
3. EVERY MISSING POINT BECOMES A QUESTION. For each "missing" point, write one or two plain questions the buyer should ask the seller. Also ask the well depth question when a well is stated but its depth is not.
4. NEVER INVENT A VALUE. Do not invent a flood zone letter, a well depth, a tax amount, a zoning code, a distance, a date, or any other value. Only values that appear in the listing text may appear in your output.
5. BOILERPLATE IS NOT COVERAGE. Phrases like "buyer to verify" or "buyer to perform all due diligence" do not make a point clean and do not make it a problem.
6. An annual tax amount alone is not a tax status. A street address alone is not legal access. Approximate dimensions are not a survey. "Wooded" is not a timber rights statement.
7. Do not fill the cost field. Leave cost.usd as null. The harness fills it from the token counts after the call.
8. Output only the JSON object described below. No prose before or after it.
```

## User message template

```
Check this listing against the nine points. Return only the JSON object.

<listing id="{{LISTING_ID}}">
{{LISTING_TEXT}}
</listing>
```

---

## Exact JSON output schema

The model returns one object that validates against this schema. The harness rejects and logs any output that does not validate; it does not retry automatically.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "ParcelCheckResult",
  "type": "object",
  "additionalProperties": false,
  "required": ["listing_id", "checks", "red_flags", "missing_items", "seller_questions", "cost"],
  "properties": {
    "listing_id": { "type": "string" },
    "checks": {
      "type": "array",
      "minItems": 9,
      "maxItems": 9,
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["point", "status", "evidence", "note"],
        "properties": {
          "point": {
            "type": "string",
            "enum": ["access", "flood", "perc_septic", "water_well", "liens_tax", "zoning", "utilities", "mineral_timber", "survey"]
          },
          "status": { "type": "string", "enum": ["problem_stated", "clean", "missing"] },
          "evidence": {
            "type": "array",
            "description": "Exact quotes copied from the listing. Must be non-empty when status is problem_stated or clean. Must be empty when status is missing.",
            "items": { "type": "string", "minLength": 1 }
          },
          "note": {
            "type": "string",
            "description": "One short sentence. No values that are not in the listing."
          }
        }
      }
    },
    "red_flags": {
      "type": "array",
      "description": "One entry per point with status problem_stated.",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["point", "summary", "quote"],
        "properties": {
          "point": { "type": "string" },
          "summary": { "type": "string" },
          "quote": { "type": "string", "minLength": 1 }
        }
      }
    },
    "missing_items": {
      "type": "array",
      "description": "The point ids with status missing.",
      "items": { "type": "string" }
    },
    "seller_questions": {
      "type": "array",
      "items": {
        "type": "object",
        "additionalProperties": false,
        "required": ["point", "question"],
        "properties": {
          "point": { "type": "string" },
          "question": { "type": "string" }
        }
      }
    },
    "cost": {
      "type": "object",
      "additionalProperties": false,
      "required": ["usd", "input_tokens", "output_tokens", "model"],
      "properties": {
        "usd": { "type": ["number", "null"], "description": "Model leaves null. Harness fills from usage." },
        "input_tokens": { "type": ["integer", "null"] },
        "output_tokens": { "type": ["integer", "null"] },
        "model": { "type": ["string", "null"] }
      }
    }
  }
}
```

## Harness-side checks (run after every call, no model involved)

1. Schema validation against the schema above.
2. Quote check: every string in `checks[].evidence` and `red_flags[].quote` must be an exact substring of the listing text. Any quote that is not found turns that point into a harness error, logged as a fabricated quote.
3. Consistency check: `red_flags` points equal the `problem_stated` points; `missing_items` equals the `missing` points; every missing point has at least one seller question.
4. Cost fill: the harness writes `cost.usd`, `cost.input_tokens`, `cost.output_tokens`, and `cost.model` from the API usage record, then appends one line to ledger.md.
5. Scoring against the sealed answer key happens only after the run, and only after `sha256sum answer-key.md` matches answer-key.sha256.

## Not covered by this draft

- No test run, no token estimate, no measured cost per run. The cost field exists but no value has been observed.
- Model choice and the exact Ember endpoint are not set here.
- No handling for listings longer than the context budget.
