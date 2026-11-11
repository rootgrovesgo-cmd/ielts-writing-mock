(() => {
  const PART1_SECONDS = 5 * 60;
  const PREP_SECONDS = 60;
  const SPEAK_SECONDS = 2 * 60;
  const PART3_SECONDS = 5 * 60;
  const PART1_PER_SET = 4;

  const el = {
    setupPanel: document.getElementById("setupPanel"),
    pickPanel: document.getElementById("pickPanel"),
    practicePanel: document.getElementById("practicePanel"),
    donePanel: document.getElementById("donePanel"),
    candidateName: document.getElementById("candidateName"),
    inviteCode: document.getElementById("inviteCode"),
    topicSelect: document.getElementById("topicSelect"),
    topicSelectLabel: document.getElementById("topicSelectLabel"),
    pickTitle: document.getElementById("pickTitle"),
    pickLead: document.getElementById("pickLead"),
    btnBegin: document.getElementById("btnBegin"),
    setupError: document.getElementById("setupError"),
    btnStart: document.getElementById("btnStart"),
    modeLabel: document.getElementById("modeLabel"),
    timerWrap: document.getElementById("timerWrap"),
    timerLabel: document.getElementById("timerLabel"),
    timer: document.getElementById("timer"),
    statusBanner: document.getElementById("statusBanner"),
    stageLabel: document.getElementById("stageLabel"),
    stageHint: document.getElementById("stageHint"),
    questionBox: document.getElementById("questionBox"),
    btnQuit: document.getElementById("btnQuit"),
    btnSkipPart: document.getElementById("btnSkipPart"),
    btnNext: document.getElementById("btnNext"),
    btnAgain: document.getElementById("btnAgain"),
    doneBanner: document.getElementById("doneBanner"),
    btnRecord: document.getElementById("btnRecord"),
    btnDownloadRec: document.getElementById("btnDownloadRec"),
    recStatus: document.getElementById("recStatus"),
    tab1: document.getElementById("tab1"),
    tab2: document.getElementById("tab2"),
    tab3: document.getElementById("tab3"),
  };

  let bank = null;
  let tickId = null;
  let remaining = 0;
  let timerKind = "";
  const rec = { stream: null, recorder: null, chunks: [], blob: null, recording: false };

  function show(node) { node.classList.remove("hidden"); }
  function hide(node) { node.classList.add("hidden"); }

  function selectedValue(name) {
    const input = document.querySelector(`input[name="${name}"]:checked`);
    return input ? input.value : "";
  }

  function wirePills(groupId, name) {
    const group = document.getElementById(groupId);
    group.addEventListener("change", () => {
      group.querySelectorAll("label").forEach((label) => {
        const input = label.querySelector("input");
        label.classList.toggle("active", !!(input && input.checked));
      });
    });
  }

  function showSetupError(msg) {
    el.setupError.textContent = msg;
    show(el.setupError);
  }
  function hideSetupError() { hide(el.setupError); }

  function showBanner(msg, kind) {
    el.statusBanner.textContent = msg;
    el.statusBanner.className = `banner ${kind || "info"}`;
    show(el.statusBanner);
  }
  function hideBanner() { hide(el.statusBanner); }

  function formatTime(sec) {
    const s = Math.max(0, Math.floor(sec));
    const m = Math.floor(s / 60);
    const r = s % 60;
    return `${String(m).padStart(2, "0")}:${String(r).padStart(2, "0")}`;
  }

  function renderTimer() {
    el.timer.textContent = formatTime(remaining);
    el.timer.classList.toggle("warn", remaining <= 60 && remaining > 15);
    el.timer.classList.toggle("danger", remaining <= 15);
  }

  function stopTimer() {
    if (tickId) {
      clearInterval(tickId);
      tickId = null;
    }
  }

  function startTimer(seconds, kind, onEnd) {
    stopTimer();
    timerKind = kind;
    remaining = seconds;
    show(el.timerWrap);
    renderTimer();
    tickId = setInterval(() => {
      remaining -= 1;
      renderTimer();
      if (remaining <= 0) {
        remaining = 0;
        renderTimer();
        stopTimer();
        if (onEnd) onEnd();
      }
    }, 1000);
  }

  function shuffle(list) {
    const copy = list.slice();
    for (let i = copy.length - 1; i > 0; i -= 1) {
      const j = Math.floor(Math.random() * (i + 1));
      [copy[i], copy[j]] = [copy[j], copy[i]];
    }
    return copy;
  }

  function takeQuestions(topic, count) {
    const qs = (topic.questions || []).slice(0, count);
    return qs.map((text) => ({
      topic: topic.topic,
      topic_zh: topic.topic_zh,
      text,
    }));
  }

  function allQuestions(topic) {
    return (topic.questions || []).map((text) => ({
      topic: topic.topic,
      topic_zh: topic.topic_zh,
      text,
    }));
  }

  function coreTopic(status) {
    const want = status === "work" ? "p1-work" : "p1-study";
    return (bank.part1 || []).find((t) => t.id === want) || (bank.part1 || [])[0];
  }

  function topicSets() {
    return (bank.part1 || []).filter((t) => t.category !== "core");
  }

  function buildPart1(status) {
    const intro = coreTopic(status);
    const extras = shuffle(topicSets()).slice(0, 2);
    const questions = [];
    let introQs = intro.questions || [];
    if (intro.id === "p1-study") {
      introQs = introQs.filter((q) => q !== "Do you work or are you a student?");
    }
    questions.push(...introQs.slice(0, PART1_PER_SET).map((text) => ({
      topic: intro.topic,
      topic_zh: intro.topic_zh,
      text,
    })));
    extras.forEach((set) => questions.push(...takeQuestions(set, PART1_PER_SET)));
    return { sets: [intro, ...extras], questions };
  }

  function findPart1Topic(id) {
    return (bank.part1 || []).find((t) => t.id === id) || null;
  }

  function findCard(id) {
    return (bank.part2 || []).find((c) => c.id === id) || null;
  }

  function randomCard() {
    const cards = bank.part2 || [];
    if (!cards.length) return null;
    return cards[Math.floor(Math.random() * cards.length)];
  }

  function isPart1Only() {
    return !!(session && session.mode === "part1");
  }

  function isPart3Only() {
    return !!(session && session.mode === "part3");
  }

  function buildSession() {
    const status = selectedValue("status") || "study";
    const mode = selectedValue("mode") || "full";

    if (mode === "part1") {
      const chosen = el.topicSelect.value;
      let part1;
      if (chosen && chosen !== "random") {
        const set = findPart1Topic(chosen);
        part1 = set ? { sets: [set], questions: allQuestions(set) } : buildPart1(status);
      } else {
        part1 = buildPart1(status);
      }
      return {
        mode,
        status,
        part1,
        card: null,
        part3: [],
        p1Index: 0,
        p3Index: 0,
        phase: "part1",
      };
    }

    if (mode === "part3") {
      let card = findCard(el.topicSelect.value);
      if (!card) card = randomCard();
      return {
        mode,
        status,
        part1: { sets: [], questions: [] },
        card,
        part3: (card && card.part3) || [],
        p1Index: 0,
        p3Index: 0,
        phase: "part3",
      };
    }

    const part1 = buildPart1(status);
    let card = null;
    if (mode === "topic") {
      card = findCard(el.topicSelect.value);
    }
    if (!card) card = randomCard();
    return {
      mode,
      status,
      part1,
      card,
      part3: (card && card.part3) || [],
      p1Index: 0,
      p3Index: 0,
      phase: "part1",
    };
  }

  let session = null;

  function setTabs(part) {
    const show1 = !isPart3Only();
    const show2 = !isPart1Only() && !isPart3Only();
    const show3 = !isPart1Only();
    el.tab1.classList.toggle("hidden", !show1);
    el.tab2.classList.toggle("hidden", !show2);
    el.tab3.classList.toggle("hidden", !show3);
    el.tab1.classList.toggle("active", part === 1 && show1);
    el.tab2.classList.toggle("active", part === 2 && show2);
    el.tab3.classList.toggle("active", part === 3 && show3);
  }

  function discussionLabel() {
    if (!session || !session.card) return "Discussion";
    const zh = session.card.title_zh || "";
    const en = session.card.title || "";
    if (zh && en) return `${zh} · ${en}`;
    return zh || en || "Discussion";
  }

  function renderPart1() {
    const q = session.part1.questions[session.p1Index];
    const total = session.part1.questions.length;
    setTabs(1);
    el.modeLabel.textContent = "Part 1";
    el.timerLabel.textContent = "Part 1 remaining";
    el.stageLabel.textContent = "Part 1 · Interview";
    el.stageHint.textContent = "Answer in a few sentences, as you would with an examiner.";
    el.questionBox.innerHTML = `
      <p class="question-kicker">${escapeHtml(q.topic)}${q.topic_zh ? " · " + escapeHtml(q.topic_zh) : ""}</p>
      <p class="question-text">${escapeHtml(q.text)}</p>
      <p class="progress-meta">Question ${session.p1Index + 1} of ${total}</p>
    `;
    const last = session.p1Index === total - 1;
    if (isPart1Only()) {
      el.btnNext.textContent = last ? "Finish practice" : "Next";
      show(el.btnSkipPart);
      el.btnSkipPart.textContent = "结束练习";
    } else {
      el.btnNext.textContent = last ? "Enter Part 2" : "Next";
      show(el.btnSkipPart);
      el.btnSkipPart.textContent = "进入 Part 2";
    }
    if (!tickId && remaining > 0) {
      startTimer(remaining, "part1", onPart1TimeUp);
    } else if (!tickId) {
      startTimer(PART1_SECONDS, "part1", onPart1TimeUp);
    }
  }

  function onPart1TimeUp() {
    if (isPart1Only()) {
      showBanner("Part 1 时间到。你可以结束练习，或先答完当前问题。", "warn");
    } else {
      showBanner("Part 1 时间到。你可以进入 Part 2，或先答完当前问题。", "warn");
    }
  }

  function renderPart2Prep() {
    const card = session.card;
    setTabs(2);
    session.phase = "part2-prep";
    el.modeLabel.textContent = "Part 2 · Preparation";
    el.timerLabel.textContent = "Preparation";
    el.stageLabel.textContent = "Part 2 · Long turn";
    el.stageHint.textContent = "You have 1 minute to prepare. You may write notes. The card stays visible when you speak.";
    el.questionBox.innerHTML = cueCardHtml(card, true);
    el.btnNext.textContent = "开始陈述";
    show(el.btnSkipPart);
    el.btnSkipPart.textContent = "跳过准备，直接陈述";
    hideBanner();
    startTimer(PREP_SECONDS, "prep", () => beginPart2Speak(true));
  }

  function beginPart2Speak(fromTimer) {
    const card = session.card;
    session.phase = "part2-speak";
    setTabs(2);
    el.modeLabel.textContent = "Part 2 · Speaking";
    el.timerLabel.textContent = "Speaking time";
    el.stageLabel.textContent = "Part 2 · Long turn";
    el.stageHint.textContent = "Speak for up to 2 minutes. The cue card remains visible.";
    const notes = document.getElementById("prepNotes");
    const kept = notes ? notes.value : "";
    el.questionBox.innerHTML = cueCardHtml(card, true, kept, true);
    el.btnNext.textContent = "Enter Part 3";
    show(el.btnSkipPart);
    el.btnSkipPart.textContent = "进入 Part 3";
    if (fromTimer) showBanner("准备时间结束，请开始陈述。", "info");
    else hideBanner();
    startTimer(SPEAK_SECONDS, "speak", () => {
      showBanner("Part 2 陈述时间到。请进入 Part 3。", "warn");
    });
  }

  function renderPart3() {
    const questions = session.part3;
    const q = questions[session.p3Index];
    setTabs(3);
    session.phase = "part3";
    el.modeLabel.textContent = "Part 3";
    el.timerLabel.textContent = "Part 3 remaining";
    el.stageLabel.textContent = "Part 3 · Discussion";
    el.stageHint.textContent = "Discuss the question. Give reasons and examples, not only personal stories.";
    el.questionBox.innerHTML = `
      <p class="question-kicker">${escapeHtml(discussionLabel())}</p>
      <p class="question-text">${escapeHtml(q)}</p>
      <p class="progress-meta">Question ${session.p3Index + 1} of ${questions.length}</p>
    `;
    el.btnNext.textContent = session.p3Index === questions.length - 1 ? "Finish practice" : "Next";
    show(el.btnSkipPart);
    el.btnSkipPart.textContent = "结束练习";
    if (timerKind !== "part3" || !tickId) {
      startTimer(PART3_SECONDS, "part3", () => {
        showBanner("Part 3 时间到。你可以结束练习，或先答完当前问题。", "warn");
      });
    }
  }

  function cueCardHtml(card, withNotes, notesValue, readOnly) {
    const bullets = (card.bullets || []).map((b) => `<li>${escapeHtml(b)}</li>`).join("");
    const notes = withNotes
      ? `<label class="notes-label" for="prepNotes">Notes</label>
         <textarea id="prepNotes" class="notes-box" ${readOnly ? "readonly" : ""} placeholder="Write brief notes here…">${escapeHtml(notesValue || "")}</textarea>`
      : "";
    return `
      <div class="cue-card">
        <h3>${escapeHtml(card.title)}</h3>
        <p class="you-should">You should say:</p>
        <ul>${bullets}</ul>
      </div>
      ${notes}
    `;
  }

  function escapeHtml(value) {
    return String(value || "")
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;");
  }

  function goPart2() {
    hideBanner();
    renderPart2Prep();
  }

  function goPart3() {
    hideBanner();
    session.p3Index = 0;
    renderPart3();
  }

  function finishPractice() {
    stopTimer();
    hide(el.timerWrap);
    hide(el.practicePanel);
    if (el.doneBanner) {
      if (isPart1Only()) {
        el.doneBanner.textContent = "You have finished this Part 1 practice session. No score is given for speaking practice.";
      } else if (isPart3Only()) {
        el.doneBanner.textContent = "You have finished this Part 3 practice session. No score is given for speaking practice.";
      } else {
        el.doneBanner.textContent = "You have finished this Part 1–3 practice session. No score is given for speaking practice.";
      }
    }
    show(el.donePanel);
    el.modeLabel.textContent = "Finished";
    hideBanner();
  }

  function onNext() {
    if (!session) return;
    if (session.phase === "part1") {
      if (session.p1Index < session.part1.questions.length - 1) {
        session.p1Index += 1;
        renderPart1();
      } else if (isPart1Only()) {
        finishPractice();
      } else {
        goPart2();
      }
      return;
    }
    if (session.phase === "part2-prep") {
      beginPart2Speak(false);
      return;
    }
    if (session.phase === "part2-speak") {
      goPart3();
      return;
    }
    if (session.phase === "part3") {
      if (session.p3Index < session.part3.length - 1) {
        session.p3Index += 1;
        renderPart3();
      } else {
        finishPractice();
      }
    }
  }

  function onSkipPart() {
    if (!session) return;
    if (session.phase === "part1") {
      if (isPart1Only()) finishPractice();
      else goPart2();
    } else if (session.phase === "part2-prep") beginPart2Speak(false);
    else if (session.phase === "part2-speak") goPart3();
    else if (session.phase === "part3") finishPractice();
  }

  function optionLabel(zh, en) {
    if (zh && en) return `${zh} — ${en}`;
    return zh || en || "";
  }

  function fillPart2Select(includeRandom) {
    const cards = bank.part2 || [];
    const randomOpt = includeRandom
      ? `<option value="random">随机抽取话题</option>`
      : "";
    el.topicSelect.innerHTML = randomOpt + cards
      .map((c) => `<option value="${escapeHtml(c.id)}">${escapeHtml(optionLabel(c.title_zh, c.title))}</option>`)
      .join("");
  }

  function fillPart1Select() {
    const topics = bank.part1 || [];
    const groups = [
      { key: "core", label: "常考开场" },
      { key: "new", label: "本季新题" },
      { key: "retained", label: "保留题目" },
    ];
    const used = new Set(groups.map((g) => g.key));
    const other = topics.filter((t) => !used.has(t.category));
    if (other.length) groups.push({ key: "__other", label: "其他" });

    const parts = [`<option value="random">随机抽取 · 开场问答 + 两个话题</option>`];
    groups.forEach((group) => {
      const items = group.key === "__other"
        ? other
        : topics.filter((t) => t.category === group.key);
      if (!items.length) return;
      const opts = items
        .map((t) => `<option value="${escapeHtml(t.id)}">${escapeHtml(optionLabel(t.topic_zh, t.topic))}</option>`)
        .join("");
      parts.push(`<optgroup label="${escapeHtml(group.label)}">${opts}</optgroup>`);
    });
    el.topicSelect.innerHTML = parts.join("");
  }

  function configurePickPanel(mode) {
    if (mode === "part1") {
      el.pickTitle.textContent = "选择 Part 1 话题";
      el.pickLead.textContent = "可随机抽取一组 Part 1 题目，或指定一个话题集练习。练习结束后不会进入 Part 2 或 Part 3。";
      el.topicSelectLabel.textContent = "Part 1 topic";
      el.btnBegin.textContent = "开始 Part 1";
      fillPart1Select();
      return;
    }
    if (mode === "part3") {
      el.pickTitle.textContent = "选择讨论话题";
      el.pickLead.textContent = "Part 3 讨论题与 Part 2 话题配套。选定或随机抽取一个话题后，直接练习对应的讨论题，无需先做 Part 2。";
      el.topicSelectLabel.textContent = "Part 2 topic · matching Part 3 set";
      el.btnBegin.textContent = "开始 Part 3";
      fillPart2Select(true);
      return;
    }
    el.pickTitle.textContent = "选择 Part 2 话题";
    el.pickLead.textContent = "选定话题后，会配上相应的 Part 3 讨论题，并从本季 Part 1 题库抽题。";
    el.topicSelectLabel.textContent = "Part 2 topic";
    el.btnBegin.textContent = "开始 Part 1";
    fillPart2Select(false);
  }

  async function startSession() {
    const name = (el.candidateName.value || "").trim();
    const code = (el.inviteCode.value || "").trim();
    if (!name) {
      showSetupError("Please enter your name before starting.");
      el.candidateName.focus();
      return null;
    }
    if (!code) {
      showSetupError("Please enter your invitation code before starting.");
      el.inviteCode.focus();
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
        module: "speaking",
        mode: selectedValue("mode") || "full",
      }),
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.ok) {
      showSetupError(data.error || "邀请码无效或已失效");
      return null;
    }
    return data;
  }

  async function loadBank() {
    const res = await fetch("/api/speaking/bank", { credentials: "same-origin" });
    const data = await res.json().catch(() => ({}));
    if (!res.ok) {
      showSetupError((data && data.error) || "题库加载失败，请重试。");
      return false;
    }
    if (!(data.part1 && data.part1.length) || !(data.part2 && data.part2.length)) {
      showSetupError("题库不完整，请稍后重试。");
      return false;
    }
    bank = data;
    fillPart2Select(false);
    return true;
  }

  async function startPractice() {
    el.btnStart.disabled = true;
    try {
      const started = await startSession();
      if (!started) return;
      const loaded = await loadBank();
      if (!loaded) return;
    } catch (err) {
      console.error(err);
      showSetupError("无法开始练习，请检查网络后重试。");
      return;
    } finally {
      el.btnStart.disabled = false;
    }
    hide(el.setupPanel);
    hide(el.donePanel);
    hide(el.practicePanel);
    const mode = selectedValue("mode") || "full";
    if (mode === "topic" || mode === "part1" || mode === "part3") {
      configurePickPanel(mode);
      show(el.pickPanel);
      el.modeLabel.textContent = "Choose a topic";
      return;
    }
    beginSession();
  }

  function sessionIsReady(s) {
    if (!s) return false;
    if (s.mode === "part1") return !!(s.part1 && s.part1.questions.length);
    if (s.mode === "part3") return !!(s.card && (s.part3 || []).length);
    return !!(s.card && s.part1.questions.length && s.part3.length);
  }

  function beginSession() {
    session = buildSession();
    if (!sessionIsReady(session)) {
      const msg = session && session.mode === "part1"
        ? "未能生成 Part 1 练习，请重试。"
        : session && session.mode === "part3"
          ? "未能生成 Part 3 练习，请重试。"
          : "未能生成完整的 Part 1–3 练习，请重试。";
      showSetupError(msg);
      hide(el.pickPanel);
      show(el.setupPanel);
      session = null;
      return;
    }
    hide(el.setupPanel);
    hide(el.pickPanel);
    hide(el.donePanel);
    show(el.practicePanel);
    if (isPart3Only()) {
      session.phase = "part3";
      session.p3Index = 0;
      remaining = 0;
      timerKind = "";
      stopTimer();
      renderPart3();
      return;
    }
    session.phase = "part1";
    session.p1Index = 0;
    remaining = 0;
    timerKind = "";
    stopTimer();
    renderPart1();
  }

  function resetToSetup() {
    stopTimer();
    stopRecording(true);
    session = null;
    remaining = 0;
    timerKind = "";
    hide(el.timerWrap);
    hide(el.practicePanel);
    hide(el.pickPanel);
    hide(el.donePanel);
    hideBanner();
    show(el.setupPanel);
    el.modeLabel.textContent = "Ready";
    el.timer.textContent = "--:--";
    el.timer.classList.remove("warn", "danger");
    el.tab1.classList.remove("hidden");
    el.tab2.classList.remove("hidden");
    el.tab3.classList.remove("hidden");
    el.tab1.classList.add("active");
    el.tab2.classList.remove("active");
    el.tab3.classList.remove("active");
    if (el.doneBanner) {
      el.doneBanner.textContent = "You have finished this Part 1–3 practice session. No score is given for speaking practice.";
    }
  }

  async function startRecording() {
    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      el.recStatus.textContent = "当前浏览器不支持录音，可直接口头练习。";
      return;
    }
    try {
      rec.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      rec.chunks = [];
      rec.blob = null;
      rec.recorder = new MediaRecorder(rec.stream);
      rec.recorder.ondataavailable = (ev) => {
        if (ev.data && ev.data.size) rec.chunks.push(ev.data);
      };
      rec.recorder.onstop = () => {
        rec.blob = new Blob(rec.chunks, { type: rec.recorder.mimeType || "audio/webm" });
        show(el.btnDownloadRec);
        el.recStatus.textContent = "录音已停，可下载到本机。";
      };
      rec.recorder.start();
      rec.recording = true;
      el.btnRecord.textContent = "停止录音";
      el.btnRecord.classList.add("recording");
      el.recStatus.textContent = "正在录音…（仅保存在本机）";
    } catch (err) {
      el.recStatus.textContent = "无法使用麦克风，可继续口头练习。";
    }
  }

  function stopRecording(silent) {
    if (rec.recorder && rec.recording) {
      try { rec.recorder.stop(); } catch (err) { /* ignore */ }
    }
    rec.recording = false;
    el.btnRecord.textContent = "开始录音";
    el.btnRecord.classList.remove("recording");
    if (rec.stream) {
      rec.stream.getTracks().forEach((t) => t.stop());
      rec.stream = null;
    }
    if (!silent && !rec.blob) el.recStatus.textContent = "";
  }

  function downloadRecording() {
    if (!rec.blob) return;
    const url = URL.createObjectURL(rec.blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ielts-speaking-practice.webm";
    document.body.appendChild(a);
    a.click();
    a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  wirePills("statusPills", "status");
  wirePills("modePills", "mode");
  el.btnStart.addEventListener("click", startPractice);
  el.btnBegin.addEventListener("click", beginSession);
  el.btnNext.addEventListener("click", onNext);
  el.btnSkipPart.addEventListener("click", onSkipPart);
  el.btnQuit.addEventListener("click", resetToSetup);
  el.btnAgain.addEventListener("click", resetToSetup);
  el.btnRecord.addEventListener("click", () => {
    if (rec.recording) stopRecording(false);
    else startRecording();
  });
  el.btnDownloadRec.addEventListener("click", downloadRecording);
})();
