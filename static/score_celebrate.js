/**
 * Pixel fireworks on reading/listening post-submit results.
 * Original 8-bit art only — no copyrighted third-party sprites or stock emoji.
 * Keep band thresholds in sync with score_celebrate.py.
 */
(function (root) {
  "use strict";

  var SMALL_FIREWORKS = "small_fireworks";
  var FIREWORKS_RING = "fireworks_ring";
  var FIREWORKS_CROWN = "fireworks_crown";
  var SMALL_MIN = 7.0;
  var RING_MIN = 7.5;
  var CROWN_MIN = 8.0;
  var STORAGE_PREFIX = "ielts-score-celebrate:";

  var PALETTE = ["#e6c24d", "#c49a3a", "#f3d56a", "#c45c4a", "#f7f4f0", "#7eb8c9", "#d7eef4"];
  var GOLD_PALETTE = ["#e6c24d", "#c49a3a", "#f3d56a", "#f7f4f0", "#c45c4a"];

  // Original pixel sprites. "." is empty; letters map to CSS color classes.
  var SPARK_SPRITE = [
    "....Y....",
    "...YCY...",
    "..YCBCY..",
    ".YCBCBCY.",
    "YCBCWBCBY",
    ".YCBCBCY.",
    "..YCBCY..",
    "...YCY...",
    "....Y....",
  ];

  var RING_SPRITE = [
    "......KKKK......",
    ".....KBBBBK.....",
    "....KBWCCWBK....",
    "....KBCNNCBK....",
    "....KBWCCWBK....",
    ".....KBBBBK.....",
    "......KKKK......",
    "......KDDK......",
    ".....KDGGDK.....",
    "...KKGGGGGKKK...",
    "..KDGGKKKKGGDK..",
    ".KDGGK....KGGDK.",
    ".KDGK......KGDK.",
    ".KDGK......KGDK.",
    ".KDGK......KGDK.",
    ".KDGGK....KGGDK.",
    "..KDGGKKKKGGDK..",
    "...KKGGGGGGKK...",
    ".....KDDDDK.....",
    "......KKKK......",
  ];

  var CROWN_SPRITE = [
    "....K.....K.....K..",
    "...KRK...KCK...KRK.",
    "...KRK.K.KCK.K.KRK.",
    "..KGGKGGKGGKGGKGGK.",
    ".KGGGGGGGGGGGGGGGGK",
    ".KGYWYWYWYWYWYWYWYK",
    ".KDGGGGGGGGGGGGGGDK",
    "..KDDDDDDDDDDDDDDK.",
    "...KKKKKKKKKKKKKK..",
  ];

  var playing = false;
  var rootEl = null;
  var timerId = 0;
  var rafId = 0;
  var onResize = null;

  function celebrationTier(band) {
    if (band == null || band === "") return null;
    var value = Number(band);
    if (!isFinite(value)) return null;
    if (value < 0 || value > 9) return null;
    if (Math.abs(value * 2 - Math.round(value * 2)) > 1e-9) return null;
    if (value >= CROWN_MIN) return FIREWORKS_CROWN;
    if (value >= RING_MIN) return FIREWORKS_RING;
    if (value >= SMALL_MIN) return SMALL_FIREWORKS;
    return null;
  }

  function prefersReducedMotion() {
    try {
      return !!(window.matchMedia && window.matchMedia("(prefers-reduced-motion: reduce)").matches);
    } catch (err) {
      return false;
    }
  }

  function isReviewMode() {
    return !!(
      root.REVIEW_CONFIG ||
      (document.body && document.body.classList.contains("attempt-review"))
    );
  }

  function storageGet(key) {
    try {
      return sessionStorage.getItem(key);
    } catch (err) {
      return null;
    }
  }

  function storageSet(key, value) {
    try {
      sessionStorage.setItem(key, value);
    } catch (err) {
      /* private mode or disabled storage */
    }
  }

  function renderSprite(rows) {
    var el = document.createElement("div");
    el.className = "score-celebrate-sprite";
    el.setAttribute("aria-hidden", "true");
    el.style.setProperty("--cols", String(rows[0].length));
    for (var r = 0; r < rows.length; r += 1) {
      var line = rows[r];
      for (var c = 0; c < line.length; c += 1) {
        var ch = line.charAt(c);
        var cell = document.createElement("span");
        cell.className = "score-celebrate-cell" + (ch === "." ? " is-empty" : " px-" + ch);
        el.appendChild(cell);
      }
    }
    return el;
  }

  function spriteFor(tier) {
    if (tier === FIREWORKS_CROWN) return CROWN_SPRITE;
    if (tier === FIREWORKS_RING) return RING_SPRITE;
    return SPARK_SPRITE;
  }

  function durationFor(tier, reduced) {
    if (reduced) return 2200;
    if (tier === FIREWORKS_CROWN) return 5200;
    if (tier === FIREWORKS_RING) return 4500;
    return 3200;
  }

  function placeEmblem(emblem, tier) {
    var card = document.querySelector("#donePanel .done-card");
    var icon = document.querySelector("#donePanel .done-icon");
    var target = icon || card;
    if (!target) return;
    var rect = target.getBoundingClientRect();
    emblem.style.left = rect.left + rect.width / 2 + "px";
    if (tier === SMALL_FIREWORKS) {
      emblem.style.top = rect.top + "px";
    } else {
      var height = emblem.offsetHeight || 80;
      emblem.style.top = Math.max(12, rect.top - height - 8) + "px";
    }
  }

  function stop() {
    if (timerId) {
      clearTimeout(timerId);
      timerId = 0;
    }
    if (rafId) {
      cancelAnimationFrame(rafId);
      rafId = 0;
    }
    if (onResize) {
      window.removeEventListener("resize", onResize);
      onResize = null;
    }
    if (rootEl && rootEl.parentNode) {
      rootEl.parentNode.removeChild(rootEl);
    }
    rootEl = null;
    playing = false;
    if (document.body) document.body.classList.remove("score-celebrate-on");
  }

  function startFireworks(canvas, tier) {
    var ctx = canvas.getContext("2d");
    var particles = [];
    var rockets = [];
    var scale = 5;
    var burstPlan = [];
    var startedAt = Date.now();

    function sizeCanvas() {
      var w = Math.max(96, Math.floor(window.innerWidth / scale));
      var h = Math.max(72, Math.floor(window.innerHeight / scale));
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
      }
    }

    function cardBounds() {
      var card = document.querySelector("#donePanel .done-card");
      var cw = canvas.width;
      var ch = canvas.height;
      if (!card) {
        return { x: cw * 0.3, y: ch * 0.25, w: cw * 0.4, h: ch * 0.5 };
      }
      var rect = card.getBoundingClientRect();
      return {
        x: rect.left / scale,
        y: rect.top / scale,
        w: rect.width / scale,
        h: rect.height / scale,
      };
    }

    function burstCount() {
      if (tier === FIREWORKS_CROWN) return 14;
      if (tier === FIREWORKS_RING) return 11;
      return 4;
    }

    function burstPower() {
      if (tier === FIREWORKS_CROWN) return 1.45;
      if (tier === FIREWORKS_RING) return 1.25;
      return 0.7;
    }

    function burstParticles() {
      if (tier === FIREWORKS_CROWN) return 36;
      if (tier === FIREWORKS_RING) return 28;
      return 16;
    }

    function pickColor() {
      var set = tier === FIREWORKS_CROWN ? GOLD_PALETTE : PALETTE;
      return set[Math.floor(Math.random() * set.length)];
    }

    function spawnBurst(x, y) {
      var n = burstParticles();
      var power = burstPower();
      for (var i = 0; i < n; i += 1) {
        var angle = (Math.PI * 2 * i) / n + Math.random() * 0.2;
        var speed = 0.25 + Math.random() * power;
        particles.push({
          x: x,
          y: y,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed,
          color: pickColor(),
          life: 28 + Math.floor(Math.random() * 24),
          max: 1,
          size: Math.random() < 0.3 ? 2 : 1,
          gravity: 0.015,
        });
      }
    }

    function spawnRocket(at) {
      var box = cardBounds();
      var cw = canvas.width;
      var ch = canvas.height;
      var x;
      var targetY;
      if (tier === SMALL_FIREWORKS) {
        x = box.x + box.w * (0.25 + Math.random() * 0.5);
        targetY = box.y + box.h * (0.05 + Math.random() * 0.35);
      } else {
        x = cw * (0.1 + Math.random() * 0.8);
        targetY = ch * (0.12 + Math.random() * 0.42);
      }
      rockets.push({
        x: x,
        y: ch - 2,
        vx: (Math.random() - 0.5) * 0.2,
        vy: -1.4 - Math.random() * 0.6,
        targetY: targetY,
        color: pickColor(),
        when: at,
        launched: false,
      });
    }

    var total = burstCount();
    var i;
    for (i = 0; i < total; i += 1) {
      burstPlan.push(180 + i * (tier === SMALL_FIREWORKS ? 520 : 280) + Math.floor(Math.random() * 120));
    }
    burstPlan.forEach(function (at) {
      spawnRocket(at);
    });

    function tick() {
      sizeCanvas();
      var cw = canvas.width;
      var ch = canvas.height;
      ctx.clearRect(0, 0, cw, ch);
      var now = Date.now() - startedAt;
      var r;
      var p;

      for (r = 0; r < rockets.length; r += 1) {
        var rocket = rockets[r];
        if (!rocket.launched) {
          if (now >= rocket.when) rocket.launched = true;
          else continue;
        }
        if (rocket.done) continue;
        rocket.x += rocket.vx;
        rocket.y += rocket.vy;
        rocket.vy += 0.012;
        ctx.fillStyle = rocket.color;
        ctx.fillRect(Math.floor(rocket.x), Math.floor(rocket.y), 1, 2);
        if (rocket.y <= rocket.targetY || rocket.vy >= 0) {
          spawnBurst(rocket.x, rocket.y);
          rocket.done = true;
        }
      }

      for (p = particles.length - 1; p >= 0; p -= 1) {
        var dot = particles[p];
        dot.x += dot.vx;
        dot.y += dot.vy;
        dot.vy += dot.gravity;
        dot.vx *= 0.985;
        dot.life -= 1;
        if (dot.life <= 0) {
          particles.splice(p, 1);
          continue;
        }
        ctx.globalAlpha = Math.max(0.2, Math.min(1, dot.life / 18));
        ctx.fillStyle = dot.color;
        ctx.fillRect(Math.floor(dot.x), Math.floor(dot.y), dot.size, dot.size);
        ctx.globalAlpha = 1;
      }

      rafId = requestAnimationFrame(tick);
    }

    sizeCanvas();
    rafId = requestAnimationFrame(tick);
  }

  function start(tier) {
    stop();
    playing = true;
    if (document.body) document.body.classList.add("score-celebrate-on");

    var reduced = prefersReducedMotion();
    var wrap = document.createElement("div");
    wrap.className = "score-celebrate is-" + tier;
    wrap.setAttribute("role", "presentation");

    var canvas = document.createElement("canvas");
    canvas.className = "score-celebrate-canvas";
    canvas.setAttribute("aria-hidden", "true");
    wrap.appendChild(canvas);

    var emblem = document.createElement("div");
    emblem.className = "score-celebrate-emblem";
    emblem.appendChild(renderSprite(spriteFor(tier)));
    wrap.appendChild(emblem);

    var skip = document.createElement("button");
    skip.type = "button";
    skip.className = "score-celebrate-skip";
    skip.textContent = "Skip";
    skip.setAttribute("aria-label", "Skip celebration");
    skip.addEventListener("click", function (event) {
      event.preventDefault();
      event.stopPropagation();
      stop();
    });
    wrap.appendChild(skip);

    canvas.addEventListener("click", function () {
      stop();
    });

    document.body.appendChild(wrap);
    rootEl = wrap;
    placeEmblem(emblem, tier);
    onResize = function () {
      placeEmblem(emblem, tier);
    };
    window.addEventListener("resize", onResize);

    if (!reduced) {
      startFireworks(canvas, tier);
    }

    timerId = setTimeout(stop, durationFor(tier, reduced));
  }

  function play(options) {
    options = options || {};
    if (isReviewMode()) return false;
    var tier = celebrationTier(options.band);
    if (!tier) return false;
    var sid = options.submissionId != null && options.submissionId !== "" ? String(options.submissionId) : "";
    var key = sid ? STORAGE_PREFIX + sid : "";
    if (key && storageGet(key)) return false;
    if (playing) return false;
    if (key) storageSet(key, "1");
    start(tier);
    return true;
  }

  root.ScoreCelebrate = {
    play: play,
    stop: stop,
    celebrationTier: celebrationTier,
    SMALL_FIREWORKS: SMALL_FIREWORKS,
    FIREWORKS_RING: FIREWORKS_RING,
    FIREWORKS_CROWN: FIREWORKS_CROWN,
  };
})(window);
