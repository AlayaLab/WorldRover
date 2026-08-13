/* WorldRover renderer-style variant — interactions */
(function () {
  "use strict";

  // scroll progress bar
  var bar = document.getElementById("progress");
  function onScroll() {
    var h = document.documentElement;
    var max = h.scrollHeight - h.clientHeight;
    bar.style.width = (max > 0 ? (h.scrollTop / max) * 100 : 0) + "%";
  }
  document.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  // decorative keyframe strip (mock video scrubber)
  var kf = document.getElementById("keyframes");
  if (kf) {
    for (var i = 0; i < 14; i++) {
      var s = document.createElement("span");
      if (i % 3 === 0) s.className = "on";
      kf.appendChild(s);
    }
  }

  // count-up stats when the stats section reveals
  function countUp(el) {
    var to = parseFloat(el.getAttribute("data-to"));
    var suffix = el.getAttribute("data-suffix") || "";
    var start = null, dur = 1100;
    function step(t) {
      if (start === null) start = t;
      var p = Math.min((t - start) / dur, 1);
      var eased = 1 - Math.pow(1 - p, 3);
      var val = to * eased;
      el.textContent = (to % 1 === 0 ? Math.round(val) : val.toFixed(1)) + (p === 1 ? suffix : "");
      if (p < 1) requestAnimationFrame(step);
    }
    requestAnimationFrame(step);
  }

  // reveal + trigger count-up
  var io = ("IntersectionObserver" in window) ? new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (!e.isIntersecting) return;
      e.target.classList.add("vis");
      e.target.querySelectorAll && e.target.querySelectorAll(".count").forEach(countUp);
      io.unobserve(e.target);
    });
  }, { threshold: 0.15 }) : null;
  document.querySelectorAll(".reveal").forEach(function (el) {
    if (io) io.observe(el); else { el.classList.add("vis"); el.querySelectorAll(".count").forEach(countUp); }
  });

  // modality switcher
  var mImg = document.getElementById("modeImg");
  var mBadge = document.getElementById("modeBadge");
  var mCap = document.getElementById("modeCap");
  var mNote = document.getElementById("modeNote");
  document.querySelectorAll("#modeTabs .toggle").forEach(function (btn) {
    btn.addEventListener("click", function () {
      document.querySelectorAll("#modeTabs .toggle").forEach(function (b) { b.classList.remove("active"); });
      btn.classList.add("active");
      mImg.src = btn.getAttribute("data-img");
      mImg.className = btn.getAttribute("data-filter");
      mBadge.textContent = btn.getAttribute("data-badge");
      mCap.textContent = btn.getAttribute("data-cap");
      var note = btn.getAttribute("data-note");
      if (note) { mNote.textContent = note; mNote.hidden = false; } else { mNote.hidden = true; }
    });
  });

  // weather / lighting switcher
  var wImg = document.getElementById("wxImg");
  var wBadge = document.getElementById("wxBadge");
  document.querySelectorAll("#wxThumbs .thumb").forEach(function (t) {
    t.addEventListener("click", function () {
      document.querySelectorAll("#wxThumbs .thumb").forEach(function (x) { x.classList.remove("active"); });
      t.classList.add("active");
      wImg.src = t.getAttribute("data-img");
      wBadge.textContent = t.getAttribute("data-name");
    });
  });

  // mock play button: gentle pulse feedback only (no real video yet)
  document.querySelectorAll(".media-frame .play").forEach(function (p) {
    p.addEventListener("click", function () {
      p.animate([{ transform: "scale(1)" }, { transform: "scale(0.9)" }, { transform: "scale(1)" }], { duration: 260 });
    });
  });
})();
