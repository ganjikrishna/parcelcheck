You are building an answer key for a land-listing checker. Read the checklist rules and ONE listing. For each of the nine points, decide the status using ONLY the listing text and the checklist rules.

Return ONLY a JSON array of exactly 9 objects, in point order 1 to 9, each:
{"point": <1-9>, "status": "problem_stated" | "clean" | "missing", "quote": "<exact words copied character for character from the listing text>"}

Rules for the quote: for problem_stated and clean, the quote MUST be copied exactly from the listing text below (a substring, character for character, including punctuation). For missing, use an empty string. Never invent or paraphrase words. Generic disclaimers such as "buyer to verify" do not make a point clean or a problem. An annual tax amount alone is not a tax status. A deed type alone is not a lien statement.

CHECKLIST RULES:
---
# ParcelCheck nine-point checklist

## Document order note

Vinay's lived list comes first: legal road access, flood zone, perc test, well depth, liens. These five are the checks he learned the hard way, so they lead the document. The remaining four (zoning, utilities, mineral and timber rights, survey status) follow. The point numbers below are the fixed IDs the checker and the answer key use.

## Scoring rule for every point

Each point gets exactly one status per listing:

- **problem stated**: the listing text itself says something adverse about this point. Every problem stated must carry the exact quoted listing words.
- **clean**: the listing text affirmatively states the point is in order. Boilerplate such as "buyer to verify" does not make a point clean.
- **missing**: the listing text does not address the point. Anything not stated is missing, never clean and never a problem. Every missing point becomes a seller question.

Generic disclaimers ("Buyer to independently verify zoning, legal access...", "Buyer to perform all due diligence regarding...") do not change a status by themselves. They neither clear a point nor flag one.

---

## 1. Legal road access

