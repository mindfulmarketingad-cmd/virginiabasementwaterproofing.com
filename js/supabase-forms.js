/* ============================================================================
   supabase-forms.js
   Sends job-request and claim-listing submissions to the shared `leads` table.

   This site writes into the SAME cross-site leads table used by the other
   properties. Rows are distinguished by:
       source     = 'virginiabasementwaterproofing.org'
       lead_type  = 'job_request' | 'claim_listing'

   Run scripts/supabase-leads.sql once in the Supabase SQL editor to add the
   columns this site needs (all additive, IF NOT EXISTS — safe to re-run and
   safe for your existing rows and other sites).

   If your leads table is not named "leads", change LEADS_TABLE below.
   ============================================================================ */
(function () {
  "use strict";

  var SUPABASE_URL = "https://tbqigevoksabizjogvtm.supabase.co";
  var SUPABASE_KEY = "sb_publishable_aHlx0Tdu2rhOTBUp3lhkQw_Lv6Awz7a";
  var LEADS_TABLE  = "leads";
  var SOURCE       = "virginiabasementwaterproofing.org";

  // Core columns that almost certainly already exist on a cross-site leads
  // table. Used as a fallback so a schema mismatch never loses a lead.
  var CORE_FIELDS = ["source", "lead_type", "name", "email", "phone", "message"];

  // ---- low-level REST insert -------------------------------------------------
  function insertRow(table, payload) {
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
      if (r.ok) return r;
      return r.text().then(function (t) {
        var err = new Error(t || ("HTTP " + r.status));
        err.status = r.status;
        err.body = t || "";
        throw err;
      });
    });
  }

  // Insert; if the schema rejects an unknown column, retry with core fields
  // only (folding the rest into message) so a lead is never lost.
  function insertLead(payload) {
    return insertRow(LEADS_TABLE, payload).catch(function (err) {
      var schemaIssue = /PGRST204|could not find|column .* does not exist|schema cache/i
        .test(err.body || err.message || "");
      if (!schemaIssue) throw err;

      var minimal = {};
      CORE_FIELDS.forEach(function (k) {
        if (payload[k] !== undefined && payload[k] !== "") minimal[k] = payload[k];
      });
      var extras = Object.keys(payload).filter(function (k) {
        return CORE_FIELDS.indexOf(k) === -1 && payload[k];
      }).map(function (k) { return k + ": " + payload[k]; });
      if (extras.length) {
        minimal.message = (minimal.message ? minimal.message + "\n\n" : "") + extras.join("\n");
      }
      if (window.console) console.warn("Supabase: falling back to core columns.", err.body);
      return insertRow(LEADS_TABLE, minimal);
    });
  }

  // ---- helpers ---------------------------------------------------------------
  function params() { return new URLSearchParams(window.location.search); }
  function getParam(name) { return params().get(name) || ""; }
  function val(form, field) {
    var el = form.querySelector("[name=" + field + "]");
    return el ? (el.value || "").trim() : "";
  }

  // marketing attribution — carried on every lead
  function attribution() {
    var q = params();
    return {
      source:       SOURCE,
      page_url:     window.location.href,
      referrer:     document.referrer || "",
      utm_source:   q.get("utm_source")   || "",
      utm_medium:   q.get("utm_medium")   || "",
      utm_campaign: q.get("utm_campaign") || "",
      utm_term:     q.get("utm_term")     || "",
      utm_content:  q.get("utm_content")  || "",
      gclid:        q.get("gclid")        || ""
    };
  }

  function merge() {
    var out = {};
    for (var i = 0; i < arguments.length; i++) {
      var o = arguments[i];
      for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) out[k] = o[k];
    }
    // strip empties so we never send blank strings for optional columns
    Object.keys(out).forEach(function (k) { if (out[k] === "" || out[k] == null) delete out[k]; });
    return out;
  }

  function showSuccess(form, selector) {
    var box = document.querySelector(selector);
    if (box) { box.style.display = "block"; box.scrollIntoView({ behavior: "smooth", block: "center" }); }
    form.style.display = "none";
  }

  function wire(form, opts) {
    form.addEventListener("submit", function (e) {
      e.preventDefault();
      if (form.checkValidity && !form.checkValidity()) { form.reportValidity(); return; }

      var btn = form.querySelector("[type=submit]");
      var label = btn ? btn.textContent : "";
      if (btn) { btn.disabled = true; btn.textContent = "Sending…"; }

      insertLead(opts.payload())
        .then(function () { showSuccess(form, opts.success); })
        .catch(function (err) {
          if (btn) { btn.disabled = false; btn.textContent = label; }
          if (window.console) console.error("Supabase error:", err.body || err);
          alert("There was a problem submitting your request. Please email "
                + "info@virginiabasementwaterproofing.org and we'll follow up right away.");
        });
    });
  }

  // ---- job request form ([data-quote]) ---------------------------------------
  var quoteForm = document.querySelector("[data-quote]");
  if (quoteForm) {
    wire(quoteForm, {
      success: ".form-success",
      payload: function () {
        return merge(attribution(), {
          lead_type:     "job_request",
          name:          val(quoteForm, "name"),
          email:         val(quoteForm, "email"),
          phone:         val(quoteForm, "phone"),
          city:          val(quoteForm, "city"),
          state:         "VA",
          zip:           val(quoteForm, "zip"),
          service:       val(quoteForm, "service"),
          message:       val(quoteForm, "message"),
          provider_slug: getParam("provider")
        });
      }
    });
  }

  // ---- claim listing form ([data-claim]) -------------------------------------
  var claimForm = document.querySelector("[data-claim]");
  if (claimForm) {
    // pre-fill the hidden provider field from ?provider=
    var slugField = claimForm.querySelector("[name=provider_slug]");
    if (slugField && !slugField.value) slugField.value = getParam("provider");

    wire(claimForm, {
      success: ".claim-success",
      payload: function () {
        return merge(attribution(), {
          lead_type:     "claim_listing",
          name:          val(claimForm, "contact_name"),
          email:         val(claimForm, "contact_email"),
          phone:         val(claimForm, "contact_phone"),
          business_name: val(claimForm, "business_name"),
          message:       val(claimForm, "description"),
          state:         "VA",
          provider_slug: val(claimForm, "provider_slug") || getParam("provider")
        });
      }
    });
  }
})();
