(function () {
  "use strict";

  const sets = window.PROMPT_SETS || [];
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
  el.candidateName.addEventListener("input", () => {
    if (el.nameError && el.candidateName.value.trim()) el.nameError.classList.add("hidden");
  });

  function formatTime(sec) {
    sec = Math.max(0, Math.floor(sec));
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
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
    let html = '<div class="table-wrap"><table class="data"><thead><tr>';
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
    const maxVal = Math.max(...series.flatMap((s) => s.values), 1);
    const W = 560, H = 280, padL = 48, padB = 40, padT = 24, padR = 20;
    const plotW = W - padL - padR;
    const plotH = H - padT - padB;
    const colors = ["#2563eb", "#f59e0b", "#10b981", "#ef4444"];
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

  function renderFlowchart(flow) {
    const steps = (flow && flow.steps) || [];
    const boxW = 200, boxH = 70, gap = 28, padX = 40, padY = 20;
    const W = boxW + padX * 2;
    const H = padY * 2 + steps.length * boxH + Math.max(steps.length - 1, 0) * gap;
    let shapes = "";
    steps.forEach((step, i) => {
      const y = padY + i * (boxH + gap);
      const x = padX;
      shapes += `<rect x="${x}" y="${y}" width="${boxW}" height="${boxH}" rx="10" fill="#eff6ff" stroke="#2563eb" stroke-width="2"/>`;
      shapes += `<text x="${x + boxW / 2}" y="${y + 28}" text-anchor="middle" font-size="14" font-weight="700" fill="#1e3a8a">${escapeHtml(step.label || "")}</text>`;
      shapes += `<text x="${x + boxW / 2}" y="${y + 50}" text-anchor="middle" font-size="11" fill="#475569">${escapeHtml(step.detail || "")}</text>`;
      if (i < steps.length - 1) {
        const ax = x + boxW / 2;
        const y1 = y + boxH;
        const y2 = y + boxH + gap;
        shapes += `<line x1="${ax}" y1="${y1}" x2="${ax}" y2="${y2 - 8}" stroke="#64748b" stroke-width="2"/>`;
        shapes += `<polygon points="${ax},${y2} ${ax - 6},${y2 - 10} ${ax + 6},${y2 - 10}" fill="#64748b"/>`;
      }
    });
    const title = flow && flow.title ? `<div class="muted" style="text-align:center;margin-bottom:8px">${escapeHtml(flow.title)}</div>` : "";
    return (
      `<div class="chart-wrap flowchart-wrap">` +
      title +
      `<div class="flowchart"><svg viewBox="0 0 ${W} ${H}" role="img" aria-label="Process diagram">` +
      shapes +
      `</svg></div></div>`
    );
  }

  function renderTask1Visual(t1) {
    if (t1.image) return renderImage(t1.image);
    if (t1.line_chart) return renderLineChart(t1.line_chart);
    if (t1.flowchart) return renderFlowchart(t1.flowchart);
    if (t1.chart) return renderBarChart(t1.chart);
    if (t1.table) return renderTable(t1.table);
    if (t1.process_steps) return renderProcess(t1.process_steps);
    return "";
  }

  function loadPromptIntoUI() {
    const set = state.set;
    el.task1Instruction.textContent = set.task1.instruction;
    el.task2Instruction.textContent = set.task2.instruction;
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

  function startExam() {
    if (!sets.length) {
      alert("未加载到题目套卷。");
      return;
    }
    const name = (el.candidateName.value || "").trim();
    if (!name) {
      if (el.nameError) el.nameError.classList.remove("hidden");
      el.candidateName.focus();
      return;
    }
    if (el.nameError) el.nameError.classList.add("hidden");
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
      full: "完整测试 60 分钟",
      task1: "仅 Task 1 · 20 分钟",
      task2: "仅 Task 2 · 40 分钟",
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
      const used = formatTime(payload.time_used_seconds);
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

  function resetToSetup() {
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
})();
