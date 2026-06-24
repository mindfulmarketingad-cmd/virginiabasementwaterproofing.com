/* ============================================================================
   map-local.js — Google Maps provider finder for city / region / service pages.

   Reads window.MAP_CONFIG (must be set BEFORE this script loads):
     { city:   "Virginia Beach" }         — city page (filter to one city)
     { cities: ["VB","Norfolk",...] }     — region page (filter to list of cities)
     { cat:    "waterproofing" }          — service pre-filter (stackable)
     { zip:    "23320" }                  — pre-center on ZIP (no location filter)

   The same static data files as the homepage map are used — zero extra API cost.
   ============================================================================ */
(function () {
  "use strict";

  var config = window.MAP_CONFIG || {};
  var VA_CENTER = { lat: 37.62, lng: -79.2 };
  var VA_ZOOM = 7;

  var els = {
    map:        document.getElementById("vaMap"),
    loading:    document.getElementById("mapLoading"),
    results:    document.getElementById("resultsList"),
    count:      document.getElementById("resultCount"),
    filter:     document.getElementById("svcFilter"),
    zipForm:    document.getElementById("zipSearch"),
    zipInput:   document.getElementById("zipInput"),
    toggles:    document.querySelectorAll(".map-toggle"),
    detail:     document.getElementById("mapDetail"),
    detailBody: document.getElementById("mapDetailBody"),
    detailBack: document.getElementById("mapDetailBack")
  };
  if (!els.map) return;

  var state = {
    map:      null,
    info:     null,
    markers:  [],
    clusterer:null,
    providers:[],
    centroids:{},
    categories:[],
    activeCat: config.cat || "",
    activeZip: "",
    cityLayer: null,
    zipLayer:  null,
    layersLoaded: { city: false, zip: false }
  };

  // ---- helpers ---------------------------------------------------------------
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;" }[c];
    });
  }

  var CAT_NAMES = {
    "waterproofing": "Basement Waterproofing",
    "crawl-space":   "Crawl Space Encapsulation",
    "foundation":    "Foundation Repair",
    "plumbing":      "Sump Pump Installation",
    "drainage":      "French Drain / Drainage",
    "water-damage":  "Water Damage Restoration",
    "general":       "General Contractor",
    "mold":          "Mold Remediation"
  };

  function stars(r) {
    if (r == null) return "";
    var full = Math.round(r);
    return "★★★★★".slice(0, full) + "☆☆☆☆☆".slice(0, 5 - full);
  }
  function dist(a, b, c, d) {
    var x = (c - a) * 111, y = (d - b) * 85;
    return Math.sqrt(x * x + y * y);
  }

  function inScope(p) {
    if (config.city && p.city !== config.city) return false;
    if (config.cities && config.cities.length && config.cities.indexOf(p.city) === -1) return false;
    return true;
  }

  function matches(p) {
    if (!inScope(p)) return false;
    if (state.activeCat && p.cats.indexOf(state.activeCat) === -1) return false;
    if (state.activeZip) {
      var ctr = state.centroids[state.activeZip];
      if (p.zip === state.activeZip) return true;
      if (ctr && dist(p.lat, p.lng, ctr[0], ctr[1]) <= 20) return true;
      return false;
    }
    return true;
  }

  // ---- detail panel (Google Maps-style) -------------------------------------
  function openDetail(p) {
    if (!els.detail) return;
    var initials = p.name.split(/\s+/).slice(0, 2).map(function (w) { return w[0] || ""; }).join("").toUpperCase();
    var cats = (p.cats || []).map(function (k) {
      return '<span class="map-detail__cat">' + esc(CAT_NAMES[k] || k) + "</span>";
    }).join("");
    var rateHtml = p.rating != null
      ? '<div class="map-detail__rating">' + stars(p.rating) +
        ' <strong>' + p.rating + '</strong>' +
        (p.reviews != null ? ' <span class="map-detail__rev">(' + p.reviews + ' reviews)</span>' : '') +
        "</div>" : "";
    var loc = esc(p.city) + ", VA" + (p.zip ? " " + esc(p.zip) : "");
    var countyLine = p.county
      ? '<div class="map-detail__section"><span class="map-detail__section-label">Service Area</span>' + esc(p.county) + "</div>"
      : "";
    var svcNames = (p.cats || []).map(function (k) { return CAT_NAMES[k] || k; }).join(", ");

    els.detailBody.innerHTML =
      '<div class="map-detail__banner"><div class="map-detail__avatar">' + initials + "</div></div>" +
      '<div class="map-detail__info">' +
        '<h2 class="map-detail__name">' + esc(p.name) + "</h2>" +
        rateHtml +
        (cats ? '<div class="map-detail__cats">' + cats + "</div>" : "") +
        '<div class="map-detail__loc">' + loc + "</div>" +
      "</div>" +
      '<div class="map-detail__divider"></div>' +
      '<div class="map-detail__actions">' +
        '<a href="/get-a-quote/?provider=' + esc(p.slug) + '" class="map-detail__primary-btn">Submit Job Request</a>' +
        '<a href="/partners/' + esc(p.slug) + '/" class="map-detail__secondary-btn">View Full Profile &rarr;</a>' +
      "</div>" +
      '<div class="map-detail__links">' +
        '<a href="/claim-listing/?provider=' + esc(p.slug) + '">Claim this listing</a>' +
      "</div>" +
      '<div class="map-detail__divider"></div>' +
      countyLine +
      '<div class="map-detail__section"><span class="map-detail__section-label">Location</span>' + loc + "</div>" +
      (svcNames ? '<div class="map-detail__section"><span class="map-detail__section-label">Listed Services</span>' + esc(svcNames) + "</div>" : "");

    els.detail.classList.add("is-open");
    els.detail.parentElement.classList.add("detail-open");
    els.detail.scrollTop = 0;
  }

  function closeDetail() {
    if (!els.detail) return;
    els.detail.classList.remove("is-open");
    els.detail.parentElement.classList.remove("detail-open");
  }

  // ---- info window content ---------------------------------------------------
  function popupHTML(p) {
    var rate = p.rating != null
      ? '<div class="gm-pop__rate">' + stars(p.rating) + " " + p.rating +
        (p.reviews != null ? ' <span>(' + p.reviews + ")</span>" : "") + "</div>"
      : "";
    var loc = esc(p.city) + (p.zip ? ", VA " + esc(p.zip) : ", VA");
    return '<div class="gm-pop"><strong>' + esc(p.name) + "</strong>" + rate +
      '<div class="gm-pop__loc">' + loc + "</div>" +
      '<a class="gm-pop__btn" href="/partners/' + esc(p.slug) + '/">View Profile</a>' +
      '<a class="gm-pop__btn gm-pop__btn--alt" href="/get-a-quote/">Submit Job Request</a></div>';
  }

  // ---- results list ----------------------------------------------------------
  function renderResults(list) {
    var n = list.length;
    var scopeLabel = config.city ? " in " + esc(config.city)
      : (config.cities && config.cities.length ? " in this region" : " across Virginia");
    var label = state.activeCat
      ? (catLabel(state.activeCat) + " providers")
      : "waterproofing &amp; restoration providers";
    els.count.textContent = "Showing " + n + " " + label.replace("&amp;","&") +
      (state.activeZip ? " near " + state.activeZip : scopeLabel.replace("&amp;","&"));

    if (!n) {
      els.results.innerHTML = '<li class="map-result__empty">No providers match this filter.' +
        (state.activeZip ? " Try a different ZIP or clear the search." : "") + "</li>";
      return;
    }
    var html = "";
    list.slice(0, 300).forEach(function (p) {
      var rate = p.rating != null
        ? '<div class="map-result__rate">' + stars(p.rating) + " " + p.rating +
          (p.reviews != null ? " <span>(" + p.reviews + ")</span>" : "") + "</div>"
        : "";
      html += '<li class="map-result" data-i="' + p._idx + '">' +
        "<h4>" + esc(p.name) + "</h4>" + rate +
        '<div class="map-result__loc">' + esc(p.city) + (p.zip ? ", VA " + esc(p.zip) : ", VA") + "</div>" +
        '<div class="map-result__actions">' +
          '<a class="map-act--primary" href="/get-a-quote/?provider=' + esc(p.slug) + '" onclick="event.stopPropagation()">Submit Job Request</a>' +
          '<a class="map-act--ghost" href="/claim-listing/?provider=' + esc(p.slug) + '" onclick="event.stopPropagation()">Claim Listing</a>' +
        "</div></li>";
    });
    els.results.innerHTML = html;
  }

  function catLabel(key) {
    for (var i = 0; i < state.categories.length; i++)
      if (state.categories[i].key === key) return state.categories[i].label;
    return "";
  }

  // ---- apply filter ----------------------------------------------------------
  function applyFilter() {
    closeDetail();
    var visible = [], visMarkers = [];
    state.markers.forEach(function (m) {
      var show = matches(m.provider);
      if (show) { visible.push(m.provider); visMarkers.push(m.marker); }
      if (!state.clusterer) m.marker.setMap(show ? state.map : null);
    });
    if (state.clusterer) {
      state.clusterer.clearMarkers();
      state.clusterer.addMarkers(visMarkers);
    }
    visible.sort(function (a, b) {
      return (b.rating || 0) - (a.rating || 0) || (b.reviews || 0) - (a.reviews || 0);
    });
    renderResults(visible);
  }

  // ---- border layers (lazy) --------------------------------------------------
  function toggleLayer(kind, btn) {
    var on = !btn.classList.contains("is-on");
    btn.classList.toggle("is-on", on);
    if (kind === "city") {
      if (!state.cityLayer) {
        state.cityLayer = new google.maps.Data();
        state.cityLayer.setStyle({ fillOpacity: 0, strokeColor: "#1b2a6b", strokeWeight: 1.1, clickable: false });
      }
      if (on) {
        if (!state.layersLoaded.city) { state.cityLayer.loadGeoJson("/data/va-cities.geojson"); state.layersLoaded.city = true; }
        state.cityLayer.setMap(state.map);
      } else {
        state.cityLayer.setMap(null);
      }
    } else {
      if (!state.zipLayer) {
        state.zipLayer = new google.maps.Data();
        state.zipLayer.setStyle({ fillOpacity: 0, strokeColor: "#2d55b0", strokeWeight: 0.6, clickable: false });
      }
      if (on) {
        if (!state.layersLoaded.zip) {
          btn.textContent = "";
          var dot = document.createElement("span"); dot.className = "dot";
          btn.appendChild(dot); btn.appendChild(document.createTextNode(" Loading…"));
          state.zipLayer.loadGeoJson("/data/va-zips.geojson", null, function () {
            btn.innerHTML = '<span class="dot"></span> ZIP borders';
          });
          state.layersLoaded.zip = true;
        }
        state.zipLayer.setMap(state.map);
      } else {
        state.zipLayer.setMap(null);
      }
    }
  }

  // ---- build map -------------------------------------------------------------
  function buildMap(MapsLib, MarkerLib) {
    // Compute initial center from in-scope providers
    var scopeProviders = state.providers.filter(inScope);
    var center = VA_CENTER, zoom = VA_ZOOM;
    if (scopeProviders.length) {
      var latSum = 0, lngSum = 0;
      scopeProviders.forEach(function (p) { latSum += p.lat; lngSum += p.lng; });
      center = { lat: latSum / scopeProviders.length, lng: lngSum / scopeProviders.length };
      zoom = config.city ? 12 : 9;
    }
    if (config.zip && state.centroids[config.zip]) {
      center = { lat: state.centroids[config.zip][0], lng: state.centroids[config.zip][1] };
      zoom = 11;
    }

    state.map = new MapsLib.Map(els.map, {
      center: center,
      zoom: zoom,
      mapTypeControl: true,
      mapTypeControlOptions: {
        style: google.maps.MapTypeControlStyle.DEFAULT,
        mapTypeIds: ["roadmap", "satellite", "hybrid", "terrain"]
      },
      streetViewControl: false,
      fullscreenControl: true,
      zoomControl: true,
      gestureHandling: "greedy",
      clickableIcons: false
    });
    state.info = new MapsLib.InfoWindow();
    els.loading.classList.add("is-hidden");

    // blue outline around the state of Virginia
    var vaBorder = new google.maps.Data();
    vaBorder.setStyle({ fillOpacity: 0, strokeColor: "#2d55b0", strokeWeight: 2.5, clickable: false });
    vaBorder.loadGeoJson("/data/va-state.geojson");
    vaBorder.setMap(state.map);

    state.providers.forEach(function (p, idx) {
      p._idx = idx;
      var marker = new MarkerLib.Marker({ position: { lat: p.lat, lng: p.lng }, title: p.name });
      marker.addListener("click", function () {
        state.info.setContent(popupHTML(p));
        state.info.open(state.map, marker);
        highlight(idx);
      });
      state.markers.push({ marker: marker, provider: p });
    });

    if (window.markerClusterer && window.markerClusterer.MarkerClusterer) {
      state.clusterer = new markerClusterer.MarkerClusterer({ map: state.map, markers: [] });
    }

    applyFilter();
  }

  function highlight(idx) {
    var items = els.results.querySelectorAll(".map-result");
    items.forEach(function (li) {
      li.classList.toggle("is-active", li.getAttribute("data-i") == idx);
      if (li.getAttribute("data-i") == idx) li.scrollIntoView({ block: "nearest" });
    });
  }

  // ---- wire UI ---------------------------------------------------------------
  function wireUI() {
    // filter dropdown
    var opts = '<option value="">All Services</option>';
    state.categories.forEach(function (c) {
      var sel = state.activeCat === c.key ? ' selected' : '';
      opts += '<option value="' + c.key + '"' + sel + '>' + esc(c.label) + " (" + c.count + ")</option>";
    });
    els.filter.innerHTML = opts;
    els.filter.addEventListener("change", function () {
      state.activeCat = els.filter.value;
      applyFilter();
    });

    // zip search
    if (els.zipForm) {
      els.zipForm.addEventListener("submit", function (e) {
        e.preventDefault();
        var z = (els.zipInput.value || "").trim().slice(0, 5);
        if (z && !/^\d{5}$/.test(z)) { els.zipInput.focus(); return; }
        state.activeZip = z;
        if (z && state.centroids[z]) {
          state.map.setCenter({ lat: state.centroids[z][0], lng: state.centroids[z][1] });
          state.map.setZoom(11);
        } else if (!z && state.map) {
          // Reset to scope center
          var scopeProviders = state.providers.filter(inScope);
          if (scopeProviders.length) {
            var latSum = 0, lngSum = 0;
            scopeProviders.forEach(function (p) { latSum += p.lat; lngSum += p.lng; });
            state.map.setCenter({ lat: latSum / scopeProviders.length, lng: lngSum / scopeProviders.length });
            state.map.setZoom(config.city ? 12 : 9);
          }
        }
        applyFilter();
      });
    }

    // results click — open detail panel
    els.results.addEventListener("click", function (e) {
      if (e.target.closest("a")) return; // let action links navigate normally
      var li = e.target.closest(".map-result");
      if (!li) return;
      var idx = +li.getAttribute("data-i");
      var m = state.markers[idx];
      if (!m) return;
      state.map.panTo(m.marker.getPosition());
      if (state.map.getZoom() < 12) state.map.setZoom(13);
      highlight(idx);
      openDetail(m.provider);
    });

    // back button
    if (els.detailBack) {
      els.detailBack.addEventListener("click", closeDetail);
    }

    // border toggles
    els.toggles.forEach(function (btn) {
      btn.addEventListener("click", function () { toggleLayer(btn.getAttribute("data-layer"), btn); });
    });
  }

  // ---- boot ------------------------------------------------------------------
  function fail(msg) {
    if (els.loading) { els.loading.textContent = msg; els.loading.classList.remove("is-hidden"); }
  }

  Promise.all([
    fetch("/data/va-providers.json").then(function (r) { return r.json(); }),
    fetch("/data/map-categories.json").then(function (r) { return r.json(); }),
    fetch("/data/va-zip-centroids.json").then(function (r) { return r.json(); })
  ]).then(function (res) {
    state.providers   = res[0];
    state.categories  = res[1];
    state.centroids   = res[2];
    wireUI();
    return Promise.all([
      google.maps.importLibrary("maps"),
      google.maps.importLibrary("marker")
    ]);
  }).then(function (libs) {
    buildMap(libs[0], libs[1]);
  }).catch(function (err) {
    fail("Map could not load. Please refresh the page.");
    if (window.console) console.error(err);
  });
})();
