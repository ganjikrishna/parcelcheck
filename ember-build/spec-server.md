Write a Python 3 file, server.py, a local-only development server for ParcelCheck. Standard library only (http.server ThreadingHTTPServer).

Setup: prep folder is PARCELCHECK_DIR env var else the script's folder. Import checker from the same folder. Bind 127.0.0.1 port 8931. Silence request logging.

GET allowlist (explicit, nothing else is ever served; the prep folder also holds the API key and the sealed answer key, which must never be served): "/" and "/index.html" serve index.html; "/cached-L01.json" serves cached-L01.json; "/cached-L07.json" serves cached-L07.json. Content type text/html for the page, application/json for the JSON files, charset utf-8, correct Content-Length. Any other path: 404.

POST /check only (other POST paths 404): parse the JSON body (400 on bad JSON). text = body "text" stripped; if empty or longer than 20000 chars, reply 400 {"error": "Listing text missing or over 20000 characters."}. Daily cap: state file server-cap.json in prep {"day": "YYYY-MM-DD", "count": n}; a new day resets the count; if count has reached 200, reply 429 {"error": "Daily live run cap reached. Cached examples still work."}; otherwise increment and save before running. Run checker.check(text, body "id" or "web"); on exception reply 502 {"error": "Checker run failed: " + first 200 chars}; on success reply 200 with the result JSON.

Module docstring describing the server, the allowlist reason, the bind, and the caps (20000 chars, 200 live runs per day counted in server-cap.json).
