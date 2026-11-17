/* Interview Prep Vault — client-side app, no build step. */
(() => {
  "use strict";

  const TOPIC_LABELS = {
    "window-functions": "Window functions",
    "joins": "Joins",
    "aggregations": "Aggregations",
    "cte": "CTEs",
    "nulls": "NULL handling",
    "dedup": "Deduplication",
    "topn-ranking": "Top-N / ranking",
    "consecutive": "Consecutive events",
    "running-total": "Running totals",
    "pyspark": "PySpark/Spark",
    "delta-lake": "Delta Lake",
    "scd": "SCD",
    "streaming": "Streaming",
    "data-modeling": "Data modeling",
    "optimization": "Optimization",
    "etl-cdc": "ETL / CDC",
    "python": "Python",
    "dsa": "DSA",
    "power-bi": "Power BI",
    "cloud": "Cloud",
    "sql-basics": "SQL basics",
    "sql-coding": "SQL coding",
  };
  const topicLabel = (t) => TOPIC_LABELS[t] || t;

  const state = {
    questions: [],
    learnings: [],
    posts: [],
    tab: "questions",
    q: "",
    field: "",
    company: "",
    topic: "",
    exp: "",
    doneView: "all",
    visible: 50,
  };
  const DONE_KEY = "ipv-qdone-v1";
  let done = new Set(JSON.parse(localStorage.getItem(DONE_KEY) || "[]"));

  const $ = (id) => document.getElementById(id);
  const els = {
    tabQuestions: $("tabQuestions"), tabLearnings: $("tabLearnings"), tabSources: $("tabSources"),
    controls: $("controls"),
    stats: $("stats"), search: $("search"), searchCount: $("searchCount"),
    field: $("fieldFilter"), company: $("companyFilter"), topic: $("topicFilter"),
    exp: $("expFilter"), doneView: $("doneFilter"), reset: $("resetBtn"),
    questions: $("questions"), learnings: $("learnings"), sources: $("sources"), empty: $("empty"),
    qTpl: $("qTpl"), sTpl: $("sTpl"), lTpl: $("lTpl"), activeTopics: $("activeTopics"),
    loadMore: $("loadMore"),
    mockBtn: $("mockBtn"), mockDialog: $("mockDialog"), mockClose: $("mockClose"),
    mockField: $("mockField"), mockCompany: $("mockCompany"), mockExp: $("mockExp"),
    mockCount: $("mockCount"), mockGo: $("mockGo"), mockOut: $("mockOut"),
  };

  /* ---------- data ---------- */

  async function load() {
    const [qRes, lRes, pRes] = await Promise.all([
      fetch("data/questions.json"), fetch("data/learnings.json"), fetch("data/posts.json"),
    ]);
    if (!qRes.ok) throw new Error("questions.json failed: " + qRes.status);
    state.questions = await qRes.json();
    state.learnings = lRes.ok ? await lRes.json() : [];
    state.posts = pRes.ok ? await pRes.json() : [];
    const qc = {};
    for (const q of state.questions) {
      for (const pid of q.sources || []) qc[pid] = (qc[pid] || 0) + 1;
    }
    for (const p of state.posts) p.question_count = qc[p.id] || 0;
  }

  /* ---------- options with counts ---------- */

  function fillSelect(select, counts, labelAll, fmt) {
    select.innerHTML = "";
    const optAll = document.createElement("option");
    optAll.value = "";
    optAll.textContent = labelAll;
    select.appendChild(optAll);
    const sorted = [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]));
    for (const [v, c] of sorted) {
      const o = document.createElement("option");
      o.value = v;
      o.textContent = fmt ? fmt(v, c) : `${v} (${c})`;
      select.appendChild(o);
    }
  }

  const countBy = (items, fn) => {
    const m = new Map();
    for (const it of items) {
      const v = fn(it);
      if (v) m.set(v, (m.get(v) || 0) + 1);
    }
    return m;
  };

  function buildOptions() {
    fillSelect(els.field, countBy(state.questions, (q) => q.field), "All fields");
    fillSelect(els.company, countBy(state.questions, (q) => q.company), "All companies");
    const topicMap = new Map();
    for (const q of state.questions) {
      for (const t of q.topics || []) topicMap.set(t, (topicMap.get(t) || 0) + 1);
    }
    fillSelect(els.topic, topicMap, "All topics", (t, c) => `${topicLabel(t)} (${c})`);
    fillSelect(els.exp, countBy(state.questions, (q) => q.exp), "Any experience");
    fillSelect(els.mockField, countBy(state.questions, (q) => q.field), "Any field");
    fillSelect(els.mockCompany, countBy(state.questions, (q) => q.company), "Any company");
    fillSelect(els.mockExp, countBy(state.questions, (q) => q.exp), "Any");
    els.field.value = state.field;
    els.company.value = state.company;
    els.topic.value = state.topic;
    els.exp.value = state.exp;
  }

  function rebuildFieldForTab() {
    if (state.tab === "learnings") {
      fillSelect(els.field, countBy(state.learnings, (l) => l.field), "All fields");
    } else {
      fillSelect(els.field, countBy(state.questions, (q) => q.field), "All fields");
    }
    els.field.value = state.field;
    if (![...els.field.options].some((o) => o.value === state.field)) {
      state.field = "";
      els.field.value = "";
    }
  }

  /* ---------- rendering ---------- */

  function chip(text, click) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "topic-chip";
    btn.textContent = text;
    if (click) btn.addEventListener("click", click);
    return btn;
  }

  function renderStats(visible, totalLabel, total) {
    const fields = new Set(state[totalLabel].map((x) => x.field)).size;
    const companies = new Set(state[totalLabel].map((x) => x.company).filter((c) => c && c !== "General")).size;
    const doneCount = state.tab === "questions" ? state.questions.filter((q) => done.has(q.id)).length : 0;
    const pct = state.questions.length && state.tab === "questions" ? Math.round((doneCount / state.questions.length) * 100) : 0;
    els.stats.innerHTML = "";
    const tiles = state.tab === "questions"
      ? [
          [state.questions.length.toLocaleString(), "unique questions", ""],
          [fields, "fields", ""],
          [companies, "companies", ""],
          [doneCount + " / " + state.questions.length, "done (" + pct + "%)", "progress"],
          [visible.toLocaleString(), "showing", ""],
        ]
      : [
          [state[totalLabel].length.toLocaleString(), state.tab === "learnings" ? "learning posts" : "source posts", ""],
          [fields, "fields", ""],
          [companies, "companies", ""],
          [visible.toLocaleString(), "showing", ""],
        ];
    for (const [b, s, cls] of tiles) {
      const div = document.createElement("div");
      div.className = "stat" + (cls ? " " + cls : "");
      const bEl = document.createElement("b");
      bEl.textContent = b;
      const sEl = document.createElement("span");
      sEl.textContent = s;
      div.append(bEl, sEl);
      els.stats.appendChild(div);
    }
  }

  function renderActiveTopics() {
    els.activeTopics.innerHTML = "";
    const counts = new Map();
    for (const q of state.questions) for (const t of q.topics || []) counts.set(t, (counts.get(t) || 0) + 1);
    const top = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 18);
    for (const [t, c] of top) {
      els.activeTopics.appendChild(chip(`#${topicLabel(t)} ${c}`, () => { state.topic = t; els.topic.value = t; state.tab = "questions"; setTabUI("questions"); render(); }));
    }
  }

  function questionMatches(q) {
    if (state.field && q.field !== state.field) return false;
    if (state.company && q.company !== state.company) return false;
    if (state.topic && !(q.topics || []).includes(state.topic)) return false;
    if (state.exp && q.exp !== state.exp) return false;
    if (state.doneView === "done" && !done.has(q.id)) return false;
    if (state.doneView === "todo" && done.has(q.id)) return false;
    if (state.q) {
      const hay = (q.text + " " + q.field + " " + q.company + " " + (q.topics || []).map(topicLabel).join(" ")).toLowerCase();
      if (!hay.includes(state.q)) return false;
    }
    return true;
  }

  function learningMatches(l) {
    if (state.field && l.field !== state.field) return false;
    if (state.q) {
      const hay = (l.text + " " + l.author + " " + l.field + " " + l.company).toLowerCase();
      if (!hay.includes(state.q)) return false;
    }
    return true;
  }

  function sourceMatches(p) {
    if (state.q) {
      return (p.text + " " + p.author + " " + p.company + " " + p.field).toLowerCase().includes(state.q);
    }
    return true;
  }

  function renderQuestion(q) {
    const node = els.qTpl.content.cloneNode(true);
    const card = node.querySelector(".card");

    const fieldB = node.querySelector("[data-field]");
    fieldB.textContent = q.field;
    fieldB.title = "Filter by this field";
    fieldB.style.cursor = "pointer";
    fieldB.addEventListener("click", () => { state.field = q.field; els.field.value = q.field; render(); });

    const compB = node.querySelector("[data-company]");
    if (q.company && q.company !== "General") {
      compB.textContent = q.company;
      compB.title = "Filter by this company";
      compB.style.cursor = "pointer";
      compB.addEventListener("click", () => { state.company = q.company; els.company.value = q.company; render(); });
    } else {
      compB.remove();
    }

    const expB = node.querySelector("[data-exp]");
    if (q.exp && q.exp !== "Not specified") {
      expB.textContent = q.exp;
    } else {
      expB.remove();
    }

    const doneBox = node.querySelector("[data-done]");
    doneBox.checked = done.has(q.id);
    doneBox.addEventListener("change", () => {
      if (doneBox.checked) done.add(q.id); else done.delete(q.id);
      localStorage.setItem(DONE_KEY, JSON.stringify([...done]));
      render();
    });

    node.querySelector("[data-text]").textContent = q.text;

    const topicsWrap = node.querySelector("[data-topics]");
    for (const t of q.topics || []) {
      topicsWrap.appendChild(chip(topicLabel(t), () => { state.topic = t; els.topic.value = t; render(); }));
    }

    const authorEl = node.querySelector("[data-author]");
    const n = (q.sources || []).length;
    if (n > 1) {
      authorEl.textContent = `${n} source posts`;
      authorEl.title = (q.authors || []).join(", ");
    } else {
      authorEl.textContent = "via " + ((q.authors || [])[0] || "unknown");
    }

    node.querySelector("[data-link]").href = "https://www.linkedin.com/feed/update/urn:li:activity:" + (q.sources || [])[0] + "/";

    if (done.has(q.id)) card.classList.add("is-done");
    return node;
  }

  function renderLearning(l) {
    const node = els.lTpl.content.cloneNode(true);
    const fieldB = node.querySelector("[data-field]");
    fieldB.textContent = l.field;
    const compB = node.querySelector("[data-company]");
    if (l.company && l.company !== "General") {
      compB.textContent = l.company;
    } else {
      compB.remove();
    }
    const body = node.querySelector("[data-text]");
    body.textContent = l.text;
    const clampBtn = node.querySelector("[data-clamp]");
    requestAnimationFrame(() => {
      if (body.scrollHeight > 260) {
        body.classList.add("clamped");
        clampBtn.hidden = false;
        clampBtn.addEventListener("click", () => {
          const clamped = body.classList.toggle("clamped");
          clampBtn.textContent = clamped ? "Show more ▾" : "Show less ▴";
        });
      }
    });
    const topicsWrap = node.querySelector("[data-topics]");
    for (const t of (l.topics || []).slice(0, 5)) {
      topicsWrap.appendChild(chip(topicLabel(t), () => { state.tab = "questions"; setTabUI("questions"); state.topic = ""; render(); }));
    }
    node.querySelector("[data-author]").textContent = "by " + (l.author || "unknown");
    node.querySelector("[data-link]").href = l.post_url;
    return node;
  }

  function renderSource(p) {
    const node = els.sTpl.content.cloneNode(true);
    const fieldB = node.querySelector("[data-field]");
    fieldB.textContent = p.field || "General";
    const compB = node.querySelector("[data-company]");
    if (p.company && p.company !== "General") {
      compB.textContent = p.company;
    } else {
      compB.remove();
    }
    node.querySelector("[data-count]").textContent = (p.question_count || 0) + " questions";
    node.querySelector("[data-author]").textContent = p.author || "Unknown";
    node.querySelector("[data-time]").textContent = p.time || "";
    node.querySelector("[data-link]").href = p.post_url;
    return node;
  }

  function render() {
    rebuildFieldForTab();
    els.loadMore.hidden = true;
    els.empty.hidden = true;
    if (state.tab === "questions") {
      const visible = state.questions.filter(questionMatches);
      const slice = visible.slice(0, state.visible);
      els.questions.innerHTML = "";
      const frag = document.createDocumentFragment();
      for (const q of slice) frag.appendChild(renderQuestion(q));
      els.questions.appendChild(frag);
      els.loadMore.hidden = visible.length <= state.visible;
      els.loadMore.textContent = `Load more (${visible.length - state.visible} remaining)`;
      els.empty.hidden = visible.length !== 0;
      els.searchCount.textContent = `${visible.length.toLocaleString()} / ${state.questions.length.toLocaleString()} questions`;
      renderStats(visible.length, "questions", state.questions.length);
    } else if (state.tab === "learnings") {
      const visible = state.learnings.filter(learningMatches);
      els.learnings.innerHTML = "";
      const frag = document.createDocumentFragment();
      for (const l of visible) frag.appendChild(renderLearning(l));
      els.learnings.appendChild(frag);
      els.empty.hidden = visible.length !== 0;
      els.searchCount.textContent = `${visible.length} / ${state.learnings.length} learnings`;
      renderStats(visible.length, "learnings", state.learnings.length);
    } else {
      const visible = state.posts.filter(sourceMatches);
      els.sources.innerHTML = "";
      const frag = document.createDocumentFragment();
      for (const p of visible) frag.appendChild(renderSource(p));
      els.sources.appendChild(frag);
      els.empty.hidden = visible.length !== 0;
      els.searchCount.textContent = `${visible.length} / ${state.posts.length} source posts`;
      renderStats(visible.length, "posts", state.posts.length);
    }
    els.questions.hidden = state.tab !== "questions";
    els.learnings.hidden = state.tab !== "learnings";
    els.sources.hidden = state.tab !== "sources";
  }

  /* ---------- mock interview ---------- */

  function runMock() {
    const field = els.mockField.value;
    const company = els.mockCompany.value;
    const exp = els.mockExp.value;
    const count = Math.max(1, Math.min(30, parseInt(els.mockCount.value, 10) || 5));
    const pool = state.questions.filter(
      (q) => (!field || q.field === field) && (!company || q.company === company) && (!exp || q.exp === exp)
    );
    els.mockOut.hidden = false;
    els.mockOut.innerHTML = "";
    if (pool.length === 0) {
      const li = document.createElement("li");
      li.textContent = "No questions match that combination.";
      els.mockOut.appendChild(li);
      return;
    }
    const picked = [];
    const copy = [...pool];
    while (picked.length < count && copy.length) {
      picked.push(copy.splice(Math.floor(Math.random() * copy.length), 1)[0]);
    }
    for (const q of picked) {
      const li = document.createElement("li");
      li.textContent = q.text;
      const a = document.createElement("a");
      a.href = "https://www.linkedin.com/feed/update/urn:li:activity:" + (q.sources || [])[0] + "/";
      a.target = "_blank";
      a.rel = "noopener";
      a.textContent = " ↗ source";
      li.appendChild(document.createElement("br"));
      li.appendChild(a);
      els.mockOut.appendChild(li);
    }
  }

  /* ---------- wiring ---------- */

  function setTabUI(tab) {
    state.tab = tab;
    els.tabQuestions.classList.toggle("active", tab === "questions");
    els.tabLearnings.classList.toggle("active", tab === "learnings");
    els.tabSources.classList.toggle("active", tab === "sources");
    // learnings/sources: hide question-specific filters
    const showQ = tab === "questions";
    els.company.parentElement.classList.toggle("hide", !showQ);
    els.topic.parentElement.classList.toggle("hide", !showQ);
    els.exp.parentElement.classList.toggle("hide", !showQ);
    els.doneView.parentElement.classList.toggle("hide", !showQ);
    els.activeTopics.classList.toggle("hide", !showQ);
    render();
  }

  function wire() {
    let debounce;
    els.search.addEventListener("input", () => {
      clearTimeout(debounce);
      debounce = setTimeout(() => { state.q = els.search.value.trim().toLowerCase(); state.visible = 50; render(); }, 120);
    });
    els.field.addEventListener("change", () => { state.field = els.field.value; state.visible = 50; render(); });
    els.company.addEventListener("change", () => { state.company = els.company.value; state.visible = 50; render(); });
    els.topic.addEventListener("change", () => { state.topic = els.topic.value; state.visible = 50; render(); });
    els.exp.addEventListener("change", () => { state.exp = els.exp.value; state.visible = 50; render(); });
    els.doneView.addEventListener("change", () => { state.doneView = els.doneView.value; state.visible = 50; render(); });
    els.reset.addEventListener("click", () => {
      state.q = ""; state.field = ""; state.company = ""; state.topic = ""; state.exp = ""; state.visible = 50;
      els.search.value = ""; els.field.value = ""; els.company.value = ""; els.topic.value = ""; els.exp.value = "";
      els.doneView.value = "all";
      rebuildFieldForTab();
      render();
    });
    els.tabQuestions.addEventListener("click", () => setTabUI("questions"));
    els.tabLearnings.addEventListener("click", () => setTabUI("learnings"));
    els.tabSources.addEventListener("click", () => setTabUI("sources"));
    els.loadMore.addEventListener("click", () => { state.visible += 100; render(); });
    els.mockBtn.addEventListener("click", () => els.mockDialog.showModal());
    els.mockClose.addEventListener("click", () => els.mockDialog.close());
    els.mockGo.addEventListener("click", runMock);
    window.addEventListener("scroll", () => {
      if (state.tab !== "questions" || els.loadMore.hidden) return;
      if (window.innerHeight + window.scrollY >= document.body.scrollHeight - 400) {
        state.visible += 100;
        render();
      }
    }, { passive: true });
  }

  /* ---------- init ---------- */

  async function init() {
    try {
      await load();
    } catch (e) {
      els.empty.hidden = false;
      els.empty.textContent = "Could not load data files — open this site through a local server, not by double-clicking the file.";
      return;
    }
    buildOptions();
    renderActiveTopics();
    wire();
    render();
  }

  init();
})();
