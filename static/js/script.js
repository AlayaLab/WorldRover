/* WorldRover project page — hero media wall + scroll reveal */
(function () {
  "use strict";

  // ---- Hero media wall: fill columns with dataset stills ----
  var IMAGES = [
    "static/images/scenes.jpg",
    "static/images/appearances.jpg",
    "static/images/whitemodel.jpg",
    "static/images/characters_humanoid.jpg",
    "static/images/characters_animal.jpg",
    "static/images/trajectory.jpg",
    "static/images/tracks.jpg",
    "static/images/thirdperson_controls.jpg",
    "static/images/panoramic.png",
    "static/images/teaser.jpg"
  ];

  function card(src) {
    var d = document.createElement("div");
    d.className = "wall-card";
    // vary the tile height so the wall reads as a masonry rather than a grid
    d.style.height = (150 + Math.round(Math.abs(hash(src)) % 110)) + "px";
    var img = document.createElement("img");
    img.src = src;
    img.alt = "";
    img.loading = "lazy";
    d.appendChild(img);
    return d;
  }

  // small deterministic hash so heights are stable across reloads
  function hash(s) {
    var h = 0;
    for (var i = 0; i < s.length; i++) { h = (h * 31 + s.charCodeAt(i)) | 0; }
    return h;
  }

  var wall = document.getElementById("media-wall");
  if (wall) {
    var COLS = 5;
    for (var c = 0; c < COLS; c++) {
      var col = document.createElement("div");
      var dir = c % 2 === 0 ? "wall-up" : "wall-down";
      var speed = c === 2 ? " slow" : c === 3 ? " fast" : "";
      col.className = "wall-column " + dir + speed;
      // enough cards to overflow, then duplicated for a seamless -50% loop
      var base = [];
      for (var i = 0; i < 6; i++) {
        base.push(IMAGES[(c * 6 + i * 2 + i) % IMAGES.length]);
      }
      base.concat(base).forEach(function (src) { col.appendChild(card(src)); });
      wall.appendChild(col);
    }
  }

  // ---- Scroll reveal ----
  var reveals = document.querySelectorAll(".reveal");
  if (!("IntersectionObserver" in window)) {
    reveals.forEach(function (el) { el.classList.add("visible"); });
    return;
  }
  var io = new IntersectionObserver(function (entries) {
    entries.forEach(function (e) {
      if (e.isIntersecting) {
        e.target.classList.add("visible");
        io.unobserve(e.target);
      }
    });
  }, { threshold: 0.12, rootMargin: "0px 0px -8% 0px" });
  reveals.forEach(function (el) { io.observe(el); });
})();

/* ---- Video showcase + interactive switchers (renderer-style) ---- */
(function () {
  "use strict";

  // decorative keyframe scrubber strips
  document.querySelectorAll("[data-keyframes]").forEach(function (kf) {
    for (var i = 0; i < 16; i++) {
      var s = document.createElement("span");
      if (i % 3 === 0) s.className = "on";
      kf.appendChild(s);
    }
  });

  // mock play button feedback (no real video yet)
  document.querySelectorAll(".showcase .play").forEach(function (p) {
    p.addEventListener("click", function () {
      p.animate(
        [{ transform: "scale(1)" }, { transform: "scale(0.9)" }, { transform: "scale(1)" }],
        { duration: 240 }
      );
    });
  });

  // modality switcher: tabs swap the frame image / filter / badge / caption
  document.querySelectorAll("[data-switch]").forEach(function (root) {
    var img = root.querySelector("[data-frame]");
    var badge = root.querySelector(".badge[data-badge]");
    var note = root.querySelector("[data-noteel]");
    var cap = root.querySelector(".switch-cap[data-cap]");
    var tabs = root.querySelectorAll(".switch-tab");
    tabs.forEach(function (btn) {
      btn.addEventListener("click", function () {
        tabs.forEach(function (b) { b.classList.remove("active"); });
        btn.classList.add("active");
        img.src = btn.getAttribute("data-img");
        img.className = btn.getAttribute("data-filter");
        badge.textContent = btn.getAttribute("data-badge");
        cap.textContent = btn.getAttribute("data-cap");
        var n = btn.getAttribute("data-note");
        if (note) { if (n) { note.textContent = n; note.hidden = false; } else { note.hidden = true; } }
      });
    });
  });

  // climate switcher: thumbnails swap the stage frame + badge
  document.querySelectorAll("[data-climate]").forEach(function (root) {
    var img = root.querySelector("[data-frame]");
    var badge = root.querySelector(".badge[data-badge]");
    var thumbs = root.querySelectorAll(".thumb");
    thumbs.forEach(function (t) {
      t.addEventListener("click", function () {
        thumbs.forEach(function (x) { x.classList.remove("active"); });
        t.classList.add("active");
        img.src = t.getAttribute("data-img");
        badge.textContent = t.getAttribute("data-name");
      });
    });
  });
})();
