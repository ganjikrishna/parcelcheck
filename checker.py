#!/usr/bin/env python3
"""ParcelCheck checker core. One structured Muse Ember pass per listing,
harness side validation, quote verification, cost fill, trace logging.

Usage:
  python3 checker.py <listing-file> [listing-id]
  python3 checker.py --text '<listing text>' [listing-id]

Reads the API key from meta-api-key.txt and the frozen prompt from
prompt-v1.json, both in the folder holding this script (override with
the PARCELCHECK_DIR environment variable). Appends one JSON line per
run to runs.jsonl in the same folder (the prompt and token trace).
Prints the validated result JSON to stdout.
"""
import json, os, pathlib, re, sys, time, urllib.request, urllib.error

PREP = pathlib.Path(os.environ.get("PARCELCHECK_DIR", pathlib.Path(__file__).resolve().parent))
API = "https://api.meta.ai/v1/responses"
MODEL = "muse-ember-1.0"
RATE_IN, RATE_OUT = 0.10 / 1e6, 0.50 / 1e6
POINTS = ["access", "flood", "perc_septic", "water_well", "liens_tax",
          "zoning", "utilities", "mineral_timber", "survey"]
STATUSES = {"problem_stated", "clean", "missing"}

def call_ember(system, user, max_out=8000):
    key = (PREP / "meta-api-key.txt").read_text().strip()
    payload = {"model": MODEL,
               "input": [{"role": "system", "content": system},
                         {"role": "user", "content": user}],
               "max_output_tokens": max_out, "store": False}
    req = urllib.request.Request(API, data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + key, "content-type": "application/json"})
    t = time.time()
    with urllib.request.urlopen(req, timeout=300) as resp:
        body = json.loads(resp.read())
    text = ""
    for item in body.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    text += c.get("text", "")
    u = body.get("usage", {})
    return text, u.get("input_tokens", 0), u.get("output_tokens", 0), round(time.time() - t, 1)

def parse_json(text):
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```[a-z]*\n|```$", "", text).strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Harness fix, 2026-11-25: two failure modes seen on L10, prose
        # added after the JSON object, and the model echoing the schema
        # before its result. Scan every object start, decode the first
        # complete object that carries a top level "checks" key, and
        # validate as usual. The prompt is unchanged.
        dec = json.JSONDecoder()
        for i, ch in enumerate(text):
            if ch != "{":
                continue
            try:
                obj, _ = dec.raw_decode(text[i:])
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict) and "checks" in obj:
                return obj
        raise

def apply_rules(result):
    """Deterministic checklist rules, applied openly and recorded in the
    result. liens_tax counts as clean only when the evidence covers both
    halves of the point (taxes stated paid or current, and liens stated
    clear), per checklist.md section 5. A phrase covering neither half
    (for example "no tax liens") does not count for either. A clean call resting on one half is downgraded
    to missing, and the standard seller question is added if the model
    did not ask it. Nothing else is edited."""
    applied = []
    for c in result.get("checks", []):
        if c.get("point") == "liens_tax" and c.get("status") == "clean":
            ev = " ".join(c.get("evidence", [])).lower()
            tax_half = "tax" in ev and any(k in ev for k in (
                "paid", "current", "through", "up to date", "up-to-date",
                "not delinquent", "no delinquent"))
            lien_half = "lien" in ev and any(k in ev for k in (
                "no lien", "free of lien", "free and clear", "clear of lien",
                "without lien", "no recorded lien", "lien free", "lien-free",
                "not subject to lien"))
            if not (tax_half and lien_half):
                c["status"] = "missing"
                c["note"] = (c.get("note", "") +
                    " Harness rule: only one half of this point (taxes or liens) is stated, so it counts as not fully addressed.").strip()
                if "liens_tax" not in result.get("missing_items", []):
                    result.setdefault("missing_items", []).append("liens_tax")
                if not any(q.get("point") == "liens_tax" for q in result.get("seller_questions", [])):
                    result.setdefault("seller_questions", []).append(
                        {"point": "liens_tax",
                         "question": "Are all property taxes paid through the current year, and are there any liens, judgments, or back taxes on this parcel?"})
                applied.append("liens_tax_clean_requires_both_halves")
    return applied


