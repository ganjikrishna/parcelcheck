"""Verifies the sealed key hash, runs the frozen checker over the ten untouched listings, scores after the runs (the checker never sees the key), writes verification-results.md."""

import hashlib
import json
import os
import sys
from pathlib import Path

prep = Path(os.environ.get("PARCELCHECK_DIR") or Path(__file__).resolve().parent)
sys.path.insert(0, str(prep))
import checker

LISTING_IDS = ["L02", "L03", "L04", "L05", "L06", "L08", "L09", "L10", "L11", "L12"]
POINTS = ["access", "flood", "perc_septic", "water_well", "liens_tax", "zoning", "utilities", "mineral_timber", "survey"]
POINT_BY_NUMBER = {1: "access", 2: "flood", 3: "perc_septic", 4: "water_well", 5: "liens_tax", 6: "zoning", 7: "utilities", 8: "mineral_timber", 9: "survey"}
STATUS_BY_WORDS = {"problem stated": "problem_stated", "clean": "clean", "missing": "missing"}


def _cost_parts(result):
    cost = result.get("cost") if isinstance(result, dict) else None
    if isinstance(cost, dict):
        usd_raw = cost["usd"] if "usd" in cost else 0.0
        try:
            usd = float(usd_raw)
        except (TypeError, ValueError):
            usd = 0.0
        return usd, cost
    if isinstance(cost, (int, float)):
        return float(cost), cost
    return 0.0, cost


def _harness_errors(result):
    if not isinstance(result, dict):
        return []
    harness = result.get("harness")
    if isinstance(harness, dict) and "errors" in harness:
        errors = harness["errors"]
        if isinstance(errors, list):
            return errors
    return []


def _got_from_checks(checks):
    got = {}
    if isinstance(checks, dict):
        for point in POINTS:
            if point in checks:
                value = checks[point]
                if isinstance(value, dict):
                    status = value.get("status")
                    if status is None:
                        status = value.get("result")
                    if status is None:
                        status = value.get("value")
                    if status is None:
                        status = value.get("state")
                    got[point] = status
                else:
                    got[point] = value
    elif isinstance(checks, list):
        for entry in checks:
            if isinstance(entry, dict):
                point = entry.get("point") or entry.get("name") or entry.get("id")
                status = entry.get("status") or entry.get("result") or entry.get("value")
                if point in POINTS:
                    got[point] = status
            elif isinstance(entry, (list, tuple)) and len(entry) >= 2:
                if entry[0] in POINTS:
                    got[entry[0]] = entry[1]
    return got


def _parse_key():
    text = (prep / "answer-key.md").read_text(encoding="utf-8")
    lines = text.splitlines()
    parsed = {}
    for lid in LISTING_IDS:
        section = []
        in_section = False
        for line in lines:
            if not in_section:
                if line.startswith(f"## {lid}:"):
                    in_section = True
                continue
            if line.startswith("## ") or line.startswith("No problem"):
                break
            section.append(line)
        mapping = {}
        row_count = 0
        for line in section:
            stripped = line.strip()
            if not stripped.startswith("|"):
                continue
            parts = [part.strip() for part in stripped.strip("|").split("|")]
            if len(parts) < 3:
                continue
            try:
                number = int(parts[0])
            except ValueError:
                continue
            if number not in POINT_BY_NUMBER:
                continue
            status_word = parts[2].lower()
            status = STATUS_BY_WORDS.get(status_word)
            if status is None:
                lowered = stripped.lower()
                if "problem stated" in lowered:
                    status = "problem_stated"
                elif "missing" in lowered:
                    status = "missing"
                elif "clean" in lowered:
                    status = "clean"
                else:
                    continue
            mapping[POINT_BY_NUMBER[number]] = status
            row_count += 1
        assert row_count == 9 and len(mapping) == 9, f"expected exactly 9 rows for {lid}, got {row_count}"
        parsed[lid] = mapping
    return parsed


