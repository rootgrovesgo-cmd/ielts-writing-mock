(function () {
  const LS_KEY = "ielts-listening-set-a";

  const el = {
    setup: document.getElementById("setupPanel"),
    exam: document.getElementById("examPanel"),
    done: document.getElementById("donePanel"),
    siteFooter: document.getElementById("siteFooter"),
    candidateName: document.getElementById("candidateName"),
    inviteCode: document.getElementById("inviteCode"),
    teacherPause: document.getElementById("teacherPause"),
    btnStart: document.getElementById("btnStart"),
    nameError: document.getElementById("nameError"),
    resumeBanner: document.getElementById("resumeBanner"),
    modeLabel: document.getElementById("modeLabel"),
    timer: document.getElementById("timer"),
    btnPause: document.getElementById("btnPause"),
    statusBanner: document.getElementById("statusBanner"),
    sectionTabs: document.getElementById("sectionTabs"),
    questionScroll: document.getElementById("questionScroll"),
    reviewScreen: document.getElementById("reviewScreen"),
    reviewList: document.getElementById("reviewList"),
    btnBackToTest: document.getElementById("btnBackToTest"),
    paletteNums: document.getElementById("paletteNums"),
    btnPrev: document.getElementById("btnPrev"),
    btnNext: document.getElementById("btnNext"),
    btnFlag: document.getElementById("btnFlag"),
    btnReview: document.getElementById("btnReview"),
    btnQuit: document.getElementById("btnQuit"),
    btnSubmit: document.getElementById("btnSubmit"),
    audioBar: document.getElementById("audioBar"),
    audio: document.getElementById("examAudio"),
    audioLabel: document.getElementById("audioLabel"),
    audioPhase: document.getElementById("audioPhase"),
    audioProgress: document.getElementById("audioProgress"),
    audioFill: document.getElementById("audioFill"),
    audioTime: document.getElementById("audioTime"),
    volume: document.getElementById("volume"),
    btnUnlockAudio: document.getElementById("btnUnlockAudio"),
    btnToggleTranscript: document.getElementById("btnToggleTranscript"),
    transcriptPanel: document.getElementById("transcriptPanel"),
    reviewModeBanner: document.getElementById("reviewModeBanner"),
    reviewModeMeta: document.getElementById("reviewModeMeta"),
    doneMsg: document.getElementById("doneMsg"),
    doneResult: document.getElementById("doneResult"),
    doneScore: document.getElementById("doneScore"),
    doneBand: document.getElementById("doneBand"),
    doneParts: document.getElementById("doneParts"),
    btnReviewPaper: document.getElementById("btnReviewPaper"),
    btnReviewMistakes: document.getElementById("btnReviewMistakes"),
    btnAgain: document.getElementById("btnAgain"),
  };

  const state = {
    running: false,
    submitted: false,
    reviewing: false,
    attemptReview: false,
    mistakesOnly: false,
    paused: false,
    allowPause: false,
    name: "",
    mode: "full",
    setId: "set-a",
    questions: [],
    currentQ: 1,
    visibleSection: 1,
    answers: {},
    flags: {},
    duration: 0,
    remaining: 0,
    pausedTotal: 0,
    pauseStartedAt: null,
    partTimes: { 1: 0, 2: 0, 3: 0, 4: 0 },
    activePart: 0,
    partTickAt: null,
    warned5: false,
    warned1: false,
    tickId: null,
    audioSection: 0,
    audioEnded: false,
    lastLegalTime: 0,
    playlist: [],
    reviewByQ: {},
    reviewMistakeQs: [],
    transcripts: {},
    showTranscript: false,
  };

  let paper = null;

  function hideSetupError() {
    if (el.nameError) el.nameError.classList.add("hidden");
  }
  function showSetupError(msg) {
    if (!el.nameError) return;
    el.nameError.textContent = msg || "Please enter your name and invitation code before starting.";
    el.nameError.classList.remove("hidden");
  }

  function selectedMode() {
    const picked = document.querySelector('input[name="mode"]:checked');
    return (picked && picked.value) || "full";
  }

  function escapeHtml(s) {
    return String(s == null ? "" : s)
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

  function formatDuration(sec) {
    sec = Math.max(0, Math.floor(Number(sec) || 0));
    if (sec < 60) return sec + "s";
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return m + "min" + s + "s";
  }

  function questionList(mode) {
    if (mode === "section1") return range(1, 10);
    if (mode === "section2") return range(11, 20);
    if (mode === "section3") return range(21, 30);
    if (mode === "section4") return range(31, 40);
    return range(1, 40);
  }

  function range(a, b) {
    const out = [];
    for (let i = a; i <= b; i++) out.push(i);
    return out;
  }

  function sectionIdForQuestion(q) {
    if (q <= 10) return 1;
    if (q <= 20) return 2;
    if (q <= 30) return 3;
    return 4;
  }

  function sectionsInMode(mode) {
    if (mode && mode.indexOf("section") === 0) return [Number(mode.replace("section", ""))];
    return [1, 2, 3, 4];
  }

  function sectionAudioDuration(id) {
    const sec = ((paper && paper.sections) || []).find((s) => Number(s.id) === Number(id));
    return (sec && sec.audio && Number(sec.audio.duration_seconds)) || 0;
  }

  function durationForMode(mode) {
    const ids = sectionsInMode(mode);
    let total = ids.reduce((sum, id) => sum + sectionAudioDuration(id), 0);
    if (mode === "full") total += Number((paper && paper.check_seconds) || 120);
    return total;
  }

  function emptyPartTimes() {
    return { 1: 0, 2: 0, 3: 0, 4: 0 };
  }

  function creditPartTime() {
    const now = Date.now();
    if (state.partTickAt == null) {
      state.partTickAt = now;
      return;
    }
    const started = state.partTickAt;
    if (!state.activePart || state.paused || !state.running || state.submitted) {
      state.partTickAt = now;
      return;
    }
    const elapsed = Math.max(0, Math.floor((now - started) / 1000));
    if (elapsed) state.partTimes[state.activePart] = (state.partTimes[state.activePart] || 0) + elapsed;
    state.partTickAt = now;
  }

  function setActivePart(id) {
    if (state.activePart === id) return;
    creditPartTime();
    state.activePart = id;
    state.partTickAt = Date.now();
  }

  function isAnswered(q) {
    return !!(state.answers[q] && String(state.answers[q]).trim());
  }

  function renderTimer() {
    if (el.timer) el.timer.textContent = formatTime(state.remaining);
  }

  function showBanner(msg, kind) {
    if (!el.statusBanner) return;
    el.statusBanner.className = "banner " + (kind || "info") + " listening-status";
    el.statusBanner.textContent = msg;
    el.statusBanner.classList.remove("hidden");
  }

  function persist() {
    if (state.attemptReview) return;
    if (!state.running || state.submitted) return;
    const payload = {
      running: true,
      savedAt: Date.now(),
      name: state.name,
      mode: state.mode,
      setId: state.setId,
      answers: state.answers,
      flags: state.flags,
      duration: state.duration,
      remaining: state.remaining,
      paused: state.paused,
      pausedTotal: state.pausedTotal,
      allowPause: state.allowPause,
      partTimes: state.partTimes,
      activePart: state.activePart,
      currentQ: state.currentQ,
      visibleSection: state.visibleSection,
      audioSection: state.audioSection,
      audioTime: el.audio ? el.audio.currentTime || 0 : 0,
      audioEnded: state.audioEnded,
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

  function renderBlank(q, prefix) {
    const val = escapeHtml(state.answers[q] || "");
    const ro = state.attemptReview ? " readonly" : "";
    return (
      '<span class="blank" data-q="' +
      q +
      '"><span class="qnum">' +
      q +
      "</span>" +
      (prefix ? '<span class="blank-prefix">' + escapeHtml(prefix) + "</span>" : "") +
      '<input type="text" id="ans-' +
      q +
      '" data-q="' +
      q +
      '" value="' +
      val +
      '" maxlength="40" autocomplete="off" spellcheck="false" aria-label="Question ' +
      q +
      '"' +
      ro +
      " /></span>"
    );
  }

  function renderParts(parts) {
    return (parts || [])
      .map((part) => {
        if (part && typeof part === "object" && part.q) return renderBlank(part.q, part.prefix || "");
        return escapeHtml(part == null ? "" : String(part));
      })
      .join("");
  }

  function renderCellLines(cell) {
    const lines = Array.isArray(cell) ? cell : cell ? [cell] : [];
    return lines
      .map((line) => {
        const parts = Array.isArray(line) ? line : [line];
        return '<div class="cell-line">' + renderParts(parts) + "</div>";
      })
      .join("");
  }

  function renderNotesTable(group) {
    const table = group.table || {};
    const headers = table.headers || [];
    let html = '<div class="notes-table-wrap">';
    if (table.title) html += '<div class="notes-title">' + escapeHtml(table.title) + "</div>";
    html += '<table class="notes-table"><thead><tr>';
    headers.forEach((h) => {
      html += "<th>" + escapeHtml(h) + "</th>";
    });
    html += "</tr></thead><tbody>";
    (table.rows || []).forEach((row) => {
      html += "<tr>";
      (row || []).forEach((cell) => {
        html += "<td>" + renderCellLines(cell);
        const qs = [];
        (Array.isArray(cell) ? cell : []).forEach((line) => {
          (Array.isArray(line) ? line : [line]).forEach((part) => {
            if (part && typeof part === "object" && part.q) qs.push(part.q);
          });
        });
        if (state.attemptReview) qs.forEach((q) => { html += renderReviewKey(q); });
        html += "</td>";
      });
      html += "</tr>";
    });
    html += "</tbody></table></div>";
    return html;
  }

  function chosenPairLetters(from, to) {
    return [state.answers[from], state.answers[to]]
      .map((v) => (v || "").toString().toUpperCase())
      .filter(Boolean);
  }

  function renderChooseTwo(group) {
    const from = group.from;
    const to = group.to;
    const selected = chosenPairLetters(from, to);
    const ro = state.attemptReview ? " disabled" : "";
    const options = group.options || {};
    let html =
      '<div class="choose-two-box" data-q="' +
      from +
      '" data-q-to="' +
      to +
      '" data-from="' +
      from +
      '" data-to="' +
      to +
      '"><div class="choose-two-stem"><span class="qnum">' +
      from +
      "–" +
      to +
      "</span><div>" +
      escapeHtml(group.stem || "") +
      '</div></div><div class="mcq-options choose-two-options">';
    Object.keys(options).forEach((letter) => {
      const id = "ans-" + from + "-" + to + "-" + letter;
      const chk = selected.indexOf(letter) >= 0 ? " checked" : "";
      html +=
        '<label for="' +
        id +
        '"><input type="checkbox" id="' +
        id +
        '" data-pair-from="' +
        from +
        '" data-pair-to="' +
        to +
        '" value="' +
        escapeHtml(letter) +
        '"' +
        chk +
        ro +
        " /> <strong>" +
        escapeHtml(letter) +
        "</strong> " +
        escapeHtml(options[letter]) +
        "</label>";
    });
    html += "</div>" + renderChooseTwoReview(group) + "</div>";
    return html;
  }

  function renderChooseTwoReview(group) {
    if (!state.attemptReview) return "";
    const from = group.from;
    const to = group.to;
    const row = state.reviewByQ[from] || state.reviewByQ[String(from)] || {};
    const row2 = state.reviewByQ[to] || state.reviewByQ[String(to)] || {};
    const official = row.correct || row2.correct || "";
    const studentLetters = [row.student, row2.student]
      .map((v) => (v || "").toString().trim())
      .filter(Boolean);
    const student = studentLetters.length ? escapeHtml(studentLetters.join(", ")) : "（未作答）";
    const ok = !!row.ok && !!row2.ok;
    const expl = row.explanation || row2.explanation || "";
    return (
      '<div class="q-review-key ' +
      (ok ? "is-ok" : "is-wrong") +
      '" data-review-q="' +
      from +
      '"><dl>' +
      '<div class="q-rev-student"><dt>你的作答</dt><dd>' +
      student +
      "</dd></div>" +
      "<div><dt>标准答案</dt><dd>" +
      escapeHtml(official) +
      "（顺序不限）</dd></div></dl>" +
      (expl ? '<div class="q-explain"><h4>解析</h4><p>' + escapeHtml(expl) + "</p></div>" : "") +
      "</div>"
    );
  }

  function renderNotes(notes) {
    let html = '<div class="notes-box">';
    if (notes && notes.title) html += '<div class="notes-title">' + escapeHtml(notes.title) + "</div>";
    ((notes && notes.sections) || []).forEach((sec) => {
      if (sec.heading) html += '<div class="notes-heading">' + escapeHtml(sec.heading) + "</div>";
      html += "<ul>";
      (sec.items || []).forEach((item) => {
        html += "<li>";
        if (item.parts) html += renderParts(item.parts);
        html += "</li>";
      });
      html += "</ul>";
    });
    html += "</div>";
    return html;
  }

  function renderSelect(q, options) {
    const cur = (state.answers[q] || "").toString().toUpperCase();
    const ro = state.attemptReview ? " disabled" : "";
    let html =
      '<select id="ans-' + q + '" data-q="' + q + '" aria-label="Question ' + q + '"' + ro + ">";
    html += '<option value="">—</option>';
    (options || []).forEach((opt) => {
      const letter = typeof opt === "string" ? opt : opt.key;
      const sel = cur === String(letter).toUpperCase() ? " selected" : "";
      html += '<option value="' + escapeHtml(letter) + '"' + sel + ">" + escapeHtml(letter) + "</option>";
    });
    html += "</select>";
    return html;
  }

  function renderForm(group) {
    let html = '<div class="form-box">';
    if (group.form_title) html += '<div class="form-title">' + escapeHtml(group.form_title) + "</div>";
    html += '<table class="form-table">';
    (group.rows || []).forEach((row) => {
      html += '<tr data-q="' + row.q + '"><th>' + escapeHtml(row.label || "");
      if (row.hint) html += ' <span class="muted">(' + escapeHtml(row.hint) + ")</span>";
      html += '</th><td class="blank-cell">' + renderBlank(row.q, row.prefix || "") + "</td></tr>";
      html += (state.attemptReview ? '<tr class="review-row"><td colspan="2">' + renderReviewKey(row.q) + "</td></tr>" : "");
    });
    html += "</table></div>";
    return html;
  }

  function renderMcq(group) {
    let html = '<div class="mcq-box">';
    (group.items || []).forEach((item) => {
      const cur = (state.answers[item.q] || "").toString().toUpperCase();
      const ro = state.attemptReview ? " disabled" : "";
      html += '<div class="mcq-item" data-q="' + item.q + '"><div class="q-item"><span class="qnum">' + item.q + "</span><div>" + escapeHtml(item.stem || "") + "</div></div>";
      html += '<div class="mcq-options">';
      Object.keys(item.options || {}).forEach((letter) => {
        const id = "ans-" + item.q + "-" + letter;
        const chk = cur === letter ? " checked" : "";
        html +=
          '<label for="' +
          id +
          '"><input type="radio" name="ans-' +
          item.q +
          '" id="' +
          id +
          '" data-q="' +
          item.q +
          '" value="' +
          escapeHtml(letter) +
          '"' +
          chk +
          ro +
          " /> <strong>" +
          escapeHtml(letter) +
          "</strong> " +
          escapeHtml(item.options[letter]) +
          "</label>";
      });
      html += "</div>" + renderReviewKey(item.q) + "</div>";
    });
    html += "</div>";
    return html;
  }

  function renderMap(group) {
    let html = '<div class="map-box">';
    if (group.map && group.map.title) html += '<div class="map-title">' + escapeHtml(group.map.title) + "</div>";
    if (group.map && group.map.svg) html += '<div class="map-svg-wrap">' + group.map.svg + "</div>";
    html += '<div class="map-items">';
    (group.items || []).forEach((item) => {
      html +=
        '<div class="q-item" data-q="' +
        item.q +
        '"><span class="qnum">' +
        item.q +
        "</span><div>" +
        escapeHtml(item.stem || "") +
        "</div>" +
        renderSelect(item.q, group.options || ["A", "B", "C", "D", "E", "F"]) +
        "</div>" +
        renderReviewKey(item.q);
    });
    html += "</div></div>";
    return html;
  }

  function renderMatching(group) {
    let html = '<div class="match-box">';
    if (group.legend && group.legend.length) {
      html += '<ul class="legend">';
      group.legend.forEach((row) => {
        html += "<li><strong>" + escapeHtml(row.key) + "</strong> " + escapeHtml(row.text) + "</li>";
      });
      html += "</ul>";
    }
    const letters = (group.legend || []).map((row) => row.key);
    html += '<div class="match-items">';
    (group.items || []).forEach((item) => {
      html +=
        '<div class="q-item" data-q="' +
        item.q +
        '"><span class="qnum">' +
        item.q +
        "</span><div>" +
        escapeHtml(item.stem || "") +
        "</div>" +
        renderSelect(item.q, letters) +
        "</div>" +
        renderReviewKey(item.q);
    });
    html += "</div></div>";
    return html;
  }

  function renderReviewKey(q) {
    if (!state.attemptReview) return "";
    const row = state.reviewByQ[q] || state.reviewByQ[String(q)];
    if (!row) return "";
    const ok = !!row.ok;
    const student = row.student_blank || !(row.student || "").trim() ? "（未作答）" : escapeHtml(row.student);
    const correct = escapeHtml(row.correct || "");
    const expl = row.explanation ? escapeHtml(row.explanation) : "";
    return (
      '<div class="q-review-key ' +
      (ok ? "is-ok" : "is-wrong") +
      '" data-review-q="' +
      q +
      '"><dl>' +
      '<div class="q-rev-student"><dt>你的作答</dt><dd>' +
      student +
      "</dd></div>" +
      "<div><dt>标准答案</dt><dd>" +
      correct +
      "</dd></div></dl>" +
      (expl ? '<div class="q-explain"><h4>解析</h4><p>' + expl + "</p></div>" : "") +
      "</div>"
    );
  }

  function groupInstructions(group) {
    const lines = group.instructions || [];
    if (!lines.length) return "";
    let html = '<div class="lis-instructions">';
    lines.forEach((line) => {
      const upper = /NO MORE THAN|ONE WORD|AND\/OR A NUMBER/i.test(line);
      html += "<p" + (upper ? ' class="word-limit"' : "") + ">" + escapeHtml(line) + "</p>";
    });
    html += "</div>";
    return html;
  }

  function renderGroup(group) {
    let body = "";
    if (group.type === "form") body = renderForm(group);
    else if (group.type === "mcq") body = renderMcq(group);
    else if (group.type === "map") body = renderMap(group);
    else if (group.type === "matching") body = renderMatching(group);
    else if (group.type === "notes") body = renderNotes(group.notes) + notesReviewKeys(group);
    else if (group.type === "notes_table") body = renderNotesTable(group);
    else if (group.type === "choose_two") body = renderChooseTwo(group);
    else body = "";
    return (
      '<section class="lis-group" data-from="' +
      group.from +
      '" data-to="' +
      group.to +
      '"><h2>' +
      escapeHtml(group.heading || "") +
      "</h2>" +
      groupInstructions(group) +
      body +
      "</section>"
    );
  }

  function notesReviewKeys(group) {
    if (!state.attemptReview) return "";
    let html = "";
    for (let q = group.from; q <= group.to; q++) html += renderReviewKey(q);
    return html;
  }

  function findSection(id) {
    return ((paper && paper.sections) || []).find((s) => Number(s.id) === Number(id));
  }

  function renderQuestions() {
    const section = findSection(state.visibleSection);
    if (!el.questionScroll || !section) return;
    const allowed = new Set(state.questions);
    let html = "<h1>Section " + section.id + "</h1>";
    if (section.context) html += '<p class="muted">' + escapeHtml(section.context) + "</p>";
    (section.groups || []).forEach((group) => {
      if (group.from && group.to && !range(group.from, group.to).some((q) => allowed.has(q))) return;
      html += renderGroup(group);
    });
    el.questionScroll.innerHTML = html;
    bindQuestionInputs();
    updateCurrentHighlight();
  }

  function bindQuestionInputs() {
    if (!el.questionScroll) return;
    el.questionScroll.querySelectorAll("input[data-q], select[data-q]").forEach((node) => {
      const apply = () => {
        if (state.attemptReview) return;
        const q = Number(node.getAttribute("data-q"));
        if (node.type === "radio") {
          if (node.checked) state.answers[q] = node.value;
        } else {
          state.answers[q] = node.value;
        }
        updatePalette();
        persist();
      };
      node.addEventListener("input", apply);
      node.addEventListener("change", apply);
      node.addEventListener("focus", () => setCurrent(Number(node.getAttribute("data-q")), false));
    });
    bindChooseTwo();
  }

  function bindChooseTwo() {
    if (!el.questionScroll) return;
    el.questionScroll.querySelectorAll("input[type=checkbox][data-pair-from]").forEach((node) => {
      node.addEventListener("change", () => {
        if (state.attemptReview) return;
        const from = Number(node.getAttribute("data-pair-from"));
        const to = Number(node.getAttribute("data-pair-to"));
        const box = node.closest(".choose-two-box");
        if (!box) return;
        const boxes = Array.prototype.slice.call(box.querySelectorAll("input[type=checkbox]"));
        if (node.checked) node.setAttribute("data-picked-at", String(Date.now()));
        else node.removeAttribute("data-picked-at");
        let checked = boxes.filter((b) => b.checked);
        if (checked.length > 2) {
          checked.sort(function (a, b) {
            return Number(a.getAttribute("data-picked-at") || 0) - Number(b.getAttribute("data-picked-at") || 0);
          });
          const drop = checked.find((b) => b !== node) || checked[0];
          drop.checked = false;
          drop.removeAttribute("data-picked-at");
          checked = boxes.filter((b) => b.checked);
        }
        const letters = checked.map((b) => b.value);
        state.answers[from] = letters[0] || "";
        state.answers[to] = letters[1] || "";
        setCurrent(from, false);
        updatePalette();
        persist();
      });
      node.addEventListener("focus", () => setCurrent(Number(node.getAttribute("data-pair-from")), false));
    });
  }

  function renderTabs() {
    if (!el.sectionTabs) return;
    const ids = sectionsInMode(state.mode);
    el.sectionTabs.innerHTML = ids
      .map((id) => {
        const on = Number(id) === Number(state.visibleSection) ? " active" : "";
        return '<button type="button" data-section="' + id + '" class="' + on.trim() + '">Section ' + id + "</button>";
      })
      .join("");
    el.sectionTabs.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", () => {
        const id = Number(btn.getAttribute("data-section"));
        const first = state.questions.find((q) => sectionIdForQuestion(q) === id);
        if (first) setCurrent(first, true);
        else {
          state.visibleSection = id;
          renderQuestions();
          renderTabs();
        }
      });
    });
  }

  function renderPalette() {
    if (!el.paletteNums) return;
    const nav = reviewNavList();
    el.paletteNums.innerHTML = state.questions
      .map((q) => {
        const classes = ["pal-num"];
        if (q === state.currentQ) classes.push("current");
        if (isAnswered(q)) classes.push("answered");
        if (state.flags[q]) classes.push("flagged");
        if (state.attemptReview) {
          const row = state.reviewByQ[q];
          if (row && (row.ok ? "ok" : "wrong")) classes.push(row.ok ? "is-ok" : "is-wrong");
        }
        if (state.mistakesOnly && nav.indexOf(q) < 0) classes.push("hidden");
        return (
          '<button type="button" class="' +
          classes.join(" ") +
          '" data-q="' +
          q +
          '">' +
          q +
          "</button>"
        );
      })
      .join("");
    el.paletteNums.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", () => setCurrent(Number(btn.getAttribute("data-q")), true));
    });
  }

  function updatePalette() {
    renderPalette();
  }

  function reviewNavList() {
    if (state.attemptReview && state.mistakesOnly && state.reviewMistakeQs.length) {
      return state.reviewMistakeQs.slice();
    }
    return state.questions.slice();
  }

  function updateCurrentHighlight() {
    if (!el.questionScroll) return;
    el.questionScroll.querySelectorAll("[data-q]").forEach((node) => {
      const q = Number(node.getAttribute("data-q"));
      const qTo = Number(node.getAttribute("data-q-to") || 0);
      node.classList.toggle("is-current", q === state.currentQ || qTo === state.currentQ);
    });
  }

  function setCurrent(q, scroll) {
    if (!state.questions.includes(q)) return;
    state.currentQ = q;
    const sid = sectionIdForQuestion(q);
    if (sid !== state.visibleSection) {
      state.visibleSection = sid;
      renderQuestions();
      renderTabs();
      if (state.attemptReview) {
        state.audioSection = sid;
        if (el.audio) {
          el.audio.src = audioUrl(sid);
          el.audio.load();
        }
        if (state.showTranscript) renderTranscript(sid);
        setAudioPhase("Review — you may replay and seek");
        updateAudioChrome();
      }
    } else {
      updateCurrentHighlight();
    }
    updatePalette();
    if (scroll && el.questionScroll) {
      const target =
        el.questionScroll.querySelector('#ans-' + q) ||
        el.questionScroll.querySelector('[data-q="' + q + '"]');
      if (target && target.scrollIntoView) target.scrollIntoView({ block: "center", behavior: "smooth" });
    }
  }

  function unansweredCount() {
    return state.questions.filter((q) => !isAnswered(q)).length;
  }
  function flaggedCount() {
    return state.questions.filter((q) => state.flags[q]).length;
  }

  function toggleFlag() {
    if (state.attemptReview) return;
    state.flags[state.currentQ] = !state.flags[state.currentQ];
    updatePalette();
    persist();
  }

  function renderReviewScreen() {
    if (!el.reviewList) return;
    el.reviewList.innerHTML = state.questions
      .map((q) => {
        const ans = isAnswered(q) ? escapeHtml(state.answers[q]) : "<em>Not answered</em>";
        const flag = state.flags[q] ? " · flagged" : "";
        return (
          '<button type="button" class="review-row" data-q="' +
          q +
          '"><strong>' +
          q +
          "</strong> " +
          ans +
          flag +
          "</button>"
        );
      })
      .join("");
    el.reviewList.querySelectorAll("button").forEach((btn) => {
      btn.addEventListener("click", () => {
        leaveReview();
        setCurrent(Number(btn.getAttribute("data-q")), true);
      });
    });
  }

  function enterReview() {
    state.reviewing = true;
    if (el.reviewScreen) el.reviewScreen.classList.remove("hidden");
    const main = document.querySelector(".listening-main");
    if (main) main.classList.add("hidden");
    renderReviewScreen();
  }

  function leaveReview() {
    state.reviewing = false;
    if (el.reviewScreen) el.reviewScreen.classList.add("hidden");
    const main = document.querySelector(".listening-main");
    if (main) main.classList.remove("hidden");
  }

  function toggleReview() {
    if (state.reviewing) leaveReview();
    else enterReview();
  }

  function setMistakesFilter(on) {
    state.mistakesOnly = !!on;
    if (el.btnReview) el.btnReview.textContent = on ? "查看整卷" : "查看错题";
    const nav = reviewNavList();
    if (nav.length && nav.indexOf(state.currentQ) < 0) setCurrent(nav[0], true);
    else {
      renderQuestions();
      updatePalette();
    }
  }

  function audioUrl(sectionId) {
    return "/api/listening/audio/" + sectionId;
  }

  function updateAudioChrome() {
    const audio = el.audio;
    const dur = audio && isFinite(audio.duration) ? audio.duration : 0;
    const cur = audio ? audio.currentTime || 0 : 0;
    if (el.audioTime) el.audioTime.textContent = formatTime(cur) + " / " + formatTime(dur);
    if (el.audioFill) el.audioFill.style.width = (dur ? (cur / dur) * 100 : 0) + "%";
    if (el.audioLabel) {
      el.audioLabel.textContent = state.audioSection ? "Section " + state.audioSection : "Audio";
    }
  }

  function setAudioPhase(text) {
    if (el.audioPhase) el.audioPhase.textContent = text;
  }

  function playlistForMode(mode) {
    return sectionsInMode(mode);
  }

  function attachAudioHandlers() {
    const audio = el.audio;
    if (!audio || audio._bound) return;
    audio._bound = true;
    audio.addEventListener("timeupdate", () => {
      if (!state.attemptReview && audio.currentTime + 0.35 < state.lastLegalTime) {
        try {
          audio.currentTime = state.lastLegalTime;
        } catch (err) {
          /* ignore */
        }
      } else {
        state.lastLegalTime = audio.currentTime;
      }
      updateAudioChrome();
      persist();
    });
    audio.addEventListener("ended", onAudioEnded);
    audio.addEventListener("play", () => {
      setAudioPhase(state.attemptReview ? "Review playback" : "Playing");
      if (el.btnUnlockAudio) el.btnUnlockAudio.classList.add("hidden");
    });
    audio.addEventListener("pause", () => {
      if (state.attemptReview) setAudioPhase("Paused");
    });
    audio.addEventListener("loadedmetadata", updateAudioChrome);
    if (el.volume) {
      audio.volume = Number(el.volume.value || 80) / 100;
      el.volume.addEventListener("input", () => {
        audio.volume = Number(el.volume.value || 0) / 100;
      });
    }
    if (el.audioProgress) {
      el.audioProgress.addEventListener("click", (evt) => {
        if (!state.attemptReview || !isFinite(audio.duration) || !audio.duration) return;
        const rect = el.audioProgress.getBoundingClientRect();
        const ratio = Math.max(0, Math.min(1, (evt.clientX - rect.left) / rect.width));
        audio.currentTime = ratio * audio.duration;
        updateAudioChrome();
      });
    }
  }

  async function playSection(sectionId, startAt) {
    const audio = el.audio;
    if (!audio) return;
    state.audioSection = sectionId;
    state.audioEnded = false;
    state.lastLegalTime = startAt || 0;
    setActivePart(sectionId);
    audio.src = audioUrl(sectionId);
    audio.load();
    if (startAt) {
      const onMeta = () => {
        try {
          audio.currentTime = startAt;
          state.lastLegalTime = startAt;
        } catch (err) {
          /* ignore */
        }
        audio.removeEventListener("loadedmetadata", onMeta);
      };
      audio.addEventListener("loadedmetadata", onMeta);
    }
    updateAudioChrome();
    setAudioPhase("Starting…");
    try {
      await audio.play();
    } catch (err) {
      setAudioPhase("Click to start the audio");
      if (el.btnUnlockAudio) {
        el.btnUnlockAudio.classList.remove("hidden");
        el.btnUnlockAudio.onclick = () => {
          audio.play().catch((e) => console.warn(e));
        };
      }
    }
  }

  function onAudioEnded() {
    if (state.attemptReview) {
      setAudioPhase("Ended");
      return;
    }
    const list = state.playlist;
    const idx = list.indexOf(state.audioSection);
    if (idx >= 0 && idx < list.length - 1) {
      playSection(list[idx + 1], 0);
      return;
    }
    state.audioEnded = true;
    if (state.mode === "full") {
      setAudioPhase("Audio finished · 2 minutes to check your answers");
      showBanner("The recording has finished. You now have time to check all your answers. The test will be submitted when the time is up.", "info");
    } else {
      setAudioPhase("Audio finished · check your answers");
      showBanner("The recording has finished. Check your answers. The test will be submitted when the time is up.", "info");
    }
    persist();
  }

  function stopTick() {
    if (state.tickId) {
      clearInterval(state.tickId);
      state.tickId = null;
    }
  }

  function tick() {
    if (!state.running || state.submitted || state.paused) return;
    state.remaining = Math.max(0, state.remaining - 1);
    creditPartTime();
    renderTimer();
    if (state.remaining === 300 && !state.warned5) {
      state.warned5 = true;
      showBanner("5 minutes remaining.", "warn");
    }
    if (state.remaining === 60 && !state.warned1) {
      state.warned1 = true;
      showBanner("1 minute remaining.", "warn");
    }
    persist();
    if (state.remaining <= 0) {
      showBanner("Time is up. Submitting now…", "warn");
      submitAnswers(true);
    }
  }

  function startTick() {
    stopTick();
    renderTimer();
    state.tickId = setInterval(tick, 1000);
    window.onbeforeunload = function () {
      if (state.running && !state.submitted) return "The test is in progress. Are you sure you want to leave?";
    };
    if (state.remaining <= 0) {
      showBanner("Time is up. Submitting now…", "warn");
      submitAnswers(true);
    }
  }

  function togglePause() {
    if (!state.allowPause || state.attemptReview || !state.running) return;
    if (!state.paused) {
      state.paused = true;
      state.pauseStartedAt = Date.now();
      creditPartTime();
      if (el.audio && !el.audio.paused) el.audio.pause();
      if (el.btnPause) el.btnPause.textContent = "Resume";
      setAudioPhase("Paused");
    } else {
      if (state.pauseStartedAt) {
        state.pausedTotal += Math.floor((Date.now() - state.pauseStartedAt) / 1000);
        state.pauseStartedAt = null;
      }
      state.paused = false;
      state.partTickAt = Date.now();
      if (el.audio && !state.audioEnded) el.audio.play().catch(() => {});
      if (el.btnPause) el.btnPause.textContent = "Pause";
      setAudioPhase(state.audioEnded ? "Audio finished" : "Playing");
    }
    persist();
  }

  function enterExamChrome() {
    if (el.setup) el.setup.classList.add("hidden");
    if (el.done) el.done.classList.add("hidden");
    if (el.exam) el.exam.classList.remove("hidden");
    if (el.siteFooter) el.siteFooter.classList.add("hidden");
    document.body.classList.add("exam-on");
  }

  function leaveExamChrome() {
    if (el.exam) el.exam.classList.add("hidden");
    if (el.siteFooter) el.siteFooter.classList.remove("hidden");
    document.body.classList.remove("exam-on");
    if (el.audio) {
      try {
        el.audio.pause();
        el.audio.removeAttribute("src");
      } catch (err) {
        /* ignore */
      }
    }
  }

  function beginFromState(opts) {
    opts = opts || {};
    enterExamChrome();
    if (el.modeLabel) el.modeLabel.textContent = state.mode === "full" ? "Full test" : "Section " + state.mode.replace("section", "");
    if (el.btnPause) {
      if (state.allowPause && !state.attemptReview) el.btnPause.classList.remove("hidden");
      else el.btnPause.classList.add("hidden");
    }
    state.visibleSection = sectionIdForQuestion(state.currentQ);
    renderTabs();
    renderQuestions();
    renderPalette();
    attachAudioHandlers();
    if (el.audioProgress) {
      el.audioProgress.classList.toggle("is-seekable", !!state.attemptReview);
    }
    if (state.attemptReview) {
      setAudioPhase("Review — you may replay and seek");
      return;
    }
    startTick();
    state.playlist = playlistForMode(state.mode);
    if (state.audioEnded) {
      setAudioPhase(state.mode === "full" ? "Audio finished · check your answers" : "Audio finished");
      return;
    }
    const startSection = state.audioSection || state.playlist[0];
    const startAt = opts.audioTime || 0;
    playSection(startSection, startAt);
  }

  async function startSession(name, mode) {
    const code = ((el.inviteCode && el.inviteCode.value) || "").trim();
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
        module: "listening",
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
    if (paper && paper.sections) return true;
    const res = await fetch("/api/listening/paper", { credentials: "same-origin" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) return false;
    paper = data;
    return !!(paper && paper.sections);
  }

  function restoreSaved(saved) {
    state.mode = saved.mode || "full";
    state.setId = saved.setId || "set-a";
    state.name = saved.name || "";
    state.duration = saved.duration || durationForMode(state.mode);
    state.pausedTotal = saved.pausedTotal || 0;
    state.allowPause = !!saved.allowPause;
    state.answers = saved.answers || {};
    state.flags = saved.flags || {};
    state.partTimes = Object.assign(emptyPartTimes(), saved.partTimes || {});
    state.activePart = saved.activePart || sectionIdForQuestion(saved.currentQ || 1);
    state.warned5 = !!saved.warned5;
    state.warned1 = !!saved.warned1;
    state.questions = questionList(state.mode);
    state.currentQ = state.questions.includes(saved.currentQ) ? saved.currentQ : state.questions[0];
    state.visibleSection = saved.visibleSection || sectionIdForQuestion(state.currentQ);
    state.audioSection = saved.audioSection || 0;
    state.audioEnded = !!saved.audioEnded;
    state.paused = !!saved.paused;
    if (state.paused) {
      state.remaining = saved.remaining || 0;
      state.partTickAt = null;
    } else {
      const elapsed = Math.floor((Date.now() - (saved.savedAt || Date.now())) / 1000);
      state.remaining = Math.max(0, (saved.remaining || 0) - elapsed);
      if (state.activePart && elapsed > 0) {
        state.partTimes[state.activePart] = (state.partTimes[state.activePart] || 0) + elapsed;
      }
      state.partTickAt = Date.now();
      if (!state.audioEnded && saved.audioTime != null) {
        saved._resumeAudioTime = (saved.audioTime || 0) + (state.paused ? 0 : elapsed);
      }
    }
    if (el.candidateName && state.name) el.candidateName.value = state.name;
    return saved._resumeAudioTime || 0;
  }

  async function startExam(fromSaved) {
    let resumeAudio = 0;
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
        resumeAudio = restoreSaved(saved);
        fromSaved = true;
      } else {
        state.name = name;
        state.mode = mode;
        state.setId = "set-a";
        state.duration = durationForMode(mode);
        state.remaining = state.duration;
        state.pausedTotal = 0;
        state.pauseStartedAt = null;
        state.paused = false;
        state.answers = {};
        state.flags = {};
        state.partTimes = emptyPartTimes();
        state.activePart = 0;
        state.partTickAt = null;
        state.warned5 = false;
        state.warned1 = false;
        state.allowPause = !!(el.teacherPause && el.teacherPause.checked);
        state.questions = questionList(state.mode);
        state.currentQ = state.questions[0];
        state.visibleSection = sectionIdForQuestion(state.currentQ);
        state.audioSection = 0;
        state.audioEnded = false;
      }
    }
    if (!paper || !paper.sections) {
      showSetupError("The listening paper could not be loaded.");
      return;
    }
    state.running = true;
    state.submitted = false;
    state.reviewing = false;
    beginFromState({ audioTime: resumeAudio });
    persist();
  }

  async function resumeIfNeeded() {
    const saved = loadPersist();
    if (!saved || !saved.running) return;
    if (el.resumeBanner) {
      el.resumeBanner.textContent = "A test is already in progress on this device. Starting will resume it for the same name.";
      el.resumeBanner.classList.remove("hidden");
    }
    if (saved.name && el.candidateName) el.candidateName.value = saved.name;
  }

  function renderDoneResult(data, payload, auto) {
    if (el.doneMsg) {
      el.doneMsg.textContent = auto
        ? "Time was up, so the test was submitted automatically."
        : "Your answers have been submitted.";
    }
    if (el.doneResult && data && data.score != null) {
      el.doneResult.classList.remove("hidden");
      if (el.doneScore) el.doneScore.textContent = data.score + " / " + data.total;
      if (el.doneBand) {
        if (data.band_estimate == null) {
          el.doneBand.textContent = "Section-only mode: raw score only (no overall band). This band table is a reference.";
        } else {
          const band = Number(data.band_estimate);
          const label = Number.isInteger(band) ? String(band) : String(band);
          el.doneBand.textContent = "Reference band " + label + " (official conversion varies by paper)";
        }
      }
      if (el.doneParts) {
        const times = data.part_times || payload.part_times || {};
        const rows = sectionsInMode(data.mode || payload.mode || "full")
          .map((id) => "<tr><th>Section " + id + "</th><td>" + formatDuration(times[id] || times[String(id)] || 0) + "</td></tr>")
          .join("");
        el.doneParts.innerHTML =
          rows +
          '<tr class="total"><th>Time used</th><td>' +
          formatDuration(data.time_used_seconds) +
          "</td></tr>";
      }
    }
    if (data && data.id) {
      if (el.btnReviewPaper) {
        el.btnReviewPaper.href = "/me/submission/" + encodeURIComponent(data.id);
        el.btnReviewPaper.classList.remove("hidden");
      }
      if (el.btnReviewMistakes) {
        el.btnReviewMistakes.href = "/me/submission/" + encodeURIComponent(data.id) + "/review";
        el.btnReviewMistakes.classList.remove("hidden");
      }
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
    creditPartTime();
    if (el.audio) {
      try {
        el.audio.pause();
      } catch (err) {
        /* ignore */
      }
    }

    const flags = state.questions.filter((q) => state.flags[q]);
    const answers = {};
    state.questions.forEach((q) => {
      answers[String(q)] = state.answers[q] != null ? String(state.answers[q]) : "";
    });
    const payload = {
      candidate_name: state.name || ((el.candidateName && el.candidateName.value) || "").trim(),
      mode: state.mode,
      prompt_set_id: state.setId || "set-a",
      answers: answers,
      flags: flags,
      duration_seconds: state.duration,
      time_remaining_seconds: Math.max(0, state.remaining),
      time_used_seconds: Math.max(0, state.duration - state.remaining),
      paused_total_seconds: state.pausedTotal,
      part_times: {
        "1": state.partTimes[1] || 0,
        "2": state.partTimes[2] || 0,
        "3": state.partTimes[3] || 0,
        "4": state.partTimes[4] || 0,
      },
      auto_submitted: !!auto,
    };

    el.btnSubmit.disabled = true;
    try {
      const res = await fetch("/api/listening/submit", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error((data && data.error) || "submit failed");
      clearPersist();
      leaveExamChrome();
      el.done.classList.remove("hidden");
      renderDoneResult(data, payload, auto);
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
    if (el.done) el.done.classList.add("hidden");
    if (el.doneResult) el.doneResult.classList.add("hidden");
    if (el.setup) el.setup.classList.remove("hidden");
  }

  function applyReviewChrome(data) {
    if (el.setup) el.setup.classList.add("hidden");
    if (el.reviewModeBanner) el.reviewModeBanner.classList.remove("hidden");
    if (el.reviewModeMeta) {
      const bits = [];
      if (data.score_label) bits.push(data.score_label);
      if (data.band_label) bits.push("参考分数 " + data.band_label);
      if (data.duration) bits.push("用时 " + data.duration);
      if (data.mistake_count != null) bits.push(data.mistake_count + " mistakes");
      el.reviewModeMeta.textContent = bits.join(" · ");
    }
    if (el.modeLabel) el.modeLabel.textContent = "回顾模式";
    if (el.btnPause) el.btnPause.classList.add("hidden");
    if (el.btnSubmit) el.btnSubmit.classList.add("hidden");
    if (el.btnQuit) el.btnQuit.classList.add("hidden");
    if (el.btnFlag) el.btnFlag.classList.add("hidden");
    if (el.btnReview) {
      el.btnReview.classList.remove("hidden");
      el.btnReview.textContent = "查看错题";
    }
    if (el.btnToggleTranscript) el.btnToggleTranscript.classList.remove("hidden");
    if (el.audioProgress) el.audioProgress.classList.add("is-seekable");
  }

  function renderTranscript(sectionId) {
    if (!el.transcriptPanel) return;
    const text = state.transcripts[String(sectionId)] || state.transcripts[sectionId] || "";
    el.transcriptPanel.textContent = text || "No transcript for this section.";
  }

  async function enterAttemptReview() {
    const cfg = window.REVIEW_CONFIG || {};
    const sid = cfg.sid;
    if (!sid) return;
    state.attemptReview = true;
    state.running = false;
    state.submitted = true;
    state.paused = false;
    state.allowPause = false;
    window.onbeforeunload = null;
    try {
      const res = await fetch("/api/me/submission/" + encodeURIComponent(sid), {
        credentials: "same-origin",
      });
      if (res.status === 401 || res.status === 403) {
        window.location.href = "/me?next=/me/submission/" + encodeURIComponent(sid);
        return;
      }
      if (res.status === 404) {
        document.body.innerHTML = "<p style='padding:24px'>未找到该答卷</p>";
        return;
      }
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error((data && data.error) || "review load failed");
      paper = data.paper;
      state.mode = data.mode || "full";
      state.setId = (data.paper && data.paper.id) || "set-a";
      state.questions = questionList(state.mode);
      state.answers = {};
      state.reviewByQ = {};
      Object.keys(data.answers || {}).forEach((k) => {
        const q = Number(k);
        state.answers[q] = data.answers[k] == null ? "" : String(data.answers[k]);
      });
      (data.questions || []).forEach((row) => {
        state.reviewByQ[row.q] = row;
        if (row.student != null && state.answers[row.q] == null) state.answers[row.q] = row.student;
      });
      state.reviewMistakeQs = (data.questions || [])
        .filter((row) => !row.ok || row.student_blank)
        .map((row) => row.q);
      state.transcripts = data.transcripts || {};
      state.flags = {};
      state.duration = data.time_used_seconds || 0;
      state.remaining = 0;
      state.currentQ = state.questions[0];
      applyReviewChrome(data);
      enterExamChrome();
      attachAudioHandlers();
      state.playlist = playlistForMode(state.mode);
      state.audioSection = state.playlist[0];
      if (el.audio) {
        el.audio.src = audioUrl(state.audioSection);
        el.audio.load();
        el.audio.controls = false;
      }
      setAudioPhase("Review — you may replay and seek");
      renderTabs();
      renderQuestions();
      renderPalette();
      const startQ =
        cfg.mistakesOnly && state.reviewMistakeQs.length ? state.reviewMistakeQs[0] : state.questions[0];
      setCurrent(startQ, true);
      if (cfg.mistakesOnly) {
        if (state.reviewMistakeQs.length) setMistakesFilter(true);
        else showBanner("全部答对，没有错题。正在查看整卷。", "info");
      }
    } catch (err) {
      console.error(err);
      showSetupError("无法加载这套已交答卷，请返回我的记录后重试。");
      if (el.setup) el.setup.classList.remove("hidden");
    }
  }

  document.querySelectorAll("#modePills label").forEach((label) => {
    label.addEventListener("click", () => {
      document.querySelectorAll("#modePills label").forEach((item) => item.classList.remove("active"));
      label.classList.add("active");
    });
  });

  if (el.btnStart) el.btnStart.addEventListener("click", () => startExam(false));
  if (el.btnPause) el.btnPause.addEventListener("click", togglePause);
  if (el.btnFlag) el.btnFlag.addEventListener("click", toggleFlag);
  if (el.btnReview) {
    el.btnReview.addEventListener("click", () => {
      if (state.attemptReview) {
        setMistakesFilter(!state.mistakesOnly);
        return;
      }
      toggleReview();
    });
  }
  if (el.btnBackToTest) el.btnBackToTest.addEventListener("click", leaveReview);
  if (el.btnPrev) {
    el.btnPrev.addEventListener("click", () => {
      const nav = reviewNavList();
      const idx = nav.indexOf(state.currentQ);
      if (idx > 0) {
        leaveReview();
        setCurrent(nav[idx - 1], true);
      }
    });
  }
  if (el.btnNext) {
    el.btnNext.addEventListener("click", () => {
      const nav = reviewNavList();
      const idx = nav.indexOf(state.currentQ);
      if (idx >= 0 && idx < nav.length - 1) {
        leaveReview();
        setCurrent(nav[idx + 1], true);
      }
    });
  }
  if (el.btnSubmit) {
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
  }
  if (el.btnQuit) el.btnQuit.addEventListener("click", resetToSetup);
  if (el.btnAgain) el.btnAgain.addEventListener("click", resetToSetup);
  if (el.btnToggleTranscript) {
    el.btnToggleTranscript.addEventListener("click", () => {
      if (!state.attemptReview) return;
      state.showTranscript = !state.showTranscript;
      if (el.transcriptPanel) el.transcriptPanel.classList.toggle("hidden", !state.showTranscript);
      if (state.showTranscript) renderTranscript(state.visibleSection || state.audioSection || 1);
    });
  }

  if (window.REVIEW_CONFIG && window.REVIEW_CONFIG.sid) {
    enterAttemptReview();
  } else {
    resumeIfNeeded();
  }
})();
