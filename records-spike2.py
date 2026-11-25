#!/usr/bin/env python3
"""Independent spike for the records verification key. Runs on Flash.
Uses the public sources directly (Census, FEMA NFHL, USDA SDA) with a
separate code path from the production Worker, so the sealed key is an
independent expectation for the scored Worker run."""
import json, urllib.request, urllib.parse

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36", "Accept": "application/json", "Referer": "https://hazards.fema.gov/"}

ADDRESSES = [
    "1000 Ocean Dr, Miami Beach, FL 33139",
    "200 Ocean Ave, Santa Monica, CA 90402",
    "600 Travis St, Houston, TX 77002",
    "301 W 2nd St, Austin, TX 78701",
    "100 W Washington St, Phoenix, AZ 85003",
    "200 E Colfax Ave, Denver, CO 80203",
    "400 W Church St, Orlando, FL 32801",
    "350 Deaderick St, Nashville, TN 37219",
    "100 Main St, Madison, GA 30650",
    "301 King St, Charleston, SC 29401",
]

def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8", "replace"))

def sda(sql):
    req = urllib.request.Request("https://SDMDataAccess.nrcs.usda.gov/Tabular/post.rest",
        data=urllib.parse.urlencode({"QUERY": sql, "FORMAT": "JSON+COLUMNNAME"}).encode(), headers=UA)
    with urllib.request.urlopen(req, timeout=40) as r:
        d = json.loads(r.read().decode("utf-8", "replace"))
    return (d.get("Table") or [])[1:]

out = []
for addr in ADDRESSES:
    row = {"input": addr}
    try:
        u = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress?" + urllib.parse.urlencode(
            {"address": addr, "benchmark": "Public_AR_Current", "format": "json"})
        m = get(u)["result"]["addressMatches"]
        if not m:
            row["error"] = "no geocode match"; out.append(row); continue
        row["matched"] = m[0]["matchedAddress"]
        lng, lat = m[0]["coordinates"]["x"], m[0]["coordinates"]["y"]
        row["lng"], row["lat"] = lng, lat
    except Exception as e:
        row["error"] = "geocode: " + str(e)[:80]; out.append(row); continue
    try:
        q = urllib.parse.urlencode({"geometry": f"{lng},{lat}", "geometryType": "esriGeometryPoint",
            "inSR": 4326, "spatialRel": "esriSpatialRelIntersects",
            "outFields": "FLD_ZONE,ZONE_SUBTY,SFHA_TF", "returnGeometry": "false", "f": "json"})
        d = None
        for attempt in range(4):
            try:
                d = get("https://hazards.fema.gov/arcgis/rest/services/public/NFHL/MapServer/28/query?" + q)
                break
            except Exception:
                if attempt == 3: raise
                import time; time.sleep(3)
        feats = d.get("features", [])
        row["fema"] = feats[0]["attributes"] if feats else None
    except Exception as e:
        row["fema_error"] = str(e)[:80]
    try:
        sub = f"(SELECT mukey FROM SDA_Get_Mukey_from_intersection_with_WktWgs84('POINT({lng} {lat})'))"
        mu = sda("SELECT muname FROM mapunit WHERE mukey IN " + sub)
        row["muname"] = mu[0][0] if mu else None
        rows = sda("SELECT ci.interplrc FROM component c JOIN cointerp ci ON ci.cokey = c.cokey "
                   "WHERE c.mukey IN " + sub + " AND ci.ruledepth = 0 AND ci.rulename = 'ENG - Septic Tank Absorption Fields' "
                   "ORDER BY c.comppct_r DESC")
        row["septic"] = rows[0][0] if rows else None
    except Exception as e:
        row["sda_error"] = str(e)[:80]
    out.append(row)
    print("done:", addr, "->", row.get("fema"), "| septic:", row.get("septic"))

print(json.dumps(out, indent=1))
