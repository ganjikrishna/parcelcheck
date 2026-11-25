#!/usr/bin/env python3
"""ParcelCheck verification run. Verifies the sealed answer key hash,
runs the frozen checker (prompt v1) over the ten untouched listings,
scores against the key, and writes verification-results.md.
The checker never sees the key; scoring happens here, after the runs.
"""
import hashlib, json, os, pathlib, re, sys

PREP = pathlib.Path(os.environ.get("PARCELCHECK_DIR", pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(PREP))
import checker

IDS = ["L02", "L03", "L04", "L05", "L06", "L08", "L09", "L10", "L11", "L12"]
NUM2POINT = {1: "access", 2: "flood", 3: "perc_septic", 4: "water_well",
             5: "liens_tax", 6: "zoning", 7: "utilities", 8: "mineral_timber", 9: "survey"}
STATUS_MAP = {"problem stated": "problem_stated", "clean": "clean", "missing": "missing"}

# 1. Seal check
digest = hashlib.sha256((PREP / "answer-key.md").read_bytes()).hexdigest()
expected = (PREP / "answer-key.sha256").read_text().split()[0]
assert digest == expected, f"KEY HASH MISMATCH: {digest} vs {expected}"
print("seal verified:", digest[:16])

# 2. Parse key rows
key_text = (PREP / "answer-key.md").read_text()
key = {}
for lid in IDS:
    sec = re.search(rf"## {lid}:.*?\n(.*?)(?=\n## |\nNo problem|\Z)", key_text, re.S).group(1)
    rows = {}
    for m in re.finditer(r"\|\s*(\d)\s*\|[^|]*\|\s*([a-z ]+?)\s*\|", sec):
        rows[NUM2POINT[int(m.group(1))]] = STATUS_MAP[m.group(2).strip()]
    assert len(rows) == 9, (lid, rows)
    key[lid] = rows

# 3. Run the checker
tot = {"points": 0, "correct": 0, "prob_key": 0, "prob_caught": 0, "false_flags": 0,
       "miss_key": 0, "miss_named": 0, "clean_key": 0, "clean_ok": 0, "usd": 0.0}
lines = ["# ParcelCheck verification results", "",
         f"Answer key sha256 verified before the run: {digest}", "",
         "Prompt: v1 (frozen). Model: muse-ember-1.0. One structured pass per listing.", ""]
detail = {}
for lid in IDS:
    raw = (PREP / "listings" / (lid + ".txt")).read_text()
    text = raw.split("\n\n", 1)[1].strip()
    try:
        r = checker.check(text, lid)
    except Exception as e:
        lines.append(f"## {lid}: RUN FAILED ({str(e)[:120]}). Tokens logged in runs.jsonl. Scored as no points matched.")
        lines.append("")
        detail[lid] = {"error": str(e)[:200]}
        tot["points"] += 9
        for p, want in key[lid].items():
            if want == "problem_stated": tot["prob_key"] += 1
            if want == "missing": tot["miss_key"] += 1
            if want == "clean": tot["clean_key"] += 1
        continue
    if r["harness"]["errors"] or "checks" not in r:
        errs = r["harness"]["errors"] or ["result has no checks key"]
        lines.append(f"## {lid}: INVALID OUTPUT ({'; '.join(errs)[:200]}). Scored as no points matched.")
        lines.append("")
        detail[lid] = {"invalid": errs, "cost": r["cost"]}
        tot["usd"] += r["cost"]["usd"]
        tot["points"] += 9
        for p, want in key[lid].items():
            if want == "problem_stated": tot["prob_key"] += 1
            if want == "missing": tot["miss_key"] += 1
            if want == "clean": tot["clean_key"] += 1
        continue
    got = {c["point"]: c["status"] for c in r["checks"]}
    detail[lid] = {"got": got, "cost": r["cost"], "harness": r["harness"]}
    tot["usd"] += r["cost"]["usd"]
    wrong = []
    for p, want in key[lid].items():
        tot["points"] += 1
        if want == "problem_stated":
            tot["prob_key"] += 1
            if got.get(p) == "problem_stated":
                tot["prob_caught"] += 1
        if want == "missing":
            tot["miss_key"] += 1
            if got.get(p) == "missing":
                tot["miss_named"] += 1
        if want == "clean":
            tot["clean_key"] += 1
            if got.get(p) == "clean":
                tot["clean_ok"] += 1
        if got.get(p) == "problem_stated" and want != "problem_stated":
            tot["false_flags"] += 1
        if got.get(p) == want:
            tot["correct"] += 1
        else:
            wrong.append(f"{p}: key {want}, got {got.get(p)}")
    lines.append(f"## {lid}: {sum(1 for p in key[lid] if got.get(p) == key[lid][p])}/9 points match, cost ${r['cost']['usd']:.4f}")
    for w in wrong:
        lines.append(f"- MISS: {w}")
    if r["harness"]["errors"]:
        lines.append(f"- HARNESS ERRORS: {r['harness']['errors']}")
    lines.append("")

lines.insert(4, f"**Totals across {tot['points']} points: {tot['correct']} exact matches. "
    f"Problems in key: {tot['prob_key']}, caught: {tot['prob_caught']}. "
    f"False problem flags: {tot['false_flags']}. "
    f"Missing in key: {tot['miss_key']}, named missing: {tot['miss_named']}. "
    f"Clean in key: {tot['clean_key']}, called clean: {tot['clean_ok']}. "
    f"Total cost of the ten runs: ${tot['usd']:.4f}.**")
lines.append("")
(PREP / "verification-results.md").write_text("\n".join(lines))
(PREP / "verification-detail.json").write_text(json.dumps(detail, indent=2))
print("\n".join(lines[:8]))
print("written verification-results.md")
