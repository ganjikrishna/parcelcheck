"""ParcelCheck - land listing diligence checker.

Sends one land listing to the Muse Ember model with a frozen prompt,
validates the model's structured answer in a harness, and logs a trace
of every run.

Usage:
    python3 checker.py <listing-file> [listing-id]
    python3 checker.py --text '<text>' [listing-id]

The tool reads the API key (meta-api-key.txt) and the frozen prompt
(prompt-v1.json) from its own folder (PARCELCHECK_DIR override), where
the data folder is the PARCELCHECK_DIR environment variable if set,
else the folder containing this script file. It appends one trace line
per run to runs.jsonl in that folder.
"""

import datetime
import json
import os
import sys
import time
import urllib.request
from pathlib import Path


PREP = Path(os.environ.get("PARCELCHECK_DIR") or Path(__file__).resolve().parent)
DATA_DIR = PREP
PREP_DIR = PREP

MODEL = "muse-ember-1.0"
API_ENDPOINT = "https://api.meta.ai/v1/responses"
ENDPOINT = API_ENDPOINT
API_URL = API_ENDPOINT

INPUT_USD_PER_MILLION = 0.10
OUTPUT_USD_PER_MILLION = 0.50
COST_INPUT_PER_MILLION = 0.10
COST_OUTPUT_PER_MILLION = 0.50
INPUT_RATE_PER_MILLION = 0.10
OUTPUT_RATE_PER_MILLION = 0.50

POINTS = [
    "access",
    "flood",
    "perc_septic",
    "water_well",
    "liens_tax",
    "zoning",
    "utilities",
    "mineral_timber",
    "survey",
]
NINE_POINTS = POINTS
VALID_STATUSES = ("problem_stated", "clean", "missing")


def _prep_dir():
    env = os.environ.get("PARCELCHECK_DIR")
    if env:
        return Path(env)
    return Path(PREP)


def _point_of(item):
    if isinstance(item, str):
        return item
    if isinstance(item, dict):
        point = item.get("point")
        return point if isinstance(point, str) else None
    return None


def _points_from_list(value):
    points = set()
    if isinstance(value, list):
        for item in value:
            point = _point_of(item)
            if isinstance(point, str):
                points.add(point)
    elif isinstance(value, str):
        points.add(value)
    elif isinstance(value, dict):
        point = _point_of(value)
        if isinstance(point, str):
            points.add(point)
    return points


def _evidence_quotes(check):
    if not isinstance(check, dict):
        return []
    evidence = check.get("evidence")
    if evidence is None:
        evidence = check.get("quotes")
    if evidence is None:
        return []
    if isinstance(evidence, str):
        return [evidence] if evidence else []
    if isinstance(evidence, dict):
        quote = evidence.get("quote")
        if quote is None:
            quote = evidence.get("text")
        return [str(quote)] if quote else []
    if isinstance(evidence, (list, tuple)):
        quotes = []
        for item in evidence:
            if isinstance(item, str):
                quotes.append(item)
            elif isinstance(item, dict):
                quote = item.get("quote")
                if quote is None:
                    quote = item.get("text")
                quotes.append(str(quote) if quote is not None else "")
            elif item is not None:
                quotes.append(str(item))
        return quotes
    return []


def _seller_questions_list(result):
    if not isinstance(result, dict):
        return []
    for key in ("seller_questions", "questions", "sellerQuestions"):
        value = result.get(key)
        if isinstance(value, list):
            return value
    return []


def _usd(input_tokens, output_tokens):
    return round(
        ((input_tokens or 0) * INPUT_USD_PER_MILLION + (output_tokens or 0) * OUTPUT_USD_PER_MILLION) / 1_000_000,
        6,
    )


