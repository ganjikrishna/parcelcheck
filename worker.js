// ParcelCheck Cloudflare Worker.
// Serves the static page and cached examples, and runs live checks
// against Muse Ember through the Meta Model API. The API key is a
// Worker secret (META_API_KEY), never in code. Live runs are capped
// per day with a Durable Object counter (default 200 per day).
//
// The system prompt below is prompt v1, frozen 2026-11-24. It must
// match prompt-v1.json in the repo character for character in the
// system field; the deploy script injects it at build time from
// prompt-v1.json, so this placeholder is replaced before deploy.
const SYSTEM_PROMPT = "__PROMPT_V1_SYSTEM__";
const MODEL = "muse-ember-1.0";
const RATE_IN = 0.10 / 1e6, RATE_OUT = 0.50 / 1e6;
const POINTS = ["access", "flood", "perc_septic", "water_well", "liens_tax",
  "zoning", "utilities", "mineral_timber", "survey"];
const STATUSES = new Set(["problem_stated", "clean", "missing"]);
const MAX_TEXT = 20000;
const DAILY_CAP = 200;

function parseJson(text) {
  text = text.trim();
  if (text.startsWith("```")) text = text.replace(/^```[a-z]*\n/, "").replace(/```$/, "").trim();
  try { return JSON.parse(text); } catch (e) {
    // Harness fix, 2026-11-25: two failure modes seen on L10, prose
    // added after the JSON object, and the model echoing the schema
    // before its result. Scan every object start, take the first
    // balanced object that carries a top level "checks" key, and
    // validate as usual. The prompt is unchanged.
    for (let i = 0; i < text.length; i++) {
      if (text[i] !== "{") continue;
      let depth = 0, inStr = false, esc = false, end = -1;
      for (let j = i; j < text.length; j++) {
        const ch = text[j];
        if (inStr) { if (esc) esc = false; else if (ch === "\\") esc = true; else if (ch === '"') inStr = false; continue; }
        if (ch === '"') inStr = true;
        else if (ch === "{") depth++;
        else if (ch === "}") { depth--; if (depth === 0) { end = j; break; } }
      }
      if (end === -1) continue;
      try {
        const obj = JSON.parse(text.slice(i, end + 1));
        if (obj && typeof obj === "object" && "checks" in obj) return obj;
      } catch (_) { /* keep scanning */ }
    }
    throw e;
  }
}

function validate(result, listingText) {
  const errors = [], warnings = [];
  const checks = result.checks;
  if (!Array.isArray(checks) || checks.length !== 9) {
    errors.push("checks must be a list of exactly 9");
    return { errors, warnings };
  }
  const seen = new Set();
  for (const c of checks) {
    const p = c.point;
    if (!POINTS.includes(p)) { errors.push("unknown point: " + p); continue; }
    seen.add(p);
    if (!STATUSES.has(c.status)) errors.push(p + ": bad status " + c.status);
    const ev = c.evidence || [];
    if ((c.status === "problem_stated" || c.status === "clean") && ev.length === 0)
      errors.push(p + ": " + c.status + " with no evidence quote");
    if (c.status === "missing" && ev.length) warnings.push(p + ": missing but carries evidence");
    for (const q of ev) if (!listingText.includes(q)) errors.push(p + ": FABRICATED QUOTE: " + String(q).slice(0, 60));
  }
  if (seen.size !== 9) errors.push("points covered: " + [...seen].sort().join(","));
  const prob = new Set(checks.filter(c => c.status === "problem_stated").map(c => c.point));
  const miss = new Set(checks.filter(c => c.status === "missing").map(c => c.point));
  const rf = new Set((result.red_flags || []).map(r => r.point));
  if (rf.size !== prob.size || [...rf].some(x => !prob.has(x))) warnings.push("red_flags do not match problem_stated points");
  const mi = new Set(result.missing_items || []);
  if (mi.size !== miss.size || [...mi].some(x => !miss.has(x))) warnings.push("missing_items do not match missing points");
  const qp = new Set((result.seller_questions || []).map(q => q.point));
  const noq = [...miss].filter(p => !qp.has(p));
  if (noq.length) warnings.push("missing points without a seller question: " + noq.sort().join(","));
  return { errors, warnings };
}

