/* ============================================================================
   GET /api/leads

   Vercel Node serverless function. Server-side-only CallRail v3 client for the
   /dashboard/ lead-call log. The CallRail API key never reaches the browser --
   this function fetches the call list, masks every phone number, and returns
   plain JSON.

   REQUIRED ENV VAR (set in Vercel -> Project -> Settings -> Environment
   Variables):
       CALLRAIL_API_KEY        CallRail API key (Account -> Settings -> API Keys)

   Optional:
       CALLRAIL_TRACKING_NUMBER   defaults to +17577202096, this site's number

   Without CALLRAIL_API_KEY this returns 503 with a setup hint rather than
   failing silently -- /dashboard/ surfaces that state as a banner, not a crash.

   Zero dependencies: talks to CallRail over its REST API with fetch, which is
   global on Vercel's Node 18+ runtime. Matches the rest of this repo, which
   has no package.json / node_modules.
   ============================================================================ */
"use strict";

var API_KEY = process.env.CALLRAIL_API_KEY || "";
var TRACKING_NUMBER = process.env.CALLRAIL_TRACKING_NUMBER || "+17577202096";
var BASE = "https://api.callrail.com/v3";

var CALL_FIELDS = [
  "recording", "recording_duration", "transcription", "source_name", "medium",
  "keywords", "landing_page_url", "device_type", "first_call", "total_calls",
  "prior_calls", "tags"
].join(",");

function authHeader() {
  return { Authorization: 'Token token="' + API_KEY + '"' };
}

// Keep all characters except the last 4, replace those with bullets. Applied
// to every phone number before it ever leaves this function.
function maskPhone(p) {
  if (!p) return p;
  var s = String(p);
  if (s.length <= 4) return "••••";
  return s.slice(0, -4) + "••••";
}

async function getAccountId() {
  var r = await fetch(BASE + "/a.json", { headers: authHeader() });
  if (!r.ok) throw new Error("callrail_accounts_" + r.status);
  var data = await r.json();
  var accounts = data.accounts || [];
  if (!accounts.length) throw new Error("callrail_no_accounts");
  return accounts[0].id;
}

async function listInboundCalls(accountId) {
  var calls = [];
  var page = 1;
  var totalPages = 1;

  do {
    var url = BASE + "/a/" + accountId + "/calls.json" +
      "?direction=inbound" +
      "&tracking_phone_number=" + encodeURIComponent(TRACKING_NUMBER) +
      "&sort=start_time&order=desc" +
      "&fields=" + encodeURIComponent(CALL_FIELDS) +
      "&per_page=250&page=" + page;

    var r = await fetch(url, { headers: authHeader() });
    if (!r.ok) throw new Error("callrail_calls_" + r.status);
    var data = await r.json();

    calls = calls.concat(data.calls || []);
    totalPages = data.total_pages || 1;
    page += 1;
  } while (page <= totalPages);

  return calls;
}

// CallRail's `tags` field is an array of OBJECTS ({id, name, tag_level,
// color, background_color, company_id, status, disabled, created_at}), not
// strings. Trim it down to what the UI actually renders.
function normalizeTags(tags) {
  if (!Array.isArray(tags)) return [];
  return tags.map(function (t) {
    return {
      name: (t && t.name) || "",
      color: (t && t.color) || null,
      background_color: (t && t.background_color) || null
    };
  }).filter(function (t) { return t.name; });
}

function status(call) {
  if (call.voicemail) return "voicemail";
  return call.answered ? "answered" : "missed";
}

function normalize(call) {
  return {
    id: call.id,
    start_time: call.start_time || null,
    duration: call.duration || 0,
    status: status(call),
    customer_name: call.customer_name || null,
    customer_phone_number: maskPhone(call.customer_phone_number),
    business_phone_number: maskPhone(call.business_phone_number),
    recording: call.recording || null,
    recording_duration: call.recording_duration || null,
    // null unless the CallRail account has Conversation Intelligence on --
    // treated as a normal empty state by the client, not an error.
    transcription: call.transcription || null,
    source_name: call.source_name || null,
    medium: call.medium || null,
    keywords: call.keywords || null,
    landing_page_url: call.landing_page_url || null,
    device_type: call.device_type || null,
    first_call: !!call.first_call,
    total_calls: call.total_calls || null,
    prior_calls: call.prior_calls || null,
    tags: normalizeTags(call.tags)
  };
}

module.exports = async function handler(req, res) {
  if (req.method === "OPTIONS") {
    res.setHeader("Allow", "GET, OPTIONS");
    return res.status(204).end();
  }
  if (req.method !== "GET") {
    res.setHeader("Allow", "GET, OPTIONS");
    return res.status(405).json({ error: "method_not_allowed" });
  }

  if (!API_KEY) {
    return res.status(503).json({
      error: "not_configured",
      hint: "Set CALLRAIL_API_KEY in the Vercel project's environment variables."
    });
  }

  try {
    var accountId = await getAccountId();
    var calls = await listInboundCalls(accountId);
    res.setHeader("Cache-Control", "no-store");
    return res.status(200).json({
      generated_at: new Date().toISOString(),
      calls: calls.map(normalize)
    });
  } catch (err) {
    console.error("leads fetch failed", err);
    return res.status(502).json({ error: "fetch_failed" });
  }
};
