Modify the existing Python file checker.py (a land-listing checker that calls the Muse Ember API). You are given the current behavior in words; change only what this spec says and keep everything else byte-for-byte in behavior.

Current behavior of the function check(listing_text, listing_id):
- It loads prompt-v1.json (version and system text), builds the user prompt, and calls call_ember(system, user, max_out=12000) once, which returns (raw_text, input_tokens, output_tokens, elapsed).
- It calls parse_json(raw_text). If parse_json raises, it writes a trace line to runs.jsonl with an "error" field and the raw head, appends the full failure entry plus the raw text to failed-runs.log, and re-raises.
- On parse success it calls apply_rules(result), then validate(result, listing_text) which returns (errors, warnings), attaches result["cost"] and result["harness"], writes a success trace line to runs.jsonl, and returns result.

Required changes, all inside check() unless stated:

1. Raise the output cap: call_ember is called with max_out=24000 instead of 12000, on every attempt.

2. Bounded retry, maximum 2 attempts total. An attempt FAILS when any of these is true:
   - the reply text is empty or whitespace only, or
   - parse_json raises, or
   - validate(result, listing_text) returns a non-empty errors list.
   Attempt flow:
   - Attempt 1: call, then parse, then apply_rules, then validate (apply_rules and validate only run when parse succeeded).
   - If attempt 1 fails: append a failure entry for attempt 1 to failed-runs.log in the same shape as the current code does (the trace-shaped dict plus "raw" and "raw_reply" fields, followed by the raw text on its own line), then make attempt 2 with the identical system and user prompts.
   - If attempt 2 succeeds: proceed with its result.
   - If attempt 2 also fails: write the runs.jsonl trace line in the current failure shape, with these additions: "attempts": 2, and the token and usd fields summed across BOTH attempts; append attempt 2's failure entry to failed-runs.log the same way; then raise the same kind of exception the current code raises (the parse exception if parsing failed, otherwise a ValueError carrying the validation errors).

3. Accounting on success: result["cost"] and the success trace line use the SUM of input_tokens, output_tokens, and usd across all attempts made. The success trace line and result["harness"] each gain two fields: "attempts" (1 or 2) and "retried" (true only when attempts is 2). The harness "seconds" field is the sum of the attempts' elapsed times. All other existing fields stay exactly as they are.

4. Do not change: parse_json, validate, apply_rules, call_ember, the prompt files, the CLI in main(), the trace field names that already exist, or the failed-runs.log entry shape. No new dependencies. Python standard library only.

Output ONLY the complete new checker.py file contents: no markdown fences, no commentary.
