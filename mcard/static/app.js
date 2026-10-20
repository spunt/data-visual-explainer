(function () {
  "use strict";
  var doc = document.documentElement;
  doc.classList.add("js");
  var wide = window.matchMedia("(min-width: 901px)");

  // ---- depth rail: active section + reading progress
  var links = Array.prototype.slice.call(document.querySelectorAll(".rail a"));
  var sections = links.map(function (a) { return document.querySelector(a.getAttribute("href")); }).filter(Boolean);
  var bar = document.querySelector(".progress span");
  function onScroll() {
    var y = window.scrollY + 90, current = null;
    sections.forEach(function (s) { if (s.offsetTop <= y) current = s; });
    links.forEach(function (a) { a.classList.toggle("active", current && a.getAttribute("href") === "#" + current.id); });
    if (bar) {
      var max = document.body.scrollHeight - window.innerHeight;
      bar.style.width = (max > 0 ? Math.min(100, 100 * window.scrollY / max) : 0) + "%";
    }
  }
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // ---- scrollytelling: the sticky stage shows the active step's figure
  var stage = document.querySelector(".scrolly .stage");
  var steps = Array.prototype.slice.call(document.querySelectorAll(".scrolly .step"));
  function activate(step) {
    if (!step || step.classList.contains("active")) return;
    steps.forEach(function (s) { s.classList.remove("active"); });
    step.classList.add("active");
    if (stage && wide.matches) {
      var fig = step.querySelector(".step-fig");
      stage.innerHTML = '<div class="fade">' + (fig ? fig.innerHTML : "") + "</div>";
      stage.setAttribute("aria-hidden", "true");
      bindTerms(stage);
    }
  }
  if ("IntersectionObserver" in window && steps.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) { if (e.isIntersecting) activate(e.target); });
    }, { rootMargin: "-40% 0px -50% 0px" });
    steps.forEach(function (s) { io.observe(s); });
    activate(steps[0]);
  }

  // ---- glossary toggletips (WCAG 2.2 SC 1.4.13: dismissible, hoverable, persistent)
  var openTip = null, pinned = false, hideTimer = null;
  function place(tip, trigger) {
    var r = trigger.getBoundingClientRect();
    tip.hidden = false;
    var w = tip.offsetWidth;
    var left = Math.max(8, Math.min(window.scrollX + r.left, window.scrollX + document.documentElement.clientWidth - w - 8));
    tip.style.left = left + "px";
    tip.style.top = (window.scrollY + r.bottom + 8) + "px";
  }
  function show(trigger, pin) {
    clearTimeout(hideTimer);
    var tip = document.getElementById("tip-" + trigger.getAttribute("data-tip"));
    if (!tip) return;
    if (openTip && openTip !== tip) openTip.hidden = true;
    openTip = tip; pinned = !!pin;
    place(tip, trigger);
    trigger.setAttribute("aria-expanded", "true");
  }
  function hide(force) {
    if (!openTip || (pinned && !force)) return;
    openTip.hidden = true; openTip = null; pinned = false;
    document.querySelectorAll('.term[aria-expanded="true"]').forEach(function (t) { t.setAttribute("aria-expanded", "false"); });
  }
  function bindTerms(root) {
    root.querySelectorAll(".term").forEach(function (t) {
      if (t.dataset.bound) return;
      t.dataset.bound = "1";
      t.setAttribute("aria-expanded", "false");
      t.addEventListener("mouseenter", function () { show(t, false); });
      t.addEventListener("mouseleave", function () { hideTimer = setTimeout(function () { hide(false); }, 250); });
      t.addEventListener("focus", function () { show(t, false); });
      t.addEventListener("blur", function () { hideTimer = setTimeout(function () { hide(false); }, 150); });
      t.addEventListener("click", function (ev) { ev.stopPropagation(); if (openTip && pinned) { hide(true); } else { show(t, true); } });
    });
  }
  bindTerms(document);
  document.querySelectorAll(".tip").forEach(function (tip) {
    tip.addEventListener("mouseenter", function () { clearTimeout(hideTimer); });
    tip.addEventListener("mouseleave", function () { hideTimer = setTimeout(function () { hide(false); }, 200); });
  });
  document.addEventListener("keydown", function (e) { if (e.key === "Escape") hide(true); });
  document.addEventListener("click", function (e) { if (openTip && !openTip.contains(e.target)) hide(true); });

  // ---- quiz
  document.querySelectorAll("fieldset.q").forEach(function (fs) {
    var answer = fs.getAttribute("data-answer");
    fs.addEventListener("change", function (e) {
      fs.querySelectorAll("label").forEach(function (l) { l.classList.remove("right", "wrong"); });
      var label = e.target.closest("label");
      label.classList.add(e.target.value === answer ? "right" : "wrong");
      var correct = fs.querySelector('input[value="' + answer + '"]');
      if (correct) correct.closest("label").classList.add("right");
      var why = fs.querySelector(".why");
      if (why) { why.hidden = false; why.setAttribute("role", "status"); }
    });
  });

  // ---- reveal + copy
  document.querySelectorAll("[data-reveal]").forEach(function (b) {
    b.addEventListener("click", function () { var t = document.querySelector(b.getAttribute("data-reveal")); if (t) t.hidden = false; });
  });
  function copy(text, btn) {
    var done = function () { var o = btn.textContent; btn.textContent = "Copied"; setTimeout(function () { btn.textContent = o; }, 1400); };
    if (navigator.clipboard && window.isSecureContext) { navigator.clipboard.writeText(text).then(done); return; }
    var ta = document.createElement("textarea"); ta.value = text; document.body.appendChild(ta); ta.select();
    try { document.execCommand("copy"); done(); } catch (e) {} document.body.removeChild(ta);
  }
  document.querySelectorAll("[data-copy]").forEach(function (b) {
    b.addEventListener("click", function () { var t = document.querySelector(b.getAttribute("data-copy")); if (t) copy(t.value || t.textContent, b); });
  });
  document.querySelectorAll("[data-copy-next]").forEach(function (b) {
    b.addEventListener("click", function () { var pre = b.closest("figure").querySelector("pre"); if (pre) copy(pre.textContent, b); });
  });
})();
