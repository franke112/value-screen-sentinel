/* The slow way, made survivable — progressive enhancement only.
   Everything on these pages works with this file absent: the chapter list,
   previous/next, the folds, and every figure in its default state are plain
   HTML and SVG. This file adds: arrow-key navigation, a "continue where you
   left off" link on the index, and the four figures a reader can move:
   the reverse DCF (two sliders), where every company stands (highlight a
   group), the rules that were tested (filter), the shadow book (read a bar).
   One file for both languages: the words come from the page itself. */
(function () {
  "use strict";
  document.documentElement.classList.add("js");

  var SV = (document.documentElement.getAttribute("lang") || "en").indexOf("sv") === 0;
  var KEY = "slowway:last";
  var page = document.body.getAttribute("data-page") || "";
  var title = document.body.getAttribute("data-title") || "";

  // Remember the last chapter opened (per browser, never leaves the machine).
  try {
    if (page && page !== "index" && page !== "sources" && page !== "ten-minutes") {
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
        a.textContent = (SV ? "Fortsätt där du slutade: " : "Continue where you left off: ") + last.title;
        cont.appendChild(a);
        cont.hidden = false;
      }
    } catch (e) { /* ignore */ }
  }

  // Arrow keys move between chapters. Never while typing, on a slider or a button.
  var prev = document.querySelector(".pager a.prev");
  var next = document.querySelector(".pager a.next");
  document.addEventListener("keydown", function (ev) {
    var t = ev.target;
    var tag = t && t.tagName ? t.tagName.toLowerCase() : "";
    if (tag === "input" || tag === "textarea" || tag === "select" || tag === "button" ||
        tag === "summary" || (t && t.isContentEditable)) return;
    if (ev.altKey || ev.ctrlKey || ev.metaKey || ev.shiftKey) return;
    if (ev.key === "ArrowRight" && next) { window.location.href = next.getAttribute("href"); }
    if (ev.key === "ArrowLeft" && prev) { window.location.href = prev.getAttribute("href"); }
  });
  var keys = document.querySelector(".pager .keys");
  if (keys) keys.hidden = false;

  // Controls that only make sense with scripts on are shipped hidden.
  var jsOnly = document.querySelectorAll(".js-only");
  for (var i = 0; i < jsOnly.length; i++) jsOnly[i].hidden = false;

  function num(x, dp) {
    var s = x.toFixed(dp === undefined ? 1 : dp);
    return SV ? s.replace(".", ",") : s;
  }
  function fill(template, values) {
    return template.replace(/\{(\w+)\}/g, function (m, k) { return values[k]; });
  }
  function attrs(el, map) {
    for (var k in map) el.setAttribute(k, map[k]);
  }

  // ------------------------------------------------------------------
  // 1. The reverse DCF: the price and your own belief, on one curve.
  // Same arithmetic as the static table on the page: ten years of cash flow
  // growing at g, then a terminal value growing at 2.5%, all at 9.5%.
  var rdcf = document.getElementById("rdcf");
  if (rdcf) {
    var T = JSON.parse(rdcf.getAttribute("data-i18n"));
    var G = JSON.parse(rdcf.getAttribute("data-geo"));
    var el = function (id) { return document.getElementById(id); };
    var valueAt = function (g) {
      var v = 0, cf = G.fcf0;
      for (var t = 1; t <= G.years; t++) { cf = cf * (1 + g); v += cf / Math.pow(1 + G.rate, t); }
      return v + cf * (1 + G.term) / (G.rate - G.term) / Math.pow(1 + G.rate, G.years);
    };
    var impliedGrowth = function (price) {
      var lo = -0.9, hi = 1.0;
      for (var i = 0; i < 100; i++) {
        var mid = (lo + hi) / 2;
        if (valueAt(mid) < price) lo = mid; else hi = mid;
      }
      return (lo + hi) / 2;
    };
    var X = function (gPct) { return G.x0 + (gPct - G.gmin) / (G.gmax - G.gmin) * (G.x1 - G.x0); };
    var Y = function (v) { return G.y1 - Math.min(v, G.vmax) / G.vmax * (G.y1 - G.y0); };
    var priceIn = el("rdcf-price"), beliefIn = el("rdcf-belief-in");
    var render = function () {
      var price = Number(priceIn.value), belief = Number(beliefIn.value);
      var g = impliedGrowth(price) * 100, v = valueAt(belief / 100);
      var px = X(g), py = Y(price), bx = X(belief), by = Y(v);
      el("rdcf-price-out").textContent = String(price);
      el("rdcf-belief-out").textContent = num(belief);
      attrs(el("rdcf-pline"), { x2: px, y1: py, y2: py });
      attrs(el("rdcf-pdrop"), { x1: px, x2: px, y1: py });
      attrs(el("rdcf-pdot"), { cx: px, cy: py });
      attrs(el("rdcf-bline"), { x1: bx, x2: bx, y2: by });
      attrs(el("rdcf-bh"), { x2: bx, y1: by, y2: by });
      attrs(el("rdcf-bsq"), { x: bx - 6, y: by - 6 });
      // the two labels keep clear of each other and of the edges
      var plab = el("rdcf-plab"), blab = el("rdcf-blab");
      plab.textContent = fill(T.plab, { p: price, g: num(g) });
      blab.textContent = fill(T.blab, { b: num(belief), v: Math.round(v) });
      var pLeft = px > G.x0 + 190;
      attrs(plab, { x: pLeft ? px - 12 : px + 12, y: py - 10, "text-anchor": pLeft ? "end" : "start" });
      var bRight = bx < G.x1 - 190;
      var bBelow = Math.abs(by - py) < 30 ? by + 34 : by + 16;
      attrs(blab, { x: bRight ? bx + 12 : bx - 12, y: Math.min(bBelow, G.y1 - 8), "text-anchor": bRight ? "start" : "end" });
      var d = (price / v - 1) * 100;
      var gap = d < -0.5 ? fill(T.below, { d: num(-d, 0) })
              : d > 0.5 ? fill(T.above, { d: num(d, 0) }) : T.equal;
      el("rdcf-read").textContent =
        fill(T.assumes, { p: price, g: num(g) }) + " " +
        fill(T.worth, { b: num(belief), v: Math.round(v) }) + " " + gap;
    };
    priceIn.addEventListener("input", render);
    beliefIn.addEventListener("input", render);
    render();

    // Hover: a hairline at the pointer's growth rate, and what that is worth.
    var plot = el("rdcf-plot"), hover = el("rdcf-hover"), svg = plot.ownerSVGElement;
    var show = function (ev) {
      var pt = svg.createSVGPoint();
      pt.x = ev.clientX; pt.y = ev.clientY;
      var loc = pt.matrixTransform(svg.getScreenCTM().inverse());
      var gPct = G.gmin + (loc.x - G.x0) / (G.x1 - G.x0) * (G.gmax - G.gmin);
      gPct = Math.max(G.gmin, Math.min(G.gmax, Math.round(gPct * 2) / 2));
      var v = valueAt(gPct / 100), x = X(gPct), y = Y(v);
      attrs(el("rdcf-hline"), { x1: x, x2: x });
      attrs(el("rdcf-hdot"), { cx: x, cy: y });
      var txt = el("rdcf-htxt");
      txt.textContent = fill(T.hover, { g: num(gPct), v: Math.round(v) });
      var w = txt.getComputedTextLength() + 16;
      var tx = Math.min(Math.max(x - w / 2, G.x0), G.x1 - w);
      attrs(el("rdcf-hbg"), { x: tx, y: G.y0, width: w });
      attrs(txt, { x: tx + 8, y: G.y0 + 15 });
      hover.setAttribute("visibility", "visible");
    };
    plot.addEventListener("pointermove", show);
    plot.addEventListener("pointerdown", show);
    plot.addEventListener("pointerleave", function () { hover.setAttribute("visibility", "hidden"); });
  }

  // ------------------------------------------------------------------
  // 2. Where every company stands: point at a group, or tab to it.
  var funnel = document.getElementById("funnel");
  if (funnel) {
    var fRead = document.getElementById("funnel-read");
    var fAll = funnel.getAttribute("data-all");
    var groups = funnel.querySelectorAll(".fgroup");
    var buttons = funnel.querySelectorAll(".fbtn");
    var pick = function (key) {
      for (var i = 0; i < groups.length; i++) {
        groups[i].classList.toggle("dim", !!key && groups[i].getAttribute("data-group") !== key);
      }
      var said = fAll;
      for (var j = 0; j < buttons.length; j++) {
        var on = buttons[j].getAttribute("data-group") === key;
        buttons[j].parentNode.classList.toggle("on", on);
        if (on) {
          said = buttons[j].querySelector(".fcount").textContent + " — " +
                 buttons[j].querySelector(".fname").textContent + ": " +
                 buttons[j].parentNode.querySelector(".fmean").textContent;
        }
      }
      fRead.textContent = said;
    };
    var bind = function (node) {
      var key = node.getAttribute("data-group");
      node.addEventListener("pointerenter", function () { pick(key); });
      node.addEventListener("pointerleave", function () { pick(null); });
      node.addEventListener("focus", function () { pick(key); });
      node.addEventListener("blur", function () { pick(null); });
      node.addEventListener("click", function () { pick(key); });
    };
    for (var b = 0; b < buttons.length; b++) bind(buttons[b]);
    for (var q = 0; q < groups.length; q++) bind(groups[q]);
  }

  // ------------------------------------------------------------------
  // 3. Every rule that was tested: show one group, or all.
  var yard = document.getElementById("graveyard");
  if (yard) {
    var chips = yard.querySelectorAll(".chip");
    var sections = yard.querySelectorAll(".gsection");
    var only = function (show) {
      for (var i = 0; i < sections.length; i++) {
        sections[i].hidden = show !== "all" && sections[i].getAttribute("data-group") !== show;
      }
      for (var j = 0; j < chips.length; j++) {
        chips[j].setAttribute("aria-pressed", chips[j].getAttribute("data-show") === show ? "true" : "false");
      }
    };
    for (var c = 0; c < chips.length; c++) {
      chips[c].addEventListener("click", function () { only(this.getAttribute("data-show")); });
    }
  }

  // ------------------------------------------------------------------
  // 4. The shadow book so far: read a part of a bar.
  var shadow = document.getElementById("shadow");
  if (shadow) {
    var sRead = document.getElementById("shadow-read");
    var sDefault = shadow.getAttribute("data-default");
    var segs = shadow.querySelectorAll(".sseg");
    var tell = function (node) {
      for (var i = 0; i < segs.length; i++) segs[i].classList.toggle("dim", !!node && segs[i] !== node);
      sRead.textContent = node ? node.getAttribute("data-tip") : sDefault;
    };
    for (var s = 0; s < segs.length; s++) {
      (function (node) {
        node.addEventListener("pointerenter", function () { tell(node); });
        node.addEventListener("pointerleave", function () { tell(null); });
        node.addEventListener("focus", function () { tell(node); });
        node.addEventListener("blur", function () { tell(null); });
        node.addEventListener("click", function () { tell(node); });
      })(segs[s]);
    }
  }
})();