def main():
    digest = hashlib.sha256((prep / "answer-key.md").read_bytes()).hexdigest()
    expected = (prep / "answer-key.sha256").read_text(encoding="utf-8").split()[0]
    assert digest == expected, f"answer-key.sha256 mismatch: expected {expected}, computed {digest}"
    print(f"seal verified: {digest[:16]}")

    if not (prep / "meta-api-key.txt").exists():
        print("STOP: meta-api-key.txt not found next to verify.py. No runs attempted, no files written.")
        sys.exit(2)

    key = _parse_key()

    executed = 0
    points = 0
    correct = 0
    prob_key = 0
    prob_caught = 0
    false_flags = 0
    miss_key = 0
    miss_named = 0
    clean_key = 0
    clean_ok = 0
    usd = 0.0

    detail = {}
    results_lines = [
        "# ParcelCheck verification results",
        "",
        f"Answer key sha256 verified before the run: {digest}",
        "",
        "Prompt: v1 (frozen). Model: muse-ember-1.0. One structured pass per listing.",
        "",
    ]

    for lid in LISTING_IDS:
        key_map = key[lid]
        key_prob = sum(1 for value in key_map.values() if value == "problem_stated")
        key_miss = sum(1 for value in key_map.values() if value == "missing")
        key_clean = sum(1 for value in key_map.values() if value == "clean")

        try:
            raw = (prep / "listings" / f"{lid}.txt").read_text(encoding="utf-8")
            text = ""
            raw_lines = raw.splitlines()
            for idx, raw_line in enumerate(raw_lines):
                if raw_line.strip() == "":
                    text = "\n".join(raw_lines[idx + 1:]).strip()
                    break
            else:
                text = raw.strip()
            result = checker.check(text, lid)
        except Exception as exc:
            error = str(exc)
            results_lines.append(f"## {lid}: RUN FAILED ({error[:120]}). Tokens logged in runs.jsonl. Scored as no points matched.")
            results_lines.append("")
            detail[lid] = {"error": error[:200]}
            points += 9
            prob_key += key_prob
            miss_key += key_miss
            clean_key += key_clean
            continue

        errors = _harness_errors(result)
        has_checks = isinstance(result, dict) and "checks" in result
        if errors or not has_checks:
            executed += 1
            usd_part, cost_detail = _cost_parts(result)
            usd += usd_part
            joined = "; ".join(str(item) for item in errors)
            results_lines.append(f"## {lid}: INVALID OUTPUT ({joined[:200]}). Scored as no points matched.")
            results_lines.append("")
            detail[lid] = {"invalid": errors, "cost": cost_detail}
            points += 9
            prob_key += key_prob
            miss_key += key_miss
            clean_key += key_clean
            continue

        executed += 1
        usd_part, cost_detail = _cost_parts(result)
        usd += usd_part
        got = _got_from_checks(result.get("checks"))
        detail[lid] = {"got": got, "cost": cost_detail, "harness": result.get("harness")}
        matches = 0
        misses = []
        for point in POINTS:
            points += 1
            key_status = key_map[point]
            got_status = got.get(point)
            if key_status == "problem_stated":
                prob_key += 1
                if got_status == "problem_stated":
                    prob_caught += 1
            elif key_status == "missing":
                miss_key += 1
                if got_status == "missing":
                    miss_named += 1
            elif key_status == "clean":
                clean_key += 1
                if got_status == "clean":
                    clean_ok += 1
            if got_status == "problem_stated" and key_status != "problem_stated":
                false_flags += 1
            if got_status == key_status:
                correct += 1
                matches += 1
            else:
                misses.append(f"{point}: key {key_status}, got {got_status}")
        results_lines.append(f"## {lid}: {matches}/9 points match, cost ${usd_part:.4f}")
        for miss in misses:
            results_lines.append(f"- MISS: {miss}")
        if errors:
            results_lines.append(f"- HARNESS ERRORS: {'; '.join(str(item) for item in errors)}")
        results_lines.append("")

    totals_line = f"**Totals across {points} points: {correct} exact matches. Problems in key: {prob_key}, caught: {prob_caught}. False problem flags: {false_flags}. Missing in key: {miss_key}, named missing: {miss_named}. Clean in key: {clean_key}, called clean: {clean_ok}. Total cost of the ten runs: ${usd:.4f}.**"
    results_lines.insert(4, totals_line)

    if executed == 0:
        print("STOP: no listing produced a result (every run failed). Published results left untouched.")
        sys.exit(1)

    content = "\n".join(results_lines)
    if not content.endswith("\n"):
        content += "\n"
    (prep / "verification-results.md").write_text(content, encoding="utf-8")
    (prep / "verification-detail.json").write_text(json.dumps(detail, indent=2) + "\n", encoding="utf-8")
    print("\n".join(results_lines[:8]))
    print("written verification-results.md")


if __name__ == "__main__":
    main()