function applyRules(result) {
  // Checklist rule, applied openly and recorded: liens_tax is clean only
  // when the evidence covers both halves (taxes current or paid, and no
  // liens), per checklist.md section 5. One half alone downgrades to
  // missing, with the standard seller question added if absent.
  const applied = [];
  for (const c of result.checks || []) {
    if (c.point === "liens_tax" && c.status === "clean") {
      const ev = (c.evidence || []).join(" ").toLowerCase();
      const taxHalf = ev.includes("tax") && ["paid", "current", "through", "up to date", "up-to-date", "not delinquent", "no delinquent"].some(k => ev.includes(k));
      const lienHalf = ev.includes("lien") && ["no lien", "free of lien", "free and clear", "clear of lien", "without lien", "no recorded lien", "lien free", "lien-free", "not subject to lien"].some(k => ev.includes(k));
      if (!(taxHalf && lienHalf)) {
        c.status = "missing";
        c.note = ((c.note || "") + " Harness rule: only one half of this point (taxes or liens) is stated, so it counts as not fully addressed.").trim();
        if (!(result.missing_items || []).includes("liens_tax"))
          (result.missing_items = result.missing_items || []).push("liens_tax");
        if (!(result.seller_questions || []).some(q => q.point === "liens_tax"))
          (result.seller_questions = result.seller_questions || []).push({
            point: "liens_tax",
            question: "Are all property taxes paid through the current year, and are there any liens, judgments, or back taxes on this parcel?" });
        applied.push("liens_tax_clean_requires_both_halves");
      }
    }
  }
  return applied;
}

async function runCheck(env, listingText, listingId) {
  const user = "Check this listing against the nine points. Return only the JSON object.\n\n" +
    `<listing id="${listingId}">\n${listingText}\n</listing>`;
  const t0 = Date.now();
  const resp = await fetch("https://api.meta.ai/v1/responses", {
    method: "POST",
    headers: { "Authorization": "Bearer " + env.META_API_KEY, "content-type": "application/json" },
    body: JSON.stringify({ model: MODEL, input: [
      { role: "system", content: SYSTEM_PROMPT },
      { role: "user", content: user } ], max_output_tokens: 12000, store: false })
  });
  if (!resp.ok) throw new Error("Ember API " + resp.status);
  const body = await resp.json();
  let text = "";
  for (const item of body.output || []) {
    if (item.type === "message") for (const c of item.content || [])
      if (c.type === "output_text") text += c.text || "";
  }
  const u = body.usage || {};
  const i = u.input_tokens || 0, o = u.output_tokens || 0;
  const result = parseJson(text);
  const applied = applyRules(result);
  const { errors, warnings } = validate(result, listingText);
  if (errors.length) throw new Error("Validation failed: " + errors[0]);
  result.cost = { usd: Math.round((i * RATE_IN + o * RATE_OUT) * 1e6) / 1e6,
    input_tokens: i, output_tokens: o, model: MODEL };
  result.harness = { errors, warnings, seconds: Math.round((Date.now() - t0) / 100) / 10, prompt_version: "v1", rules_applied: applied };
  return result;
}

// ---- Public records mode ---------------------------------------------
// One box, no modes to pick. If the input is just an address, or a
// pasted listing contains an address, the Worker checks live public
// records (US Census geocoder, FEMA flood maps, USDA soil survey,
// US Fish and Wildlife wetlands inventory, all free, no keys) and
// feeds the records text through the same frozen Ember pass. Every
// records sentence is quotable evidence, so the quote-or-drop rule
// still holds. A source that fails or has no data simply adds no
// sentence, and that point stays a seller question.

async function fetchJson(url, opts = {}, timeoutMs = 7000) {
  const r = await fetch(url, { ...opts, signal: AbortSignal.timeout(timeoutMs) });
  if (!r.ok) throw new Error("fetch " + r.status);
  return r.json();
}

function looksLikeAddress(text) {
  const t = text.trim();
  if (t.length > 200 || t.split(/\s+/).length > 22) return false;
  if (!/\d/.test(t)) return false;
  return /,/.test(t) || /\b\d{5}(-\d{4})?\b/.test(t);
}

function extractAddress(text) {
  const m = text.match(/\d{1,6}\s+[A-Za-z0-9][A-Za-z0-9 .'-]*?\b(?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Ln|Lane|Blvd|Hwy|Highway|Ct|Court|Cir|Circle|Way|Trl|Trail|Pkwy|Parkway)\b[^,\n]{0,40},\s*[A-Za-z][A-Za-z .'-]+,\s*[A-Z]{2}\s+\d{5}/);
  return m ? m[0].trim() : null;
}

