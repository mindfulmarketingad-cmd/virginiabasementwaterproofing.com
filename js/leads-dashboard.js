/* ============================================================================
   leads-dashboard.js — public lead-call proof page at /dashboard/

   Fetches /api/leads (a server-only proxy that holds the real API key) and
   renders a trend chart, a stat banner, and a per-call list. Every phone
   number arrives from the server already masked; nothing here ever sees a
   full number.

   Chart is hand-built SVG, matching js/dashboard.js -- dependency-free,
   same --blue line-chart treatment used for the site analytics page.

   Day buckets use this site's own timezone (America/New_York) rather than
   the visitor's local timezone, so "Today" means the same thing no matter
   who is looking at the page.
   ============================================================================ */
(function () {
  "use strict";

  var TZ = "America/New_York";
  var BLUE = "#2d55b0";
  var GRID = "#e3e8ee";
  var MUTED = "#5a6b7b";

  var el = function (id) { return document.getElementById(id); };

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

  function num(n) { return (n || 0).toLocaleString("en-US"); }
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  // YYYY-MM-DD in the site's timezone, not the visitor's.
  function dayKey(d) {
    return d.toLocaleDateString("en-CA", { timeZone: TZ });
  }
  function shortDate(key) {
    var p = key.split("-");
    return Number(p[1]) + "/" + Number(p[2]);
  }
  function clockTime(iso) {
    return new Date(iso).toLocaleString("en-US", {
      timeZone: TZ, month: "short", day: "numeric",
      hour: "numeric", minute: "2-digit"
    });
  }
  function durationStr(sec) {
    sec = sec || 0;
    var m = Math.floor(sec / 60), s = sec % 60;
    return m + ":" + (s < 10 ? "0" : "") + s;
  }
  function isNew(iso) {
    return (Date.now() - new Date(iso).getTime()) < 48 * 3600 * 1000;
  }
  function statusLabel(s) {
    return s === "answered" ? "Answered" : s === "voicemail" ? "Voicemail" : "Missed";
  }

  // ---- chart -----------------------------------------------------------
  function trendChart(node, series) {
    if (!series.length) { node.innerHTML = '<p class="dash-empty">No data yet.</p>'; return; }

    var w = 560, h = 210, padL = 42, padR = 46, padT = 12, padB = 30;
    var plotW = w - padL - padR, plotH = h - padT - padB;
    var max = Math.max.apply(null, series.map(function (d) { return d.value; }));
    if (max < 4) max = 4;
    var step = series.length > 1 ? plotW / (series.length - 1) : 0;

    function X(i) { return padL + i * step; }
    function Y(v) { return padT + plotH - (v / max) * plotH; }

    var parts = ['<svg viewBox="0 0 ' + w + ' ' + h + '" role="img" aria-label="Calls per day">'];

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
    parts.push('<path d="' + dPath + " L" + X(series.length - 1) + "," + (padT + plotH) +
      " L" + padL + "," + (padT + plotH) + ' Z" fill="' + BLUE + '" opacity="0.1"/>');
    parts.push('<path d="' + dPath + '" fill="none" stroke="' + BLUE +
      '" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>');

    var lastI = series.length - 1, last = series[lastI];
    parts.push('<circle cx="' + X(lastI) + '" cy="' + Y(last.value) + '" r="4.5" fill="' +
      BLUE + '" stroke="#fff" stroke-width="2"/>');
    parts.push('<text x="' + (X(lastI) + 10) + '" y="' + (Y(last.value) + 4) +
      '" text-anchor="start" font-size="12" font-weight="700" fill="' + MUTED + '">' +
      num(last.value) + "</text>");

    [0, Math.floor(lastI / 2), lastI].filter(function (v, i, arr) {
      return arr.indexOf(v) === i;
    }).forEach(function (i) {
      var a = i === 0 ? "start" : (i === lastI ? "end" : "middle");
      parts.push('<text x="' + X(i) + '" y="' + (h - 9) + '" text-anchor="' + a +
        '" font-size="11" fill="' + MUTED + '">' + shortDate(series[i].key) + "</text>");
    });

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
      showTip("<b>" + shortDate(series[i].key) + "</b><br>" + num(series[i].value) + " calls",
        e.clientX, e.clientY);
    });
    hit.addEventListener("mouseleave", function () {
      cross.setAttribute("opacity", "0"); hideTip();
    });
  }

  // ---- stats -------------------------------------------------------------
  function renderStats(calls) {
    var now = new Date();
    var todayKey = dayKey(now);
    var weekAgo = Date.now() - 7 * 24 * 3600 * 1000;
    var monthKey = now.toLocaleDateString("en-CA", { timeZone: TZ }).slice(0, 7);

    var total = calls.length, today = 0, week = 0, month = 0;
    calls.forEach(function (c) {
      if (!c.start_time) return;
      var t = new Date(c.start_time);
      var k = dayKey(t);
      if (k === todayKey) today++;
      if (t.getTime() >= weekAgo) week++;
      if (k.slice(0, 7) === monthKey) month++;
    });

    el("statTotal").textContent = num(total);
    el("statMonth").textContent = num(month);
    el("statWeek").textContent = num(week);
    el("statToday").textContent = num(today);
  }

  function renderChart(calls) {
    var days = [];
    for (var i = 7; i >= 0; i--) {
      var d = new Date(Date.now() - i * 24 * 3600 * 1000);
      days.push(dayKey(d));
    }
    var byDay = {};
    days.forEach(function (k) { byDay[k] = 0; });
    calls.forEach(function (c) {
      if (!c.start_time) return;
      var k = dayKey(new Date(c.start_time));
      if (byDay.hasOwnProperty(k)) byDay[k]++;
    });
    trendChart(el("leadsChart"), days.map(function (k) { return { key: k, value: byDay[k] }; }));
  }

  // ---- call list -----------------------------------------------------------
  function tagChip(t) {
    var bg = t.background_color || "#eef2fa";
    var fg = t.color || "#1b2a6b";
    return '<span class="lead-tag" style="background:' + esc(bg) + ';color:' + esc(fg) + ';">' +
      esc(t.name) + "</span>";
  }

  function callDetail(c) {
    var rows = [
      ["Call length", durationStr(c.duration)],
      ["Forwarded to", esc(c.business_phone_number || "&mdash;")],
      ["Caller history", c.first_call ? "First-time caller" :
        "Returning caller" + (c.prior_calls ? " (" + num(c.prior_calls) + " prior call" +
          (c.prior_calls === 1 ? "" : "s") + ")" : "")],
      ["Total calls from this number", c.total_calls != null ? num(c.total_calls) : "&mdash;"],
      ["Source", esc(c.source_name || "&mdash;")],
      ["Medium", esc(c.medium || "&mdash;")],
      ["Device", esc(c.device_type || "&mdash;")],
      ["Search keywords", esc(c.keywords || "&mdash;")],
      ["Landing page", c.landing_page_url ?
        '<a href="' + esc(c.landing_page_url) + '">' + esc(c.landing_page_url) + "</a>" : "&mdash;"]
    ];

    var dl = rows.map(function (r) {
      return '<div class="lead-detail__row"><dt>' + esc(r[0]) + "</dt><dd>" + r[1] + "</dd></div>";
    }).join("");

    var tags = c.tags && c.tags.length ?
      '<div class="lead-detail__row"><dt>Tags</dt><dd>' +
      c.tags.map(tagChip).join(" ") + "</dd></div>" : "";

    var audio = c.recording ?
      '<div class="lead-detail__row"><dt>Recording</dt><dd><audio controls preload="none" ' +
      'src="' + esc(c.recording) + '"></audio></dd></div>' : "";

    var transcript = '<div class="lead-detail__row"><dt>Transcript</dt><dd>' +
      (c.transcription ? '<p class="lead-transcript">' + esc(c.transcription) + "</p>" :
        '<span class="text-muted">No transcript available</span>') + "</dd></div>";

    return '<dl class="lead-detail">' + dl + tags + audio + transcript + "</dl>";
  }

  function callRow(c) {
    var name = c.customer_name || c.customer_phone_number || "Unknown caller";
    var badges = '<span class="lead-badge lead-badge--verified">Verified</span>' +
      (isNew(c.start_time) ? '<span class="lead-badge lead-badge--new">New</span>' : "");

    return '<li class="lead-row">' +
      '<details>' +
      '<summary>' +
      '<span class="lead-row__who">' +
      '<span class="lead-row__name">' + esc(name) + "</span>" + badges +
      "</span>" +
      '<span class="lead-row__when">' + esc(clockTime(c.start_time)) + "</span>" +
      '<span class="lead-row__meta">' +
      esc(durationStr(c.duration)) +
      '<span class="lead-status lead-status--' + c.status + '">' + statusLabel(c.status) +
      "</span></span>" +
      "</summary>" +
      callDetail(c) +
      "</details></li>";
  }

  function renderList(calls) {
    var list = el("leadsList");
    if (!calls.length) {
      list.innerHTML = '<li class="dash-empty">No calls recorded yet.</li>';
      return;
    }
    list.innerHTML = calls.map(callRow).join("");
  }

  function showError(hint) {
    var banner = el("leadsError");
    banner.hidden = false;
    if (hint) banner.querySelector("p").textContent = hint;
    el("leadsUpdated").textContent = "Unavailable";
    el("leadsList").innerHTML = '<li class="dash-empty">Call data is unavailable right now.</li>';
    el("leadsChart").innerHTML = '<p class="dash-empty">No data yet.</p>';
  }

  async function load() {
    try {
      var r = await fetch("/api/leads", { headers: { Accept: "application/json" } });
      var data = await r.json();
      if (!r.ok) {
        showError(data && data.hint);
        return;
      }
      var calls = data.calls || [];
      renderStats(calls);
      renderChart(calls);
      renderList(calls);
      el("leadsUpdated").textContent = "Updated just now";
    } catch (err) {
      showError();
    }
  }

  document.addEventListener("DOMContentLoaded", load);
})();
