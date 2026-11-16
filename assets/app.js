/* Interview Prep Vault — client-side app, no build step. */
(() => {
  "use strict";

  const state = {
    posts: [],
    q: "",
    field: "",
    company: "",
    topic: "",
    difficulty: "",
    doneView: "all",
  };
  const DONE_KEY = "ipv-done-v1";
  let done = new Set(JSON.parse(localStorage.getItem(DONE_KEY) || "[]"));

  const $ = (id) => document.getElementById(id);
  const els = {
    stats: $("stats"), search: $("search"), searchCount: $("searchCount"),
    field: $("fieldFilter"), company: $("companyFilter"), topic: $("topicFilter"),
    difficulty: $("difficultyFilter"), doneView: $("doneFilter"), reset: $("resetBtn"),
    posts: $("posts"), empty: $("empty"), tpl: $("cardTpl"), activeTopics: $("activeTopics"),
    mockBtn: $("mockBtn"), mockDialog: $("mockDialog"), mockClose: $("mockClose"),
    mockField: $("mockField"), mockCompany: $("mockCompany"), mockCount: $("mockCount"),
    mockGo: $("mockGo"), mockOut: $("mockOut"),
  };

  /* ---------- data ---------- */

  async function load() {
    const res = await fetch("data/posts.json");
    if (!res.ok) throw new Error("posts.json failed: " + res.status);
    state.posts = await res.json();
  }

  /* ---------- rendering ---------- */

  function fillSelect(select, values, labelAll) {
    select.innerHTML = "";
    const optAll = document.createElement("option");
    optAll.value = "";
    optAll.textContent = labelAll;
    select.appendChild(optAll);
    for (const v of values) {
      const o = document.createElement("option");
      o.value = v;
      o.textContent = v;
      select.appendChild(o);
    }
  }

  function renderStats(visible) {
    const n = state.posts.length;
    const companies = new Set(state.posts.map((p) => p.company)).size;
    const fields = new Set(state.posts.map((p) => p.field)).size;
    const doneCount = state.posts.filter((p) => done.has(p.id)).length;
    const pct = n ? Math.round((doneCount / n) * 100) : 0;
    els.stats.innerHTML = "";
    for (const [b, s, cls] of [
      [n, "posts", ""],
      [fields, "fields", ""],
      [companies, "companies", ""],
      [doneCount + " / " + n, "done (" + pct + "%)", "progress"],
      [visible, "showing", ""],
    ]) {
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

  function chip(text, click) {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "topic-chip";
    btn.textContent = text;
    if (click) btn.addEventListener("click", click);
    return btn;
  }

  function renderCard(post) {
    const node = els.tpl.content.cloneNode(true);
    const card = node.querySelector(".card");

    const fieldB = node.querySelector("[data-field]");
    fieldB.textContent = post.field;
    fieldB.title = "Filter by this field";
    fieldB.style.cursor = "pointer";
    fieldB.addEventListener("click", () => { state.field = post.field; els.field.value = post.field; applyTopicOptions(); render(); });

    const compB = node.querySelector("[data-company]");
    if (post.company && post.company !== "General") {
      compB.textContent = post.company;
      compB.style.cursor = "pointer";
      compB.addEventListener("click", () => { state.company = post.company; els.company.value = post.company; applyTopicOptions(); render(); });
    } else {
      compB.remove();
    }

    const diffB = node.querySelector("[data-diff]");
    if (post.difficulty) {
      diffB.textContent = post.difficulty;
      diffB.className = "badge diff-" + post.difficulty;
    } else {
      diffB.remove();
    }

    const doneBox = node.querySelector("[data-done]");
    doneBox.checked = done.has(post.id);
    doneBox.addEventListener("change", () => {
      if (doneBox.checked) done.add(post.id); else done.delete(post.id);
      localStorage.setItem(DONE_KEY, JSON.stringify([...done]));
      render();
    });

    const body = node.querySelector("[data-text]");
    body.textContent = post.text;

    const clampBtn = node.querySelector("[data-clamp]");
    requestAnimationFrame(() => {
      if (body.scrollHeight > 220) {
        body.classList.add("clamped");
        clampBtn.hidden = false;
        clampBtn.addEventListener("click", () => {
          const clamped = body.classList.toggle("clamped");
          clampBtn.textContent = clamped ? "Show more ▾" : "Show less ▴";
        });
      }
    });

    const topicsWrap = node.querySelector("[data-topics]");
    for (const t of post.topics || []) {
      topicsWrap.appendChild(chip("#" + t, () => { state.topic = t; els.topic.value = t; render(); }));
    }

    const authorEl = node.querySelector("[data-author]");
    if (post.author_url) {
      const a = document.createElement("a");
      a.href = post.author_url;
      a.target = "_blank";
      a.rel = "noopener";
      a.textContent = "by " + post.author;
      a.className = "src-link";
      a.style.fontSize = "13px";
      a.style.fontWeight = "400";
      authorEl.appendChild(a);
    } else {
      authorEl.textContent = "by " + (post.author || "unknown");
    }

    node.querySelector("[data-link]").href = post.post_url;

    if (done.has(post.id)) card.classList.add("is-done");
    card.dataset.id = post.id;
    return node;
  }

  /* ---------- filtering ---------- */

  function matches(post) {
    if (state.field && post.field !== state.field) return false;
    if (state.company && post.company !== state.company) return false;
    if (state.topic && !(post.topics || []).includes(state.topic)) return false;
    if (state.difficulty && post.difficulty !== state.difficulty) return false;
    if (state.doneView === "done" && !done.has(post.id)) return false;
    if (state.doneView === "todo" && done.has(post.id)) return false;
    if (state.q) {
      const hay = (post.text + " " + post.author + " " + post.company + " " + post.field + " " + (post.topics || []).join(" ")).toLowerCase();
      if (!hay.includes(state.q)) return false;
    }
    return true;
  }

  function applyTopicOptions() {
    /* topics limited to what is reachable under current field+company */
    const pool = state.posts.filter(
      (p) => (!state.field || p.field === state.field) && (!state.company || p.company === state.company)
    );
    const topics = [...new Set(pool.flatMap((p) => p.topics || []))].sort((a, b) => a.localeCompare(b));
    fillSelect(els.topic, topics, "All topics");
    if (state.topic && !topics.includes(state.topic)) state.topic = "";
    els.topic.value = state.topic;
  }

  function renderActiveTopics() {
    els.activeTopics.innerHTML = "";
    for (const t of [...new Set(state.posts.flatMap((p) => p.topics || []))]
      .sort((a, b) => a.localeCompare(b))
      .slice(0, 24)) {
      els.activeTopics.appendChild(chip("#" + t, () => { state.topic = t; els.topic.value = t; render(); }));
    }
  }

  function render() {
    const visible = state.posts.filter(matches);
    els.posts.innerHTML = "";
    const frag = document.createDocumentFragment();
    for (const post of visible) frag.appendChild(renderCard(post));
    els.posts.appendChild(frag);
    els.empty.hidden = visible.length !== 0;
    els.searchCount.textContent = visible.length + " / " + state.posts.length + " posts";
    renderStats(visible.length);
  }

  /* ---------- mock interview ---------- */

  function openMock() {
    els.mockDialog.showModal();
  }

  function runMock() {
    const field = els.mockField.value;
    const company = els.mockCompany.value;
    const count = Math.max(1, Math.min(30, parseInt(els.mockCount.value, 10) || 5));
    let pool = state.posts.filter(
      (p) => (!field || p.field === field) && (!company || p.company === company)
    );
    if (pool.length === 0) {
      els.mockOut.hidden = false;
      els.mockOut.innerHTML = "";
      const li = document.createElement("li");
      li.textContent = "No posts match that combination.";
      els.mockOut.appendChild(li);
      return;
    }
    const picked = [];
    const copy = [...pool];
    while (picked.length < count && copy.length) {
      picked.push(copy.splice(Math.floor(Math.random() * copy.length), 1)[0]);
    }
    els.mockOut.hidden = false;
    els.mockOut.innerHTML = "";
    for (const p of picked) {
      const li = document.createElement("li");
      li.textContent = p.text.length > 600 ? p.text.slice(0, 600) + "…" : p.text;
      const a = document.createElement("a");
      a.href = p.post_url;
      a.target = "_blank";
      a.rel = "noopener";
      a.textContent = " ↗ source";
      li.appendChild(document.createElement("br"));
      li.appendChild(a);
      els.mockOut.appendChild(li);
    }
  }

  /* ---------- wiring ---------- */

  function wire() {
    let debounce;
    els.search.addEventListener("input", () => {
      clearTimeout(debounce);
      debounce = setTimeout(() => { state.q = els.search.value.trim().toLowerCase(); render(); }, 120);
    });
    els.field.addEventListener("change", () => { state.field = els.field.value; applyTopicOptions(); render(); });
    els.company.addEventListener("change", () => { state.company = els.company.value; applyTopicOptions(); render(); });
    els.topic.addEventListener("change", () => { state.topic = els.topic.value; render(); });
    els.difficulty.addEventListener("change", () => { state.difficulty = els.difficulty.value; render(); });
    els.doneView.addEventListener("change", () => { state.doneView = els.doneView.value; render(); });
    els.reset.addEventListener("click", () => {
      state.q = ""; state.field = ""; state.company = ""; state.topic = ""; state.difficulty = "";
      els.search.value = ""; els.field.value = ""; els.company.value = ""; els.topic.value = ""; els.difficulty.value = "";
      els.doneView.value = "all";
      applyTopicOptions();
      render();
    });
    els.mockBtn.addEventListener("click", openMock);
    els.mockClose.addEventListener("click", () => els.mockDialog.close());
    els.mockGo.addEventListener("click", runMock);
  }

  /* ---------- init ---------- */

  async function init() {
    try {
      await load();
    } catch (e) {
      document.getElementById("posts").innerHTML = "";
      els.empty.hidden = false;
      els.empty.textContent = "Could not load data/posts.json — open this site through a local server, not by double-clicking the file.";
      return;
    }
    fillSelect(els.field, [...new Set(state.posts.map((p) => p.field))].sort((a, b) => a.localeCompare(b)), "All fields");
    fillSelect(els.company, [...new Set(state.posts.map((p) => p.company))].sort((a, b) => a.localeCompare(b)), "All companies");
    applyTopicOptions();
    renderActiveTopics();
    wire();
    render();
  }

  init();
})();
