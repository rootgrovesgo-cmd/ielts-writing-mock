(function () {
  "use strict";

  let sets = [];
  const DURATIONS = { task1: 20 * 60, task2: 40 * 60, full: 60 * 60 };

  const el = {
    setup: document.getElementById("setupPanel"),
    exam: document.getElementById("examPanel"),
    done: document.getElementById("donePanel"),
    timer: document.getElementById("timer"),
    modeLabel: document.getElementById("modeLabel"),
    btnStart: document.getElementById("btnStart"),
    btnPause: document.getElementById("btnPause"),
    btnSubmit: document.getElementById("btnSubmit"),
    btnReset: document.getElementById("btnReset"),
    btnAgain: document.getElementById("btnAgain"),
    teacherPause: document.getElementById("teacherPause"),
    candidateName: document.getElementById("candidateName"),
    inviteCode: document.getElementById("inviteCode"),
    promptSet: document.getElementById("promptSet"),
    modePills: document.getElementById("modePills"),
    tab1: document.getElementById("tab1"),
    tab2: document.getElementById("tab2"),
    task1Panel: document.getElementById("task1Panel"),
    task2Panel: document.getElementById("task2Panel"),
    task1Instruction: document.getElementById("task1Instruction"),
    task2Instruction: document.getElementById("task2Instruction"),
    task1Visual: document.getElementById("task1Visual"),
    task1Answer: document.getElementById("task1Answer"),
    task2Answer: document.getElementById("task2Answer"),
    wc1: document.getElementById("wc1"),
    wc2: document.getElementById("wc2"),
    statusBanner: document.getElementById("statusBanner"),
    doneMsg: document.getElementById("doneMsg"),
    taskTabs: document.getElementById("taskTabs"),
    nameError: document.getElementById("nameError"),
    reviewModeBanner: document.getElementById("reviewModeBanner"),
    reviewModeMeta: document.getElementById("reviewModeMeta"),
  };

  const state = {
    running: false,
    paused: false,
    mode: "full",
    remaining: 0,
    duration: 0,
    pausedTotal: 0,
    pauseStartedAt: null,
    tickId: null,
    set: null,
    submitted: false,
    warned5: false,
    warned1: false,
    attemptReview: false,
  };

  // Mode pill UI
  el.modePills.addEventListener("change", (e) => {
    if (e.target.name !== "mode") return;
    el.modePills.querySelectorAll("label").forEach((lab) => {
      lab.classList.toggle("active", lab.querySelector("input").checked);
    });
  });

  function selectedMode() {
    const r = document.querySelector('input[name="mode"]:checked');
    return r ? r.value : "full";
  }

  function findSet(id) {
    return sets.find((s) => s.id === id) || sets[0];
  }

  function countWords(text) {
    const t = (text || "").trim();
    if (!t) return 0;
    return t.split(/\s+/).length;
  }

  function updateWordCounts() {
    const w1 = countWords(el.task1Answer.value);
    const w2 = countWords(el.task2Answer.value);
    el.wc1.textContent = String(w1);
    el.wc2.textContent = String(w2);
    el.wc1.classList.toggle("ok", w1 >= 150);
    el.wc1.classList.toggle("low", w1 < 150);
    el.wc2.classList.toggle("ok", w2 >= 250);
    el.wc2.classList.toggle("low", w2 < 250);
  }

  el.task1Answer.addEventListener("input", updateWordCounts);
  el.task2Answer.addEventListener("input", updateWordCounts);
  function hideSetupError() {
    if (el.nameError) el.nameError.classList.add("hidden");
  }

  function showSetupError(msg) {
    if (!el.nameError) return;
    el.nameError.textContent = msg || "Please enter your name and invitation code before starting.";
    el.nameError.classList.remove("hidden");
  }

  el.candidateName.addEventListener("input", hideSetupError);
  if (el.inviteCode) el.inviteCode.addEventListener("input", hideSetupError);

  function formatTime(sec) {
    sec = Math.max(0, Math.floor(sec));
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
  }

  function formatDuration(sec) {
    sec = Math.max(0, Math.floor(Number(sec) || 0));
    if (sec < 60) return sec + "s";
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return m + "min" + s + "s";
  }

  function renderTimer() {
    el.timer.textContent = formatTime(state.remaining);
    el.timer.classList.toggle("warn", state.remaining <= 300 && state.remaining > 60);
    el.timer.classList.toggle("danger", state.remaining <= 60);
  }

  function showBanner(msg, kind) {
    el.statusBanner.textContent = msg;
    el.statusBanner.className = "banner " + (kind || "info");
    el.statusBanner.classList.remove("hidden");
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function renderBarChart(chart) {
    const cats = chart.categories || [];
    const series = chart.series || [];
    const maxVal = Math.max(...series.flatMap((s) => s.values), 1);
    const W = 520, H = 260, padL = 48, padB = 40, padT = 20, padR = 16;
    const plotW = W - padL - padR;
    const plotH = H - padT - padB;
    const groupW = plotW / cats.length;
    const barW = (groupW * 0.7) / series.length;
    const colors = ["#2563eb", "#f59e0b", "#10b981"];

    let bars = "";
    cats.forEach((cat, i) => {
      series.forEach((ser, si) => {
        const v = ser.values[i] || 0;
        const h = (v / maxVal) * plotH;
        const x = padL + i * groupW + groupW * 0.15 + si * barW;
        const y = padT + plotH - h;
        bars += `<rect x="${x}" y="${y}" width="${barW - 2}" height="${h}" fill="${colors[si % colors.length]}" rx="2"/>`;
        bars += `<text x="${x + (barW - 2) / 2}" y="${y - 4}" text-anchor="middle" font-size="10" fill="#475569">${v}</text>`;
      });
      const cx = padL + i * groupW + groupW / 2;
      bars += `<text x="${cx}" y="${H - 12}" text-anchor="middle" font-size="11" fill="#334155">${escapeHtml(cat)}</text>`;
    });

    // y axis ticks
    let ticks = "";
    for (let t = 0; t <= 4; t++) {
      const val = Math.round((maxVal * t) / 4);
      const y = padT + plotH - (plotH * t) / 4;
      ticks += `<line x1="${padL}" y1="${y}" x2="${W - padR}" y2="${y}" stroke="#e2e8f0"/>`;
      ticks += `<text x="${padL - 6}" y="${y + 3}" text-anchor="end" font-size="10" fill="#64748b">${val}</text>`;
    }

    const legend = series
      .map(
        (s, i) =>
          `<span><i class="swatch" style="background:${colors[i % colors.length]}"></i>${escapeHtml(s.name)}</span>`
      )
      .join("");

    return (
      `<div class="chart-wrap">` +
      `<div class="muted" style="text-align:center;margin-bottom:6px">${escapeHtml(chart.yLabel || "")}</div>` +
      `<div class="bar-chart"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Bar chart">` +
      ticks +
      bars +
      `</svg></div>` +
      `<div class="legend">${legend}</div></div>`
    );
  }

  function renderTable(table) {
    const headers = table.headers || [];
    const rows = table.rows || [];
    const caption = table.caption || table.title || "";
    let html = '<div class="table-wrap"><table class="data">';
    if (caption) html += `<caption>${escapeHtml(caption)}</caption>`;
    html += "<thead><tr>";
    headers.forEach((h) => {
      html += `<th>${escapeHtml(h)}</th>`;
    });
    html += "</tr></thead><tbody>";
    rows.forEach((row) => {
      html += "<tr>";
      row.forEach((cell) => {
        html += `<td>${escapeHtml(cell)}</td>`;
      });
      html += "</tr>";
    });
    html += "</tbody></table></div>";
    return html;
  }

  function renderProcess(steps) {
    let html = '<div class="process-wrap"><ol class="process-list">';
    (steps || []).forEach((step) => {
      html += `<li>${escapeHtml(step)}</li>`;
    });
    html += "</ol></div>";
    return html;
  }

  function renderImage(image) {
    if (!image || !image.src) return "";
    return (
      `<div class="chart-wrap image-wrap">` +
      `<img class="task1-image" src="${escapeHtml(image.src)}" alt="${escapeHtml(image.alt || "Task 1 chart")}" />` +
      `</div>`
    );
  }

  function renderLineChart(chart) {
    const labels = chart.xLabels || [];
    const series = chart.series || [];
    const maxVal = chart.yMax != null ? Number(chart.yMax) : Math.max(...series.flatMap((s) => s.values), 1);
    const W = 560, H = 280, padL = 48, padB = 40, padT = 24, padR = 20;
    const plotW = W - padL - padR;
    const plotH = H - padT - padB;
    const colors = ["#2563eb", "#f59e0b", "#10b981", "#ef4444", "#8b5cf6"];
    const n = Math.max(labels.length - 1, 1);

    let ticks = "";
    for (let t = 0; t <= 4; t++) {
      const val = Math.round((maxVal * t) / 4);
      const y = padT + plotH - (plotH * t) / 4;
      ticks += `<line x1="${padL}" y1="${y}" x2="${W - padR}" y2="${y}" stroke="#e2e8f0"/>`;
      ticks += `<text x="${padL - 6}" y="${y + 3}" text-anchor="end" font-size="10" fill="#64748b">${val}</text>`;
    }

    let xLabels = "";
    labels.forEach((lab, i) => {
      const x = padL + (plotW * i) / n;
      xLabels += `<text x="${x}" y="${H - 12}" text-anchor="middle" font-size="10" fill="#334155">${escapeHtml(lab)}</text>`;
    });

    let lines = "";
    series.forEach((ser, si) => {
      const pts = (ser.values || []).map((v, i) => {
        const x = padL + (plotW * i) / n;
        const y = padT + plotH - (v / maxVal) * plotH;
        return `${x},${y}`;
      });
      const color = colors[si % colors.length];
      lines += `<polyline fill="none" stroke="${color}" stroke-width="2.5" points="${pts.join(" ")}"/>`;
      (ser.values || []).forEach((v, i) => {
        const x = padL + (plotW * i) / n;
        const y = padT + plotH - (v / maxVal) * plotH;
        lines += `<circle cx="${x}" cy="${y}" r="3.5" fill="${color}"/>`;
      });
    });

    const legend = series
      .map(
        (s, i) =>
          `<span><i class="swatch" style="background:${colors[i % colors.length]}"></i>${escapeHtml(s.name)}</span>`
      )
      .join("");

    return (
      `<div class="chart-wrap">` +
      `<div class="muted" style="text-align:center;margin-bottom:6px">${escapeHtml(chart.yLabel || "")}</div>` +
      `<div class="line-chart"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Line graph">` +
      ticks +
      lines +
      xLabels +
      `</svg></div>` +
      `<div class="legend">${legend}</div></div>`
    );
  }

  function flowchartNum(value) {
    const number = Number(value);
    if (Number.isInteger(number)) return String(number);
    return String(Math.round(number * 100) / 100);
  }

  function flowchartWrapText(text, maxChars) {
    const limit = maxChars == null ? 22 : maxChars;
    const words = String(text || "").split(/\s+/).filter(Boolean);
    if (!words.length) return [];
    const lines = [words[0]];
    for (let i = 1; i < words.length; i += 1) {
      const trial = `${lines[lines.length - 1]} ${words[i]}`;
      if (trial.length <= limit) lines[lines.length - 1] = trial;
      else lines.push(words[i]);
    }
    return lines;
  }

  function flowchartKind(step, index) {
    const label = String((step && step.label) || "").toLowerCase();
    const mapping = [
      ["collection", "collection"],
      ["sorting", "sorting"],
      ["washing", "washing"],
      ["shred", "washing"],
      ["melting", "melting"],
      ["pellet", "melting"],
      ["manufactur", "manufacturing"],
      ["distribution", "distribution"],
    ];
    for (const [needle, kind] of mapping) {
      if (label.includes(needle)) return kind;
    }
    const fallback = [
      "collection",
      "sorting",
      "washing",
      "melting",
      "manufacturing",
      "distribution",
    ];
    return fallback[index] || "collection";
  }

  const FLOWCHART_BOTTLE = {
    sm: [6, 2, 4, 5, 10, 16],
    md: [6, 3, 4, 6, 12, 20],
    lg: [8, 3, 4, 7, 14, 24],
  };

  function flowchartBottle(x, y, size, fill, rotate) {
    const key = size || "md";
    const color = fill || "#f4f4f4";
    const [cw, ch, nw, nh, bw, bh] = FLOWCHART_BOTTLE[key];
    const bodyY = y - bh;
    const neckY = bodyY - nh;
    const capY = neckY - ch;
    const inner =
      `<rect x="${flowchartNum(x - cw / 2)}" y="${flowchartNum(capY)}" width="${flowchartNum(cw)}" height="${flowchartNum(ch)}" rx="1" fill="#444" stroke="#222" stroke-width="1"/>` +
      `<rect x="${flowchartNum(x - nw / 2)}" y="${flowchartNum(neckY)}" width="${flowchartNum(nw)}" height="${flowchartNum(nh)}" fill="${color}" stroke="#222" stroke-width="1"/>` +
      `<rect x="${flowchartNum(x - bw / 2)}" y="${flowchartNum(bodyY)}" width="${flowchartNum(bw)}" height="${flowchartNum(bh)}" rx="2" fill="${color}" stroke="#222" stroke-width="1.3"/>`;
    if (rotate) {
      return `<g transform="rotate(${flowchartNum(rotate)} ${flowchartNum(x)} ${flowchartNum(y)})">${inner}</g>`;
    }
    return `<g>${inner}</g>`;
  }

  function flowchartArt(kind) {
    const bottle = flowchartBottle;
    if (kind === "collection") {
      return (
        `<line x1="16" y1="76" x2="144" y2="76" stroke="#222" stroke-width="1.2"/>` +
        bottle(36, 48, "md", "#f7f7f7") +
        bottle(52, 50, "sm", "#e4e4e4") +
        `<path d="M22,38 L28,76 L64,76 L70,38 Z" fill="#d0d0d0" stroke="#222" stroke-width="1.5"/>` +
        `<line x1="20" y1="38" x2="72" y2="38" stroke="#222" stroke-width="2"/>` +
        `<rect x="84" y="48" width="50" height="28" fill="#e6e6e6" stroke="#222" stroke-width="1.5"/>` +
        `<line x1="97" y1="48" x2="97" y2="76" stroke="#222" stroke-width="1.2"/>` +
        `<line x1="109" y1="48" x2="109" y2="76" stroke="#222" stroke-width="1.2"/>` +
        `<line x1="121" y1="48" x2="121" y2="76" stroke="#222" stroke-width="1.2"/>` +
        bottle(100, 76, "sm", "#fafafa") +
        bottle(116, 76, "md", "#d8d8d8")
      );
    }
    if (kind === "sorting") {
      return (
        `<line x1="16" y1="76" x2="144" y2="76" stroke="#222" stroke-width="1.2"/>` +
        `<rect x="16" y="58" width="128" height="6" fill="#d6d6d6" stroke="#222" stroke-width="1.3"/>` +
        `<line x1="22" y1="64" x2="22" y2="76" stroke="#222" stroke-width="1.3"/>` +
        `<line x1="138" y1="64" x2="138" y2="76" stroke="#222" stroke-width="1.3"/>` +
        `<line x1="80" y1="26" x2="80" y2="58" stroke="#222" stroke-width="1.2" stroke-dasharray="3 2"/>` +
        bottle(40, 58, "md", "#ffffff") +
        bottle(58, 58, "md", "#f2f2f2") +
        bottle(102, 58, "md", "#c4c4c4") +
        bottle(122, 58, "lg", "#a8a8a8") +
        `<rect x="28" y="66" width="40" height="10" rx="1" fill="#f3f3f3" stroke="#222" stroke-width="1.2"/>` +
        `<rect x="92" y="66" width="40" height="10" rx="1" fill="#cfcfcf" stroke="#222" stroke-width="1.2"/>`
      );
    }
    if (kind === "washing") {
      return (
        `<line x1="14" y1="80" x2="146" y2="80" stroke="#222" stroke-width="1.2"/>` +
        `<path d="M14,50 L18,70 Q40,82 62,70 L66,50" fill="#d9d9d9" stroke="#222" stroke-width="1.5"/>` +
        `<ellipse cx="40" cy="50" rx="26" ry="8" fill="#f4f4f4" stroke="#222" stroke-width="1.3"/>` +
        bottle(42, 64, "sm", "#f7f7f7", -26) +
        `<path d="M24,28 C24,28 20,34 20,36 A4,4 0 0 0 28,36 C28,34 24,28 24,28 Z" fill="#f4f4f4" stroke="#222" stroke-width="1"/>` +
        `<path d="M54,20 C54,20 51,25 51,27 A3,3 0 0 0 57,27 C57,25 54,20 54,20 Z" fill="#f4f4f4" stroke="#222" stroke-width="1"/>` +
        `<path d="M90,16 L82,28 L146,28 L138,16 Z" fill="#e8e8e8" stroke="#222" stroke-width="1.4"/>` +
        `<rect x="90" y="28" width="48" height="24" fill="#d0d0d0" stroke="#222" stroke-width="1.5"/>` +
        `<rect x="106" y="36" width="16" height="6" fill="#fff" stroke="#222" stroke-width="1.2"/>` +
        `<line x1="98" y1="32" x2="110" y2="48" stroke="#222" stroke-width="1.3"/>` +
        `<line x1="114" y1="32" x2="126" y2="48" stroke="#222" stroke-width="1.3"/>` +
        `<polygon points="94,58 102,56 104,68 92,66" fill="#d8d8d8" stroke="#222" stroke-width="1"/>` +
        `<polygon points="110,56 120,54 122,66 108,64" fill="#c8c8c8" stroke="#222" stroke-width="1"/>` +
        `<polygon points="126,60 136,58 134,72 124,70" fill="#e0e0e0" stroke="#222" stroke-width="1"/>` +
        `<polygon points="104,70 114,68 116,80 102,78" fill="#d0d0d0" stroke="#222" stroke-width="1"/>`
      );
    }
    if (kind === "melting") {
      return (
        `<line x1="16" y1="80" x2="144" y2="80" stroke="#222" stroke-width="1.2"/>` +
        `<rect x="22" y="20" width="52" height="42" fill="#d4d4d4" stroke="#222" stroke-width="1.5"/>` +
        `<ellipse cx="48" cy="20" rx="26" ry="7" fill="#c4c4c4" stroke="#222" stroke-width="1.4"/>` +
        `<ellipse cx="48" cy="28" rx="18" ry="5" fill="#f2f2f2" stroke="#222" stroke-width="1.1"/>` +
        `<path d="M32,76 Q26,68 32,60 Q38,68 32,76 Z" fill="#f0f0f0" stroke="#222" stroke-width="1.2"/>` +
        `<path d="M48,78 Q40,66 48,54 Q56,66 48,78 Z" fill="#e6e6e6" stroke="#222" stroke-width="1.2"/>` +
        `<path d="M64,76 Q58,68 64,60 Q70,68 64,76 Z" fill="#f0f0f0" stroke="#222" stroke-width="1.2"/>` +
        `<path d="M74,40 H88 V52" fill="none" stroke="#222" stroke-width="2"/>` +
        `<line x1="88" y1="52" x2="88" y2="60" stroke="#222" stroke-width="1.4" stroke-dasharray="2 2"/>` +
        `<rect x="76" y="60" width="64" height="16" fill="#eeeeee" stroke="#222" stroke-width="1.3"/>` +
        `<circle cx="86" cy="68" r="4" fill="#c8c8c8" stroke="#222" stroke-width="1"/>` +
        `<circle cx="98" cy="68" r="4" fill="#d4d4d4" stroke="#222" stroke-width="1"/>` +
        `<circle cx="110" cy="68" r="4" fill="#c0c0c0" stroke="#222" stroke-width="1"/>` +
        `<circle cx="122" cy="68" r="4" fill="#d8d8d8" stroke="#222" stroke-width="1"/>` +
        `<circle cx="134" cy="68" r="4" fill="#bcbcbc" stroke="#222" stroke-width="1"/>`
      );
    }
    if (kind === "manufacturing") {
      return (
        `<line x1="12" y1="80" x2="148" y2="80" stroke="#222" stroke-width="1.2"/>` +
        `<path d="M18,22 L14,12 L54,12 L50,22 Z" fill="#e4e4e4" stroke="#222" stroke-width="1.4"/>` +
        `<rect x="10" y="22" width="48" height="40" fill="#d2d2d2" stroke="#222" stroke-width="1.5"/>` +
        `<circle cx="34" cy="42" r="10" fill="#f3f3f3" stroke="#222" stroke-width="1.3"/>` +
        `<circle cx="34" cy="42" r="3" fill="#c0c0c0" stroke="#222" stroke-width="1"/>` +
        `<line x1="18" y1="62" x2="18" y2="80" stroke="#222" stroke-width="1.4"/>` +
        `<line x1="50" y1="62" x2="50" y2="80" stroke="#222" stroke-width="1.4"/>` +
        `<rect x="58" y="52" width="90" height="6" fill="#c8c8c8" stroke="#222" stroke-width="1.3"/>` +
        `<circle cx="64" cy="58" r="4" fill="#f0f0f0" stroke="#222" stroke-width="1.1"/>` +
        `<circle cx="140" cy="58" r="4" fill="#f0f0f0" stroke="#222" stroke-width="1.1"/>` +
        `<line x1="70" y1="62" x2="70" y2="80" stroke="#222" stroke-width="1.3"/>` +
        `<line x1="136" y1="62" x2="136" y2="80" stroke="#222" stroke-width="1.3"/>` +
        bottle(78, 52, "sm", "#ffffff") +
        `<rect x="92" y="34" width="20" height="18" rx="1" fill="#e8e8e8" stroke="#222" stroke-width="1.2"/>` +
        `<path d="M92,40 Q97,37 102,40 Q107,43 112,40" fill="none" stroke="#222" stroke-width="1.1"/>` +
        `<path d="M92,46 Q97,43 102,46 Q107,49 112,46" fill="none" stroke="#222" stroke-width="1.1"/>` +
        `<rect x="122" y="34" width="20" height="18" fill="#e0e0e0" stroke="#222" stroke-width="1.2"/>` +
        `<line x1="122" y1="40" x2="142" y2="40" stroke="#222" stroke-width="1.1"/>` +
        `<line x1="132" y1="34" x2="132" y2="52" stroke="#222" stroke-width="1.1"/>`
      );
    }
    return (
      `<line x1="12" y1="80" x2="148" y2="80" stroke="#222" stroke-width="1.2"/>` +
      `<rect x="12" y="52" width="26" height="28" fill="#e6e6e6" stroke="#222" stroke-width="1.3"/>` +
      `<line x1="12" y1="61" x2="38" y2="61" stroke="#222" stroke-width="1.1"/>` +
      `<line x1="25" y1="52" x2="25" y2="80" stroke="#222" stroke-width="1.1"/>` +
      `<rect x="18" y="32" width="26" height="22" fill="#f0f0f0" stroke="#222" stroke-width="1.3"/>` +
      `<line x1="18" y1="40" x2="44" y2="40" stroke="#222" stroke-width="1.1"/>` +
      `<line x1="31" y1="32" x2="31" y2="54" stroke="#222" stroke-width="1.1"/>` +
      `<rect x="56" y="28" width="58" height="32" fill="#d8d8d8" stroke="#222" stroke-width="1.5"/>` +
      `<line x1="70" y1="28" x2="70" y2="60" stroke="#222" stroke-width="1.1"/>` +
      `<line x1="86" y1="28" x2="86" y2="60" stroke="#222" stroke-width="1.1"/>` +
      `<line x1="102" y1="28" x2="102" y2="60" stroke="#222" stroke-width="1.1"/>` +
      `<path d="M114,38 L134,38 L144,50 L144,60 L114,60 Z" fill="#c8c8c8" stroke="#222" stroke-width="1.5"/>` +
      `<rect x="122" y="42" width="16" height="10" fill="#fff" stroke="#222" stroke-width="1.1"/>` +
      `<circle cx="74" cy="68" r="8" fill="#444" stroke="#222" stroke-width="1.3"/>` +
      `<circle cx="74" cy="68" r="3" fill="#eee" stroke="#222" stroke-width="1"/>` +
      `<circle cx="128" cy="68" r="8" fill="#444" stroke="#222" stroke-width="1.3"/>` +
      `<circle cx="128" cy="68" r="3" fill="#eee" stroke="#222" stroke-width="1"/>`
    );
  }

  function flowchartLayout(count) {
    const colW = 160, colGap = 48, rowH = 136, rowGap = 30, padX = 16, padY = 8;
    let cells;
    let width;
    let rows;
    if (count === 6) {
      cells = [[0, 0], [1, 0], [1, 1], [0, 1], [0, 2], [1, 2]];
      width = padX * 2 + colW * 2 + colGap;
      rows = 3;
    } else {
      cells = [];
      for (let i = 0; i < count; i += 1) cells.push([0, i]);
      width = padX * 2 + colW;
      rows = Math.max(count, 1);
    }
    const height = padY * 2 + rows * rowH + Math.max(rows - 1, 0) * rowGap;
    const origins = cells.map(([col, row]) => [
      padX + col * (colW + colGap),
      padY + row * (rowH + rowGap),
    ]);
    const arrows = [];
    for (let i = 0; i < count - 1; i += 1) {
      const [col1, row1] = cells[i];
      const [col2, row2] = cells[i + 1];
      const [x1, y1] = origins[i];
      const [x2, y2] = origins[i + 1];
      if (row1 === row2) {
        const midY = y1 + 42;
        if (col2 > col1) arrows.push([x1 + colW, midY, x2, midY]);
        else arrows.push([x1, midY, x2 + colW, midY]);
      } else {
        const ax = x1 + 80;
        arrows.push([ax, y1 + rowH, ax, y2]);
      }
    }
    return { width, height, origins, arrows };
  }

  function flowchartArrow(x1, y1, x2, y2, size) {
    const head = size == null ? 7 : size;
    const dx = x2 - x1;
    const dy = y2 - y1;
    if (Math.abs(dx) >= Math.abs(dy)) {
      const direction = dx > 0 ? 1 : -1;
      return (
        `<line x1="${x1}" y1="${y1}" x2="${x2 - direction * head}" y2="${y2}" stroke="#222" stroke-width="1.6"/>` +
        `<polygon points="${x2},${y2} ${x2 - direction * head},${y2 - 5} ${x2 - direction * head},${y2 + 5}" fill="#222" stroke="#222" stroke-width="0.5"/>`
      );
    }
    const direction = dy > 0 ? 1 : -1;
    return (
      `<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2 - direction * head}" stroke="#222" stroke-width="1.6"/>` +
      `<polygon points="${x2},${y2} ${x2 - 5},${y2 - direction * head} ${x2 + 5},${y2 - direction * head}" fill="#222" stroke="#222" stroke-width="0.5"/>`
    );
  }

  function renderFlowchart(flow) {
    const steps = (flow && flow.steps) || [];
    const { width, height, origins, arrows } = flowchartLayout(steps.length);
    let shapes = "";
    steps.forEach((step, i) => {
      const [x, y] = origins[i];
      const kind = flowchartKind(step, i);
      shapes += `<g class="flowchart-scene" transform="translate(${x} ${y})">`;
      shapes += flowchartArt(kind);
      shapes += `<text x="80" y="100" text-anchor="middle" font-size="11" font-weight="700" font-family="Arial, Helvetica, sans-serif" fill="#111">${escapeHtml(step.label || "")}</text>`;
      const detailLines = flowchartWrapText(step.detail || "");
      detailLines.forEach((line, lineI) => {
        const yy = 112 + lineI * 11;
        shapes += `<text x="80" y="${yy}" text-anchor="middle" font-size="9" font-family="Arial, Helvetica, sans-serif" fill="#555">${escapeHtml(line)}</text>`;
      });
      shapes += `</g>`;
    });
    arrows.forEach((arrow) => {
      shapes += flowchartArrow(arrow[0], arrow[1], arrow[2], arrow[3]);
    });
    const title = flow && flow.title ? `<div class="flowchart-title">${escapeHtml(flow.title)}</div>` : "";
    return (
      `<div class="chart-wrap flowchart-wrap">` +
      title +
      `<div class="flowchart flowchart-comic">` +
      `<svg viewBox="0 0 ${width} ${height}" role="img" aria-label="Process diagram">` +
      shapes +
      `</svg></div></div>`
    );
  }

  function pieLabelFill(color, outside) {
    if (outside) return "#111111";
    const raw = String(color || "").replace("#", "");
    if (raw.length !== 6) return "#ffffff";
    const lin = (c) => {
      const x = c / 255;
      return x <= 0.04045 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4);
    };
    const r = lin(parseInt(raw.slice(0, 2), 16));
    const g = lin(parseInt(raw.slice(2, 4), 16));
    const b = lin(parseInt(raw.slice(4, 6), 16));
    const luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b;
    return luminance >= 0.35 ? "#111111" : "#ffffff";
  }

  function fmtNum(n) {
    return String(Math.round(n * 1000) / 1000);
  }

  function renderPieCharts(data) {
    const categories = (data && data.categories) || [];
    const charts = (data && data.charts) || [];
    const unit = (data && data.unit) || "%";
    const colors = ["#1a1a1a", "#4a4a4a", "#8a8a8a", "#c8c8c8", "#ffffff"];
    const size = 220;
    const cx = 110;
    const cy = 110;
    const radius = 80;

    const pies = charts
      .map((chart) => {
        const values = (chart.values || []).map(Number);
        const total = values.reduce((sum, v) => sum + v, 0) || 1;
        let angle = -Math.PI / 2;
        let slices = "";
        let labels = "";
        values.forEach((value, i) => {
          const frac = value / total;
          const start = angle;
          const end = angle + frac * 2 * Math.PI;
          angle = end;
          if (value <= 0) return;
          const color = colors[i % colors.length];
          const x1 = cx + radius * Math.cos(start);
          const y1 = cy + radius * Math.sin(start);
          const x2 = cx + radius * Math.cos(end);
          const y2 = cy + radius * Math.sin(end);
          const largeArc = frac > 0.5 ? 1 : 0;
          slices +=
            `<path d="M ${fmtNum(cx)},${fmtNum(cy)} L ${fmtNum(x1)},${fmtNum(y1)} ` +
            `A ${radius},${radius} 0 ${largeArc} 1 ${fmtNum(x2)},${fmtNum(y2)} Z" ` +
            `fill="${color}" stroke="#222" stroke-width="1"/>`;
          const mid = (start + end) / 2;
          // Keep labels on the slice except when a wedge is too thin to fit text.
          const outside = frac < 0.03;
          const lr = radius * (outside ? 1.18 : 0.62);
          const lx = cx + lr * Math.cos(mid);
          const ly = cy + lr * Math.sin(mid);
          const fill = pieLabelFill(color, outside);
          const pct = `${Number.isInteger(value) ? value : value}${unit}`;
          const fontSize = !outside && value < 10 ? 9 : 11;
          labels +=
            `<text x="${fmtNum(lx)}" y="${fmtNum(ly)}" text-anchor="middle" ` +
            `dominant-baseline="middle" font-size="${fontSize}" font-weight="600" fill="${fill}">` +
            `${escapeHtml(pct)}</text>`;
        });
        const aria = escapeHtml(chart.label || "Pie chart");
        return (
          `<div class="pie-chart">` +
          `<div class="pie-chart-label">${escapeHtml(chart.label || "")}</div>` +
          `<svg viewBox="0 0 ${size} ${size}" role="img" aria-label="${aria}">` +
          slices +
          labels +
          `</svg></div>`
        );
      })
      .join("");

    const legend = categories
      .map(
        (cat, i) =>
          `<span><i class="swatch" style="background:${colors[i % colors.length]}"></i>${escapeHtml(cat)}</span>`
      )
      .join("");
    const title = data && data.title
      ? `<div class="pie-charts-title">${escapeHtml(data.title)}</div>`
      : "";
    return (
      `<div class="chart-wrap pie-charts">` +
      title +
      `<div class="pie-charts-row">${pies}</div>` +
      `<div class="legend">${legend}</div></div>`
    );
  }

  function renderTask1Visual(t1) {
    if (t1.image) return renderImage(t1.image);
    if (t1.table && t1.line_chart) {
      return `<div class="combined-visual">${renderTable(t1.table)}${renderLineChart(t1.line_chart)}</div>`;
    }
    if (t1.line_chart) return renderLineChart(t1.line_chart);
    if (t1.flowchart) return renderFlowchart(t1.flowchart);
    if (t1.pie_charts) return renderPieCharts(t1.pie_charts);
    if (t1.chart) return renderBarChart(t1.chart);
    if (t1.table) return renderTable(t1.table);
    if (t1.process_steps) return renderProcess(t1.process_steps);
    return "";
  }


  function isTask2RubricLine(line) {
    const t = String(line || "").trim();
    if (/^give reasons for your answer\b/i.test(t)) return true;
    if (/^write at least 250 words\.?$/i.test(t)) return true;
    return false;
  }

  function formatTask2Instruction(text) {
    const raw = text == null ? "" : String(text);
    if (!raw) return "";
    const lines = raw.split("\n");
    const idx = lines.findIndex(isTask2RubricLine);
    if (idx === -1) {
      return `<strong class="task2-question">${escapeHtml(raw)}</strong>`;
    }
    const question = lines.slice(0, idx).join("\n").replace(/[ \t\r\n]+$/, "");
    const rest = lines.slice(idx).join("\n");
    const parts = [];
    if (question) parts.push(`<strong class="task2-question">${escapeHtml(question)}</strong>`);
    if (rest) parts.push(escapeHtml(rest));
    return question && rest ? parts.join("\n\n") : parts.join("");
  }

  function loadPromptIntoUI() {
    const set = state.set;
    el.task1Instruction.textContent = set.task1.instruction;
    el.task2Instruction.innerHTML = formatTask2Instruction(set.task2.instruction);
    el.task1Visual.innerHTML = renderTask1Visual(set.task1);
  }

  function switchTask(n) {
    const show1 = n === 1;
    el.task1Panel.classList.toggle("hidden", !show1);
    el.task2Panel.classList.toggle("hidden", show1);
    el.tab1.classList.toggle("active", show1);
    el.tab2.classList.toggle("active", !show1);
  }

  el.tab1.addEventListener("click", () => switchTask(1));
  el.tab2.addEventListener("click", () => switchTask(2));

  function stopTick() {
    if (state.tickId) {
      clearInterval(state.tickId);
      state.tickId = null;
    }
  }

  function tick() {
    if (!state.running || state.paused || state.submitted) return;
    state.remaining -= 1;
    renderTimer();

    if (!state.warned5 && state.remaining === 300) {
      state.warned5 = true;
      showBanner("还剩 5 分钟，请注意收尾与检查。", "warn");
    }
    if (!state.warned1 && state.remaining === 60) {
      state.warned1 = true;
      showBanner("还剩 1 分钟！时间结束后将自动提交。", "warn");
    }
    if (state.remaining <= 0) {
      state.remaining = 0;
      renderTimer();
      showBanner("时间到，正在自动提交……", "warn");
      submitAnswers(true);
    }
  }

  async function startSession() {
    const name = (el.candidateName.value || "").trim();
    const code = (el.inviteCode && el.inviteCode.value || "").trim();
    if (!name) {
      showSetupError("Please enter your name before starting.");
      el.candidateName.focus();
      return null;
    }
    if (!code) {
      showSetupError("Please enter your invitation code before starting.");
      if (el.inviteCode) el.inviteCode.focus();
      return null;
    }
    hideSetupError();
    const res = await fetch("/api/session/start", {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        candidate_name: name,
        invite_code: code,
        module: "writing",
        mode: selectedMode(),
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) {
      showSetupError(data.error || "邀请码无效或已失效");
      return null;
    }
    return data;
  }

  async function loadPromptSets() {
    const res = await fetch("/api/prompts", { credentials: "same-origin" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      showSetupError((data && data.error) || "题目加载失败，请重试。");
      return false;
    }
    sets = data.sets || [];
    if (!sets.length) {
      showSetupError("未加载到题目套卷。");
      return false;
    }
    return true;
  }

  async function startExam() {
    el.btnStart.disabled = true;
    try {
      const started = await startSession();
      if (!started) return;
      const loaded = await loadPromptSets();
      if (!loaded) return;
    } catch (err) {
      console.error(err);
      showSetupError("无法开始考试，请检查网络后重试。");
      return;
    } finally {
      el.btnStart.disabled = false;
    }
    state.mode = selectedMode();
    state.set = findSet(el.promptSet.value);
    state.duration = DURATIONS[state.mode] || DURATIONS.full;
    state.remaining = state.duration;
    state.pausedTotal = 0;
    state.pauseStartedAt = null;
    state.running = true;
    state.paused = false;
    state.submitted = false;
    state.warned5 = false;
    state.warned1 = false;

    el.task1Answer.value = "";
    el.task2Answer.value = "";
    updateWordCounts();
    loadPromptIntoUI();

    // Show/hide tasks by mode
    const only1 = state.mode === "task1";
    const only2 = state.mode === "task2";
    el.taskTabs.classList.toggle("hidden", only1 || only2);
    if (only2) {
      switchTask(2);
      el.task1Panel.classList.add("hidden");
    } else {
      switchTask(1);
      if (only1) el.task2Panel.classList.add("hidden");
    }

    const modeNames = {
      full: "Full test · 60 min",
      task1: "Task 1 · 20 min",
      task2: "Task 2 · 40 min",
    };
    el.modeLabel.textContent = modeNames[state.mode] || state.mode;

    el.setup.classList.add("hidden");
    el.done.classList.add("hidden");
    el.exam.classList.remove("hidden");
    el.statusBanner.classList.add("hidden");

    const allowPause = el.teacherPause.checked;
    el.btnPause.classList.toggle("hidden", !allowPause);
    el.btnPause.textContent = "暂停";

    renderTimer();
    stopTick();
    state.tickId = setInterval(tick, 1000);

    // Prevent accidental leave
    window.onbeforeunload = function () {
      if (state.running && !state.submitted) return "考试进行中，确定离开？";
    };
  }

  function togglePause() {
    if (state.attemptReview) return;
    if (!state.running || state.submitted) return;
    if (!state.paused) {
      state.paused = true;
      state.pauseStartedAt = Date.now();
      el.btnPause.textContent = "继续";
      showBanner("计时已暂停（教师模式）。", "info");
    } else {
      if (state.pauseStartedAt) {
        state.pausedTotal += Math.floor((Date.now() - state.pauseStartedAt) / 1000);
        state.pauseStartedAt = null;
      }
      state.paused = false;
      el.btnPause.textContent = "暂停";
      el.statusBanner.classList.add("hidden");
    }
  }

  async function submitAnswers(auto) {
    if (state.attemptReview) return;
    if (state.submitted) return;
    state.submitted = true;
    state.running = false;
    stopTick();
    window.onbeforeunload = null;

    if (state.pauseStartedAt) {
      state.pausedTotal += Math.floor((Date.now() - state.pauseStartedAt) / 1000);
      state.pauseStartedAt = null;
    }

    const payload = {
      candidate_name: el.candidateName.value.trim() || null,
      mode: state.mode,
      prompt_set_id: state.set.id,
      task1_prompt_id: state.set.task1.id,
      task2_prompt_id: state.set.task2.id,
      task1_text: state.mode === "task2" ? "" : el.task1Answer.value,
      task2_text: state.mode === "task1" ? "" : el.task2Answer.value,
      duration_seconds: state.duration,
      time_remaining_seconds: Math.max(0, state.remaining),
      time_used_seconds: Math.max(0, state.duration - state.remaining),
      paused_total_seconds: state.pausedTotal,
      auto_submitted: !!auto,
    };

    el.btnSubmit.disabled = true;
    try {
      const res = await fetch("/api/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error("submit failed");

      el.exam.classList.add("hidden");
      el.done.classList.remove("hidden");
      const used = formatDuration(payload.time_used_seconds);
      el.doneMsg.innerHTML =
        (auto ? "时间到，系统已自动交卷。" : "提交成功！") +
        `<br/>姓名：${escapeHtml(payload.candidate_name || "")}` +
        `<br/>用时 ${used}` +
        `<br/>Task 1：${countWords(payload.task1_text)} 词 · Task 2：${countWords(payload.task2_text)} 词` +
        `<br/><strong>已提交，可以关闭页面。</strong>`;
    } catch (err) {
      state.submitted = false;
      state.running = true;
      state.tickId = setInterval(tick, 1000);
      showBanner("提交失败，请检查网络后重试。若多次失败，请联系老师。", "error");
      el.btnSubmit.disabled = false;
      console.error(err);
    }
  }


  function reviewConfig() {
    return window.REVIEW_CONFIG || {};
  }

  function reviewApiUrl(sid) {
    const cfg = reviewConfig();
    if (cfg.apiUrl) return cfg.apiUrl;
    return "/api/me/submission/" + encodeURIComponent(sid);
  }

  function reviewAuthRedirect(sid) {
    const cfg = reviewConfig();
    if (cfg.admin) return cfg.backHref || "/admin";
    if (cfg.backHref && String(cfg.backHref).startsWith("/admin")) return cfg.backHref;
    return "/me?next=/me/submission/" + encodeURIComponent(sid);
  }

  function reviewBackHref() {
    const cfg = reviewConfig();
    return cfg.backHref || "/me";
  }

  function reviewBackLabel() {
    const cfg = reviewConfig();
    return cfg.backLabel || "返回我的记录";
  }

  function resetToSetup() {
    if (state.attemptReview) {
      window.location.href = reviewBackHref();
      return;
    }
    if (state.running && !state.submitted) {
      if (!confirm("确定放弃当前答卷并重置？")) return;
    }
    stopTick();
    state.running = false;
    state.submitted = false;
    window.onbeforeunload = null;
    el.btnSubmit.disabled = false;
    el.btnPause.classList.add("hidden");
    el.timer.textContent = "--:--";
    el.timer.classList.remove("warn", "danger");
    el.modeLabel.textContent = "Ready";
    el.exam.classList.add("hidden");
    el.done.classList.add("hidden");
    el.setup.classList.remove("hidden");
  }

  el.btnStart.addEventListener("click", startExam);
  el.btnPause.addEventListener("click", togglePause);
  el.btnSubmit.addEventListener("click", () => {
    if (!confirm("确认提交答卷？提交后不可修改。")) return;
    submitAnswers(false);
  });
  el.btnReset.addEventListener("click", resetToSetup);
  el.btnAgain.addEventListener("click", resetToSetup);

  function lockWritingReview() {
    if (el.task1Answer) {
      el.task1Answer.readOnly = true;
      el.task1Answer.setAttribute("readonly", "readonly");
    }
    if (el.task2Answer) {
      el.task2Answer.readOnly = true;
      el.task2Answer.setAttribute("readonly", "readonly");
    }
    if (el.btnSubmit) el.btnSubmit.classList.add("hidden");
    if (el.btnReset) {
      el.btnReset.textContent = reviewBackLabel();
    }
    if (el.btnPause) el.btnPause.classList.add("hidden");
    if (el.modeLabel) el.modeLabel.textContent = "回顾模式";
    if (el.reviewModeBanner) el.reviewModeBanner.classList.remove("hidden");
  }

  async function enterAttemptReview() {
    const cfg = window.REVIEW_CONFIG || {};
    const sid = cfg.sid;
    if (!sid) return;
    state.attemptReview = true;
    state.running = false;
    state.submitted = true;
    state.paused = false;
    window.onbeforeunload = null;
    try {
      const res = await fetch(reviewApiUrl(sid), {
        credentials: "same-origin",
      });
      if (res.status === 401 || res.status === 403) {
        window.location.href = reviewAuthRedirect(sid);
        return;
      }
      if (res.status === 404) {
        document.body.innerHTML = "<p style='padding:24px'>未找到该答卷</p>";
        return;
      }
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error((data && data.error) || "review load failed");
      if (data.set) {
        state.set = data.set;
        sets = [data.set];
      }
      state.mode = data.mode || "full";
      state.duration = data.time_used_seconds || 0;
      state.remaining = 0;
      if (!state.set || !state.set.task1) {
        showSetupError("未能加载本题的写作题目。");
        if (el.setup) el.setup.classList.remove("hidden");
        return;
      }
      loadPromptIntoUI();
      el.task1Answer.value = data.task1_text || "";
      el.task2Answer.value = data.task2_text || "";
      updateWordCounts();
      const only1 = state.mode === "task1";
      const only2 = state.mode === "task2";
      el.taskTabs.classList.toggle("hidden", only1 || only2);
      if (only2) {
        switchTask(2);
        el.task1Panel.classList.add("hidden");
      } else {
        switchTask(1);
        if (only1) el.task2Panel.classList.add("hidden");
      }
      if (el.setup) el.setup.classList.add("hidden");
      if (el.done) el.done.classList.add("hidden");
      el.exam.classList.remove("hidden");
      lockWritingReview();
      if (el.reviewModeMeta) {
        const bits = [];
        if (data.duration) bits.push("用时 " + data.duration);
        if (state.mode !== "task2") bits.push("Task 1 " + (data.task1_word_count || 0) + " 词");
        if (state.mode !== "task1") bits.push("Task 2 " + (data.task2_word_count || 0) + " 词");
        el.reviewModeMeta.textContent = bits.join(" · ");
      }
    } catch (err) {
      console.error(err);
      showSetupError("无法加载这套已交答卷，请返回我的记录后重试。");
      if (el.setup) el.setup.classList.remove("hidden");
    }
  }

  if (window.REVIEW_CONFIG && window.REVIEW_CONFIG.sid) {
    enterAttemptReview();
  }

})();
