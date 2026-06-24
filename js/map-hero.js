/* ============================================================================
   Homepage map hero — Virginia waterproofing services finder.

   Data is PRE-FETCHED and static (data/va-providers.json, sourced from Google
   Maps via Outscraper) so there are ZERO runtime Places/Geocoding API calls.
   The only Google API used at runtime is the Maps JavaScript base map itself.
   ZIP search resolves against a local centroid table (no Geocoding billing).
   Business phone numbers are intentionally never shown — leads route to us.
   ============================================================================ */
(function () {
  "use strict";

  var VA_CENTER = { lat: 37.62, lng: -79.2 };
  var VA_ZOOM = 7;

  var els = {
    map: document.getElementById("vaMap"),
    loading: document.getElementById("mapLoading"),
    results: document.getElementById("resultsList"),
    count: document.getElementById("resultCount"),
    filter: document.getElementById("svcFilter"),
    zipForm: document.getElementById("zipSearch"),
    zipInput: document.getElementById("zipInput"),
    toggles: document.querySelectorAll(".map-toggle")
  };
  if (!els.map) return; // not on this page

  var state = {
    map: null,
    info: null,
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

  // ---- info window content (NO phone numbers) ------------------------------
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
    list.slice(0, 300).forEach(function (p, i) {
      var rate = p.rating != null
        ? '<div class="map-result__rate">' + stars(p.rating) + " " + p.rating +
          (p.reviews != null ? " <span>(" + p.reviews + ")</span>" : "") + "</div>"
        : "";
      html += '<li class="map-result" data-i="' + p._idx + '">' +
        "<h4>" + esc(p.name) + "</h4>" + rate +
        '<div class="map-result__loc">' + esc(p.city) + (p.zip ? ", VA " + esc(p.zip) : ", VA") + "</div></li>";
    });
    els.results.innerHTML = html;
  }

  function catLabel(key) {
    for (var i = 0; i < state.categories.length; i++)
      if (state.categories[i].key === key) return state.categories[i].label;
    return "";
  }

  // ---- apply current filter to markers + list ------------------------------
  // Works whether or not the MarkerClusterer library is present: with it, the
  // clusterer owns the markers; without it, we toggle marker.setMap directly.
  function applyFilter() {
    var visible = [];
    var visMarkers = [];
    state.markers.forEach(function (m) {
      var show = matches(m.provider);
      if (show) { visible.push(m.provider); visMarkers.push(m.marker); }
      if (!state.clusterer) m.marker.setMap(show ? state.map : null);
    });
    if (state.clusterer) {
      state.clusterer.clearMarkers();
      state.clusterer.addMarkers(visMarkers);
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

  // ---- build everything once Google Maps + data are ready ------------------
  function buildMap(MapsLib, MarkerLib) {
    state.map = new MapsLib.Map(els.map, {
      center: VA_CENTER,
      zoom: VA_ZOOM,
      mapTypeControl: true,          // native Map | Satellite toggle
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

    // build markers
    state.providers.forEach(function (p, idx) {
      p._idx = idx;
      var marker = new MarkerLib.Marker({
        position: { lat: p.lat, lng: p.lng },
        title: p.name
      });
      marker.addListener("click", function () {
        state.info.setContent(popupHTML(p));
        state.info.open(state.map, marker);
        highlight(idx);
      });
      state.markers.push({ marker: marker, provider: p });
    });

    // cluster if the library is available (graceful fallback to plain markers)
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
        state.map.setCenter({ lat: state.centroids[z][0], lng: state.centroids[z][1] });
        state.map.setZoom(11);
      } else if (!z) {
        state.map.setCenter(VA_CENTER); state.map.setZoom(VA_ZOOM);
      }
      applyFilter();
    });

    // results click delegation
    els.results.addEventListener("click", function (e) {
      var li = e.target.closest(".map-result");
      if (!li) return;
      var idx = +li.getAttribute("data-i");
      var m = state.markers[idx];
      if (!m) return;
      state.map.panTo(m.marker.getPosition());
      if (state.map.getZoom() < 12) state.map.setZoom(13);
      state.info.setContent(popupHTML(m.provider));
      state.info.open(state.map, m.marker);
      highlight(idx);
    });

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
    return Promise.all([
      google.maps.importLibrary("maps"),
      google.maps.importLibrary("marker")
    ]);
  }).then(function (libs) {
    buildMap(libs[0], libs[1]);
  }).catch(function (err) {
    fail("Map could not load. Please refresh or call (757) 743-9050.");
    if (window.console) console.error(err);
  });
})();
