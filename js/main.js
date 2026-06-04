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

  // Zip search -> sends to contractors page with zip param
  var zipForm = document.getElementById("zip-form");
  if (zipForm) {
    zipForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var zip = (document.getElementById("zip-input") || {}).value || "";
      zip = zip.trim();
      if (!/^\d{5}$/.test(zip)) {
        alert("Please enter a valid 5-digit Virginia ZIP code.");
        return;
      }
      window.location.href = "contractors.html?zip=" + encodeURIComponent(zip);
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
