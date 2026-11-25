const MODEL = "muse-ember-1.0";
const API = "https://api.meta.ai/v1/responses";
const API_URL = API;
const INPUT_USD_PER_MILLION = 0.10;
const OUTPUT_USD_PER_MILLION = 0.50;
const MAX_TEXT = 20000;
const DAILY_CAP = 200;
const SYSTEM_PROMPT = "__PROMPT_V1_SYSTEM__";
const POINTS = ["access", "flood", "perc_septic", "water_well", "liens_tax", "zoning", "utilities", "mineral_timber", "survey"];
const STATUSES = ["problem_stated", "clean", "missing"];
const BROWSER_HEADERS = {
  "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
  "Accept": "application/json",
  "Referer": "https://hazards.fema.gov/"
};

function pointOf(item) {
  if (typeof item === "string") return item;
  if (item && typeof item === "object") return item.point;
  return undefined;
}

function setsEqual(a, b) {
  if (a.size !== b.size) return false;
  for (const v of a) if (!b.has(v)) return false;
  return true;
}

function parseJson(text) {
  let t = String(text).trim();
  if (t.startsWith("```")) {
    const firstNewline = t.indexOf("\n");
    if (firstNewline !== -1) t = t.slice(firstNewline + 1);
    else t = t.slice(3);
    const trimmed = t.trimEnd();
    if (trimmed.endsWith("```")) t = trimmed.slice(0, -3);
    t = t.trim();
  }
  try {
    return JSON.parse(t);
  } catch {}
  for (let i = 0; i < t.length; i++) {
    if (t[i] !== "{") continue;
    let depth = 0;
    let inString = false;
    let escaped = false;
    for (let j = i; j < t.length; j++) {
      const ch = t[j];
      if (inString) {
        if (escaped) escaped = false;
        else if (ch === "\\") escaped = true;
        else if (ch === '"') inString = false;
      } else {
        if (ch === '"') inString = true;
        else if (ch === "{") depth++;
        else if (ch === "}") {
          depth--;
          if (depth === 0) {
            try {
              const obj = JSON.parse(t.slice(i, j + 1));
              if (obj && typeof obj === "object" && "checks" in obj) return obj;
            } catch {}
            break;
          }
        }
      }
    }
  }
  throw new Error("Invalid JSON");
}

function validate(result, listingText) {
  const errors = [];
  const warnings = [];
  const checks = result ? result.checks : null;
  if (!Array.isArray(checks) || checks.length !== 9) {
    errors.push("checks must be a list of exactly 9");
    return { errors, warnings };
  }
  for (const check of checks) {
    const point = check ? check.point : undefined;
    const status = check ? check.status : undefined;
    if (!POINTS.includes(point)) errors.push(`${point}: unknown point`);
    if (!STATUSES.includes(status)) errors.push(`${point}: bad status`);
    const evidence = check && Array.isArray(check.evidence) ? check.evidence : [];
    if ((status === "problem_stated" || status === "clean") && evidence.length === 0) {
      errors.push(`${point}: ${status} with no evidence`);
    }
    for (const q of evidence) {
      if (typeof q !== "string" || !listingText.includes(q)) {
        errors.push(`${point} FABRICATED QUOTE: ${q}`);
      }
    }
    if (status === "missing" && evidence.length > 0) {
      warnings.push(`${point}: missing check carrying evidence`);
    }
  }
  const problemPoints = new Set(checks.filter((c) => c.status === "problem_stated").map((c) => c.point));
  const redFlags = Array.isArray(result.red_flags) ? result.red_flags : [];
  const redPoints = new Set(redFlags.map((r) => pointOf(r)));
  if (!setsEqual(problemPoints, redPoints)) warnings.push("red_flags points differ from problem_stated points");
  const missingPoints = new Set(checks.filter((c) => c.status === "missing").map((c) => c.point));
  const missingItems = Array.isArray(result.missing_items) ? result.missing_items : [];
  const missingItemPoints = new Set(missingItems.map((r) => pointOf(r)));
  if (!setsEqual(missingPoints, missingItemPoints)) warnings.push("missing_items differ from missing points");
  const questions = Array.isArray(result.seller_questions) ? result.seller_questions : [];
  for (const p of missingPoints) {
    if (!questions.some((q) => pointOf(q) === p)) warnings.push(`${p}: missing point without a seller question`);
  }
  return { errors, warnings };
}

