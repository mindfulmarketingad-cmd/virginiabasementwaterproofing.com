/* ============================================================================
   POST /api/analytics/track

   Vercel Node serverless function. Validates the incoming event, classifies
   listing pages server-side (so the taxonomy can't be spoofed by the client),
   promotes a plain pageview to listing_view on a listing page, and inserts the
   row with the service-role key.

   Zero dependencies: talks to Supabase over its REST endpoint with fetch, which
   is global on Vercel's Node 18+ runtime. That keeps this repo free of a
   package.json / node_modules, matching the rest of the site.

   REQUIRED ENV VAR (set in Vercel -> Project -> Settings -> Environment
   Variables):
       SUPABASE_SERVICE_ROLE_KEY   service_role key from Supabase -> Settings -> API

   Optional:
       SUPABASE_URL                defaults to the project URL below
       ANALYTICS_TABLE             defaults to virginiabasementwaterproofing_dashboard

   Without SUPABASE_SERVICE_ROLE_KEY this returns 503 with a setup hint rather
   than failing silently -- /dashboard/ surfaces that state too.
   ============================================================================ */
"use strict";

var Analytics = require("../../js/analytics.js");
var DATA = require("./_listings.json");

var SUPABASE_URL =
  process.env.SUPABASE_URL || "https://tbqigevoksabizjogvtm.supabase.co";
var SERVICE_KEY = process.env.SUPABASE_SERVICE_ROLE_KEY || "";
var TABLE =
  process.env.ANALYTICS_TABLE || "virginiabasementwaterproofing_dashboard";

// Keep any single field from being used as a storage vector.
var LIMITS = {
  path: 512, referrer: 512, session_id: 64, visitor_id: 64,
  listing_slug: 160, listing_name: 200, city: 120, query: 200
};

function clean(value, max) {
  if (value === null || value === undefined) return null;
  var s = String(value).trim();
  if (!s) return null;
  return s.length > max ? s.slice(0, max) : s;
}

function readBody(req) {
  // Vercel usually parses JSON bodies for us; fall back to reading the stream
  // so this also works when the body arrives via sendBeacon as a blob.
  if (req.body && typeof req.body === "object") return Promise.resolve(req.body);
  if (typeof req.body === "string") {
    try { return Promise.resolve(JSON.parse(req.body)); }
    catch (e) { return Promise.resolve(null); }
  }
  return new Promise(function (resolve) {
    var raw = "";
    req.on("data", function (c) {
      raw += c;
      if (raw.length > 16000) { req.destroy(); resolve(null); }
    });
    req.on("end", function () {
      if (!raw) return resolve(null);
      try { resolve(JSON.parse(raw)); } catch (e) { resolve(null); }
    });
    req.on("error", function () { resolve(null); });
  });
}

module.exports = async function handler(req, res) {
  if (req.method === "OPTIONS") {
    res.setHeader("Allow", "POST, OPTIONS");
    return res.status(204).end();
  }
  if (req.method !== "POST") {
    res.setHeader("Allow", "POST, OPTIONS");
    return res.status(405).json({ error: "method_not_allowed" });
  }

  var body = await readBody(req);
  if (!body) return res.status(400).json({ error: "invalid_body" });

  var eventType = clean(body.event_type, 40);
  if (!eventType || !Analytics.isValidEvent(eventType)) {
    return res.status(400).json({ error: "invalid_event_type" });
  }

  var path = clean(body.path, LIMITS.path) || "/";

  // Classify server-side rather than trusting whatever the client claimed.
  var info = Analytics.classifyListingPath(path);

  // A pageview on a listing page IS a listing view -- promote it so the two
  // never have to be reconciled at query time.
  if (eventType === Analytics.EVENTS.PAGEVIEW && info.isListing) {
    eventType = Analytics.EVENTS.LISTING_VIEW;
  }

  // Prefer the slug the client reported for click events fired from a card
  // (the click target's listing, not the page it happened on); otherwise use
  // the slug from the path.
  var listingSlug = clean(body.listing_slug, LIMITS.listing_slug) || info.listingSlug;

  var listingName = null;
  var city = null;

  if (listingSlug && DATA.listings[listingSlug]) {
    listingName = DATA.listings[listingSlug][0] || null;
    city = DATA.listings[listingSlug][1] || null;
  }
  if (!city && info.city) {
    city = DATA.cities[info.city] || info.city; // display name, else the slug
  }
  if (!listingName) listingName = clean(body.listing_name, LIMITS.listing_name);
  if (!city) city = clean(body.city, LIMITS.city);

  var row = {
    event_type:   eventType,
    path:         path,
    referrer:     clean(body.referrer, LIMITS.referrer),
    session_id:   clean(body.session_id, LIMITS.session_id),
    visitor_id:   clean(body.visitor_id, LIMITS.visitor_id),
    listing_slug: listingSlug || null,
    listing_name: listingName || null,
    city:         city || null,
    query:        clean(body.query, LIMITS.query)
  };

  if (!SERVICE_KEY) {
    return res.status(503).json({
      error: "not_configured",
      hint: "Set SUPABASE_SERVICE_ROLE_KEY in the Vercel project environment variables."
    });
  }

  try {
    var r = await fetch(SUPABASE_URL + "/rest/v1/" + TABLE, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        apikey: SERVICE_KEY,
        Authorization: "Bearer " + SERVICE_KEY,
        Prefer: "return=minimal"
      },
      body: JSON.stringify(row)
    });

    if (!r.ok) {
      var detail = await r.text();
      // Logged for the Vercel function log; not echoed to the browser.
      console.error("analytics insert failed", r.status, detail);
      return res.status(502).json({ error: "insert_failed", status: r.status });
    }
  } catch (err) {
    console.error("analytics insert threw", err);
    return res.status(502).json({ error: "insert_failed" });
  }

  return res.status(202).json({ ok: true, event_type: eventType });
};