def call_ember(system, user, max_out=8000):
    prep = _prep_dir()
    key = (prep / "meta-api-key.txt").read_text(encoding="utf-8").strip()
    payload = {
        "model": MODEL,
        "input": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "max_output_tokens": max_out,
        "store": False,
    }
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        API_ENDPOINT,
        data=data,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    start = time.time()
    raw_response = urllib.request.urlopen(request, timeout=300)
    if hasattr(raw_response, "__enter__") and hasattr(raw_response, "__exit__"):
        with raw_response as response:
            body = response.read()
    else:
        try:
            body = raw_response.read()
        finally:
            try:
                raw_response.close()
            except Exception:
                pass
    elapsed = round(time.time() - start, 1)
    parsed = json.loads(body.decode("utf-8") if isinstance(body, (bytes, bytearray)) else body)
    text_parts = []
    for item in parsed.get("output", []) or []:
        if not isinstance(item, dict) or item.get("type") != "message":
            continue
        for content in item.get("content", []) or []:
            if isinstance(content, dict) and content.get("type") == "output_text":
                text_parts.append(content.get("text", ""))
    text = "".join(text_parts)
    usage = parsed.get("usage", {}) or {}
    input_tokens = usage.get("input_tokens", 0) or 0
    output_tokens = usage.get("output_tokens", 0) or 0
    return text, input_tokens, output_tokens, elapsed


def parse_json(text):
    stripped = text.strip()
    processed = stripped
    if processed.startswith("```"):
        newline_idx = processed.find("\n")
        if newline_idx != -1:
            processed = processed[newline_idx + 1:].strip()
        else:
            processed = processed[3:].strip()
        if processed.endswith("```"):
            processed = processed[:-3].strip()
    try:
        return json.loads(processed)
    except Exception as original_error:
        decoder = json.JSONDecoder()
        for idx, ch in enumerate(processed):
            if ch == "{":
                try:
                    obj, _end = decoder.raw_decode(processed, idx)
                except Exception:
                    continue
                if isinstance(obj, dict) and "checks" in obj:
                    return obj
        raise original_error


def apply_rules(result):
    """Apply deterministic harness rules to result.

    Rule liens_tax_clean_requires_both_halves: liens and tax status
    counts as clean only when the evidence covers both halves (taxes
    stated paid or current, liens stated clear), per checklist
    section 5, and a phrase covering neither half (for example
    "no tax liens") counts for neither.

    A clean liens_tax check whose evidence does not state both that
    taxes are paid/current and that liens are clear is downgraded to
    missing, with a seller question added if needed.
    """
    applied = []
    if not isinstance(result, dict):
        return applied
    checks = result.get("checks")
    if not isinstance(checks, list):
        return applied
    target = None
    for check in checks:
        if isinstance(check, dict) and check.get("point") == "liens_tax":
            target = check
            break
    if target is None or target.get("status") != "clean":
        return applied

    quotes = _evidence_quotes(target)
    text = " ".join(quotes).lower()

    tax_half = "tax" in text and any(
        phrase in text
        for phrase in (
            "paid",
            "current",
            "through",
            "up to date",
            "up-to-date",
            "not delinquent",
            "no delinquent",
        )
    )
    lien_half = "lien" in text and any(
        phrase in text
        for phrase in (
            "no lien",
            "free of lien",
            "free and clear",
            "clear of lien",
            "without lien",
            "no recorded lien",
            "lien free",
            "lien-free",
            "not subject to lien",
        )
    )

    if tax_half and lien_half:
        return applied

    target["status"] = "missing"
    sentence = "Harness rule: only one half of this point (taxes or liens) is stated, so it counts as not fully addressed."
    note = target.get("note")
    if isinstance(note, str) and note:
        target["note"] = note.rstrip() + " " + sentence
    else:
        target["note"] = sentence

    missing_items = result.get("missing_items")
    if not isinstance(missing_items, list):
        missing_items = []
        result["missing_items"] = missing_items
    if "liens_tax" not in _points_from_list(missing_items):
        missing_items.append("liens_tax")

    seller_questions = None
    for key in ("seller_questions", "questions", "sellerQuestions"):
        value = result.get(key)
        if isinstance(value, list):
            seller_questions = value
            break
    if seller_questions is None:
        seller_questions = []
        result["seller_questions"] = seller_questions
    if "liens_tax" not in _points_from_list(seller_questions):
        seller_questions.append(
            {
                "point": "liens_tax",
                "question": "Are all property taxes paid through the current year, and are there any liens, judgments, or back taxes on this parcel?",
            }
        )

    applied.append("liens_tax_clean_requires_both_halves")
    return applied