function applyRules(result) {
  const applied = [];
  if (!result || !Array.isArray(result.checks)) return applied;
  const check = result.checks.find((c) => c && c.point === "liens_tax");
  if (check && check.status === "clean") {
    const ev = (Array.isArray(check.evidence) ? check.evidence : []).join(" ").toLowerCase();
    const taxHalf = ev.includes("tax") && ["paid", "current", "through", "up to date", "up-to-date", "not delinquent", "no delinquent"].some((k) => ev.includes(k));
    const lienHalf = ev.includes("lien") && ["no lien", "free of lien", "free and clear", "clear of lien", "without lien", "no recorded lien", "lien free", "lien-free", "not subject to lien"].some((k) => ev.includes(k));
    if (!(taxHalf && lienHalf)) {
      check.status = "missing";
      check.note = `${check.note || ""} Harness rule: only one half of this point (taxes or liens) is stated, so it counts as not fully addressed.`;
      if (!Array.isArray(result.missing_items)) result.missing_items = [];
      if (!result.missing_items.includes("liens_tax")) result.missing_items.push("liens_tax");
      if (!Array.isArray(result.seller_questions)) result.seller_questions = [];
      if (!result.seller_questions.some((q) => pointOf(q) === "liens_tax")) {
        result.seller_questions.push({ point: "liens_tax", question: "Are all property taxes paid through the current year, and are there any liens, judgments, or back taxes on this parcel?" });
      }
      applied.push("liens_tax_clean_requires_both_halves");
    }
  }
  return applied;
}

async function runCheck(env, listingText, listingId) {
  const start = Date.now();
  const user = `Check this listing against the nine points. Return only the JSON object.\n\n<listing id="${listingId}">\n${listingText}\n</listing>`;
  const resp = await fetch(API, {
    method: "POST",
    headers: {
      "Authorization": `Bearer ${env.META_API_KEY}`,
      "Content-Type": "application/json"
    },
    body: JSON.stringify({
      model: MODEL,
      input: [
        { role: "system", content: SYSTEM_PROMPT },
        { role: "user", content: user }
      ],
      max_output_tokens: 12000,
      store: false
    })
  });
  if (!resp.ok) throw new Error(`Ember API ${resp.status}`);
  const data = await resp.json();
  let outputText = "";
  if (data && Array.isArray(data.output)) {
    for (const item of data.output) {
      if (item && Array.isArray(item.content)) {
        for (const part of item.content) {
          if (part && part.type === "output_text" && typeof part.text === "string") outputText += part.text;
        }
      }
    }
    if (!outputText) {
      for (const item of data.output) {
        if (item && Array.isArray(item.content)) {
          for (const part of item.content) {
            if (part && typeof part.text === "string") outputText += part.text;
          }
        }
      }
    }
  }
  const result = parseJson(outputText);
  const rules_applied = applyRules(result);
  const { errors, warnings } = validate(result, listingText);
  if (errors.length) throw new Error(`Validation failed: ${errors[0]}`);
  const input_tokens = (data.usage && (data.usage.input_tokens ?? data.usage.inputTokens)) || 0;
  const output_tokens = (data.usage && (data.usage.output_tokens ?? data.usage.outputTokens)) || 0;
  const usd = Math.round(((input_tokens / 1000000) * INPUT_USD_PER_MILLION + (output_tokens / 1000000) * OUTPUT_USD_PER_MILLION) * 1000000) / 1000000;
  result.cost = { usd, input_tokens, output_tokens, model: MODEL };
  result.harness = {
    errors,
    warnings,
    seconds: parseFloat(((Date.now() - start) / 1000).toFixed(1)),
    prompt_version: "v1",
    rules_applied
  };
  return result;
}