def validate(result, listing_text):
    """Harness checks. Returns (errors, warnings). Never edits statuses;
    a failed quote check is reported, not silently fixed."""
    errors, warnings = [], []
    checks = result.get("checks")
    if not isinstance(checks, list) or len(checks) != 9:
        errors.append("checks must be a list of exactly 9")
        return errors, warnings
    seen = set()
    for c in checks:
        p = c.get("point")
        if p not in POINTS:
            errors.append(f"unknown point: {p}")
            continue
        seen.add(p)
        if c.get("status") not in STATUSES:
            errors.append(f"{p}: bad status {c.get('status')}")
        ev = c.get("evidence", [])
        if c.get("status") in ("problem_stated", "clean") and not ev:
            errors.append(f"{p}: {c.get('status')} with no evidence quote")
        if c.get("status") == "missing" and ev:
            warnings.append(f"{p}: missing but carries evidence")
        for q in ev:
            if q not in listing_text:
                errors.append(f"{p}: FABRICATED QUOTE: {q[:60]!r}")
    if seen != set(POINTS):
        errors.append(f"points covered: {sorted(seen)}")
    prob = {c["point"] for c in checks if c.get("status") == "problem_stated"}
    miss = {c["point"] for c in checks if c.get("status") == "missing"}
    if {r.get("point") for r in result.get("red_flags", [])} != prob:
        warnings.append("red_flags do not match problem_stated points")
    if set(result.get("missing_items", [])) != miss:
        warnings.append("missing_items do not match missing points")
    qpoints = {q.get("point") for q in result.get("seller_questions", [])}
    if not miss.issubset(qpoints):
        warnings.append(f"missing points without a seller question: {sorted(miss - qpoints)}")
    return errors, warnings

def check(listing_text, listing_id):
    prompt = json.loads((PREP / "prompt-v1.json").read_text())
    user = ("Check this listing against the nine points. Return only the JSON object.\n\n"
            f'<listing id="{listing_id}">\n{listing_text}\n</listing>')
    raw, i, o, dt = call_ember(prompt["system"], user, max_out=12000)
    try:
        result = parse_json(raw)
    except Exception as e:
        fail = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "listing_id": listing_id,
                "prompt_version": prompt["version"], "model": MODEL,
                "input_tokens": i, "output_tokens": o,
                "usd": round(i * RATE_IN + o * RATE_OUT, 6),
                "error": "parse failure: " + str(e), "raw_head": raw[:400]}
        with open(PREP / "runs.jsonl", "a") as f:
            f.write(json.dumps(fail) + "\n")
        with open(PREP / "failed-runs.log", "a") as f:
            f.write(json.dumps(fail) + "\n" + raw + "\n---\n")
        raise
    applied = apply_rules(result)
    errors, warnings = validate(result, listing_text)
    usd = round(i * RATE_IN + o * RATE_OUT, 6)
    result["cost"] = {"usd": usd, "input_tokens": i, "output_tokens": o, "model": MODEL}
    result["harness"] = {"errors": errors, "warnings": warnings, "seconds": dt,
                         "prompt_version": prompt["version"], "rules_applied": applied}
    trace = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "listing_id": listing_id,
             "prompt_version": prompt["version"], "model": MODEL,
             "input_tokens": i, "output_tokens": o, "usd": usd,
             "errors": errors, "warnings": warnings, "rules_applied": applied}
    with open(PREP / "runs.jsonl", "a") as f:
        f.write(json.dumps(trace) + "\n")
    return result

def main():
    args = sys.argv[1:]
    if args and args[0] == "--text":
        text, lid = args[1], (args[2] if len(args) > 2 else "adhoc")
    else:
        path = pathlib.Path(args[0])
        raw = path.read_text()
        text = raw.split("\n\n", 1)[1].strip() if "\n\n" in raw else raw
        lid = args[1] if len(args) > 1 else path.stem
    result = check(text, lid)
    print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
