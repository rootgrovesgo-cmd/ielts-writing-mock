(function () {
  "use strict";

  let paper = window.READING_PAPER || null;
  const LS_KEY = "rosette-reading-exam-v1";
  const DURATIONS = {
    full: 60 * 60,
    passage1: 20 * 60,
    passage2: 20 * 60,
    passage3: 20 * 60,
  };
  const MODE_LABELS = {
    full: "Academic Reading · Full test",
    passage1: "Academic Reading · Passage 1",
    passage2: "Academic Reading · Passage 2",
    passage3: "Academic Reading · Passage 3",
  };
  const MODE_RANGES = {
    full: [1, 40],
    passage1: [1, 13],
    passage2: [14, 26],
    passage3: [27, 40],
  };

  const el = {
    setup: document.getElementById("setupPanel"),
    exam: document.getElementById("examPanel"),
    done: document.getElementById("donePanel"),
    footer: document.getElementById("siteFooter"),
    timer: document.getElementById("timer"),
    modeLabel: document.getElementById("modeLabel"),
    btnStart: document.getElementById("btnStart"),
    btnPause: document.getElementById("btnPause"),
    btnSubmit: document.getElementById("btnSubmit"),
    btnQuit: document.getElementById("btnQuit"),
    btnAgain: document.getElementById("btnAgain"),
    btnPrev: document.getElementById("btnPrev"),
    btnNext: document.getElementById("btnNext"),
    btnFlag: document.getElementById("btnFlag"),
    btnReview: document.getElementById("btnReview"),
    btnBackToTest: document.getElementById("btnBackToTest"),
    teacherPause: document.getElementById("teacherPause"),
    candidateName: document.getElementById("candidateName"),
    inviteCode: document.getElementById("inviteCode"),
    modePills: document.getElementById("modePills"),
    nameError: document.getElementById("nameError"),
    resumeBanner: document.getElementById("resumeBanner"),
    statusBanner: document.getElementById("statusBanner"),
    doneMsg: document.getElementById("doneMsg"),
    passageLabel: document.getElementById("passageLabel"),
    passageGuidance: document.getElementById("passageGuidance"),
    passageTitle: document.getElementById("passageTitle"),
    passageBody: document.getElementById("passageBody"),
    passageScroll: document.getElementById("passageScroll"),
    questionScroll: document.getElementById("questionScroll"),
    paletteNums: document.getElementById("paletteNums"),
    reviewScreen: document.getElementById("reviewScreen"),
    reviewList: document.getElementById("reviewList"),
    readingSplit: document.getElementById("readingSplit"),
    splitter: document.getElementById("splitter"),
    passagePane: document.getElementById("passagePane"),
    questionPane: document.getElementById("questionPane"),
    paneToggle: document.getElementById("paneToggle"),
    btnHighlight: document.getElementById("btnHighlight"),
    btnClearHighlight: document.getElementById("btnClearHighlight"),
    btnAddNote: document.getElementById("btnAddNote"),
    hlMenu: document.getElementById("hlMenu"),
    noteModal: document.getElementById("noteModal"),
    noteText: document.getElementById("noteText"),
    btnNoteSave: document.getElementById("btnNoteSave"),
    btnNoteCancel: document.getElementById("btnNoteCancel"),
  };

  const state = {
    running: false,
    paused: false,
    submitted: false,
    mode: "full",
    remaining: 0,
    duration: 0,
    pausedTotal: 0,
    pauseStartedAt: null,
    tickId: null,
    name: "",
    setId: "set-a",
    currentQ: 1,
    questions: [],
    answers: {},
    flags: {},
    passageHtml: {},
    currentPassage: 0,
    hlSeq: 0,
    warned5: false,
    warned1: false,
    reviewing: false,
    allowPause: false,
    pendingNoteRange: null,
    pendingNoteMark: null,
  };

  el.modePills.addEventListener("change", (e) => {
    if (e.target.name !== "mode") return;
    el.modePills.querySelectorAll("label").forEach((lab) => {
      lab.classList.toggle("active", lab.querySelector("input").checked);
    });
  });

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

  function selectedMode() {
    const r = document.querySelector('input[name="mode"]:checked');
    return r ? r.value : "full";
  }

  function questionList(mode) {
    const range = MODE_RANGES[mode] || MODE_RANGES.full;
    const list = [];
    for (let i = range[0]; i <= range[1]; i++) list.push(i);
    return list;
  }

  function passageForQuestion(q) {
    if (q <= 13) return 1;
    if (q <= 26) return 2;
    return 3;
  }

  function findPassage(id) {
    return (paper.passages || []).find((p) => p.id === id);
  }

  function escapeHtml(s) {
    return String(s)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function formatTime(sec) {
    sec = Math.max(0, Math.floor(sec));
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return String(m).padStart(2, "0") + ":" + String(s).padStart(2, "0");
  }

  function isAnswered(q) {
    const v = state.answers[q];
    return v != null && String(v).trim() !== "";
  }

  function formatInstruction(text) {
    return escapeHtml(text)
      .replace(/ONE WORD ONLY/g, "<span class=\"emph\">ONE WORD ONLY</span>")
      .replace(/A, B, C or D/g, "<span class=\"emph\">A, B, C or D</span>")
      .replace(/A–F/g, "<span class=\"emph\">A–F</span>");
  }

  function renderTimer() {
    el.timer.textContent = formatTime(state.remaining);
    el.timer.classList.toggle("warn", state.remaining <= 300 && state.remaining > 60);
    el.timer.classList.toggle("danger", state.remaining <= 60);
  }

  function showBanner(msg, kind) {
    el.statusBanner.textContent = msg;
    el.statusBanner.className = "banner " + (kind || "info") + " reading-status";
    el.statusBanner.classList.remove("hidden");
  }

  function persist() {
    if (!state.running || state.submitted) return;
    const payload = {
      running: true,
      mode: state.mode,
      setId: state.setId,
      name: state.name,
      remaining: state.remaining,
      duration: state.duration,
      pausedTotal: state.pausedTotal,
      paused: state.paused,
      savedAt: Date.now(),
      allowPause: state.allowPause,
      answers: state.answers,
      flags: state.flags,
      currentQ: state.currentQ,
      passageHtml: snapshotPassageHtml(),
      hlSeq: state.hlSeq,
      warned5: state.warned5,
      warned1: state.warned1,
    };
    try {
      localStorage.setItem(LS_KEY, JSON.stringify(payload));
    } catch (err) {
      console.warn("localStorage save failed", err);
    }
  }

  function clearPersist() {
    try {
      localStorage.removeItem(LS_KEY);
    } catch (err) {
      /* ignore */
    }
  }

  function loadPersist() {
    try {
      const raw = localStorage.getItem(LS_KEY);
      if (!raw) return null;
      return JSON.parse(raw);
    } catch (err) {
      return null;
    }
  }

  function snapshotPassageHtml() {
    const map = Object.assign({}, state.passageHtml);
    if (state.currentPassage && el.passageBody) {
      map[state.currentPassage] = el.passageBody.innerHTML;
    }
    return map;
  }

  function renderPassage(id, forceClean) {
    if (state.currentPassage && el.passageBody && state.currentPassage !== id) {
      state.passageHtml[state.currentPassage] = el.passageBody.innerHTML;
    }
    const p = findPassage(id);
    if (!p) return;
    state.currentPassage = id;
    el.passageLabel.textContent = p.label || ("Reading Passage " + id);
    el.passageGuidance.textContent = p.time_guidance || "";
    el.passageTitle.textContent = p.title || "";
    if (!forceClean && state.passageHtml[id]) {
      el.passageBody.innerHTML = state.passageHtml[id];
    } else {
      el.passageBody.innerHTML = (p.paragraphs || [])
        .map((para) => "<p>" + escapeHtml(para) + "</p>")
        .join("");
    }
    el.passageScroll.scrollTop = 0;
  }

  function renderBlank(q) {
    const val = escapeHtml(state.answers[q] || "");
    return (
      '<span class="blank" data-q="' +
      q +
      '"><span class="qnum">' +
      q +
      '</span><input type="text" id="ans-' +
      q +
      '" data-q="' +
      q +
      '" value="' +
      val +
      '" maxlength="40" autocomplete="off" spellcheck="false" aria-label="Question ' +
      q +
      '" /></span>'
    );
  }

  function renderParts(parts) {
    return (parts || [])
      .map((part) => {
        if (part && typeof part === "object" && part.q) return renderBlank(part.q);
        return escapeHtml(part == null ? "" : String(part));
      })
      .join("");
  }

  function renderNotes(notes) {
    let html = '<div class="notes-box">';
    if (notes.title) html += '<div class="notes-title">' + escapeHtml(notes.title) + "</div>";
    (notes.sections || []).forEach((sec) => {
      if (sec.heading) html += '<div class="notes-heading">' + escapeHtml(sec.heading) + "</div>";
      html += "<ul>";
      (sec.items || []).forEach((item) => {
        html += "<li>";
        if (item.parts) html += renderParts(item.parts);
        else if (item.text) html += escapeHtml(item.text);
        if (item.children && item.children.length) {
          html += "<ul>";
          item.children.forEach((ch) => {
            html += "<li>" + renderParts(ch.parts || []) + "</li>";
          });
          html += "</ul>";
        }
        html += "</li>";
      });
      html += "</ul>";
    });
    html += "</div>";
    return html;
  }

  function renderLegend(legend) {
    let html = '<div class="legend-box">';
    (legend || []).forEach((row) => {
      html +=
        '<div class="legend-row"><span class="val">' +
        escapeHtml(row.value) +
        '</span><span>' +
        escapeHtml(row.meaning) +
        "</span></div>";
    });
    html += "</div>";
    return html;
  }

  function renderSelect(q, options) {
    const cur = (state.answers[q] || "").toUpperCase();
    let html =
      '<select class="q-select" id="ans-' +
      q +
      '" data-q="' +
      q +
      '" aria-label="Question ' +
      q +
      '">';
    html += '<option value="">Select…</option>';
    options.forEach((opt) => {
      const sel = cur === opt ? " selected" : "";
      html += '<option value="' + opt + '"' + sel + ">" + opt + "</option>";
    });
    html += "</select>";
    return html;
  }

  function renderTfngLike(group) {
    const opts = (group.legend || []).map((r) => r.value);
    let html = "";
    (group.items || []).forEach((item) => {
      if (!state.questions.includes(item.q)) return;
      html +=
        '<div class="q-item" id="q-' +
        item.q +
        '" data-q="' +
        item.q +
        '"><div class="q-stem"><span class="q-no">' +
        item.q +
        '</span><span class="q-stem-text">' +
        escapeHtml(item.stem) +
        "</span></div>" +
        renderSelect(item.q, opts) +
        "</div>";
    });
    return html;
  }

  function renderMcq(group) {
    let html = "";
    (group.items || []).forEach((item) => {
      if (!state.questions.includes(item.q)) return;
      const cur = (state.answers[item.q] || "").toUpperCase();
      html +=
        '<div class="q-item" id="q-' +
        item.q +
        '" data-q="' +
        item.q +
        '"><div class="q-stem"><span class="q-no">' +
        item.q +
        '</span><span class="q-stem-text">' +
        escapeHtml(item.stem) +
        "</span></div><ul class='mcq-options'>";
      Object.keys(item.options || {}).forEach((letter) => {
        const checked = cur === letter ? " checked" : "";
        html +=
          "<li><label><input type='radio' name='q" +
          item.q +
          "' value='" +
          letter +
          "' data-q='" +
          item.q +
          "'" +
          checked +
          " /><span class='mcq-letter'>" +
          letter +
          "</span><span>" +
          escapeHtml(item.options[letter]) +
          "</span></label></li>";
      });
      html += "</ul></div>";
    });
    return html;
  }

  function renderMatching(group) {
    let html = '<div class="endings-box"><ol>';
    Object.keys(group.endings || {}).forEach((letter) => {
      html +=
        '<li><span class="end-letter">' +
        letter +
        "</span><span>" +
        escapeHtml(group.endings[letter]) +
        "</span></li>";
    });
    html += "</ol></div>";
    const letters = Object.keys(group.endings || {});
    (group.items || []).forEach((item) => {
      if (!state.questions.includes(item.q)) return;
      html +=
        '<div class="q-item" id="q-' +
        item.q +
        '" data-q="' +
        item.q +
        '"><div class="q-stem"><span class="q-no">' +
        item.q +
        '</span><span class="q-stem-text">' +
        escapeHtml(item.stem) +
        "</span></div>" +
        renderSelect(item.q, letters) +
        '<div class="dup-hint">This ending is already used. In the real test each letter is usually used once.</div></div>';
    });
    return html;
  }

  function renderQuestions() {
    const groups = paper.groups || [];
    let html = "";
    groups.forEach((g) => {
      const overlap = state.questions.some((q) => q >= g.from && q <= g.to);
      if (!overlap) return;
      html += '<section class="q-group" data-group="' + escapeHtml(g.id) + '">';
      html += '<h3 class="q-group-heading">' + escapeHtml(g.heading) + "</h3>";
      html += '<div class="q-instructions">';
      (g.instructions || []).forEach((line) => {
        html += "<p>" + formatInstruction(line) + "</p>";
      });
      html += "</div>";
      if (g.type === "notes") html += renderNotes(g.notes || {});
      else if (g.type === "tfng" || g.type === "ynng") {
        html += renderLegend(g.legend);
        html += renderTfngLike(g);
      } else if (g.type === "mcq") html += renderMcq(g);
      else if (g.type === "matching_endings") html += renderMatching(g);
      html += "</section>";
    });
    el.questionScroll.innerHTML = html;
    bindQuestionInputs();
    checkMatchingDups();
    updateCurrentHighlight();
  }

  function bindQuestionInputs() {
    el.questionScroll.querySelectorAll("input[data-q], select[data-q]").forEach((node) => {
      const handler = () => {
        const q = Number(node.getAttribute("data-q"));
        let val = "";
        if (node.type === "radio") {
          if (!node.checked) return;
          val = node.value;
        } else {
          val = node.value;
        }
        state.answers[q] = val;
        setCurrent(q, false);
        checkMatchingDups();
        updatePalette();
        persist();
      };
      node.addEventListener("input", handler);
      node.addEventListener("change", handler);
      node.addEventListener("focus", () => setCurrent(Number(node.getAttribute("data-q")), false));
    });
    el.questionScroll.querySelectorAll(".q-item").forEach((item) => {
      item.addEventListener("click", () => {
        const q = Number(item.getAttribute("data-q"));
        if (q) setCurrent(q, false);
      });
    });
  }

  function matchingQuestions() {
    const g = (paper.groups || []).find((x) => x.type === "matching_endings");
    if (!g) return [];
    return state.questions.filter((q) => q >= g.from && q <= g.to);
  }

  function checkMatchingDups() {
    const qs = matchingQuestions();
    const used = {};
    qs.forEach((q) => {
      const v = String(state.answers[q] || "").trim().toUpperCase();
      if (!v) return;
      (used[v] || (used[v] = [])).push(q);
    });
    qs.forEach((q) => {
      const item = document.getElementById("q-" + q);
      const sel = item ? item.querySelector("select") : null;
      const v = String(state.answers[q] || "").trim().toUpperCase();
      const dup = !!(v && used[v] && used[v].length > 1);
      if (sel) sel.classList.toggle("dup-warn", dup);
      if (item) item.classList.toggle("select-warn", dup);
    });
  }

  function renderPalette() {
    const qs = state.questions;
    let html = "";
    qs.forEach((q, i) => {
      const prev = qs[i - 1];
      if (prev && passageForQuestion(q) !== passageForQuestion(prev)) {
        html += '<span class="pal-sep" aria-hidden="true"></span>';
      }
      html +=
        '<button type="button" class="pal-btn" data-q="' +
        q +
        '" id="pal-' +
        q +
        '" aria-label="Question ' +
        q +
        '">' +
        q +
        "</button>";
    });
    el.paletteNums.innerHTML = html;
    el.paletteNums.querySelectorAll(".pal-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        leaveReview();
        setCurrent(Number(btn.getAttribute("data-q")), true);
        showMobilePane("questions");
      });
    });
    updatePalette();
  }

  function updatePalette() {
    state.questions.forEach((q) => {
      const btn = document.getElementById("pal-" + q);
      if (!btn) return;
      btn.classList.toggle("current", q === state.currentQ);
      btn.classList.toggle("answered", isAnswered(q));
      btn.classList.toggle("flagged", !!state.flags[q]);
    });
    el.btnFlag.classList.toggle("flagged", !!state.flags[state.currentQ]);
    el.btnFlag.textContent = state.flags[state.currentQ] ? "Flagged" : "Flag";
    const idx = state.questions.indexOf(state.currentQ);
    el.btnPrev.disabled = idx <= 0;
    el.btnNext.disabled = idx < 0 || idx >= state.questions.length - 1;
  }

  function updateCurrentHighlight() {
    el.questionScroll.querySelectorAll(".q-item").forEach((item) => {
      item.classList.toggle("current", Number(item.getAttribute("data-q")) === state.currentQ);
    });
  }


  function scrollQuestionIntoView(q) {
    const pane = el.questionScroll;
    if (!pane) return;
    const item = document.getElementById("q-" + q) || document.getElementById("ans-" + q);
    if (!item) return;
    const group = item.closest(".q-group");
    let target = item;
    if (group) {
      const first = group.querySelector("[data-q]");
      if (first && Number(first.getAttribute("data-q")) === q) target = group;
    }
    const top =
      target.getBoundingClientRect().top -
      pane.getBoundingClientRect().top +
      pane.scrollTop -
      8;
    pane.scrollTo({ top: Math.max(0, top), behavior: "auto" });
  }

  function setCurrent(q, scroll) {
    if (!state.questions.includes(q)) return;
    const needPassage = passageForQuestion(q);
    if (needPassage !== state.currentPassage) renderPassage(needPassage);
    state.currentQ = q;
    updateCurrentHighlight();
    updatePalette();
    if (scroll) {
      scrollQuestionIntoView(q);
      const input = document.getElementById("ans-" + q);
      if (input && typeof input.focus === "function") {
        try {
          input.focus({ preventScroll: true });
        } catch (err) {
          input.focus();
        }
      }
    }
    persist();
  }

  function showMobilePane(which) {
    el.exam.classList.toggle("show-passage", which === "passage");
    el.exam.classList.toggle("show-questions", which === "questions");
    el.paneToggle.querySelectorAll("button").forEach((b) => {
      b.classList.toggle("active", b.getAttribute("data-pane") === which);
    });
  }

  el.paneToggle.addEventListener("click", (e) => {
    const btn = e.target.closest("button[data-pane]");
    if (!btn) return;
    showMobilePane(btn.getAttribute("data-pane"));
  });

  function startSplitter() {
    let dragging = false;
    el.splitter.addEventListener("mousedown", (e) => {
      e.preventDefault();
      dragging = true;
      el.splitter.classList.add("dragging");
      document.body.style.cursor = "col-resize";
      document.body.style.userSelect = "none";
    });
    window.addEventListener("mousemove", (e) => {
      if (!dragging) return;
      const rect = el.readingSplit.getBoundingClientRect();
      const min = 240;
      let x = e.clientX - rect.left;
      x = Math.max(min, Math.min(rect.width - min - 6, x));
      el.passagePane.style.flex = "0 0 " + x + "px";
      el.passagePane.style.width = x + "px";
    });
    window.addEventListener("mouseup", () => {
      if (!dragging) return;
      dragging = false;
      el.splitter.classList.remove("dragging");
      document.body.style.cursor = "";
      document.body.style.userSelect = "";
    });
  }

  function selectionInPassage() {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || !sel.rangeCount) return null;
    const range = sel.getRangeAt(0);
    if (!el.passageBody.contains(range.commonAncestorContainer)) return null;
    return { sel, range };
  }

  function hideHlMenu() {
    el.hlMenu.classList.add("hidden");
  }

  function showHlMenuNear(clientX, clientY) {
    el.hlMenu.classList.remove("hidden");
    const x = Math.min(clientX, window.innerWidth - 160);
    const y = Math.min(clientY, window.innerHeight - 120);
    el.hlMenu.style.left = x + "px";
    el.hlMenu.style.top = y + "px";
  }

  function applyHighlight(range) {
    const mark = document.createElement("mark");
    mark.className = "hl";
    state.hlSeq += 1;
    mark.dataset.hid = String(state.hlSeq);
    try {
      range.surroundContents(mark);
    } catch (err) {
      mark.appendChild(range.extractContents());
      range.insertNode(mark);
    }
    window.getSelection().removeAllRanges();
    persist();
    return mark;
  }

  function unwrapMark(mark) {
    if (!mark || !mark.parentNode) return;
    const parent = mark.parentNode;
    while (mark.firstChild) parent.insertBefore(mark.firstChild, mark);
    parent.removeChild(mark);
    parent.normalize();
  }

  function marksInRange(range) {
    const marks = [];
    el.passageBody.querySelectorAll("mark.hl").forEach((m) => {
      try {
        if (range.intersectsNode(m)) marks.push(m);
      } catch (err) {
        /* ignore */
      }
    });
    return marks;
  }

  function doHighlight() {
    const ctx = selectionInPassage();
    if (!ctx) return;
    applyHighlight(ctx.range);
    hideHlMenu();
  }

  function doClearHighlight() {
    const ctx = selectionInPassage();
    if (ctx) {
      marksInRange(ctx.range).forEach(unwrapMark);
      window.getSelection().removeAllRanges();
    } else {
      const focused = el.passageBody.querySelector("mark.hl[data-active='1']");
      if (focused) unwrapMark(focused);
    }
    hideHlMenu();
    persist();
  }

  function openNoteModal(mark, range) {
    state.pendingNoteMark = mark || null;
    state.pendingNoteRange = range || null;
    el.noteText.value = mark && mark.dataset.note ? mark.dataset.note : "";
    el.noteModal.classList.remove("hidden");
    el.noteText.focus();
  }

  function closeNoteModal() {
    el.noteModal.classList.add("hidden");
    state.pendingNoteMark = null;
    state.pendingNoteRange = null;
  }

  function attachNoteToMark(mark, text) {
    const note = (text || "").trim();
    if (!note) {
      delete mark.dataset.note;
      mark.classList.remove("has-note");
      const dot = mark.querySelector(".note-dot");
      if (dot) dot.remove();
      mark.removeAttribute("title");
      return;
    }
    mark.dataset.note = note;
    mark.classList.add("has-note");
    mark.setAttribute("title", note);
    if (!mark.querySelector(".note-dot")) {
      const dot = document.createElement("span");
      dot.className = "note-dot";
      dot.setAttribute("aria-hidden", "true");
      mark.appendChild(dot);
    }
  }

  function doAddNote() {
    hideHlMenu();
    const active = el.passageBody.querySelector("mark.hl[data-active='1']");
    const ctx = selectionInPassage();
    if (active && (!ctx || ctx.range.intersectsNode(active))) {
      openNoteModal(active, null);
      return;
    }
    if (ctx) {
      openNoteModal(null, ctx.range);
      return;
    }
    if (active) openNoteModal(active, null);
  }

  el.btnHighlight.addEventListener("click", doHighlight);
  el.btnClearHighlight.addEventListener("click", doClearHighlight);
  el.btnAddNote.addEventListener("click", doAddNote);

  el.passageBody.addEventListener("mouseup", (e) => {
    setTimeout(() => {
      const ctx = selectionInPassage();
      if (!ctx) {
        hideHlMenu();
        return;
      }
      showHlMenuNear(e.clientX + 8, e.clientY + 8);
    }, 0);
  });

  el.passageBody.addEventListener("click", (e) => {
    const mark = e.target.closest("mark.hl");
    el.passageBody.querySelectorAll("mark.hl").forEach((m) => m.removeAttribute("data-active"));
    if (mark) {
      mark.dataset.active = "1";
      if (mark.classList.contains("has-note") && !selectionInPassage()) {
        openNoteModal(mark, null);
      }
    }
  });

  el.hlMenu.addEventListener("click", (e) => {
    const btn = e.target.closest("button[data-act]");
    if (!btn) return;
    const act = btn.getAttribute("data-act");
    if (act === "highlight") doHighlight();
    else if (act === "clear") doClearHighlight();
    else if (act === "note") doAddNote();
  });

  document.addEventListener("mousedown", (e) => {
    if (!el.hlMenu.contains(e.target)) hideHlMenu();
  });

  el.btnNoteSave.addEventListener("click", () => {
    let mark = state.pendingNoteMark;
    if (!mark && state.pendingNoteRange) {
      mark = applyHighlight(state.pendingNoteRange);
    }
    if (mark) attachNoteToMark(mark, el.noteText.value);
    closeNoteModal();
    persist();
  });
  el.btnNoteCancel.addEventListener("click", closeNoteModal);

  function unansweredCount() {
    return state.questions.filter((q) => !isAnswered(q)).length;
  }

  function flaggedCount() {
    return state.questions.filter((q) => state.flags[q]).length;
  }

  function renderReview() {
    const rows = state.questions
      .map((q) => {
        const answered = isAnswered(q);
        const flagged = !!state.flags[q];
        return (
          '<button type="button" class="review-row" data-q="' +
          q +
          '"><span class="rv-q">Q' +
          q +
          '</span><span class="rv-preview">' +
          (answered ? escapeHtml(String(state.answers[q])) : "—") +
          '</span><span class="rv-status ' +
          (answered ? "answered" : "unanswered") +
          '">' +
          (answered ? "Answered" : "Not answered") +
          '</span><span class="rv-flag">' +
          (flagged ? "⚑ Flagged" : "") +
          "</span></button>"
        );
      })
      .join("");
    el.reviewList.innerHTML = rows;
    el.reviewList.querySelectorAll(".review-row").forEach((row) => {
      row.addEventListener("click", () => {
        const q = Number(row.getAttribute("data-q"));
        leaveReview();
        setCurrent(q, true);
        showMobilePane("questions");
      });
    });
  }

  function enterReview() {
    state.reviewing = true;
    document.body.classList.add("reviewing");
    el.reviewScreen.classList.remove("hidden");
    renderReview();
    el.btnReview.textContent = "Questions";
  }

  function leaveReview() {
    if (!state.reviewing) return;
    state.reviewing = false;
    document.body.classList.remove("reviewing");
    el.reviewScreen.classList.add("hidden");
    el.btnReview.textContent = "Review";
  }

  function toggleReview() {
    if (state.reviewing) leaveReview();
    else enterReview();
  }

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
    if (state.remaining % 5 === 0) persist();
    if (!state.warned5 && state.remaining === 300) {
      state.warned5 = true;
      showBanner("5 minutes remaining. Check any unanswered questions.", "warn");
    }
    if (!state.warned1 && state.remaining === 60) {
      state.warned1 = true;
      showBanner("1 minute remaining. The test will be submitted automatically when time is up.", "warn");
    }
    if (state.remaining <= 0) {
      state.remaining = 0;
      renderTimer();
      showBanner("Time is up. Submitting now…", "warn");
      submitAnswers(true);
    }
  }

  function enterExamChrome() {
    document.body.classList.add("exam-on");
    el.setup.classList.add("hidden");
    el.done.classList.add("hidden");
    el.exam.classList.remove("hidden");
    if (el.footer) el.footer.classList.add("hidden");
    el.statusBanner.classList.add("hidden");
    showMobilePane("passage");
  }

  function leaveExamChrome() {
    document.body.classList.remove("exam-on", "reviewing");
    el.exam.classList.add("hidden");
    if (el.footer) el.footer.classList.remove("hidden");
    el.btnPause.classList.add("hidden");
    el.timer.textContent = "--:--";
    el.timer.classList.remove("warn", "danger");
    el.modeLabel.textContent = "Ready";
    el.btnSubmit.disabled = false;
  }

  function beginFromState() {
    enterExamChrome();
    renderPassage(passageForQuestion(state.currentQ), false);
    renderQuestions();
    renderPalette();
    setCurrent(state.currentQ, true);
    el.modeLabel.textContent = MODE_LABELS[state.mode] || state.mode;
    el.btnPause.classList.toggle("hidden", !state.allowPause);
    el.btnPause.textContent = state.paused ? "Resume" : "Pause";
    if (state.paused) showBanner("The timer is paused (teacher mode).", "info");
    renderTimer();
    stopTick();
    state.tickId = setInterval(tick, 1000);
    window.onbeforeunload = function () {
      if (state.running && !state.submitted) return "The test is in progress. Are you sure you want to leave?";
    };
    if (state.remaining <= 0) {
      showBanner("Time is up. Submitting now…", "warn");
      submitAnswers(true);
    }
  }

  async function startSession(name, mode) {
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
        module: "reading",
        mode: mode,
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) {
      showSetupError(data.error || "邀请码无效或已失效");
      return null;
    }
    return data;
  }

  async function ensurePaper() {
    if (paper && paper.groups) return true;
    const res = await fetch("/api/reading/paper", { credentials: "same-origin" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      return false;
    }
    paper = data;
    return !!(paper && paper.groups);
  }

  function restoreSaved(saved) {
    state.mode = saved.mode || "full";
    state.setId = saved.setId || "set-a";
    state.name = saved.name || "";
    state.duration = saved.duration || DURATIONS[state.mode];
    state.pausedTotal = saved.pausedTotal || 0;
    state.allowPause = !!saved.allowPause;
    state.answers = saved.answers || {};
    state.flags = saved.flags || {};
    state.passageHtml = saved.passageHtml || {};
    state.hlSeq = saved.hlSeq || 0;
    state.warned5 = !!saved.warned5;
    state.warned1 = !!saved.warned1;
    state.questions = questionList(state.mode);
    state.currentQ = state.questions.includes(saved.currentQ) ? saved.currentQ : state.questions[0];
    state.paused = !!saved.paused;
    if (state.paused) {
      state.remaining = saved.remaining || 0;
    } else {
      const elapsed = Math.floor((Date.now() - (saved.savedAt || Date.now())) / 1000);
      state.remaining = Math.max(0, (saved.remaining || 0) - elapsed);
    }
    if (el.candidateName && state.name) el.candidateName.value = state.name;
  }

  async function startExam(fromSaved) {
    if (!fromSaved) {
      const name = (el.candidateName.value || "").trim();
      const mode = selectedMode();
      el.btnStart.disabled = true;
      try {
        const started = await startSession(name, mode);
        if (!started) return;
        const loaded = await ensurePaper();
        if (!loaded) {
          showSetupError("试卷加载失败，请重试。");
          return;
        }
      } catch (err) {
        console.error(err);
        showSetupError("无法开始考试，请检查网络后重试。");
        return;
      } finally {
        el.btnStart.disabled = false;
      }
      const saved = loadPersist();
      if (saved && saved.running && saved.name === name) {
        restoreSaved(saved);
        fromSaved = true;
      } else {
        state.name = name;
        state.mode = mode;
        state.setId = "set-a";
        state.duration = DURATIONS[state.mode] || DURATIONS.full;
        state.remaining = state.duration;
        state.pausedTotal = 0;
        state.pauseStartedAt = null;
        state.paused = false;
        state.answers = {};
        state.flags = {};
        state.passageHtml = {};
        state.hlSeq = 0;
        state.warned5 = false;
        state.warned1 = false;
        state.allowPause = !!(el.teacherPause && el.teacherPause.checked);
        state.questions = questionList(state.mode);
        state.currentQ = state.questions[0];
        state.currentPassage = 0;
      }
    }
    if (!paper || !paper.groups) {
      showSetupError("The reading paper could not be loaded.");
      return;
    }
    state.running = true;
    state.submitted = false;
    state.reviewing = false;
    beginFromState();
    persist();
  }

  async function resumeIfNeeded() {
    const saved = loadPersist();
    if (!saved || !saved.running) return;
    if (el.candidateName && saved.name) el.candidateName.value = saved.name;
    try {
      const loaded = await ensurePaper();
      if (!loaded) {
        if (el.resumeBanner) {
          el.resumeBanner.textContent = "Your test is still in progress. Enter your name and invitation code to continue.";
          el.resumeBanner.classList.remove("hidden");
        }
        return;
      }
    } catch (err) {
      console.error(err);
      if (el.resumeBanner) {
        el.resumeBanner.textContent = "Your test is still in progress. Enter your name and invitation code to continue.";
        el.resumeBanner.classList.remove("hidden");
      }
      return;
    }
    restoreSaved(saved);
    startExam(true);
  }

  function togglePause() {
    if (!state.running || state.submitted || !state.allowPause) return;
    if (!state.paused) {
      state.paused = true;
      state.pauseStartedAt = Date.now();
      el.btnPause.textContent = "Resume";
      showBanner("The timer is paused (teacher mode).", "info");
    } else {
      if (state.pauseStartedAt) {
        state.pausedTotal += Math.floor((Date.now() - state.pauseStartedAt) / 1000);
        state.pauseStartedAt = null;
      }
      state.paused = false;
      el.btnPause.textContent = "Pause";
      el.statusBanner.classList.add("hidden");
    }
    persist();
  }

  function toggleFlag() {
    const q = state.currentQ;
    if (!q) return;
    if (state.flags[q]) delete state.flags[q];
    else state.flags[q] = true;
    updatePalette();
    if (state.reviewing) renderReview();
    persist();
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

    const flags = state.questions.filter((q) => state.flags[q]);
    const answers = {};
    state.questions.forEach((q) => {
      answers[String(q)] = state.answers[q] != null ? String(state.answers[q]) : "";
    });

    const payload = {
      candidate_name: state.name || (el.candidateName.value || "").trim(),
      mode: state.mode,
      prompt_set_id: state.setId || "set-a",
      answers: answers,
      flags: flags,
      duration_seconds: state.duration,
      time_remaining_seconds: Math.max(0, state.remaining),
      time_used_seconds: Math.max(0, state.duration - state.remaining),
      paused_total_seconds: state.pausedTotal,
      auto_submitted: !!auto,
    };

    el.btnSubmit.disabled = true;
    try {
      const res = await fetch("/api/reading/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error((data && data.error) || "submit failed");
      clearPersist();
      leaveExamChrome();
      el.done.classList.remove("hidden");
      const used = formatTime(payload.time_used_seconds);
      el.doneMsg.innerHTML =
        (auto ? "Time is up. Your answers have been submitted automatically." : "Submitted.") +
        "<br/>Name: " +
        escapeHtml(payload.candidate_name || "") +
        "<br/>Time used: " +
        used +
        "<br/><strong>You may close this page.</strong>";
    } catch (err) {
      state.submitted = false;
      state.running = true;
      state.tickId = setInterval(tick, 1000);
      showBanner("Submission failed. Please check your connection and try again, or contact your teacher.", "error");
      el.btnSubmit.disabled = false;
      window.onbeforeunload = function () {
        if (state.running && !state.submitted) return "The test is in progress. Are you sure you want to leave?";
      };
      console.error(err);
    }
  }

  function resetToSetup() {
    if (state.running && !state.submitted) {
      if (!confirm("Quit this test? Your answers on this device will be discarded.")) return;
    }
    stopTick();
    state.running = false;
    state.submitted = false;
    state.reviewing = false;
    window.onbeforeunload = null;
    clearPersist();
    leaveExamChrome();
    el.done.classList.add("hidden");
    el.setup.classList.remove("hidden");
  }

  el.btnStart.addEventListener("click", () => startExam(false));
  el.btnPause.addEventListener("click", togglePause);
  el.btnFlag.addEventListener("click", toggleFlag);
  el.btnReview.addEventListener("click", toggleReview);
  el.btnBackToTest.addEventListener("click", leaveReview);
  el.btnPrev.addEventListener("click", () => {
    const idx = state.questions.indexOf(state.currentQ);
    if (idx > 0) {
      leaveReview();
      setCurrent(state.questions[idx - 1], true);
    }
  });
  el.btnNext.addEventListener("click", () => {
    const idx = state.questions.indexOf(state.currentQ);
    if (idx >= 0 && idx < state.questions.length - 1) {
      leaveReview();
      setCurrent(state.questions[idx + 1], true);
    }
  });
  el.btnSubmit.addEventListener("click", () => {
    const u = unansweredCount();
    const f = flaggedCount();
    let msg = "Are you sure you want to submit? You cannot change your answers after submitting.";
    if (u || f) {
      msg += "\n\n";
      if (u) msg += u + " question(s) not answered. ";
      if (f) msg += f + " flagged for review.";
    }
    if (!confirm(msg)) return;
    submitAnswers(false);
  });
  el.btnQuit.addEventListener("click", resetToSetup);
  el.btnAgain.addEventListener("click", resetToSetup);

  startSplitter();
  showMobilePane("passage");
  resumeIfNeeded();
})();
