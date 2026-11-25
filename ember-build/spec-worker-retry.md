Modify the Cloudflare Worker JavaScript file below. Change ONLY the function runCheck, exactly as specified, and return the complete file with every other function and line unchanged.

Current runCheck behavior: it builds the user prompt, makes one POST fetch to the Ember API with max_output_tokens 12000, throws on a non-OK response, extracts the output text, calls parseJson (which throws on an unparseable reply), then applyRules, then validate; if validate returns a non-empty errors array it throws. It then computes cost from the response usage and attaches result.cost and result.harness.

Required changes inside runCheck:

1. max_output_tokens becomes 24000 on every attempt.

2. Bounded retry, maximum 2 attempts. Structure the body as an attempt loop:
   - Each attempt performs the fetch exactly as today. A non-OK response still throws immediately (no retry on HTTP errors).
   - An attempt FAILS when: the extracted output text is empty or whitespace only, OR parseJson throws, OR validate returns a non-empty errors array.
   - On a failed first attempt, run the identical request a second time. On a failed second attempt, throw: the parse error if parsing failed, otherwise an Error with the message "Validation failed: " plus the first validation error, as today. An empty reply on the final attempt throws an Error with the message "Empty reply from model".
   - applyRules runs on each attempt whose parse succeeded, before validate, as today.

3. Accounting: result.cost uses the SUM of input_tokens, output_tokens, and the computed usd across all attempts made (compute each attempt's usd from its own usage with the existing formula, then sum). result.harness gains two fields: "attempts" (1 or 2) and "retried" (true only when attempts is 2). The harness "seconds" stays the total elapsed time from the start of runCheck. All other cost and harness fields stay as they are.

4. Do not change any other function, the SYSTEM_PROMPT placeholder line, the records functions, the request handler, or the counter logic. No new imports.

Output ONLY the complete new worker file contents: no markdown fences, no commentary.