def validate(result, listing_text):
    errors = []
    warnings = []
    if not isinstance(result, dict):
        return ["checks must be a list of exactly 9"], []
    checks = result.get("checks")
    if not isinstance(checks, list) or len(checks) != 9:
        return ["checks must be a list of exactly 9"], []

    seen = set()
    problem_points = set()
    missing_points = set()

    for check in checks:
        if not isinstance(check, dict):
            errors.append(f"Unknown point: {check!r}")
            continue
        point = check.get("point")
        if isinstance(point, str):
            seen.add(point)
        if point not in POINTS:
            errors.append(f"Unknown point: {point}")
        status = check.get("status")
        if status not in VALID_STATUSES:
            errors.append(f"Invalid status for {point}: {status}")
        if status == "problem_stated" and isinstance(point, str):
            problem_points.add(point)
        if status == "missing" and isinstance(point, str):
            missing_points.add(point)

        quotes = _evidence_quotes(check)
        has_evidence = any(q for q in quotes)
        if status in ("problem_stated", "clean") and not has_evidence:
            errors.append(f"{point}: status {status} has no evidence")
        if status == "missing" and has_evidence:
            warnings.append(f"{point}: missing check carries evidence")
        for quote in quotes:
            if quote not in listing_text:
                errors.append(f"FABRICATED QUOTE for {point}: {quote}")

    if seen != set(POINTS):
        errors.append("checks do not cover all nine points")

    red_flag_points = _points_from_list(result.get("red_flags"))
    if red_flag_points != problem_points:
        warnings.append(
            f"red_flags points {sorted(red_flag_points)} differ from problem_stated points {sorted(problem_points)}"
        )

    missing_items_points = _points_from_list(result.get("missing_items"))
    if missing_items_points != missing_points:
        warnings.append(
            f"missing_items points {sorted(missing_items_points)} differ from missing points {sorted(missing_points)}"
        )

    seller_points = _points_from_list(_seller_questions_list(result))
    lacking = [p for p in POINTS if p in missing_points and p not in seller_points]
    for p in sorted(missing_points - set(POINTS)):
        if p not in seller_points:
            lacking.append(p)
    if lacking:
        warnings.append(f"missing points lack seller questions: {', '.join(lacking)}")

    return errors, warnings