async function fetchJson(url, opts = {}, timeoutMs = 7000) {
  const res = await fetch(url, { ...opts, signal: AbortSignal.timeout(timeoutMs) });
  if (!res.ok) throw new Error(`Fetch failed: ${res.status}`);
  return await res.json();
}

function looksLikeAddress(text) {
  const t = String(text).trim();
  if (!t || t.length > 200) return false;
  const words = t.split(/\s+/).filter(Boolean);
  if (words.length > 22) return false;
  if (!/\d/.test(t)) return false;
  return t.includes(",") || /\b\d{5}(?:-\d{4})?\b/.test(t);
}

function extractAddress(text) {
  const re = /\b\d{1,6}\s+(?:[A-Za-z0-9.'-]+\s+){0,4}?(?:St|Street|Ave|Avenue|Rd|Road|Dr|Drive|Ln|Lane|Blvd|Hwy|Highway|Ct|Court|Cir|Circle|Way|Trl|Trail|Pkwy|Parkway)\b(?:\s+[A-Za-z0-9.'-]+)*,\s*[A-Za-z.'-]+(?:\s+[A-Za-z.'-]+)*,\s*[A-Z]{2}\s+\d{5}(?:-\d{4})?\b/;
  const m = String(text).match(re);
  return m ? m[0].trim() : null;
}

async function geocode(address) {
  const params = new URLSearchParams({ address, benchmark: "Public_AR_Current", format: "json" });
  const url = `https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?${params.toString()}`;
  const data = await fetchJson(url);
  const matches = (data.result || {}).addressMatches;
  if (!matches || !matches.length) return null;
  const m = matches[0];
  return { matched: m.matchedAddress, lat: m.coordinates.y, lng: m.coordinates.x };
}

async function femaLine(lng, lat) {
  const params = new URLSearchParams({
    geometry: `${lng},${lat}`,
    geometryType: "esriGeometryPoint",
    inSR: "4326",
    spatialRel: "esriSpatialRelIntersects",
    outFields: "FLD_ZONE,ZONE_SUBTY,SFHA_TF",
    returnGeometry: "false",
    f: "json"
  });
  const primary = `https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query?${params.toString()}`;
  const mirror = `https://hazards.fema.gov/arcgis/rest/services/FIRMette/NFHLREST_FIRMette/MapServer/20/query?${params.toString()}`;
  let data;
  try {
    data = await fetchJson(primary, { headers: BROWSER_HEADERS });
  } catch (e) {
    await new Promise((r) => setTimeout(r, 900));
    try {
      data = await fetchJson(primary, { headers: BROWSER_HEADERS });
    } catch (e2) {
      data = await fetchJson(mirror, { headers: BROWSER_HEADERS });
    }
  }
  const features = data && Array.isArray(data.features) ? data.features : [];
  if (!features.length) return "FEMA National Flood Hazard Layer: no flood hazard data is published for this point.";
  const attrs = features[0].attributes || {};
  let line = `FEMA National Flood Hazard Layer: the flood zone at this point is Zone ${attrs.FLD_ZONE}`;
  if (attrs.ZONE_SUBTY) line += `, ${String(attrs.ZONE_SUBTY).toLowerCase()}`;
  line += ".";
  if (attrs.SFHA_TF === "T") {
    line += " This point is in a Special Flood Hazard Area, with a 1 percent or greater annual chance of flooding. Flood insurance is required for buildings with federally backed mortgages in this area.";
  } else {
    line += " This point is not in a Special Flood Hazard Area.";
  }
  return line;
}

