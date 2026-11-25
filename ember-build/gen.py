#!/usr/bin/env python3
"""Build runner: Muse Ember writes ParcelCheck code from a written spec.
Usage: python3 gen.py <task> <spec-file> <out-file> [max-output-tokens]
Every call is traced to build-runs.jsonl next to this script."""
import json, pathlib, sys, time, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
PREP = pathlib.Path.home() / "parcelcheck-prep"
API = "https://api.meta.ai/v1/responses"
MODEL = "muse-ember-1.0"
RATE_IN, RATE_OUT = 0.10 / 1e6, 0.50 / 1e6
SYSTEM = ("You are Muse Ember, writing production code for the ParcelCheck project. "
          "Follow the spec exactly. Output ONLY the complete file contents: no markdown "
          "fences, no commentary, no explanation before or after the code.")

def main():
    task, spec_file, out_file = sys.argv[1], sys.argv[2], sys.argv[3]
    max_out = int(sys.argv[4]) if len(sys.argv) > 4 else 16000
    spec = pathlib.Path(spec_file).read_text()
    key = (PREP / "meta-api-key.txt").read_text().strip()
    payload = {"model": MODEL,
               "input": [{"role": "system", "content": SYSTEM},
                         {"role": "user", "content": spec}],
               "max_output_tokens": max_out, "store": False}
    req = urllib.request.Request(API, data=json.dumps(payload).encode(),
        headers={"Authorization": "Bearer " + key, "content-type": "application/json"})
    t = time.time()
    with urllib.request.urlopen(req, timeout=600) as resp:
        body = json.loads(resp.read())
    dt = round(time.time() - t, 1)
    text = ""
    for item in body.get("output", []):
        if item.get("type") == "message":
            for c in item.get("content", []):
                if c.get("type") == "output_text":
                    text += c.get("text", "")
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        text = "\n".join(lines[1:-1] if lines[-1].startswith("```") else lines[1:]).strip()
    u = body.get("usage", {})
    i, o = u.get("input_tokens", 0), u.get("output_tokens", 0)
    usd = round(i * RATE_IN + o * RATE_OUT, 6)
    pathlib.Path(out_file).write_text(text + "\n")
    trace = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "task": task,
             "out_file": str(out_file), "model": MODEL, "spec": str(spec_file),
             "input_tokens": i, "output_tokens": o, "usd": usd, "seconds": dt,
             "out_chars": len(text)}
    with open(HERE / "build-runs.jsonl", "a") as f:
        f.write(json.dumps(trace) + "\n")
    print(f"{task}: {len(text)} chars, in {i} / out {o} tokens, ${usd}, {dt}s -> {out_file}")

if __name__ == "__main__":
    main()