def check(listing_text, listing_id):
    prep = _prep_dir()
    with open(prep / "prompt-v1.json", encoding="utf-8") as fh:
        prompt_data = json.load(fh)
    prompt_version = prompt_data.get("version")
    system = prompt_data.get("system")
    user = f"Check this listing against the nine points. Return only the JSON object.\n\n<listing id=\"{listing_id}\">\n{listing_text}\n</listing>"
    ts = datetime.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M:%S%z")

    total_input_tokens = 0
    total_output_tokens = 0
    total_usd = 0
    total_elapsed = 0
    attempts = 0

    result = None
    rules_applied = []
    errors = []
    warnings = []

    last_exc = None
    last_error = None
    last_raw_text = ""

    for attempt in range(1, 3):
        attempts = attempt
        raw_text, input_tokens, output_tokens, elapsed = call_ember(system, user, max_out=24000)
        if not isinstance(raw_text, str):
            raw_text = str(raw_text)
        usd = _usd(input_tokens, output_tokens)
        total_input_tokens += input_tokens or 0
        total_output_tokens += output_tokens or 0
        total_usd += usd
        total_elapsed += elapsed or 0

        attempt_result = None
        attempt_rules_applied = []
        attempt_errors = []
        attempt_warnings = []
        attempt_exc = None
        attempt_error = None

        if not raw_text.strip():
            attempt_exc = ValueError("empty reply")
            attempt_error = "empty reply"
        else:
            try:
                attempt_result = parse_json(raw_text)
            except Exception as exc:
                attempt_exc = exc
                attempt_error = f"parse failure: {exc}"
            else:
                attempt_rules_applied = apply_rules(attempt_result)
                attempt_errors, attempt_warnings = validate(attempt_result, listing_text)
                if attempt_errors:
                    attempt_exc = ValueError(f"validation failed: {attempt_errors}")
                    attempt_error = f"validation failed: {attempt_errors}"

        if attempt_exc is None:
            result = attempt_result
            rules_applied = attempt_rules_applied
            errors = attempt_errors
            warnings = attempt_warnings
            break

        last_exc = attempt_exc
        last_error = attempt_error
        last_raw_text = raw_text

        failed_trace = {
            "ts": ts,
            "listing_id": listing_id,
            "prompt_version": prompt_version,
            "model": MODEL,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "usd": usd,
            "error": attempt_error,
            "raw_head": raw_text[:400],
        }
        failed_entry = dict(failed_trace)
        failed_entry["raw"] = raw_text
        failed_entry["raw_reply"] = raw_text

        if attempt < 2:
            with open(prep / "failed-runs.log", "a", encoding="utf-8") as fh:
                fh.write(json.dumps(failed_entry) + "\n")
                fh.write(raw_text + "\n")
        else:
            trace = {
                "ts": ts,
                "listing_id": listing_id,
                "prompt_version": prompt_version,
                "model": MODEL,
                "input_tokens": total_input_tokens,
                "output_tokens": total_output_tokens,
                "usd": total_usd,
                "error": last_error,
                "raw_head": last_raw_text[:400],
                "attempts": 2,
            }
            with open(prep / "runs.jsonl", "a", encoding="utf-8") as fh:
                fh.write(json.dumps(trace) + "\n")
            with open(prep / "failed-runs.log", "a", encoding="utf-8") as fh:
                fh.write(json.dumps(failed_entry) + "\n")
                fh.write(raw_text + "\n")
            raise last_exc

    result["cost"] = {
        "usd": total_usd,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "model": MODEL,
    }
    result["harness"] = {
        "errors": errors,
        "warnings": warnings,
        "seconds": total_elapsed,
        "prompt_version": prompt_version,
        "rules_applied": rules_applied,
        "attempts": attempts,
        "retried": attempts == 2,
    }
    trace = {
        "ts": ts,
        "listing_id": listing_id,
        "prompt_version": prompt_version,
        "model": MODEL,
        "input_tokens": total_input_tokens,
        "output_tokens": total_output_tokens,
        "usd": total_usd,
        "errors": errors,
        "warnings": warnings,
        "rules_applied": rules_applied,
        "attempts": attempts,
        "retried": attempts == 2,
    }
    with open(prep / "runs.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(trace) + "\n")
    return result


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    if not argv:
        print("usage: python3 checker.py <listing-file> [listing-id] | --text '<text>' [listing-id]", file=sys.stderr)
        return 2
    if argv[0] == "--text":
        if len(argv) < 2:
            print("usage: python3 checker.py --text '<text>' [listing-id]", file=sys.stderr)
            return 2
        listing_text = argv[1]
        listing_id = argv[2] if len(argv) > 2 else "adhoc"
    else:
        listing_file = argv[0]
        listing_id = argv[1] if len(argv) > 1 else Path(listing_file).stem
        content = Path(listing_file).read_text(encoding="utf-8")
        lines = content.splitlines()
        blank_idx = None
        for i, line in enumerate(lines):
            if line.strip() == "":
                blank_idx = i
                break
        if blank_idx is not None:
            listing_text = "\n".join(lines[blank_idx + 1:]).strip()
        else:
            listing_text = content.strip()
    result = check(listing_text, listing_id)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
