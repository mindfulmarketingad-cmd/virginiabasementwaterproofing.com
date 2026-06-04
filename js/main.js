/* Virginia Basement Waterproofing — site interactions */
(function () {
  "use strict";

  // Mobile nav toggle
  var toggle = document.querySelector(".nav-toggle");
  var nav = document.getElementById("main-nav");
  if (toggle && nav) {
    toggle.addEventListener("click", function () {
      var open = nav.classList.toggle("open");
      toggle.setAttribute("aria-expanded", open ? "true" : "false");
    });
  }

  // Current year in footer
  var yr = document.querySelectorAll("[data-year]");
  yr.forEach(function (el) { el.textContent = new Date().getFullYear(); });

  // ---- Local dealer lookup (dynamic by ZIP / geolocation) ----
  var DEALERS = {
    tidewater:  { name: "Tidewater Dry Basements",            region: "Hampton Roads",      url: "/partners/tidewater-dry-basements/" },
    capital:    { name: "Capital Foundation & Waterproofing", region: "Greater Richmond",   url: "/partners/" },
    blueridge:  { name: "Blue Ridge Crawl & Basement",        region: "Western Virginia",   url: "/partners/" },
    olddom:     { name: "Old Dominion Waterproofing",         region: "Northern Virginia",  url: "/partners/" },
    shenandoah: { name: "Shenandoah Valley Foundation Pros",  region: "Shenandoah Valley",  url: "/partners/" }
  };
  // Map of Virginia 3-digit ZIP prefixes -> dealer key
  var ZIP3_MAP = {
    "220": "olddom", "221": "olddom", "222": "olddom", "223": "olddom",
    "224": "capital", "225": "capital", "227": "capital",
    "226": "shenandoah", "228": "shenandoah", "244": "shenandoah",
    "229": "blueridge", "239": "blueridge", "240": "blueridge", "241": "blueridge",
    "242": "blueridge", "243": "blueridge", "245": "blueridge", "246": "blueridge",
    "230": "capital", "231": "capital", "232": "capital", "238": "capital",
    "233": "tidewater", "234": "tidewater", "235": "tidewater", "236": "tidewater", "237": "tidewater"
  };
  var DEFAULT_DEALER = { name: "Virginia Basement Waterproofing Network", region: "Virginia", url: "/partners/" };

  function dealerForZip(zip) {
    var key = ZIP3_MAP[String(zip).slice(0, 3)];
    return key ? DEALERS[key] : DEFAULT_DEALER;
  }

  var dealerCard = document.getElementById("dealer-card");

  function renderDealer(zip) {
    if (!dealerCard) return;
    var d = dealerForZip(zip);
    var zipEl = document.getElementById("dealer-zip");
    var nameEl = document.getElementById("dealer-name");
    if (zipEl) zipEl.textContent = "Zip Code: " + zip;
    if (nameEl) nameEl.innerHTML = '<a href="' + d.url + '">' + d.name + "</a>";
  }

  function dealerPrompt(msg) {
    if (!dealerCard) return;
    var zipEl = document.getElementById("dealer-zip");
    var nameEl = document.getElementById("dealer-name");
    if (zipEl) zipEl.textContent = "";
    if (nameEl) nameEl.textContent = msg || "Enter your ZIP code above to find your local dealer.";
  }

  // Detect the visitor's location by IP on first load (no API key required).
  function detectLocation() {
    if (!dealerCard) return;
    fetch("https://ipwho.is/")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var zip = data && (data.postal || data.postal_code);
        if (zip && /^\d{5}/.test(String(zip))) {
          zip = String(zip).slice(0, 5);
          var inp = document.getElementById("zip-input");
          if (inp && !inp.value) inp.value = zip;
          renderDealer(zip);
        } else {
          dealerPrompt();
        }
      })
      .catch(function () { dealerPrompt(); });
  }

  // "Change Location" -> focus hero ZIP if present; else swap in an inline mini-form
  var dealerChange = document.getElementById("dealer-change");
  if (dealerChange) {
    dealerChange.addEventListener("click", function (e) {
      e.preventDefault();
      var heroInp = document.getElementById("zip-input");
      if (heroInp) {
        heroInp.focus();
        heroInp.select();
        heroInp.scrollIntoView({ behavior: "smooth", block: "center" });
        return;
      }
      // No hero input — inject a mini ZIP form inside the card
      var existing = document.getElementById("dealer-mini-form");
      if (existing) { existing.querySelector("input").focus(); return; }
      var mini = document.createElement("form");
      mini.id = "dealer-mini-form";
      mini.style.cssText = "display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;";
      mini.innerHTML =
        '<input type="text" inputmode="numeric" maxlength="5" placeholder="Enter ZIP code"' +
        ' style="padding:9px 12px;border:none;border-radius:7px;font-size:1rem;width:140px;">' +
        '<button type="submit" class="btn btn--primary" style="padding:9px 18px;">Go</button>';
      dealerChange.insertAdjacentElement("afterend", mini);
      mini.querySelector("input").focus();
      mini.addEventListener("submit", function (ev) {
        ev.preventDefault();
        var z = mini.querySelector("input").value.trim();
        if (!/^\d{5}$/.test(z)) return;
        renderDealer(z);
        mini.remove();
      });
    });
  }

  // Hero ZIP form -> update the dealer card inline
  var zipForm = document.getElementById("zip-form");
  if (zipForm) {
    zipForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var zip = (document.getElementById("zip-input") || {}).value || "";
      zip = zip.trim();
      if (!/^\d{5}$/.test(zip)) {
        dealerPrompt("Please enter a valid 5-digit ZIP code.");
        return;
      }
      renderDealer(zip);
    });
  }

  if (dealerCard) detectLocation();

  // ---- Partner directory search filter ----
  var partnerSearch = document.getElementById("partner-search");
  if (partnerSearch) {
    var listings = Array.prototype.slice.call(document.querySelectorAll(".listing"));
    var countEl = document.getElementById("partner-count");
    var totalCount = listings.length;
    partnerSearch.addEventListener("input", function () {
      var q = partnerSearch.value.trim().toLowerCase();
      var shown = 0;
      listings.forEach(function (el) {
        var hay = el.getAttribute("data-search") || "";
        var match = !q || hay.indexOf(q) !== -1;
        el.style.display = match ? "" : "none";
        if (match) shown++;
      });
      if (countEl) {
        countEl.textContent = q
          ? "Showing " + shown + " of " + totalCount + " contractors"
          : "Showing all " + totalCount + " contractors";
      }
    });
  }

  // Quote form (client-side confirmation only — no backend)
  var quoteForms = document.querySelectorAll("form[data-quote]");
  quoteForms.forEach(function (form) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var ok = form.querySelector(".form-success");
      if (ok) {
        ok.style.display = "block";
        ok.scrollIntoView({ behavior: "smooth", block: "center" });
      }
      form.reset();
    });
  });

  // Pre-fill contractors page heading from zip param
  var params = new URLSearchParams(window.location.search);
  var zipParam = params.get("zip");
  var zipNote = document.getElementById("zip-note");
  if (zipParam && zipNote) {
    zipNote.textContent = "Showing basement waterproofing contractors serving ZIP code " + zipParam + ".";
  }
})();
