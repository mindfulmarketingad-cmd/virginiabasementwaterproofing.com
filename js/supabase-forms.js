/* ============================================================================
   supabase-forms.js
   Handles job-request and claim-listing form submissions to Supabase.
https://tbqigevoksabizjogvtm.supabase.co
   SETUP: Set SUPABASE_URL to your project URL, e.g.:

   The anon/publishable key is already embedded below.

   Required Supabase tables:
     job_requests  (name, phone, email, zip, city, service, message, provider, created_at)
     claim_listings (provider_slug, business_name, contact_name, contact_email, contact_phone, created_at)
   ============================================================================ */
(function () {
  "use strict";

  var SUPABASE_URL = ""; // TODO: set to https://<project-ref>.supabase.co
  var SUPABASE_KEY = "sb_publishable_aHlx0Tdu2rhOTBUp3lhkQw_Lv6Awz7a";

  // ---- low-level REST insert -------------------------------------------------
  function insertRow(table, payload) {
    if (!SUPABASE_URL) {
      return Promise.reject(new Error("SUPABASE_URL not configured"));
    }
    return fetch(SUPABASE_URL + "/rest/v1/" + table, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "apikey": SUPABASE_KEY,
        "Authorization": "Bearer " + SUPABASE_KEY,
        "Prefer": "return=minimal"
      },
      body: JSON.stringify(payload)
    }).then(function (r) {
      if (!r.ok) return r.text().then(function (t) { throw new Error(t); });
      return r;
    });
  }

  // ---- read provider param from URL ------------------------------------------
  function getParam(name) {
    var params = new URLSearchParams(window.location.search);
    return params.get(name) || "";
  }

  // ---- job request form ([data-quote]) ---------------------------------------
  var quoteForm = document.querySelector("[data-quote]");
  if (quoteForm) {
    // Pre-fill hidden provider if ?provider= in URL
    var providerSlug = getParam("provider");

    quoteForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var btn = quoteForm.querySelector("[type=submit]");
      btn.disabled = true;
      btn.textContent = "Submitting…";

      var data = {
        name:     (quoteForm.querySelector("[name=name]") || {}).value || "",
        phone:    (quoteForm.querySelector("[name=phone]") || {}).value || "",
        email:    (quoteForm.querySelector("[name=email]") || {}).value || "",
        zip:      (quoteForm.querySelector("[name=zip]") || {}).value || "",
        city:     (quoteForm.querySelector("[name=city]") || {}).value || "",
        service:  (quoteForm.querySelector("[name=service]") || {}).value || "",
        message:  (quoteForm.querySelector("[name=message]") || {}).value || "",
        provider: providerSlug || getParam("provider"),
        page_url: window.location.href
      };

      insertRow("job_requests", data)
        .then(function () {
          var success = document.querySelector(".form-success");
          if (success) success.style.display = "block";
          quoteForm.style.display = "none";
        })
        .catch(function (err) {
          btn.disabled = false;
          btn.textContent = "Submit Job Request";
          if (window.console) console.error("Supabase error:", err);
          alert("There was a problem submitting your request. Please email info@virginiabasementwaterproofing.org directly.");
        });
    });
  }

  // ---- claim listing form ([data-claim]) -------------------------------------
  var claimForm = document.querySelector("[data-claim]");
  if (claimForm) {
    claimForm.addEventListener("submit", function (e) {
      e.preventDefault();
      var btn = claimForm.querySelector("[type=submit]");
      btn.disabled = true;
      btn.textContent = "Submitting…";

      var data = {
        provider_slug:  (claimForm.querySelector("[name=provider_slug]") || {}).value || getParam("provider"),
        business_name:  (claimForm.querySelector("[name=business_name]") || {}).value || "",
        contact_name:   (claimForm.querySelector("[name=contact_name]") || {}).value || "",
        contact_email:  (claimForm.querySelector("[name=contact_email]") || {}).value || "",
        contact_phone:  (claimForm.querySelector("[name=contact_phone]") || {}).value || "",
        page_url:       window.location.href
      };

      insertRow("claim_listings", data)
        .then(function () {
          var success = document.querySelector(".claim-success");
          if (success) success.style.display = "block";
          claimForm.style.display = "none";
        })
        .catch(function (err) {
          btn.disabled = false;
          btn.textContent = "Submit Claim";
          if (window.console) console.error("Supabase error:", err);
          alert("There was a problem submitting your claim. Please email info@virginiabasementwaterproofing.org directly.");
        });
    });
  }
})();
