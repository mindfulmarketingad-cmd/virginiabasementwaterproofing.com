/* ============================================================================
   Homepage map hero — Virginia waterproofing services finder.

   Base map: Leaflet + free CARTO/OpenStreetMap raster tiles (NO API key, NO
   billing). Provider data is PRE-FETCHED and static (data/va-providers.json).
   There are ZERO paid map API calls — tiles are served free by CARTO/OSM and
   the optional satellite layer by Esri. Business phone numbers are never shown.
   ============================================================================ */
(function () {
  "use strict";

  var VA_CENTER = [37.62, -79.2];
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
  if (!els.map) return; // not on this page

  var state = {
    map: null,
    markers: [],        // { marker, provider }
    clusterer: null,
    providers: [],
    centroids: {},
    categories: [],
    activeCat: "",      // "" = all
    activeZip: "",      // "" = none
    cityLayer: null,
    zipLayer: null,
    layersLoaded: { city: false, zip: false }
  };

  // ---- helpers -------------------------------------------------------------
  function esc(s) {
    return String(s == null ? "" : s).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
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

  // navy teardrop pin (inline SVG — no external image, avoids broken icon paths)
  var PIN = L.divIcon({
    className: "vbw-pin",
    html: '<svg width="26" height="34" viewBox="0 0 26 34" xmlns="http://www.w3.org/2000/svg">' +
          '<path d="M13 0C5.8 0 0 5.8 0 13c0 9.6 13 21 13 21s13-11.4 13-21C26 5.8 20.2 0 13 0z" fill="#1b2a6b"/>' +
          '<circle cx="13" cy="13" r="5" fill="#fff"/></svg>',
    iconSize: [26, 34],
    iconAnchor: [13, 34],
    popupAnchor: [0, -32]
  });

  function stars(r) {
    if (r == null) return "";
    var full = Math.round(r);
    return "★★★★★".slice(0, full) + "☆☆☆☆☆".slice(0, 5 - full);
  }
  function dist(a, b, c, d) { // rough km between two lat/lng
    var x = (c - a) * 111, y = (d - b) * 85;
    return Math.sqrt(x * x + y * y);
  }
  function matches(p) {
    if (state.activeCat && p.cats.indexOf(state.activeCat) === -1) return false;
    if (state.activeZip) {
      var ctr = state.centroids[state.activeZip];
      if (p.zip === state.activeZip) return true;
      if (ctr && dist(p.lat, p.lng, ctr[0], ctr[1]) <= 20) return true;
      return false;
    }
    return true;
  }

  // ---- detail panel (Google Maps-style) ------------------------------------
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
        '<a href="/get-a-quote/?provider=' + esc(p.slug) + '" class="map-detail__primary-btn">Instant Free Quote</a>' +
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

  // ---- popup content (NO phone numbers) ------------------------------------
  function popupHTML(p) {
    var rate = p.rating != null
      ? '<div class="gm-pop__rate">' + stars(p.rating) + " " + p.rating +
        (p.reviews != null ? ' <span>(' + p.reviews + ")</span>" : "") + "</div>"
      : "";
    var loc = esc(p.city) + (p.zip ? ", VA " + esc(p.zip) : ", VA");
    return '<div class="gm-pop"><strong>' + esc(p.name) + "</strong>" + rate +
      '<div class="gm-pop__loc">' + loc + "</div>" +
      '<a class="gm-pop__btn" href="/partners/' + esc(p.slug) + '/">View Profile</a>' +
      '<a class="gm-pop__btn gm-pop__btn--alt" href="/get-a-quote/">Instant Free Quote</a></div>';
  }

  // ---- results list --------------------------------------------------------
  function renderResults(list) {
    var n = list.length;
    var label = state.activeCat
      ? (catLabel(state.activeCat) + " providers")
      : "waterproofing & restoration providers";
    els.count.textContent = "Showing " + n + " " + label +
      (state.activeZip ? " near " + state.activeZip : " across Virginia");

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
          '<a class="map-act--primary" href="/get-a-quote/?provider=' + esc(p.slug) + '" onclick="event.stopPropagation()">Instant Free Quote</a>' +
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

  // ---- apply current filter to markers + list (closes detail if open) -----
  function applyFilter() {
    closeDetail();
    var visible = [];
    var visMarkers = [];
    state.markers.forEach(function (m) {
      var show = matches(m.provider);
      if (show) { visible.push(m.provider); visMarkers.push(m.marker); }
    });
    if (state.clusterer) {
      state.clusterer.clearLayers();
      state.clusterer.addLayers(visMarkers);
    }
    // sort list: rating desc then reviews desc
    visible.sort(function (a, b) {
      return (b.rating || 0) - (a.rating || 0) || (b.reviews || 0) - (a.reviews || 0);
    });
    renderResults(visible);
  }

  // ---- border layers (lazy) ------------------------------------------------
  function toggleLayer(kind, btn) {
    var on = !btn.classList.contains("is-on");
    btn.classList.toggle("is-on", on);

    if (kind === "city") {
      if (on) {
        if (!state.layersLoaded.city) {
          state.layersLoaded.city = true;
          fetch("/data/va-cities.geojson").then(function (r) { return r.json(); }).then(function (geo) {
            state.cityLayer = L.geoJSON(geo, {
              style: { fill: false, color: "#1b2a6b", weight: 1.1, interactive: false }
            });
            if (btn.classList.contains("is-on")) state.cityLayer.addTo(state.map);
          });
        } else if (state.cityLayer) {
          state.cityLayer.addTo(state.map);
        }
      } else if (state.cityLayer) {
        state.map.removeLayer(state.cityLayer);
      }
    } else {
      if (on) {
        if (!state.layersLoaded.zip) {
          state.layersLoaded.zip = true;
          btn.innerHTML = '<span class="dot"></span> Loading…';
          fetch("/data/va-zips.geojson").then(function (r) { return r.json(); }).then(function (geo) {
            state.zipLayer = L.geoJSON(geo, {
              style: { fill: false, color: "#2d55b0", weight: 0.6, interactive: false }
            });
            btn.innerHTML = '<span class="dot"></span> ZIP borders';
            if (btn.classList.contains("is-on")) state.zipLayer.addTo(state.map);
          });
        } else if (state.zipLayer) {
          state.zipLayer.addTo(state.map);
        }
      } else if (state.zipLayer) {
        state.map.removeLayer(state.zipLayer);
      }
    }
  }

  // ---- build everything once Leaflet + data are ready ----------------------
  function buildMap() {
    state.map = L.map(els.map, {
      center: VA_CENTER,
      zoom: VA_ZOOM,
      zoomControl: true,
      scrollWheelZoom: true,
      worldCopyJump: true
    });

    // free base layers — CARTO Voyager (street) + Esri World Imagery (satellite)
    var street = L.tileLayer(
      "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png",
      { subdomains: "abcd", maxZoom: 20,
        attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>' }
    ).addTo(state.map);

    var satellite = L.tileLayer(
      "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
      { maxZoom: 19, attribution: "Tiles &copy; Esri" }
    );

    L.control.layers({ "Map": street, "Satellite": satellite }, null, { position: "topright" }).addTo(state.map);

    // blue outline around the state of Virginia
    fetch("/data/va-state.geojson").then(function (r) { return r.json(); }).then(function (geo) {
      L.geoJSON(geo, { style: { fill: false, color: "#2d55b0", weight: 2.5, interactive: false } }).addTo(state.map);
    }).catch(function () {});

    els.loading.classList.add("is-hidden");

    // clusterer
    state.clusterer = L.markerClusterGroup({
      maxClusterRadius: 50,
      showCoverageOnHover: false,
      chunkedLoading: true
    });
    state.map.addLayer(state.clusterer);

    // build markers
    state.providers.forEach(function (p, idx) {
      p._idx = idx;
      var marker = L.marker([p.lat, p.lng], { icon: PIN, title: p.name });
      marker.bindPopup(popupHTML(p));
      marker.on("click", function () { highlight(idx); });
      state.markers.push({ marker: marker, provider: p });
    });

    applyFilter();
  }

  function highlight(idx) {
    var items = els.results.querySelectorAll(".map-result");
    items.forEach(function (li) {
      li.classList.toggle("is-active", li.getAttribute("data-i") == idx);
      if (li.getAttribute("data-i") == idx) li.scrollIntoView({ block: "nearest" });
    });
  }

  // ---- wire UI -------------------------------------------------------------
  function wireUI() {
    // filter dropdown
    var opts = '<option value="">All Services</option>';
    state.categories.forEach(function (c) {
      opts += '<option value="' + c.key + '">' + esc(c.label) + " (" + c.count + ")</option>";
    });
    els.filter.innerHTML = opts;
    els.filter.addEventListener("change", function () {
      state.activeCat = els.filter.value;
      applyFilter();
    });

    // zip search
    els.zipForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var z = (els.zipInput.value || "").trim().slice(0, 5);
      if (z && !/^\d{5}$/.test(z)) { els.zipInput.focus(); return; }
      state.activeZip = z;
      if (z && state.centroids[z]) {
        state.map.setView([state.centroids[z][0], state.centroids[z][1]], 11);
      } else if (!z) {
        state.map.setView(VA_CENTER, VA_ZOOM);
      }
      applyFilter();
    });

    // results click delegation — open detail panel
    els.results.addEventListener("click", function (e) {
      if (e.target.closest("a")) return; // let action links navigate normally
      var li = e.target.closest(".map-result");
      if (!li) return;
      var idx = +li.getAttribute("data-i");
      var m = state.markers[idx];
      if (!m) return;
      var z = state.map.getZoom() < 12 ? 13 : state.map.getZoom();
      state.map.setView(m.marker.getLatLng(), z);
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

  // ---- boot ----------------------------------------------------------------
  function fail(msg) {
    if (els.loading) { els.loading.textContent = msg; els.loading.classList.remove("is-hidden"); }
  }

  Promise.all([
    fetch("/data/va-providers.json").then(function (r) { return r.json(); }),
    fetch("/data/map-categories.json").then(function (r) { return r.json(); }),
    fetch("/data/va-zip-centroids.json").then(function (r) { return r.json(); })
  ]).then(function (res) {
    state.providers = res[0];
    state.categories = res[1];
    state.centroids = res[2];
    wireUI();
    buildMap();
  }).catch(function (err) {
    fail("Map could not load. Please refresh the page.");
    if (window.console) console.error(err);
  });
})();