async function wetlandsLine(lng, lat) {
  const params = new URLSearchParams({
    geometry: `${lng},${lat}`,
    geometryType: "esriGeometryPoint",
    inSR: "4326",
    spatialRel: "esriSpatialRelIntersects",
    outFields: "WETLAND_TYPE",
    returnGeometry: "false",
    f: "json"
  });
  const url = `https://fwspublicservices.wim.usgs.gov/wetlandsmapservice/rest/services/Wetlands/MapServer/0/query?${params.toString()}`;
  const data = await fetchJson(url, { headers: BROWSER_HEADERS });
  const features = data && Array.isArray(data.features) ? data.features : [];
  if (!features.length) return "US Fish and Wildlife Service National Wetlands Inventory: no wetlands are mapped at this point.";
  const attrs = features[0].attributes || {};
  const type = attrs.WETLAND_TYPE || "wetland";
  return `US Fish and Wildlife Service National Wetlands Inventory: a mapped wetland is present at this point (type: ${type}). Building or filling in a mapped wetland can require federal permits.`;
}

async function sda(sql) {
  const body = new URLSearchParams({ QUERY: sql, FORMAT: "JSON+COLUMNNAME" });
  const data = await fetchJson(
    "https://SDMDataAccess.nrcs.usda.gov/Tabular/post.rest",
    { method: "POST", headers: { "Content-Type": "application/x-www-form-urlencoded" }, body: body.toString() },
    9000
  );
  const table = data && Array.isArray(data.Table) ? data.Table : [];
  return table.slice(1);
}

async function soilLines(lng, lat) {
  const sub = `(SELECT mukey FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('POINT(${lng} ${lat})'))`;
  let firstRows;
  try {
    firstRows = await sda(`SELECT muname FROM mapunit WHERE mukey IN ${sub}`);
  } catch {
    return [];
  }
  if (!firstRows || !firstRows.length) return [];
  const muname = Array.isArray(firstRows[0]) ? firstRows[0][0] : firstRows[0];
  if (!muname) return [];
  const lines = [`USDA soil survey: the soil at this point is ${muname}.`];
  try {
    const secondSql = `SELECT component.compname, component.comppct_r, component.drainagecl, cointerp.interplrc FROM mapunit INNER JOIN component ON component.mukey = mapunit.mukey LEFT JOIN cointerp ON cointerp.cokey = component.cokey AND cointerp.ruledepth = 0 AND cointerp.rulename = 'ENG - Septic Tank Absorption Fields' WHERE mapunit.mukey IN ${sub} ORDER BY component.comppct_r DESC`;
    const rows = await sda(secondSql);
    if (rows && rows.length) {
      const row = Array.isArray(rows[0]) ? rows[0] : [];
      const name = row[0];
      const pct = row[1];
      const drainagecl = row[2];
      const rating = row[3];
      if (drainagecl) {
        lines.push(`USDA soil survey: the main soil component (${name}, ${pct} percent of the area) has a drainage class of ${String(drainagecl).toLowerCase()}.`);
      }
      if (rating && rating !== "Not rated") {
        lines.push(`USDA soil survey: this soil is rated for septic tank absorption fields as: ${rating}.`);
      }
    }
  } catch {
    return lines;
  }
  return lines;
}

async function buildRecords(address) {
  const geo = await geocode(address);
  if (!geo) return null;
  const { matched, lat, lng } = geo;
  const results = await Promise.allSettled([femaLine(lng, lat), wetlandsLine(lng, lat), soilLines(lng, lat)]);
  const lines = [];
  const sources = ["US Census Bureau geocoder"];
  const names = ["FEMA National Flood Hazard Layer", "US Fish and Wildlife Service National Wetlands Inventory", "USDA soil survey"];
  results.forEach((r, i) => {
    if (r.status !== "fulfilled") return;
    if (typeof r.value === "string") {
      lines.push(r.value);
      sources.push(names[i]);
    } else if (Array.isArray(r.value) && r.value.length) {
      lines.push(...r.value);
      sources.push(names[i]);
    }
  });
  const floodLine = lines.find((l) => l.startsWith("FEMA National Flood Hazard Layer")) || null;
  const septicLine = lines.find((l) => l.includes("rated for septic tank absorption fields as:")) || null;
  const floodHazard = floodLine ? floodLine.includes("This point is in a Special Flood Hazard Area") : false;
  let septicRating = null;
  if (septicLine) {
    septicRating = (septicLine.split("rated for septic tank absorption fields as:")[1] || "").trim().replace(/\.$/, "").trim();
  }
  return { matched, lat, lng, lines, sources, facts: { floodLine, septicLine, floodHazard, septicRating } };
}