**What it means.** The parcel has a legal, recorded right to reach a public road, either by direct public road frontage or by a recorded easement. Physical access (a path or a neighbor's driveway) is not the same as legal access.

**Problem stated wording.** "landlocked", "land-locked", "no road access", "no established road access", "no legal road frontage or access", "Road Frontage: None", "Roads: None", "does not have direct public road frontage". A landlocked parcel that relies on an easement is still a problem stated (quote both the landlocked words and the easement words).

**Covered clean.** The listing states road frontage or a named road access, for example "Road access: Paved Road", "Road Frontage Type: ... 2 Lane Road", or "Accessed via a common driveway", with no landlocked wording.

**Missing.** Only a street address, or no mention of road frontage or access at all. An address alone does not prove legal access.

**Seller questions (missing case).**
- Does the parcel have direct frontage on a publicly maintained road, and if not, is there a recorded access easement? Please send the recording reference.
- If access is by a shared or private drive, is there a recorded road maintenance agreement?

## 2. Flood zone

**What it means.** Whether any part of the parcel lies in a FEMA flood zone (Zone A, AE, floodway, 100-year or 500-year floodplain) or contains wetlands. This drives building rules, insurance cost, and septic placement.

**Problem stated wording.** "FEMA Zone AE floodplain", "floodway", "100 yr flood plain", "500-year flood zone", "Flood Plains", "lies in multiple flood zones", "wetlands", "Base Flood Elevation".

**Covered clean.** The listing states the parcel is outside the flood zone, for example "FEMA Zone X" or "not in a flood zone".

**Missing.** No flood zone or wetland statement at all. Nearby water, sloughs, or rivers mentioned without a flood statement are still missing, not a problem.

**Seller questions (missing case).**
- What FEMA flood zone designation applies to the parcel, and which FIRM panel number covers it?
- Is any portion of the parcel in a floodway or mapped wetland?

## 3. Perc test and septic feasibility

**What it means.** Whether the soil has passed a percolation test or a septic permit has been approved, so that a septic system can be installed. If public sewer is stated as available, septic feasibility is not needed and the point is clean.

**Problem stated wording.** "failed perc", "will not perc", "septic ... may be affected by floodplain and wetland conditions", "will require county review", "septic system must be installed" stated alongside a restriction, "no septic permit".

**Covered clean.** "approved perc test", "Perc Approved Septic", "passing perc test for septic", "perc test completed, well and septic approved", "Perc Test On File" with approval wording, or "Sewer available" (public sewer).

**Missing.** No perc test, septic, or sewer statement, or a field such as "Sewer: None" or "Sewer: Septic Tank" with no perc or septic approval wording. These say what system is expected, not that the soil will support it.

**Seller questions (missing case).**
- Has a perc test or soil evaluation been done on this parcel, and can you send the result and the date?
- Has the county health department issued or denied a septic permit for this parcel?

## 4. Water source and well depth

**What it means.** Where drinking water will come from (public water connection or a private well) and, for a well, how deep it is and its yield.

**Problem stated wording.** "Well Needed", "A well must be drilled", "neither is currently present", "no water", "dry well".

**Covered clean.** A water source is stated as present or available: "Water and Sewer available", "Water Source: Well, Private", "Existing drilled well", "a well on-site", "well ... approved by the ... Board of Health". Well depth is a sub-item: if a well is stated but its depth is not, the point is still scored clean, and the checker still asks the depth question.

**Missing.** No water statement, or a vague field such as "Water Source: Other" with nothing else.

**Seller questions (missing case).**
- What is the water source for the parcel: public water at the lot line, an existing well, or a well still to be drilled?
- If there is a well, what is its depth, its yield in gallons per minute, and the date of the last water test? (Ask this one even when the point is clean but depth is not stated.)

## 5. Liens and tax status

**What it means.** Whether property taxes are current, and whether any liens, judgments, or back taxes attach to the parcel. Tax sale parcels carry this risk by definition.

**Problem stated wording.** "Years Due", "delinquent", "tax sale", "Starting bid" on a tax sale list, "lien", "judgment", "back taxes".

**Covered clean.** The listing states taxes are current or paid and there are no liens, for example "taxes paid through 2025, no liens".

**Missing.** No statement of tax payment status or liens. An annual tax amount alone ("Property Tax: $1,351.87", "Taxes: $660.48") is not a tax status and is scored missing. A deed type ("Deed: Warranty") is not a lien statement and is scored missing.

**Seller questions (missing case).**
- Are all property taxes paid through the current year, and are there any delinquent years?
- Are there any recorded liens, judgments, or assessments against the parcel, and will you deliver clear title at closing?

## 6. Zoning

**What it means.** The zoning designation and whether it permits the buyer's intended use (home, mobile home, farm, commercial).

**Problem stated wording.** "There is no permitted use in its current state", "not buildable", "variance required", or a stated use conflict.

**Covered clean.** A zoning designation is stated with no stated conflict, for example "Zoned AU agricultural", "zoned RA-30", "Zoning: C-2", "SF6", "Zoning: AC, Agricultural Conservation".

**Missing.** No zoning designation stated. A subdivision approval without a zoning designation is still missing.

**Seller questions (missing case).**
- What is the current zoning designation, and does it allow a single-family home (or the buyer's intended use)?
- Are there any pending rezonings, overlays, or deed restrictions that limit use?

## 7. Utilities

**What it means.** Availability of electricity, natural gas, and telephone, internet, or cable at or near the parcel. Water and sewer are scored under points 3 and 4, not here.

**Problem stated wording.** "Utilities: None", "no utilities are represented as available", "Natural Gas Not Available", "no power".

**Covered clean.** "Electricity Available", "Cable Available", "electric and fiber already run to the shared driveway".

**Missing.** No statement about electricity, gas, or telecom. "Buyer to verify utilities" is missing.

**Seller questions (missing case).**
- Is electric service available at the lot line, and which utility serves it? If not, how far away is the nearest pole?
- Is internet or phone service available at the parcel?

## 8. Mineral and timber rights

**What it means.** Whether mineral rights and timber rights convey with the land or were severed and retained by a prior owner or a third party.

**Problem stated wording.** "mineral rights reserved", "mineral rights do not convey", "timber rights retained", "timber lease", "subject to mineral lease".

**Covered clean.** "all mineral and timber rights convey", "seller owns and conveys mineral rights".

**Missing.** No mention of mineral or timber rights. Describing the land as "wooded" says nothing about who owns the timber and is missing.

**Seller questions (missing case).**
- Do all mineral rights convey with the parcel, or have any been reserved or leased?
- Do the timber rights convey, and is there any existing timber lease or cutting contract?

## 9. Survey status

**What it means.** Whether a current boundary survey exists, and whether boundaries, easements, and buildable area are established.

**Problem stated wording.** "no survey", "survey needed", "boundaries approximate" stated as an issue, or a statement that key limits "must be confirmed through a survey".

**Covered clean.** "recent boundary survey on file", "surveyed in [year]", "survey available".

**Missing.** No survey statement. Approximate dimensions ("Approx. 247' x 186'") or a lot size source ("Lot Size Source: Assessor") are not a survey and are scored missing.

**Seller questions (missing case).**
- Is there a recorded boundary survey for this parcel, and what is its date? Please send a copy.
- Are the corners marked, and are there any known encroachments or boundary disputes?

---

LISTING TEXT:
---
Source: Long & Foster Real Estate (0 Doctor Perry Road, Ijamsville, MD 21754, MLS #MDFR2065000)
URL: https://www.longandfoster.com/cookiedrummond/realestate/details/54790973/0-doctor-perry-road-ijamsville-md-21754
Collected: 2026-11-25
Note: excerpt of the listing page as retrieved on 2026-11-25.

0 DOCTOR PERRY ROAD, IJAMSVILLE, MD 21754. Vacant Land, 32.14 Acres. $1,250,000 ACTIVE.

Overview: 32 Gorgeous Acres at the Foot of Sugarloaf Mountain! Breathtaking views of the mountains and surrounding countryside. This beautiful property features: 20 GPM well already in place. Perc approved. Ideal building site in the center of the property. 30% wooded, partly fenced, with a potential pond site, stream, and Urbana Lake at the back. Perfect for a farmette, private estate, or country retreat. Buyer to perform due diligence on any land use changes, zoning variances, or feasibility studies. Located next to the famous PB Dye Golf Course with AG zoning, this property offers both privacy and convenience with easy access to I-270 and sought-after Urbana schools.

Details: County: FREDERICK. Subdivision Name: URBANA. Tax Information: County Tax: 100.00. Tax Annual Amount: $100.00. Tax Assessed Value: 8200.00. Tax Year: 2025. Zoning: A. Lot Information: Lot Size Acres: 32.14. Road Responsibility: City/County. Road Surface Type: Access - On Grade, Black Top. Water Source: Well. Farm Land Preservation: No. Fencing: Partially. Sewer: Septic Exists. Water Access: No.
