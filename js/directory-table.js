/* ============================================================================
   Directory tables (/partners/ and /reviews/).

   Progressive enhancement only: the table is fully rendered in the HTML, so it
   works with JS off. This adds live text search, column sorting and a row
   counter on top of it.
   ============================================================================ */
(function () {
  "use strict";

  var table = document.querySelector("[data-directory-table]");
  if (!table) return;

  var tbody = table.tBodies[0];
  var rows = Array.prototype.slice.call(tbody.rows);
  var search = document.getElementById("dirSearch");
  var counter = document.getElementById("dirCount");
  var note = document.querySelector(".dir-empty-note");
  var total = rows.length;

  function label(n) {
    return n === total
      ? total + " businesses"
      : n + " of " + total + " businesses";
  }

  // ---- search --------------------------------------------------------------
  function filter() {
    var q = (search.value || "").trim().toLowerCase();
    var shown = 0;
    rows.forEach(function (tr) {
      var hit = !q || (tr.getAttribute("data-search") || "").indexOf(q) !== -1;
      tr.hidden = !hit;
      if (hit) shown++;
    });
    if (counter) counter.textContent = label(shown);
    table.classList.toggle("is-empty", shown === 0);
    if (note) note.style.display = shown === 0 ? "block" : "none";
  }

  if (search) {
    search.addEventListener("input", filter);
    search.form.addEventListener("submit", function (e) { e.preventDefault(); });
  }

  // ---- sorting -------------------------------------------------------------
  function cellValue(tr, idx, numeric) {
    var td = tr.cells[idx];
    if (!td) return numeric ? -Infinity : "";
    var raw = td.getAttribute("data-sort");
    if (raw == null) raw = td.textContent;
    raw = raw.trim();
    if (!numeric) return raw.toLowerCase();
    var n = parseFloat(raw.replace(/,/g, ""));
    return isNaN(n) ? -Infinity : n;
  }

  Array.prototype.forEach.call(table.tHead.rows[0].cells, function (th, idx) {
    if (!th.hasAttribute("data-sortable")) return;
    var numeric = th.getAttribute("data-sortable") === "number";
    th.tabIndex = 0;
    th.setAttribute("role", "button");

    function sort() {
      // third click on the same column restores the original order
      var dir = th.getAttribute("data-dir");
      dir = dir === "asc" ? "desc" : dir === "desc" ? "" : (numeric ? "desc" : "asc");

      Array.prototype.forEach.call(table.tHead.rows[0].cells, function (o) {
        o.removeAttribute("data-dir");
        o.removeAttribute("aria-sort");
      });

      var ordered;
      if (!dir) {
        ordered = rows.slice();
      } else {
        var sign = dir === "asc" ? 1 : -1;
        ordered = rows.slice().sort(function (a, b) {
          var va = cellValue(a, idx, numeric), vb = cellValue(b, idx, numeric);
          if (va < vb) return -1 * sign;
          if (va > vb) return 1 * sign;
          return 0;
        });
        th.setAttribute("data-dir", dir);
        th.setAttribute("aria-sort", dir === "asc" ? "ascending" : "descending");
      }

      var frag = document.createDocumentFragment();
      ordered.forEach(function (tr) { frag.appendChild(tr); });
      tbody.appendChild(frag);
    }

    th.addEventListener("click", sort);
    th.addEventListener("keydown", function (e) {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); sort(); }
    });
  });

  if (counter) counter.textContent = label(total);
})();