function applyRecordsOverride(result, facts) {
  if (!facts || !result) return;
  if (!result.harness) result.harness = {};
  if (!Array.isArray(result.harness.rules_applied)) result.harness.rules_applied = [];
  if (!Array.isArray(result.checks)) return;
  const flood = result.checks.find((c) => c && c.point === "flood");
  if (flood && flood.status === "clean" && facts.floodHazard && facts.floodLine) {
    flood.status = "problem_stated";
    flood.evidence = [facts.floodLine];
    flood.note = "The listing does not flag a flood problem, but FEMA records put this point in a Special Flood Hazard Area. The record is the flag.";
    flood.source = "records";
    if (!Array.isArray(result.red_flags)) result.red_flags = [];
    if (!result.red_flags.some((r) => pointOf(r) === "flood")) {
      result.red_flags.push({ point: "flood", summary: "FEMA records: Special Flood Hazard Area", quote: facts.floodLine });
    }
    if (Array.isArray(result.missing_items)) result.missing_items = result.missing_items.filter((x) => x !== "flood" && pointOf(x) !== "flood");
    if (Array.isArray(result.seller_questions)) result.seller_questions = result.seller_questions.filter((x) => pointOf(x) !== "flood");
    result.harness.rules_applied.push("records_override_flood");
  }
  const perc = result.checks.find((c) => c && c.point === "perc_septic");
  const rating = facts.septicRating;
  if (perc && perc.status === "clean" && facts.septicLine && (rating === "Somewhat limited" || rating === "Very limited")) {
    perc.status = "problem_stated";
    perc.evidence = [...(Array.isArray(perc.evidence) ? perc.evidence : []), facts.septicLine];
    perc.note = `The listing's perc position reads clean, but USDA soil data rates this soil ${rating} for septic absorption. Both are shown; the records rating is the flag.`;
    perc.source = "records";
    if (!Array.isArray(result.red_flags)) result.red_flags = [];
    if (!result.red_flags.some((r) => pointOf(r) === "perc_septic")) {
      result.red_flags.push({ point: "perc_septic", summary: `USDA soil rating: ${rating} for septic absorption`, quote: facts.septicLine });
    }
    if (Array.isArray(result.missing_items)) result.missing_items = result.missing_items.filter((x) => x !== "perc_septic" && pointOf(x) !== "perc_septic");
    if (Array.isArray(result.seller_questions)) result.seller_questions = result.seller_questions.filter((x) => pointOf(x) !== "perc_septic");
    result.harness.rules_applied.push("records_override_perc_septic");
  }
}

function tagRecordsSources(result, listingText) {
  if (!result || !Array.isArray(result.checks)) return;
  for (const check of result.checks) {
    if (check && Array.isArray(check.evidence) && check.evidence.length > 0) {
      if (check.evidence.every((q) => typeof q !== "string" || !listingText.includes(q))) {
        check.source = "records";
      }
    }
  }
}