async function geocode(address) {
  const u = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?" +
    new URLSearchParams({ address, benchmark: "Public_AR_Current", format: "json" });
  const d = await fetchJson(u);
  const m = (d.result || {}).addressMatches || [];
  if (!m.length) return null;
  return { matched: m[0].matchedAddress, lat: m[0].coordinates.y, lng: m[0].coordinates.x };
}

async function femaLine(lng, lat) {
  const q = new URLSearchParams({ geometry: lng + "," + lat, geometryType: "esriGeometryPoint",
    inSR: "4326", spatialRel: "esriSpatialRelIntersects",
    outFields: "FLD_ZONE,ZONE_SUBTY,SFHA_TF", returnGeometry: "false", f: "json" });
  const heads = { headers: { "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
    "Accept": "application/json", "Referer": "https://hazards.fema.gov/" } };
  let d;
  try {
    d = await fetchJson("https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query?" + q, heads);
  } catch (e) {
    // FEMA's gateway resets connections intermittently (1 of 10 scored
    // verification runs lost its flood answer this way). One pause and
    // retry, then the FIRMette mirror of the same layer.
    await new Promise(r => setTimeout(r, 900));
    try {
      d = await fetchJson("https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query?" + q, heads);
    } catch (e2) {
      d = await fetchJson("https://hazards.fema.gov/arcgis/rest/services/FIRMette/NFHLREST_FIRMette/MapServer/20/query?" + q, heads);
    }
  }
  const feats = d.features || [];
  if (!feats.length) return "FEMA National Flood Hazard Layer: no flood hazard data is published for this point.";
  const a = feats[0].attributes;
  let s = "FEMA National Flood Hazard Layer: the flood zone at this point is Zone " + a.FLD_ZONE;
  if (a.ZONE_SUBTY) s += ", " + String(a.ZONE_SUBTY).toLowerCase();
  s += ".";
  if (a.SFHA_TF === "T") s += " This point is in a Special Flood Hazard Area, with a 1 percent or greater annual chance of flooding. Flood insurance is required for buildings with federally backed mortgages in this area.";
  else s += " This point is not in a Special Flood Hazard Area.";
  return s;
}

async function wetlandsLine(lng, lat) {
  const q = new URLSearchParams({ geometry: lng + "," + lat, geometryType: "esriGeometryPoint",
    inSR: "4326", spatialRel: "esriSpatialRelIntersects",
    outFields: "WETLAND_TYPE", returnGeometry: "false", f: "json" });
  const d = await fetchJson("https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest/services/Wetlands/MapServer/0/query?" + q);
  const feats = d.features || [];
  if (!feats.length) return "US Fish and Wildlife Service National Wetlands Inventory: no wetlands are mapped at this point.";
  return "US Fish and Wildlife Service National Wetlands Inventory: a mapped wetland is present at this point (type: " +
    (feats[0].attributes.WETLAND_TYPE || "wetland") + "). Building or filling in a mapped wetland can require federal permits.";
}

