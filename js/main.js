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

  // Mega menu — desktop hover + click, mobile click
  document.querySelectorAll(".nav-item").forEach(function (item) {
    var isTouch = false;
    item.addEventListener("mouseenter", function () {
      if (isTouch) return;
      item.classList.add("open");
    });
    item.addEventListener("mouseleave", function () {
      if (isTouch) return;
      item.classList.remove("open");
    });
    item.querySelector("a").addEventListener("click", function (e) {
      // On mobile or touch, toggle instead of navigating
      if (window.innerWidth <= 900 || isTouch) {
        e.preventDefault();
        item.classList.toggle("open");
      }
    });
    item.addEventListener("touchstart", function () { isTouch = true; }, { passive: true });
  });
  // Close mega menu on outside click
  document.addEventListener("click", function (e) {
    if (!e.target.closest(".nav-item")) {
      document.querySelectorAll(".nav-item.open").forEach(function (el) {
        el.classList.remove("open");
      });
    }
  });

  // Current year in footer
  var yr = document.querySelectorAll("[data-year]");
  yr.forEach(function (el) { el.textContent = new Date().getFullYear(); });

  // ── Contractor lookup by ZIP ─────────────────────────────────────────────────
  // Real ZIP → contractor data from the Virginia directory
  var VBW_BY_ZIP = {
    "20106":{"n":"Early's Flooring Specialists & More","u":"/partners/early-s-flooring-specialists-more/"},
    "20109":{"n":"Rainbow Restoration of Gainesville, VA","u":"/partners/rainbow-restoration-of-gainesville-va/"},
    "20110":{"n":"Drying Tech of PWC","u":"/partners/drying-tech-of-pwc/"},
    "20111":{"n":"Power Wash Plus Inc","u":"/partners/power-wash-plus-inc/"},
    "20112":{"n":"SC Companies, Inc","u":"/partners/sc-companies-inc/"},
    "20115":{"n":"Umpire Mitigation","u":"/partners/umpire-mitigation/"},
    "20120":{"n":"True Dry","u":"/partners/true-dry/"},
    "20121":{"n":"Nova Construction Pro","u":"/partners/nova-construction-pro/"},
    "20130":{"n":"Trusted Veterans Restoration LLC","u":"/partners/trusted-veterans-restoration-llc/"},
    "20132":{"n":"Merit Restorations","u":"/partners/merit-restorations-purcellville/"},
    "20136":{"n":"JES Foundation Repair","u":"/partners/jes-foundation-repair-bristow/"},
    "20137":{"n":"denchfield llc","u":"/partners/denchfield-llc/"},
    "20147":{"n":"Galaxy Restoration","u":"/partners/galaxy-restoration/"},
    "20148":{"n":"Roto-Rooter Plumbing & Water Cleanup","u":"/partners/roto-rooter-plumbing-water-cleanup-ashburn/"},
    "20151":{"n":"Coventry Services LLC","u":"/partners/coventry-services-llc/"},
    "20152":{"n":"SERVPRO of North Arlington","u":"/partners/servpro-of-north-arlington/"},
    "20155":{"n":"ProTrust Water Damage Restoration","u":"/partners/protrust-water-damage-restoration-gainesville/"},
    "20158":{"n":"Home Paramount Pest Control","u":"/partners/home-paramount-pest-control-hamilton/"},
    "20164":{"n":"Raven Rock Restorations","u":"/partners/raven-rock-restorations/"},
    "20165":{"n":"Mold Removal Services","u":"/partners/mold-removal-services/"},
    "20166":{"n":"Century Waterproofing","u":"/partners/century-waterproofing/"},
    "20170":{"n":"AquaPassage","u":"/partners/aquapassage/"},
    "20171":{"n":"RestorTech, Inc.","u":"/partners/restortech-inc/"},
    "20175":{"n":"Summit Restoration","u":"/partners/summit-restoration/"},
    "20176":{"n":"D & D Painting & Repairs","u":"/partners/d-d-painting-repairs/"},
    "20180":{"n":"Applied Restoration Group","u":"/partners/applied-restoration-group/"},
    "20187":{"n":"Roto-Rooter Plumbing & Water Cleanup","u":"/partners/roto-rooter-plumbing-water-cleanup-warrenton/"},
    "20191":{"n":"Expert","u":"/partners/expert/"},
    "20197":{"n":"Milcon Roofing, Design & Build","u":"/partners/milcon-roofing-design-build/"},
    "22026":{"n":"Minuteman Restoration","u":"/partners/minuteman-restoration/"},
    "22030":{"n":"Greenway home improvements","u":"/partners/greenway-home-improvements/"},
    "22031":{"n":"Ultimate Water Damage Restoration, LLC","u":"/partners/ultimate-water-damage-restoration-llc/"},
    "22042":{"n":"Fairfax Construction","u":"/partners/fairfax-construction/"},
    "22046":{"n":"Home Paramount Pest Control","u":"/partners/home-paramount-pest-control-falls-church/"},
    "22079":{"n":"Voda Cleaning & Restoration","u":"/partners/voda-cleaning-restoration/"},
    "22101":{"n":"Mclean","u":"/partners/mclean/"},
    "22150":{"n":"PuroClean of Springfield","u":"/partners/puroclean-of-springfield/"},
    "22151":{"n":"Flood USA - Water Damage Restoration Services","u":"/partners/flood-usa-water-damage-restoration-services/"},
    "22153":{"n":"Valor Mold Removal","u":"/partners/valor-mold-removal/"},
    "22182":{"n":"Water Damage DMV","u":"/partners/water-damage-dmv/"},
    "22191":{"n":"Primary Roofing and Waterproofing INC","u":"/partners/primary-roofing-and-waterproofing-inc/"},
    "22192":{"n":"Serviclean Inc","u":"/partners/serviclean-inc/"},
    "22193":{"n":"Water Damage Pro Master","u":"/partners/water-damage-pro-master/"},
    "22203":{"n":"Crawl Space Brothers","u":"/partners/crawl-space-brothers/"},
    "22204":{"n":"Value Dry Basement Waterproofing","u":"/partners/value-dry-basement-waterproofing/"},
    "22205":{"n":"Royal Restoration - Water Damage Arlington","u":"/partners/royal-restoration-water-damage-arlington/"},
    "22207":{"n":"Roto-Rooter Plumbing & Water Cleanup","u":"/partners/roto-rooter-plumbing-water-cleanup/"},
    "22209":{"n":"All State Masonry & Construction","u":"/partners/all-state-masonry-construction/"},
    "22304":{"n":"DMV Foundation Solutions","u":"/partners/dmv-foundation-solutions/"},
    "22306":{"n":"ServiceMaster National Capital Restoration","u":"/partners/servicemaster-national-capital-restoration/"},
    "22309":{"n":"Roto-Rooter Plumbing & Water Cleanup","u":"/partners/roto-rooter-plumbing-water-cleanup-alexandria/"},
    "22310":{"n":"O'Neill Plumbing Services L.L.C.","u":"/partners/o-neill-plumbing-services-l-l-c/"},
    "22311":{"n":"Roofing Premium Contractor Solution LLC","u":"/partners/roofing-premium-contractor-solution-llc/"},
    "22312":{"n":"Pipe Pro Solutions","u":"/partners/pipe-pro-solutions/"},
    "22314":{"n":"Paragon Property Restoration","u":"/partners/paragon-property-restoration/"},
    "22401":{"n":"Professional Restoration Services","u":"/partners/professional-restoration-services/"},
    "22405":{"n":"Semper Dry Water Removal","u":"/partners/semper-dry-water-removal/"},
    "22406":{"n":"Spartan Emergency Water Removal","u":"/partners/spartan-emergency-water-removal/"},
    "22407":{"n":"Virginia Restoration Experts","u":"/partners/virginia-restoration-experts/"},
    "22408":{"n":"Crawlspace Medic of Fredericksburg","u":"/partners/crawlspace-medic-of-fredericksburg/"},
    "22473":{"n":"Basement Solutions, LLC","u":"/partners/basement-solutions-llc/"},
    "22485":{"n":"S&S Waterproofing and Foundation Repair","u":"/partners/s-s-waterproofing-and-foundation-repair/"},
    "22503":{"n":"Bay Restoration & Air Duct Services","u":"/partners/bay-restoration-air-duct-services/"},
    "22551":{"n":"Operation Dry Space","u":"/partners/operation-dry-space/"},
    "22553":{"n":"Foundation Medix","u":"/partners/foundation-medix-spotsylvania-courthouse/"},
    "22554":{"n":"PuroClean of Stafford","u":"/partners/puroclean-of-stafford/"},
    "22556":{"n":"Dry Force","u":"/partners/dry-force/"},
    "22601":{"n":"Voda Cleaning & Restoration of Martinsburg & Winchester","u":"/partners/voda-cleaning-restoration-of-martinsburg-winchester/"},
    "22602":{"n":"Lux Foundation Solutions","u":"/partners/lux-foundation-solutions/"},
    "22603":{"n":"Home Paramount Pest Control","u":"/partners/home-paramount-pest-control-winchester/"},
    "22630":{"n":"SERVPRO of Winchester","u":"/partners/servpro-of-winchester/"},
    "22642":{"n":"Aalcon Co. - Basement Waterproofing and Foundations Contractor","u":"/partners/aalcon-co-basement-waterproofing-and-foundations-contractor/"},
    "22701":{"n":"Voda Cleaning & Restoration of Culpeper-Warrenton","u":"/partners/voda-cleaning-restoration-of-culpeper-warrenton/"},
    "22720":{"n":"TD&D Unlimited, LLC","u":"/partners/td-d-unlimited-llc/"},
    "22727":{"n":"ServiceMaster of Warrenton/Culpeper","u":"/partners/servicemaster-of-warrenton-culpeper/"},
    "22728":{"n":"Copper Fox Foundation Repair","u":"/partners/copper-fox-foundation-repair/"},
    "22734":{"n":"Genesis, LLC","u":"/partners/genesis-llc/"},
    "22801":{"n":"Pure Maintenance of the Blue Ridge","u":"/partners/pure-maintenance-of-the-blue-ridge/"},
    "22802":{"n":"Spotless Specialty Cleaning","u":"/partners/spotless-specialty-cleaning/"},
    "22821":{"n":"Mold Removal Worx LLC","u":"/partners/mold-removal-worx-llc/"},
    "22844":{"n":"Paul Davis Restoration of Northwest Virginia","u":"/partners/paul-davis-restoration-of-northwest-virginia/"},
    "22901":{"n":"Piedmont Waterproofing Contractors","u":"/partners/piedmont-waterproofing-contractors/"},
    "22902":{"n":"ServiceMaster of Charlottesville","u":"/partners/servicemaster-of-charlottesville/"},
    "22903":{"n":"UpliftPro Crew","u":"/partners/upliftpro-crew/"},
    "22911":{"n":"Crawlspace RX","u":"/partners/crawlspace-rx/"},
    "22960":{"n":"SERVPRO of Louisa, Orange & Madison Counties","u":"/partners/servpro-of-louisa-orange-madison-counties/"},
    "22968":{"n":"Paul Davis Restoration of Central Virginia","u":"/partners/paul-davis-restoration-of-central-virginia/"},
    "22974":{"n":"Rainbow Restoration of Charlottesville","u":"/partners/rainbow-restoration-of-charlottesville/"},
    "22980":{"n":"Restoration 1 of Charlottesville","u":"/partners/restoration-1-of-charlottesville/"},
    "23005":{"n":"Stable Foundations","u":"/partners/stable-foundations-ashland/"},
    "23030":{"n":"SERVPRO of York/James City County/Poquoson","u":"/partners/servpro-of-york-james-city-county-poquoson/"},
    "23060":{"n":"Acculevel","u":"/partners/acculevel-glen-allen/"},
    "23071":{"n":"PBS Crawlspace & Foundation Specialists","u":"/partners/pbs-crawlspace-foundation-specialists/"},
    "23106":{"n":"Restoration Specialists Of Virginia","u":"/partners/restoration-specialists-of-virginia/"},
    "23111":{"n":"PuroClean of NE Richmond","u":"/partners/puroclean-of-ne-richmond/"},
    "23112":{"n":"Affordable Crawlspace Care","u":"/partners/affordable-crawlspace-care/"},
    "23114":{"n":"RVA Restoration","u":"/partners/rva-restoration/"},
    "23139":{"n":"PuroClean of Richmond","u":"/partners/puroclean-of-richmond/"},
    "23146":{"n":"Rainbow Restoration of Richmond","u":"/partners/rainbow-restoration-of-richmond/"},
    "23168":{"n":"The Drying Company","u":"/partners/the-drying-company/"},
    "23169":{"n":"Foundation Medix","u":"/partners/foundation-medix-topping/"},
    "23185":{"n":"Roto-Rooter Plumbing & Water Cleanup","u":"/partners/roto-rooter-plumbing-water-cleanup-williamsburg/"},
    "23188":{"n":"Williamsburg Hero Mold Removal","u":"/partners/williamsburg-hero-mold-removal/"},
    "23192":{"n":"Pace Foundation Specialist LLC","u":"/partners/pace-foundation-specialist-llc/"},
    "23219":{"n":"SERVPRO of Richmond","u":"/partners/servpro-of-richmond/"},
    "23220":{"n":"B Dry System","u":"/partners/b-dry-system/"},
    "23223":{"n":"International Roofing Corp.","u":"/partners/international-roofing-corp/"},
    "23224":{"n":"Virginia Foundation Solutions, Inc.","u":"/partners/virginia-foundation-solutions-inc-richmond/"},
    "23225":{"n":"Acculevel","u":"/partners/acculevel-richmond/"},
    "23226":{"n":"Five Stars Restoration","u":"/partners/five-stars-restoration/"},
    "23227":{"n":"Crawlspace Medic of Richmond","u":"/partners/crawlspace-medic-of-richmond/"},
    "23228":{"n":"Rapid Response Restoration","u":"/partners/rapid-response-restoration/"},
    "23230":{"n":"H2O PRO Plumbing","u":"/partners/h2o-pro-plumbing/"},
    "23231":{"n":"JLJ Construction LLC","u":"/partners/jlj-construction-llc/"},
    "23233":{"n":"Commonwealth Restoration Specialists","u":"/partners/commonwealth-restoration-specialists/"},
    "23234":{"n":"Roto-Rooter Plumbing & Drain Services","u":"/partners/roto-rooter-plumbing-drain-services/"},
    "23236":{"n":"United Restorations","u":"/partners/united-restorations/"},
    "23237":{"n":"Kefficient Foundation & Waterproofing","u":"/partners/kefficient-foundation-waterproofing/"},
    "23320":{"n":"We Crawl Space Foundation Repair","u":"/partners/we-crawl-space-foundation-repair/"},
    "23322":{"n":"Hawk Crawlspace & Foundation Repair","u":"/partners/hawk-crawlspace-foundation-repair/"},
    "23323":{"n":"Personal Touch Services","u":"/partners/personal-touch-services/"},
    "23324":{"n":"Semper Dry Water Removal","u":"/partners/semper-dry-water-removal-chesapeake/"},
    "23347":{"n":"Munsey&Marshall Construction LLC","u":"/partners/munsey-marshall-construction-llc/"},
    "23430":{"n":"Patriot Crawl Space Repairs","u":"/partners/patriot-crawl-space-repairs/"},
    "23434":{"n":"D.C. Crawlspace Solutions LLC","u":"/partners/d-c-crawlspace-solutions-llc/"},
    "23435":{"n":"SERVPRO of Suffolk/Smithfield/Franklin","u":"/partners/servpro-of-suffolk-smithfield-franklin/"},
    "23451":{"n":"J.M. Froehler Construction","u":"/partners/j-m-froehler-construction/"},
    "23452":{"n":"VA Beach Hero Mold Removal","u":"/partners/va-beach-hero-mold-removal/"},
    "23453":{"n":"Tidewater Restoration and Cleaning","u":"/partners/tidewater-restoration-and-cleaning/"},
    "23454":{"n":"Service Pro's LLC","u":"/partners/service-pro-s-llc/"},
    "23455":{"n":"QXO","u":"/partners/qxo/"},
    "23456":{"n":"ABC Service Company - Crawl Space and Foundation Repair Virginia Beach","u":"/partners/abc-service-company-crawl-space-and-foundation-repair-virginia-beach/"},
    "23462":{"n":"Valcourt Building Services - Virginia Beach","u":"/partners/valcourt-building-services-virginia-beach/"},
    "23464":{"n":"KH, LLC","u":"/partners/kh-llc/"},
    "23502":{"n":"BAY Crawl Space & Foundation Repair","u":"/partners/bay-crawl-space-foundation-repair/"},
    "23503":{"n":"7 Cities Exteriors LLC","u":"/partners/7-cities-exteriors-llc/"},
    "23504":{"n":"Rainbow Restoration of Norfolk","u":"/partners/rainbow-restoration-of-norfolk/"},
    "23507":{"n":"Norfolk Water Damage Restoration | Dreyer Pro","u":"/partners/norfolk-water-damage-restoration-dreyer-pro/"},
    "23510":{"n":"Red Turtle Roofing of Norfolk","u":"/partners/red-turtle-roofing-of-norfolk/"},
    "23513":{"n":"Roto-Rooter Plumbing & Water Cleanup","u":"/partners/roto-rooter-plumbing-water-cleanup-norfolk/"},
    "23601":{"n":"911 Restoration of Virginia Peninsula","u":"/partners/911-restoration-of-virginia-peninsula/"},
    "23602":{"n":"Atlantic Power Wash","u":"/partners/atlantic-power-wash/"},
    "23605":{"n":"Skyline Roofing","u":"/partners/skyline-roofing/"},
    "23606":{"n":"Extreme Restoration Inc","u":"/partners/extreme-restoration-inc/"},
    "23607":{"n":"Newport News Water Damage Restoration","u":"/partners/newport-news-water-damage-restoration/"},
    "23651":{"n":"Legendary Solutions, Inc.","u":"/partners/legendary-solutions-inc/"},
    "23661":{"n":"Roto-Rooter Plumbing & Water Cleanup","u":"/partners/roto-rooter-plumbing-water-cleanup-hampton/"},
    "23666":{"n":"All Good Supply Corporation","u":"/partners/all-good-supply-corporation/"},
    "23669":{"n":"Tidewater LLC","u":"/partners/tidewater-llc/"},
    "23692":{"n":"NanoShield Roofing and Coatings","u":"/partners/nanoshield-roofing-and-coatings/"},
    "23693":{"n":"ServiceMaster Premier Restoration Services","u":"/partners/servicemaster-premier-restoration-services/"},
    "23701":{"n":"GO Now","u":"/partners/go-now/"},
    "23703":{"n":"K Plus Caulking","u":"/partners/k-plus-caulking/"},
    "23704":{"n":"Roto-Rooter Plumbing & Water Cleanup","u":"/partners/roto-rooter-plumbing-water-cleanup-portsmouth/"},
    "23831":{"n":"Tiger C Construction, LLC","u":"/partners/tiger-c-construction-llc/"},
    "23834":{"n":"River City Moisture And Mold","u":"/partners/river-city-moisture-and-mold/"},
    "23841":{"n":"Brown Brothers Roofing, INC","u":"/partners/brown-brothers-roofing-inc/"},
    "23851":{"n":"Morgan Construction Partners General Contracting","u":"/partners/morgan-construction-partners-general-contracting/"},
    "23860":{"n":"Randall's Crawlspace, Foundation, and Structural Repair","u":"/partners/randall-s-crawlspace-foundation-and-structural-repair/"},
    "23875":{"n":"Vance Insulation","u":"/partners/vance-insulation/"},
    "23901":{"n":"Mast Enterprises/Mast Roofing","u":"/partners/mast-enterprises-mast-roofing/"},
    "23927":{"n":"Deep River","u":"/partners/deep-river/"},
    "23944":{"n":"AquaXtreme LLC","u":"/partners/aquaxtreme-llc/"},
    "23947":{"n":"Francisco's Cleaning & Restoration Service, Inc.","u":"/partners/francisco-s-cleaning-restoration-service-inc/"},
    "23970":{"n":"Rozier Termite & Pest Control, Inc.","u":"/partners/rozier-termite-pest-control-inc/"},
    "24011":{"n":"Austin and Sons Surface Protection","u":"/partners/austin-and-sons-surface-protection/"},
    "24012":{"n":"Appalachian Foundation Services","u":"/partners/appalachian-foundation-services/"},
    "24013":{"n":"Star City Crawl Space","u":"/partners/star-city-crawl-space/"},
    "24014":{"n":"Southwest Builders Inc.","u":"/partners/southwest-builders-inc/"},
    "24015":{"n":"ECC Restoration, Inc","u":"/partners/ecc-restoration-inc/"},
    "24017":{"n":"FIRST ONSITE Property Restoration","u":"/partners/first-onsite-property-restoration-roanoke/"},
    "24018":{"n":"Sure-Dri Basement Waterproofing","u":"/partners/sure-dri-basement-waterproofing/"},
    "24019":{"n":"The Crew Cleaning & Restoration","u":"/partners/the-crew-cleaning-restoration-hollins/"},
    "24060":{"n":"VA Commercial Roofers Blacksburg","u":"/partners/va-commercial-roofers-blacksburg/"},
    "24073":{"n":"All Pest Control Inc","u":"/partners/all-pest-control-inc/"},
    "24078":{"n":"Shelter Construction Services - Shelter Roofing & Solar","u":"/partners/shelter-construction-services-shelter-roofing-solar/"},
    "24101":{"n":"Moorman’s Wildlife Management and Pest Control","u":"/partners/moorman-s-wildlife-management-and-pest-control/"},
    "24112":{"n":"Roto-Rooter Plumbing, Drain, & Water Cleanup Service","u":"/partners/roto-rooter-plumbing-drain-water-cleanup-service/"},
    "24121":{"n":"The Crew Cleaning & Restoration","u":"/partners/the-crew-cleaning-restoration/"},
    "24153":{"n":"ServiceMaster of Roanoke","u":"/partners/servicemaster-of-roanoke/"},
    "24175":{"n":"Seal-Tite Basement Waterproofing - Roanoke","u":"/partners/seal-tite-basement-waterproofing-roanoke/"},
    "24179":{"n":"Bone-Dry Construction & Basement Waterproofing, Inc.","u":"/partners/bone-dry-construction-basement-waterproofing-inc/"},
    "24184":{"n":"Lakeside Renovations","u":"/partners/lakeside-renovations/"},
    "24201":{"n":"Garland Building Services LLC","u":"/partners/garland-building-services-llc/"},
    "24202":{"n":"Master Foundation and Crawl Space Repair","u":"/partners/master-foundation-and-crawl-space-repair/"},
    "24228":{"n":"Soft Wash America","u":"/partners/soft-wash-america/"},
    "24230":{"n":"Fortitude Construction LLC","u":"/partners/fortitude-construction-llc/"},
    "24340":{"n":"DG Foundation & Drainage LLC","u":"/partners/dg-foundation-drainage-llc/"},
    "24360":{"n":"C&S Construction Services, Inc.","u":"/partners/c-s-construction-services-inc/"},
    "24382":{"n":"Astrid Environmental Services","u":"/partners/astrid-environmental-services/"},
    "24401":{"n":"Baber Enterprises Roofing and More","u":"/partners/baber-enterprises-roofing-and-more/"},
    "24421":{"n":"Churchville Pump Service Inc","u":"/partners/churchville-pump-service-inc/"},
    "24467":{"n":"Rainbow Restoration of Harrisonburg & Staunton","u":"/partners/rainbow-restoration-of-harrisonburg-staunton/"},
    "24501":{"n":"Merit Restorations","u":"/partners/merit-restorations/"},
    "24502":{"n":"Level Up Foundation Repair","u":"/partners/level-up-foundation-repair/"},
    "24504":{"n":"AquaSpores","u":"/partners/aquaspores/"},
    "24521":{"n":"Acculevel","u":"/partners/acculevel/"},
    "24523":{"n":"E 37 Waterproofing","u":"/partners/e-37-waterproofing/"},
    "24540":{"n":"The Crew Cleaning","u":"/partners/the-crew-cleaning/"},
    "24541":{"n":"Virginia Restoration Company","u":"/partners/virginia-restoration-company/"},
    "24550":{"n":"Rainbow Restoration of Lynchburg","u":"/partners/rainbow-restoration-of-lynchburg/"},
    "24551":{"n":"The Crew Cleaning & Restoration of Lynchburg","u":"/partners/the-crew-cleaning-restoration-of-lynchburg/"},
    "24553":{"n":"Mid-Atlantic Home Improvement","u":"/partners/mid-atlantic-home-improvement/"},
    "24556":{"n":"SERVPRO of Lynchburg / Bedford & Campbell Counties","u":"/partners/servpro-of-lynchburg-bedford-campbell-counties/"},
    "24558":{"n":"Solutions Heating & Cooling","u":"/partners/solutions-heating-cooling-halifax/"},
    "24588":{"n":"Omega Disaster Restoration","u":"/partners/omega-disaster-restoration-rustburg/"},
    "24641":{"n":"Rife Remodeling & Flooring","u":"/partners/rife-remodeling-flooring/"}
  };

  // Regional fallback: when an exact ZIP isn't listed, match the numerically
  // nearest real contractor sharing the same area, so the banner always links
  // to a genuine business listing page.
  var DEFAULT_CONTRACTOR = { n: "Virginia Basement Waterproofing Network", u: "/partners/" };
  var ZIP_KEYS = Object.keys(VBW_BY_ZIP).map(Number).sort(function (a, b) { return a - b; });

  function contractorForZip(zip) {
    zip = String(zip).replace(/\D/g, "").slice(0, 5);
    if (VBW_BY_ZIP[zip]) return VBW_BY_ZIP[zip];
    var target = parseInt(zip, 10);
    if (isNaN(target) || !ZIP_KEYS.length) return DEFAULT_CONTRACTOR;
    // Find the numerically closest listed ZIP (same prefix preferred via distance)
    var best = ZIP_KEYS[0], bestDist = Math.abs(ZIP_KEYS[0] - target);
    for (var i = 1; i < ZIP_KEYS.length; i++) {
      var d = Math.abs(ZIP_KEYS[i] - target);
      if (d < bestDist) { bestDist = d; best = ZIP_KEYS[i]; }
    }
    return VBW_BY_ZIP[String(best)] || DEFAULT_CONTRACTOR;
  }

  // ── Dealer/contractor banner ─────────────────────────────────────────────────
  var dealerCard = document.getElementById("dealer-card");

  function renderDealer(zip) {
    if (!dealerCard) return;
    var c = contractorForZip(zip);
    var zipEl  = document.getElementById("dealer-zip");
    var nameEl = document.getElementById("dealer-name");
    var changeEl = document.getElementById("dealer-change");
    if (zipEl) zipEl.textContent = "ZIP: " + zip;
    if (nameEl) nameEl.innerHTML = '<a href="' + c.u + '" style="color:#fff;font-weight:700;">' + c.n + "</a>";
    if (changeEl) changeEl.style.display = "flex";
    // Remove any location prompt if present
    var prompt = document.getElementById("vbw-loc-prompt");
    if (prompt) prompt.remove();
  }

  function showLocationPrompt() {
    if (!dealerCard) return;
    var nameEl = document.getElementById("dealer-name");
    var changeEl = document.getElementById("dealer-change");
    if (nameEl) nameEl.textContent = "Enable location to find your nearest contractor";
    if (changeEl) changeEl.style.display = "none";
    // Insert enable-location button if not already present
    if (!document.getElementById("vbw-loc-prompt")) {
      var btn = document.createElement("button");
      btn.id = "vbw-loc-prompt";
      btn.textContent = "Enable Location";
      btn.style.cssText =
        "margin-top:8px;padding:7px 16px;background:var(--accent);color:#fff;" +
        "border:none;border-radius:7px;font-weight:700;cursor:pointer;font-size:.9rem;";
      btn.addEventListener("click", function () {
        btn.remove();
        requestGeoLocation();
      });
      var right = dealerCard.querySelector(".service-banner__right");
      if (right) right.appendChild(btn);
    }
    // Still try IP fallback silently
    ipFallback(true);
  }

  function ipFallback(silent) {
    fetch("https://ipwho.is/")
      .then(function (r) { return r.json(); })
      .then(function (data) {
        var zip = data && (data.postal || data.postal_code);
        if (zip && /^\d{5}/.test(String(zip))) {
          renderDealer(String(zip).slice(0, 5));
        } else if (!silent) {
          setDefaultMessage();
        }
      })
      .catch(function () { if (!silent) setDefaultMessage(); });
  }

  function setDefaultMessage() {
    var nameEl = document.getElementById("dealer-name");
    if (nameEl) nameEl.innerHTML =
      'Call <a href="tel:+17577439050" style="color:#fff;font-weight:700;">(757) 743-9050</a> for your local contractor';
  }

  function requestGeoLocation() {
    if (!navigator.geolocation) { ipFallback(false); return; }
    var nameEl = document.getElementById("dealer-name");
    if (nameEl) nameEl.textContent = "Detecting your location…";
    navigator.geolocation.getCurrentPosition(
      function (pos) {
        // Reverse-geocode lat/lng to ZIP via free API (no key required)
        var lat = pos.coords.latitude, lon = pos.coords.longitude;
        fetch("https://api.bigdatacloud.net/data/reverse-geocode-client?latitude=" + lat + "&longitude=" + lon + "&localityLanguage=en")
          .then(function (r) { return r.json(); })
          .then(function (d) {
            var zip = d && d.postcode;
            if (zip && /^\d{5}/.test(String(zip))) {
              renderDealer(String(zip).slice(0, 5));
            } else {
              ipFallback(false);
            }
          })
          .catch(function () { ipFallback(false); });
      },
      function (err) {
        if (err.code === 1 /* PERMISSION_DENIED */) {
          showLocationPrompt();
        } else {
          ipFallback(false);
        }
      },
      { timeout: 8000, maximumAge: 300000 }
    );
  }

  function detectLocation() {
    if (!dealerCard) return;
    if (navigator.geolocation) {
      var nameEl = document.getElementById("dealer-name");
      if (nameEl) nameEl.textContent = "Detecting your location…";
      // Use a short timeout to check if permission was previously granted
      navigator.permissions && navigator.permissions.query({ name: "geolocation" })
        .then(function (status) {
          if (status.state === "denied") {
            showLocationPrompt();
          } else {
            requestGeoLocation();
          }
        })
        .catch(function () { requestGeoLocation(); });
      if (!navigator.permissions) requestGeoLocation();
    } else {
      ipFallback(false);
    }
  }

  // "Change Location" → inject a mini ZIP form
  var dealerChange = document.getElementById("dealer-change");
  if (dealerChange) {
    dealerChange.addEventListener("click", function (e) {
      e.preventDefault();
      var existing = document.getElementById("dealer-mini-form");
      if (existing) { existing.querySelector("input").focus(); return; }
      var mini = document.createElement("form");
      mini.id = "dealer-mini-form";
      mini.style.cssText = "display:flex;gap:8px;margin-top:10px;flex-wrap:wrap;";
      mini.innerHTML =
        '<input type="text" inputmode="numeric" maxlength="5" placeholder="Enter ZIP code"' +
        ' style="padding:9px 12px;border:none;border-radius:7px;font-size:1rem;width:140px;color:#111;">' +
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

  if (dealerCard) detectLocation();

  // ── Partner directory search filter ─────────────────────────────────────────
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

  // ── Quote form (client-side confirmation) ────────────────────────────────────
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
