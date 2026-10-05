/* The slow way, made survivable — progressive enhancement only.
   Everything on these pages works with this file absent:
   the chapter list, previous/next, the folds and the figures are plain HTML.
   This file adds: arrow-key navigation, a "continue where you left off"
   link on the index, and the one interactive figure (chapter 7). */
(function () {
  "use strict";
  document.documentElement.classList.add("js");

  var KEY = "slowway:last";
  var page = document.body.getAttribute("data-page") || "";
  var title = document.body.getAttribute("data-title") || "";

  // Remember the last chapter opened (per browser, never leaves the machine).
  try {
    if (page && page !== "index" && page !== "sources") {
      localStorage.setItem(KEY, JSON.stringify({ page: page, title: title }));
    }
  } catch (e) { /* storage may be unavailable; nothing depends on it */ }

  // Index: offer to continue.
  var cont = document.getElementById("continue");
  if (cont) {
    try {
      var last = JSON.parse(localStorage.getItem(KEY) || "null");
      if (last && last.page) {
        var a = document.createElement("a");
        a.href = last.page + ".html";
        a.textContent = "Continue where you left off: " + last.title;
        cont.appendChild(a);
        cont.hidden = false;
      }
    } catch (e) { /* ignore */ }
  }

  // Arrow keys move between chapters. Never while typing or on a slider.
  var prev = document.querySelector(".pager a.prev");
  var next = document.querySelector(".pager a.next");
  document.addEventListener("keydown", function (ev) {
    var t = ev.target;
    var tag = t && t.tagName ? t.tagName.toLowerCase() : "";
    if (tag === "input" || tag === "textarea" || tag === "select" || (t && t.isContentEditable)) return;
    if (ev.altKey || ev.ctrlKey || ev.metaKey || ev.shiftKey) return;
    if (ev.key === "ArrowRight" && next) { window.location.href = next.getAttribute("href"); }
    if (ev.key === "ArrowLeft" && prev) { window.location.href = prev.getAttribute("href"); }
  });
  var keys = document.querySelector(".pager .keys");
  if (keys) keys.hidden = false;

  // Chapter 7: the reverse DCF, run forwards and backwards.
  // Same arithmetic as the static table on the page: ten years of cash flow
  // growing at g, then a terminal value growing at 2.5%, all discounted at 9.5%.
  var slider = document.getElementById("rdcf-price");
  if (slider) {
    var RATE = 0.095, TERM = 0.025, YEARS = 10, FCF0 = 10;
    function valueAt(g) {
      var v = 0, cf = FCF0;
      for (var t = 1; t <= YEARS; t++) {
        cf = cf * (1 + g);
        v += cf / Math.pow(1 + RATE, t);
      }
      var terminal = cf * (1 + TERM) / (RATE - TERM);
      v += terminal / Math.pow(1 + RATE, YEARS);
      return v;
    }
    function impliedGrowth(price) {
      var lo = -0.9, hi = 1.0;
      for (var i = 0; i < 100; i++) {
        var mid = (lo + hi) / 2;
        if (valueAt(mid) < price) lo = mid; else hi = mid;
      }
      return (lo + hi) / 2;
    }
    var out = document.getElementById("rdcf-out");
    var outPrice = document.getElementById("rdcf-price-out");
    function render() {
      var price = Number(slider.value);
      var g = impliedGrowth(price);
      outPrice.textContent = price + " per share";
      var pct = (g * 100).toFixed(1);
      out.textContent = "The price assumes cash flow grows about " + pct + "% a year for ten years.";
    }
    slider.addEventListener("input", render);
    render();
    var wrap = document.getElementById("rdcf-explore");
    if (wrap) wrap.hidden = false;
  }
})();