async function sda(sql) {
  const r = await fetch("https://SDMDataAccess.nrcs.usda.gov/Tabular/post.rest", {
    method: "POST", headers: { "content-type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({ QUERY: sql, FORMAT: "JSON+COLUMNNAME" }),
    signal: AbortSignal.timeout(9000) });
  if (!r.ok) throw new Error("sda " + r.status);
  const d = await r.json();
  return (d.Table || []).slice(1);
}

async function soilLines(lng, lat) {
  const sub = "(SELECT mukey FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('POINT(" + lng + " " + lat + ")'))";
  const mu = await sda("SELECT muname FROM mapunit WHERE mukey IN " + sub);
  if (!mu.length) return [];
  const lines = ["USDA soil survey: the soil at this point is " + mu[0][0] + "."];
  const rows = await sda("SELECT c.compname, c.comppct_r, c.drainagecl, ci.interplrc FROM component c " +
    "LEFT JOIN cointerp ci ON ci.cokey = c.cokey AND ci.ruledepth = 0 AND ci.rulename = 'ENG - Septic Tank Absorption Fields' " +
    "WHERE c.mukey IN " + sub + " ORDER BY c.comppct_r DESC");
  if (rows.length) {
    const [name, pct, drain, septic] = rows[0];
    if (drain) lines.push("USDA soil survey: the main soil component (" + name + ", " + pct + " percent of the area) has a drainage class of " + String(drain).toLowerCase() + ".");
    // "Not rated" (most urban soils) carries no septic information; the
    // records verification on 2026-11-25 showed the sentence "rated as:
    // Not rated" read as a problem flag 5 times out of 5. Omit it, and
    // the point stays an honest seller question.
    if (septic && septic !== "Not rated") lines.push("USDA soil survey: this soil is rated for septic tank absorption fields as: " + septic + ".");
  }
  return lines;
}

async function buildRecords(address) {
  const g = await geocode(address);
  if (!g) return null;
  const lines = [], sources = ["US Census Bureau geocoder"];
  const jobs = [
    ["FEMA National Flood Hazard Layer", femaLine(g.lng, g.lat)],
    ["US Fish and Wildlife Service wetlands inventory", wetlandsLine(g.lng, g.lat)],
    ["USDA soil survey", soilLines(g.lng, g.lat)],
  ];
  const settled = await Promise.allSettled(jobs.map(j => j[1]));
  settled.forEach((r, i) => {
    if (r.status !== "fulfilled") return;
    const v = r.value;
    if (typeof v === "string") { lines.push(v); sources.push(jobs[i][0]); }
    else if (Array.isArray(v) && v.length) { lines.push(...v); sources.push(jobs[i][0]); }
  });
  const floodLine = lines.find(l => l.startsWith("FEMA National Flood Hazard Layer")) || null;
  const septicLine = lines.find(l => l.includes("rated for septic tank absorption fields as:")) || null;
  const facts = {
    floodHazard: !!(floodLine && floodLine.includes("This point is in a Special Flood Hazard Area")),
    floodLine,
    septicRating: septicLine ? septicLine.split("rated for septic tank absorption fields as:")[1].trim().replace(/\.$/, "") : null,
    septicLine,
  };
  return { matched: g.matched, lat: g.lat, lng: g.lng, lines, sources, facts };
}

function applyRecordsOverride(result, facts) {
  // When live records state a hazard the model called clean, the record
  // wins and is flagged. Only ever upgrades clean to problem_stated,
  // only on the records' own quoted words, and is recorded in the run.
  if (!facts) return;
  const applied = result.harness.rules_applied || (result.harness.rules_applied = []);
  const checks = result.checks || [];
  const dropQ = pt => { result.seller_questions = (result.seller_questions || []).filter(q => q.point !== pt); };
  const addFlag = (pt, summary, quote) => {
    if (!(result.red_flags || []).some(f => f.point === pt))
      (result.red_flags = result.red_flags || []).push({ point: pt, summary, quote });
    result.missing_items = (result.missing_items || []).filter(x => x !== pt);
    dropQ(pt);
  };
  const flood = checks.find(c => c.point === "flood");
  if (flood && flood.status === "clean" && facts.floodHazard && facts.floodLine) {
    flood.status = "problem_stated";
    flood.evidence = [facts.floodLine];
    flood.note = "The listing does not flag a flood problem, but FEMA records put this point in a Special Flood Hazard Area. The record is the flag.";
    flood.source = "records";
    addFlag("flood", "FEMA records: Special Flood Hazard Area", facts.floodLine);
    applied.push("records_override_flood");
  }
  const perc = checks.find(c => c.point === "perc_septic");
  if (perc && perc.status === "clean" && facts.septicLine &&
      (facts.septicRating === "Somewhat limited" || facts.septicRating === "Very limited")) {
    perc.status = "problem_stated";
    perc.evidence = [...(perc.evidence || []), facts.septicLine];
    perc.note = "The listing's perc position reads clean, but USDA soil data rates this soil " + facts.septicRating + " for septic absorption. Both are shown; the records rating is the flag.";
    perc.source = "records";
    addFlag("perc_septic", "USDA soil rating: " + facts.septicRating + " for septic absorption", facts.septicLine);
    applied.push("records_override_perc_septic");
  }
}

function tagRecordsSources(result, listingText) {
  // In a combined run, mark checks whose evidence comes only from the
  // records block, so the page can credit the records, not the listing.
  for (const c of result.checks || []) {
    const ev = c.evidence || [];
    if (ev.length && ev.every(q => !listingText.includes(q))) c.source = "records";
  }
}

async function runSmart(env, text, id) {
  // Just an address: records only.
  if (looksLikeAddress(text)) {
    const rec = await buildRecords(text).catch(() => null);
    if (rec && rec.lines.length) {
      const recordsText = "Public records check for the property at: " + rec.matched + "\n" +
        "Coordinates of the point checked: latitude " + rec.lat + ", longitude " + rec.lng + ".\n" +
        rec.lines.join("\n") + "\n" +
        "This text is compiled from live public records, not from a seller listing. It covers only the points the records speak to. Anything the records do not cover is not addressed here and still needs the seller or the county.";
      const result = await runCheck(env, recordsText, "address");
      applyRecordsOverride(result, rec.facts);
      result.mode = "records";
      result.matched_address = rec.matched;
      result.sources = rec.sources;
      return result;
    }
  }
  // A listing with an address inside: listing plus live records.
  const addr = extractAddress(text);
  if (addr) {
    const rec = await buildRecords(addr).catch(() => null);
    if (rec && rec.lines.length) {
      const combined = text + "\n\nPUBLIC RECORDS CHECKED TODAY for the address in this listing (" + rec.matched + "):\n" +
        rec.lines.join("\n");
      const result = await runCheck(env, combined, id);
      applyRecordsOverride(result, rec.facts);
      tagRecordsSources(result, text);
      result.mode = "listing+records";
      result.matched_address = rec.matched;
      result.sources = rec.sources;
      return result;
    }
  }
  // Plain listing text.
  const result = await runCheck(env, text, id);
  result.mode = "listing";
  if (looksLikeAddress(text)) {
    result.records_note = "That looked like an address, but it was not found in the US public records ParcelCheck uses, so records were not checked. It was read as listing text instead. ParcelCheck covers US addresses.";
  } else if (addr) {
    result.records_note = "An address was found in the text, but public records were not checked for it. This report covers the listing text only.";
  }
  return result;
}

export class RunCounter {
  constructor(state, env) { this.state = state; }
  async fetch(request) {
    const today = new Date().toISOString().slice(0, 10);
    let stored = (await this.state.storage.get("state")) || { day: today, count: 0 };
    if (stored.day !== today) stored = { day: today, count: 0 };
    if (stored.count >= DAILY_CAP)
      return new Response(JSON.stringify({ ok: false }), { headers: { "content-type": "application/json" } });
    stored.count += 1;
    await this.state.storage.put("state", stored);
    return new Response(JSON.stringify({ ok: true, count: stored.count }), { headers: { "content-type": "application/json" } });
  }
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "POST" && url.pathname === "/check") {
      let body;
      try { body = await request.json(); } catch { return json(400, { error: "Bad request." }); }
      const text = (body.text || "").trim();
      if (!text) return json(400, { error: "Nothing to check yet. Paste a listing, or type a street address with city and state." });
      if (text.length > MAX_TEXT) return json(400, { error: "That text is over 20000 characters. Paste the listing description and its fields, not the whole page." });
      if (!looksLikeAddress(text)) {
        if (text.trim().split(/\s+/).length < 8) return json(400, { error: "That is too short to check. Paste a full listing, or type a street address with city, state, and ZIP." });
        if (!/\d/.test(text) && !/(acre|land|sale|sold|price|road|lot|property|zoning|well|septic|tax|parcel|county|bed|bath)/i.test(text))
          return json(400, { error: "That does not look like a listing or an address. Paste a full listing, or type a street address with city, state, and ZIP." });
      }
      const id = env.RUN_COUNTER.idFromName("global");
      const stub = env.RUN_COUNTER.get(id);
      const cap = await (await stub.fetch("https://counter/")).json();
      if (!cap.ok) return json(429, { error: "Daily live run cap reached. Cached examples still work." });
      try {
        return json(200, await runSmart(env, text, body.id || "web"));
      } catch (e) {
        return json(502, { error: "Checker run failed: " + String(e).slice(0, 200) });
      }
    }
    return env.ASSETS.fetch(request);
  }
};

function json(code, obj) {
  return new Response(JSON.stringify(obj), { status: code,
    headers: { "content-type": "application/json; charset=utf-8" } });
}
