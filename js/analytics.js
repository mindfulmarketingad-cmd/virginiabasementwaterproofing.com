/* ============================================================================
   analytics.js — shared analytics vocabulary + path classification.

   Loaded BOTH in the browser (as <script>, exposing window.VBWAnalytics) and by
   the serverless function at api/analytics/track.js (via require). Keeping one
   file means the event taxonomy and the path rules can never drift apart
   between what the client sends and what the server validates.

   Deliberately dependency-free and ES5 so it runs unchanged in either place.
   ============================================================================ */
(function (root, factory) {
  "use strict";
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api; // node
  root.VBWAnalytics = api;                                               // browser
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  // ---- event vocabulary ----------------------------------------------------
  // The first six are shared with the other directory dashboards so the sites
  // stay comparable. call_click and directions_click are structurally
  // impossible on this site (no phone numbers published anywhere, no
  // directions links) and will always read zero -- they are kept so the schema
  // matches the other properties. quote_click / claim_click are this site's
  // real conversion actions.
  var EVENTS = {
    PAGEVIEW:         "pageview",
    LISTING_VIEW:     "listing_view",
    CALL_CLICK:       "call_click",
    DIRECTIONS_CLICK: "directions_click",
    SEARCH:           "search",
    REVIEW_CLICK:     "review_click",
    QUOTE_CLICK:      "quote_click",
    CLAIM_CLICK:      "claim_click"
  };

  var EVENT_LIST = Object.keys(EVENTS).map(function (k) { return EVENTS[k]; });

  // Actions that represent a visitor trying to reach a contractor. Used by the
  // dashboard's "Lead Actions" stat. Distinct from "Leads Received", which
  // counts real rows in the `leads` table.
  var LEAD_ACTIONS = [
    EVENTS.QUOTE_CLICK,
    EVENTS.CALL_CLICK,
    EVENTS.CLAIM_CLICK,
    EVENTS.DIRECTIONS_CLICK
  ];

  // Human labels for the dashboard's charts and tables.
  var EVENT_LABELS = {
    pageview:         "Page Views",
    listing_view:     "Listing Views",
    quote_click:      "Quote Requests",
    claim_click:      "Claim Listing",
    review_click:     "Review Clicks",
    search:           "Searches",
    call_click:       "Phone Clicks",
    directions_click: "Directions"
  };

  // ---- service slugs -------------------------------------------------------
  // /find/<find-slug>-<city>-va/  and  /<city>/<legacy-slug>/
  // Both are needed to split a path correctly, because service names and city
  // names can each contain hyphens (e.g. basement-water-damage-restoration +
  // mt-sidney). Longest-first matching resolves the ambiguity.
  var FIND_SLUGS = [
    "basement-water-damage-restoration", "thermal-dry-floor-installation",
    "crawl-space-encapsulation", "french-drain-installation",
    "mobile-home-vapor-barrier", "sump-pump-installation",
    "emergency-water-clean-up", "basement-crack-repair", "black-mold-treatment",
    "basement-remodeling", "basement-finishing", "foundation-repair",
    "mold-remediation", "waterproofing", "mold-removal"
  ];

  var LEGACY_SLUGS = [
    "basement-water-damage-restoration", "thermal-dry-floor-installation",
    "crawl-space-encapsulation", "french-drain-installation",
    "mobile-home-vapor-barrier", "sump-pump-installation",
    "emergency-water-clean-up", "basement-crack-repair", "black-mold-treatment",
    "basement-waterproofing", "basement-remodeling", "foundation-repair"
  ];

  function byLengthDesc(a, b) { return b.length - a.length; }
  FIND_SLUGS.sort(byLengthDesc);
  LEGACY_SLUGS.sort(byLengthDesc);

  function segments(path) {
    return String(path || "/").split("?")[0].split("#")[0]
      .split("/").filter(function (s) { return s.length > 0; });
  }

  /**
   * Map a URL path to the listing and/or city it represents.
   *
   * Returns { isListing, listingSlug, city, service, kind } where city is a
   * SLUG (e.g. "mt-sidney"), not a display name -- the server resolves the
   * display name and business name from api/analytics/_listings.json.
   *
   * Recognised shapes on this site:
   *   /partners/<slug>/                  listing detail  -> isListing
   *   /reviews/<slug>/                   listing reviews -> isListing
   *   /find/<service>-<city>-va/         city searchmap
   *   /find/<service>-va/                statewide searchmap
   *   /<city|zip>/<service>/             city or ZIP money page
   */
  function classifyListingPath(path) {
    var out = {
      isListing: false, listingSlug: null, city: null, service: null, kind: "page"
    };
    var seg = segments(path);
    if (!seg.length) { out.kind = "home"; return out; }

    // /partners/<slug>/ and /reviews/<slug>/ -- the hubs themselves have no slug
    if ((seg[0] === "partners" || seg[0] === "reviews") && seg.length >= 2) {
      out.isListing   = true;
      out.listingSlug = seg[1];
      out.kind        = seg[0] === "partners" ? "listing" : "listing_reviews";
      return out;
    }

    // /find/<service>[-<city>]-va/
    if (seg[0] === "find" && seg.length >= 2) {
      out.kind = "find";
      var rest = seg[1];
      if (rest.slice(-3) === "-va") rest = rest.slice(0, -3);
      for (var i = 0; i < FIND_SLUGS.length; i++) {
        var svc = FIND_SLUGS[i];
        if (rest === svc) { out.service = svc; return out; }          // statewide
        if (rest.indexOf(svc + "-") === 0) {                           // city page
          out.service = svc;
          out.city = rest.slice(svc.length + 1) || null;
          return out;
        }
      }
      return out;
    }

    // /<city|zip>/<service>/
    if (seg.length >= 2 && LEGACY_SLUGS.indexOf(seg[1]) !== -1) {
      out.kind    = "money";
      out.service = seg[1];
      out.city    = seg[0];
      return out;
    }

    if (seg[0] === "blog")      out.kind = "blog";
    else if (seg[0] === "find") out.kind = "find";
    return out;
  }

  function isValidEvent(t) { return EVENT_LIST.indexOf(t) !== -1; }

  return {
    EVENTS: EVENTS,
    EVENT_LIST: EVENT_LIST,
    EVENT_LABELS: EVENT_LABELS,
    LEAD_ACTIONS: LEAD_ACTIONS,
    classifyListingPath: classifyListingPath,
    isValidEvent: isValidEvent
  };
});
