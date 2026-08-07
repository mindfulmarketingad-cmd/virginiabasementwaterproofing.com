/* ============================================================================
   dashboard.js — public site analytics for /dashboard/

   Reads the virginiabasementwaterproofing_dashboard table with the publishable
   key (the table's RLS allows public SELECT and holds no PII), aggregates in
   the browser, and holds a Supabase Realtime postgres_changes subscription for
   the live panel.

   Charts are hand-built SVG rather than a charting library so the page stays
   dependency-free apart from supabase-js, which is needed for Realtime anyway.

   Chart color: the site's own --blue (#2d55b0) and --accent (#c8102e). That
   pair was validated as a categorical palette before use -- CVD ΔE 20.9
   (protan) / 32.3 (tritan), normal-vision ΔE 31.6, contrast >= 3:1 on white.
   The two trend charts are deliberately SEPARATE single-series charts (small
   multiples) rather than one dual-axis chart: page views run orders of
   magnitude above lead actions, and forcing them onto one scale would either
   flatten the lead line to nothing or invent a shared scale that misleads.
   ============================================================================ */
(function () {
  "use strict";

  var SUPABASE_URL = "https://tbqigevoksabizjogvtm.supabase.co";
  var SUPABASE_KEY = "sb_publishable_aHlx0Tdu2rhOTBUp3lhkQw_Lv6Awz7a";
  var TABLE        = "virginiabasementwaterproofing_dashboard";
  var PAGE_SIZE    = 1000;   // PostgREST default ceiling per request
  var MAX_ROWS     = 60000;  // hard cap so a huge range can't hang the tab

  var BLUE   = "#2d55b0";
  var ACCENT = "#c8102e";
  var GRID   = "#e3e8ee";
  var MUTED  = "#5a6b7b";

  var A = window.VBWAnalytics;
  var el = function (id) { return document.getElementById(id); };
  var supa = null;
  var state = { days: 30, rows: [], liveCount: 0, loading: false };

  // ---- helpers -------------------------------------------------------------
  function num(n) { return (n || 0).toLocaleString("en-US"); }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }
  function dayKey(d) {
    return d.getFullYear() + "-" +
      ("0" + (d.getMonth() + 1)).slice(-2) + "-" + ("0" + d.getDate()).slice(-2);
  }
  function shortDate(key) {
    var p = key.split("-");
    return Number(p[1]) + "/" + Number(p[2]);
  }
  function clockTime(iso) {
    var d = new Date(iso);
    return ("0" + d.getHours()).slice(-2) + ":" + ("0" + d.getMinutes()).slice(-2) +
           ":" + ("0" + d.getSeconds()).slice(-2);
  }
  function label(t) { return (A && A.EVENT_LABELS[t]) || t; }

  // ---- tooltip -------------------------------------------------------------
  var tip = document.createElement("div");
  tip.className = "dash-tip";
  document.body.appendChild(tip);
  function showTip(html, x, y) {
    tip.innerHTML = html;
    tip.classList.add("is-on");
    var r = tip.getBoundingClientRect();
    var left = Math.min(Math.max(8, x - r.width / 2), window.innerWidth - r.width - 8);
    var top = y - r.height - 12;
    if (top < 8) top = y + 18;
    tip.style.left = left + "px";
    tip.style.top = top + "px";
  }
  function hideTip() { tip.classList.remove("is-on"); }

  // ---- data ----------------------------------------------------------------
  function sinceISO(days) {
    var d = new Date();
    d.setDate(d.getDate() - (days - 1));
    d.setHours(0, 0, 0, 0);
    return d.toISOString();
  }

  async function fetchRows(days) {
    var since = sinceISO(days);
    var all = [], from = 0;
    while (from < MAX_ROWS) {
      var res = await supa
        .from(TABLE)
        .select("created_at,event_type,path,session_id,visitor_id,listing_slug,listing_name,city")
        .gte("created_at", since)
        .order("created_at", { ascending: false })
        .range(from, from + PAGE_SIZE - 1);
      if (res.error) throw res.error;
      var batch = res.data || [];
      all = all.concat(batch);
      if (batch.length < PAGE_SIZE) break;
      from += PAGE_SIZE;
    }
    return all;
  }

  async function fetchLeadCount(days) {
    try {
      var res = await supa.rpc("vbw_dashboard_lead_count", { days: days });
      if (res.error) return null; // RPC not installed yet -- hide the card
      return typeof res.data === "number" ? res.data : null;
    } catch (e) { return null; }
  }

  // ---- aggregation ---------------------------------------------------------
  function aggregate(rows, days) {
    var leadSet = {};
    (A ? A.LEAD_ACTIONS : []).forEach(function (t) { leadSet[t] = true; });

    var sessions = {}, visitors = {}, byType = {}, byDay = {}, byBiz = {};

    // Seed every day in range so a quiet day plots as 0 rather than vanishing.
    for (var i = days - 1; i >= 0; i--) {
      var d = new Date(); d.setDate(d.getDate() - i);
      byDay[dayKey(d)] = { views: 0, leads: 0 };
    }

    rows.forEach(function (r) {
      var t = r.event_type;
      byType[t] = (byType[t] || 0) + 1;
      if (r.session_id) sessions[r.session_id] = 1;
      if (r.visitor_id) visitors[r.visitor_id] = 1;

      var k = dayKey(new Date(r.created_at));
      if (!byDay[k]) byDay[k] = { views: 0, leads: 0 };
      if (t === "pageview" || t === "listing_view") byDay[k].views++;
      if (leadSet[t]) byDay[k].leads++;

      if (r.listing_slug) {
        var b = byBiz[r.listing_slug];
        if (!b) {
          b = byBiz[r.listing_slug] = {
            slug: r.listing_slug, name: r.listing_name || r.listing_slug,
            city: r.city || "", views: 0, quote: 0, review: 0, claim: 0,
            leadActions: 0, total: 0
          };
        }
        if (r.listing_name && b.name === b.slug) b.name = r.listing_name;
        if (r.city && !b.city) b.city = r.city;
        if (t === "listing_view") b.views++;
        else if (t === "quote_click") b.quote++;
        else if (t === "review_click") b.review++;
        else if (t === "claim_click") b.claim++;
        if (leadSet[t]) b.leadActions++;
        b.total++;
      }
    });

    var leadActions = 0;
    Object.keys(byType).forEach(function (t) { if (leadSet[t]) leadActions += byType[t]; });

    var days_ = Object.keys(byDay).sort();

    return {
      sessions: Object.keys(sessions).length,
      visitors: Object.keys(visitors).length,
      leadActions: leadActions,
      searches: byType.search || 0,
      impressions: (byType.pageview || 0) + (byType.listing_view || 0),
      listingViews: byType.listing_view || 0,
      byType: byType,
      trend: days_.map(function (k) {
        return { key: k, views: byDay[k].views, leads: byDay[k].leads };
      }),
      businesses: Object.keys(byBiz).map(function (k) { return byBiz[k]; })
        .sort(function (a, b) { return b.total - a.total; })
    };
  }

  // ---- charts --------------------------------------------------------------
  // Horizontal bar. ONE series, so every bar takes the SAME hue -- a
  // darker-where-bigger ramp would double-encode length as color.
  function barChart(node, items) {
    if (!items.length) { node.innerHTML = '<p class="dash-empty">No activity in this range yet.</p>'; return; }

    var rowH = 34, barH = 18, padL = 132, padR = 54, padT = 6;
    var h = items.length * rowH + padT;
    var w = 560;
    var plotW = w - padL - padR;
    var max = Math.max.apply(null, items.map(function (d) { return d.value; })) || 1;

    var parts = ['<svg viewBox="0 0 ' + w + ' ' + h + '" role="img" ' +
      'aria-label="Visitor actions by type">'];

    items.forEach(function (d, i) {
      var y = padT + i * rowH;
      var bw = Math.max(d.value > 0 ? 2 : 0, Math.round((d.value / max) * plotW));
      var cy = y + rowH / 2;
      // Category label in muted ink -- text never wears the series color.
      parts.push('<text x="' + (padL - 12) + '" y="' + (cy + 4) + '" text-anchor="end" ' +
        'font-size="12.5" fill="' + MUTED + '">' + esc(d.label) + "</text>");
      if (bw > 0) {
        // 4px rounded data-end, square at the baseline.
        parts.push('<path d="' + roundedRightBar(padL, cy - barH / 2, bw, barH, 4) +
          '" fill="' + BLUE + '"/>');
      }
      // Value sits OUTSIDE the bar end so it can never be clipped by a short bar.
      parts.push('<text x="' + (padL + bw + 9) + '" y="' + (cy + 4) + '" font-size="12.5" ' +
        'font-weight="700" fill="' + MUTED + '" style="font-variant-numeric:tabular-nums">' +
        num(d.value) + "</text>");
      // Hit area spans the whole row so the target is far bigger than the mark.
      parts.push('<rect x="0" y="' + y + '" width="' + w + '" height="' + rowH +
        '" fill="transparent" data-i="' + i + '"/>');
    });
    parts.push("</svg>");
    node.innerHTML = parts.join("");

    var svg = node.querySelector("svg");
    svg.addEventListener("mousemove", function (e) {
      var t = e.target.getAttribute && e.target.getAttribute("data-i");
      if (t === null || t === undefined) { hideTip(); return; }
      var d = items[+t];
      showTip("<b>" + esc(d.label) + "</b><br>" + num(d.value) + " events", e.clientX, e.clientY);
    });
    svg.addEventListener("mouseleave", hideTip);
  }

  function roundedRightBar(x, y, w, h, r) {
    r = Math.min(r, w, h / 2);
    return "M" + x + "," + y +
      "H" + (x + w - r) + "a" + r + "," + r + " 0 0 1 " + r + "," + r +
      "V" + (y + h - r) + "a" + r + "," + r + " 0 0 1 " + (-r) + "," + r +
      "H" + x + "Z";
  }

  // Single-series line chart. No legend (the card title names the series);
  // only the final point is direct-labelled.
  function lineChart(node, series, color, seriesLabel) {
    if (!series.length) { node.innerHTML = '<p class="dash-empty">No data yet.</p>'; return; }

    // padR leaves room for the endpoint marker AND its value label, which sits
    // to the RIGHT of the last point -- nothing is plotted there, so the label
    // can never collide with the line or the area wash.
    var w = 560, h = 210, padL = 42, padR = 46, padT = 12, padB = 30;
    var plotW = w - padL - padR, plotH = h - padT - padB;
    var max = Math.max.apply(null, series.map(function (d) { return d.value; }));
    if (max < 4) max = 4;                       // keep a sane scale when quiet
    var step = series.length > 1 ? plotW / (series.length - 1) : 0;

    function X(i) { return padL + i * step; }
    function Y(v) { return padT + plotH - (v / max) * plotH; }

    var parts = ['<svg viewBox="0 0 ' + w + ' ' + h + '" role="img" aria-label="' +
      esc(seriesLabel) + ' per day">'];

    // Recessive solid hairline grid -- never dashed.
    for (var g = 0; g <= 3; g++) {
      var gv = (max / 3) * g, gy = Y(gv);
      parts.push('<line x1="' + padL + '" y1="' + gy + '" x2="' + (w - padR) + '" y2="' + gy +
        '" stroke="' + GRID + '" stroke-width="1"/>');
      parts.push('<text x="' + (padL - 8) + '" y="' + (gy + 4) + '" text-anchor="end" ' +
        'font-size="11" fill="' + MUTED + '" style="font-variant-numeric:tabular-nums">' +
        Math.round(gv) + "</text>");
    }

    var dPath = series.map(function (d, i) {
      return (i ? "L" : "M") + X(i).toFixed(1) + "," + Y(d.value).toFixed(1);
    }).join(" ");
    // Area wash at ~10% opacity, never a saturated block.
    parts.push('<path d="' + dPath + " L" + X(series.length - 1) + "," + (padT + plotH) +
      " L" + padL + "," + (padT + plotH) + ' Z" fill="' + color + '" opacity="0.1"/>');
    parts.push('<path d="' + dPath + '" fill="none" stroke="' + color +
      '" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>');

    // Endpoint marker: >=8px, with a 2px surface ring.
    var lastI = series.length - 1, last = series[lastI];
    parts.push('<circle cx="' + X(lastI) + '" cy="' + Y(last.value) + '" r="4.5" fill="' +
      color + '" stroke="#fff" stroke-width="2"/>');

    // Selective direct label: the endpoint only, placed in the right-hand
    // padding so it clears the line, the area wash and the marker.
    parts.push('<text x="' + (X(lastI) + 10) + '" y="' + (Y(last.value) + 4) +
      '" text-anchor="start" font-size="12" font-weight="700" fill="' + MUTED + '">' +
      num(last.value) + "</text>");

    // x labels: first, middle, last only -- never one per point.
    [0, Math.floor(lastI / 2), lastI].filter(function (v, i, arr) {
      return arr.indexOf(v) === i;
    }).forEach(function (i) {
      var a = i === 0 ? "start" : (i === lastI ? "end" : "middle");
      parts.push('<text x="' + X(i) + '" y="' + (h - 9) + '" text-anchor="' + a +
        '" font-size="11" fill="' + MUTED + '">' + shortDate(series[i].key) + "</text>");
    });

    // Crosshair + hover band.
    parts.push('<line class="dash-cross" x1="0" y1="' + padT + '" x2="0" y2="' + (padT + plotH) +
      '" stroke="' + MUTED + '" stroke-width="1" opacity="0"/>');
    parts.push('<rect x="' + padL + '" y="' + padT + '" width="' + plotW + '" height="' + plotH +
      '" fill="transparent" class="dash-hit"/>');
    parts.push("</svg>");
    node.innerHTML = parts.join("");

    var svg = node.querySelector("svg");
    var cross = svg.querySelector(".dash-cross");
    var hit = svg.querySelector(".dash-hit");
    hit.addEventListener("mousemove", function (e) {
      var box = svg.getBoundingClientRect();
      var rel = (e.clientX - box.left) / box.width * w;
      var i = step ? Math.round((rel - padL) / step) : 0;
      i = Math.max(0, Math.min(lastI, i));
      cross.setAttribute("x1", X(i)); cross.setAttribute("x2", X(i));
      cross.setAttribute("opacity", "0.35");
      showTip("<b>" + shortDate(series[i].key) + "</b><br>" + num(series[i].value) + " " +
        esc(seriesLabel.toLowerCase()), e.clientX, e.clientY);
    });
    hit.addEventListener("mouseleave", function () {
      cross.setAttribute("opacity", "0"); hideTip();
    });
  }

  // ---- render --------------------------------------------------------------
  function renderStats(agg, leadCount) {
    el("statSessions").textContent  = num(agg.sessions);
    el("statVisitors").textContent  = num(agg.visitors);
    el("statLeadActions").textContent = num(agg.leadActions);
    el("statSearches").textContent  = num(agg.searches);
    el("statImpressions").textContent = num(agg.impressions);

    var card = el("statLeadsCard");
    if (leadCount === null) {
      card.hidden = true; // RPC not installed; don't show an empty promise
    } else {
      card.hidden = false;
      el("statLeads").textContent = num(leadCount);
    }
  }

  function renderBreakdown(agg) {
    var items = (A ? A.EVENT_LIST : Object.keys(agg.byType))
      .map(function (t) { return { label: label(t), value: agg.byType[t] || 0, type: t }; })
      .filter(function (d) { return d.value > 0; })
      .sort(function (a, b) { return b.value - a.value; });
    barChart(el("chartActions"), items);
  }

  function renderTrends(agg) {
    lineChart(el("chartViews"),
      agg.trend.map(function (d) { return { key: d.key, value: d.views }; }),
      BLUE, "Page Views");
    lineChart(el("chartLeads"),
      agg.trend.map(function (d) { return { key: d.key, value: d.leads }; }),
      ACCENT, "Lead Actions");
  }

  function renderBusinesses(agg) {
    var body = el("bizBody");
    if (!agg.businesses.length) {
      body.innerHTML = '<tr><td colspan="7" class="dash-empty">' +
        "No listing activity in this range yet.</td></tr>";
      el("bizCount").textContent = "";
      return;
    }
    el("bizCount").textContent = agg.businesses.length + " businesses with activity";
    body.innerHTML = agg.businesses.map(function (b) {
      return "<tr>" +
        '<td class="dir-name"><a href="/partners/' + esc(b.slug) + '/">' + esc(b.name) + "</a></td>" +
        "<td>" + (esc(b.city) || '<span class="text-muted">&mdash;</span>') + "</td>" +
        '<td class="num">' + num(b.views) + "</td>" +
        '<td class="num">' + num(b.quote) + "</td>" +
        '<td class="num">' + num(b.review) + "</td>" +
        '<td class="num">' + num(b.leadActions) + "</td>" +
        '<td class="num"><strong>' + num(b.total) + "</strong></td>" +
        "</tr>";
    }).join("");
  }

  // ---- live panel ----------------------------------------------------------
  function setLive(stateName, text) {
    var d = el("liveDot");
    d.setAttribute("data-state", stateName);
    d.lastChild.nodeValue = " " + text;
  }

  function pushLive(row) {
    state.liveCount++;
    el("liveCount").textContent = num(state.liveCount);
    var feed = el("liveFeed");
    if (feed.querySelector(".dash-empty")) feed.innerHTML = "";
    var li = document.createElement("li");
    li.innerHTML =
      '<span class="dash-feed__type">' + esc(label(row.event_type)) + "</span>" +
      '<span class="dash-feed__path">' + esc(row.listing_name || row.path || "") + "</span>" +
      '<span class="dash-feed__time">' + clockTime(row.created_at || new Date().toISOString()) + "</span>";
    feed.insertBefore(li, feed.firstChild);
    while (feed.children.length > 40) feed.removeChild(feed.lastChild);
  }

  function subscribeLive() {
    try {
      supa.channel("vbw-dashboard-live")
        .on("postgres_changes",
            { event: "INSERT", schema: "public", table: TABLE },
            function (payload) { pushLive(payload["new"] || {}); })
        .subscribe(function (status) {
          if (status === "SUBSCRIBED")            setLive("live", "Live");
          else if (status === "CHANNEL_ERROR")    setLive("error", "Live feed unavailable");
          else if (status === "TIMED_OUT")        setLive("error", "Live feed timed out");
        });
    } catch (e) {
      setLive("error", "Live feed unavailable");
    }
  }

  // ---- load ----------------------------------------------------------------
  async function load() {
    if (state.loading) return;
    state.loading = true;
    el("dashUpdated").textContent = "Loading…";
    try {
      var results = await Promise.all([fetchRows(state.days), fetchLeadCount(state.days)]);
      state.rows = results[0];
      var agg = aggregate(state.rows, state.days);
      renderStats(agg, results[1]);
      renderBreakdown(agg);
      renderTrends(agg);
      renderBusinesses(agg);
      el("dashSetup").hidden = state.rows.length > 0;
      el("dashUpdated").textContent = "Updated " +
        new Date().toLocaleTimeString("en-US", { hour: "numeric", minute: "2-digit" });
    } catch (err) {
      el("dashUpdated").textContent = "Could not load analytics";
      el("dashSetup").hidden = false;
      if (window.console) console.error("[dashboard]", err);
    }
    state.loading = false;
  }

  // ---- boot ----------------------------------------------------------------
  function init() {
    if (!window.supabase || !window.supabase.createClient) {
      el("dashUpdated").textContent = "Analytics library failed to load";
      el("dashSetup").hidden = false;
      return;
    }
    supa = window.supabase.createClient(SUPABASE_URL, SUPABASE_KEY);

    Array.prototype.forEach.call(document.querySelectorAll(".dash-range"), function (btn) {
      btn.addEventListener("click", function () {
        Array.prototype.forEach.call(document.querySelectorAll(".dash-range"), function (b) {
          b.setAttribute("aria-pressed", b === btn ? "true" : "false");
        });
        state.days = Number(btn.getAttribute("data-days")) || 30;
        load();
      });
    });

    load();
    subscribeLive();
    // Re-aggregate periodically so the cards and charts follow the live feed.
    setInterval(function () { if (!document.hidden) load(); }, 60000);
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