async function runSmart(env, text, id) {
  let records_note = null;
  if (looksLikeAddress(text)) {
    let records = null;
    try {
      records = await buildRecords(text);
    } catch {
      records = null;
    }
    if (records && records.lines && records.lines.length) {
      const recordsText = `Public records check for the property at: ${records.matched}\nCoordinates of the point checked: latitude ${records.lat}, longitude ${records.lng}.\n${records.lines.join("\n")}\nThis text is compiled from live public records, not from a seller listing. It covers only the points the records speak to. Anything the records do not cover is not addressed here and still needs the seller or the county.`;
      const result = await runCheck(env, recordsText, "address");
      applyRecordsOverride(result, records.facts);
      result.mode = "records";
      result.matched_address = records.matched;
      result.sources = records.sources;
      return result;
    }
    records_note = "That looked like an address, but it was not found in the US public records ParcelCheck uses, so records were not checked. It was read as listing text instead. ParcelCheck covers US addresses.";
  } else {
    const addr = extractAddress(text);
    if (addr) {
      let records = null;
      try {
        records = await buildRecords(addr);
      } catch {
        records = null;
      }
      if (records && records.lines && records.lines.length) {
        const combined = text + "\n\nPUBLIC RECORDS CHECKED TODAY for the address in this listing (" + records.matched + "):\n" + records.lines.join("\n");
        const result = await runCheck(env, combined, id);
        applyRecordsOverride(result, records.facts);
        tagRecordsSources(result, text);
        result.mode = "listing+records";
        result.matched_address = records.matched;
        result.sources = records.sources;
        return result;
      }
      records_note = "An address was found in the text, but public records were not checked for it. This report covers the listing text only.";
    }
  }
  const result = await runCheck(env, text, id);
  result.mode = "listing";
  if (records_note) result.records_note = records_note;
  return result;
}

export class RunCounter {
  constructor(state, env) {
    this.state = state;
    this.env = env;
  }
  async fetch(request) {
    const storage = this.state.storage;
    const day = new Date().toISOString().slice(0, 10);
    let s = await storage.get("state");
    if (!s || s.day !== day) s = { day, count: 0 };
    if (s.count >= DAILY_CAP) {
      return new Response(JSON.stringify({ ok: false }), { headers: { "Content-Type": "application/json; charset=utf-8" } });
    }
    s.count += 1;
    await storage.put("state", s);
    return new Response(JSON.stringify({ ok: true, count: s.count }), { headers: { "Content-Type": "application/json; charset=utf-8" } });
  }
}

function jsonResponse(data, status = 200) {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8" }
  });
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    if (request.method === "POST" && url.pathname === "/check") {
      let body;
      try {
        body = await request.json();
      } catch {
        return jsonResponse({ error: "Bad request." }, 400);
      }
      const text = body && typeof body.text === "string" ? body.text.trim() : "";
      if (!text) return jsonResponse({ error: "Nothing to check yet. Paste a listing, or type a street address with city and state." }, 400);
      if (text.length > MAX_TEXT) return jsonResponse({ error: "That text is over 20000 characters. Paste the listing description and its fields, not the whole page." }, 400);
      if (!looksLikeAddress(text)) {
        const words = text.split(/\s+/).filter(Boolean);
        if (words.length < 8) return jsonResponse({ error: "That is too short to check. Paste a full listing, or type a street address with city, state, and ZIP." }, 400);
        if (!/\d/.test(text) && !/(acre|land|sale|sold|price|road|lot|property|zoning|well|septic|tax|parcel|county|bed|bath)/i.test(text)) {
          return jsonResponse({ error: "That does not look like a listing or an address. Paste a full listing, or type a street address with city, state, and ZIP." }, 400);
        }
      }
      if (env && env.RUN_COUNTER) {
        const counterId = typeof env.RUN_COUNTER.idFromName === "function" ? env.RUN_COUNTER.idFromName("global") : "global";
        const stub = env.RUN_COUNTER.get(counterId);
        let capResp;
        try {
          capResp = await stub.fetch(new Request("https://run-counter/"));
        } catch {
          capResp = await stub.fetch("https://run-counter/");
        }
        let capData;
        if (capResp && typeof capResp.json === "function") capData = await capResp.json();
        else capData = capResp;
        if (capData && capData.ok === false) {
          return jsonResponse({ error: "Daily live run cap reached. Cached examples still work." }, 429);
        }
      }
      try {
        const result = await runSmart(env, text, (body && body.id) || "web");
        return jsonResponse(result, 200);
      } catch (e) {
        const msg = e && e.message ? e.message : String(e);
        return jsonResponse({ error: `Checker run failed: ${msg.slice(0, 200)}` }, 502);
      }
    }
    return env.ASSETS.fetch(request);
  }
};
