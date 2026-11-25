"use strict";
/* ---------- sprites (鳥獣戯画風: 狐=Fable 猿=Opus 兎=Sonnet 蛙=Haiku) ---------- */
const HEADS = {
  fable: [
    "..kk........kk..",
    ".kfFk......kFfk.",
    ".kfFFkkkkkkFFfk.",
    ".kffffffffffffk.",
    ".kffeffffffeffk.",
    "..kffwwwwwwffk..",
    "...kwwwkkwwwk...",
    "....kwwwwwwk....",
    ".....kkkkkk.....",
  ],
  opus: [
    "................",
    "....kkkkkkkk....",
    "...kffffffffk...",
    ".kkfFFFffFFFfkk.",
    "kFkfFeFFFFeFfkFk",
    ".kkfFFFFFFFFfkk.",
    "...kfFFkkFFfk...",
    "....kFFFFFFk....",
    ".....kkkkkk.....",
  ],
  sonnet: [
    "...kk......kk...",
    "..kfFk....kFfk..",
    "..kfFk....kFfk..",
    "..kfFk....kFfk..",
    "..kffkkkkkkffk..",
    "..kffffffffffk..",
    "..kfeffffffefk..",
    "..kffffFFffffk..",
    "...kkkkkkkkkk...",
  ],
  haiku: [
    "................",
    "..kkk......kkk..",
    ".kwwwk....kwwwk.",
    ".kwewkkkkkkwewk.",
    ".kffffffffffffk.",
    "kffffffffffffffk",
    "kfkkkkkkkkkkkkfk",
    ".kffffffffffffk.",
    "..kkkkkkkkkkkk..",
  ],
};
const BODY = [
  "....krrrrrrk....",
  "...krrRwwRrrk...",
  "..krrrrRRrrrrk..",
  ".krrrrrrrrrrrrk.",
  ".krrffrrrrffrrk.",
  "krrrrrrrrrrrrrrk",
  "kRRrrrrrrrrrrRRk",
  ".kkkkkkkkkkkkkk.",
];
const HAT = [ // 烏帽子 for judges
  "......kkkk......",
  ".....khhhhk.....",
  ".....khhhhk.....",
  "....khhhhhhk....",
];
const FUR = {
  fable: { f: "#e08a2c", F: "#f6c36a" },
  opus: { f: "#8a5a34", F: "#f0c9a0" },
  sonnet: { f: "#f4f0e6", F: "#f0a0a8" },
  haiku: { f: "#5fae4a", F: "#8fd070" },
};
const ROBE = {
  left: { r: "#c8372d", R: "#7d1f1c" },
  right: { r: "#2f6fd0", R: "#1b3f86" },
  judge: { r: "#6b4a9a", R: "#3f2a63" },
};
const NAMES = { fable: "Fable", opus: "Opus", sonnet: "Sonnet", haiku: "Haiku" };
const MODELS = ["fable", "opus", "sonnet", "haiku"];

function drawSprite(cv, model, robe, { hat = false, hidden = false } = {}) {
  const rows = [...(hat ? HAT : []), ...(model ? HEADS[model] : HEADS.opus), ...BODY];
  cv.width = 16; cv.height = rows.length;
  const g = cv.getContext("2d");
  const pal = { k: "#1b1626", w: "#ffffff", e: "#1b1626", h: "#2a2a34", ...(FUR[model] || {}), ...ROBE[robe] };
  rows.forEach((row, y) => [...row].forEach((c, x) => {
    if (c === ".") return;
    g.fillStyle = hidden ? "#0d0a14" : pal[c];
    g.fillRect(x, y, 1, 1);
  }));
  if (hidden) { g.fillStyle = "#d9a441"; [[7,3],[8,3],[9,4],[8,5],[8,7]].forEach(([x,y]) => g.fillRect(x, y + 4, 1, 1)); }
}
function hiddenSprite(cv) { // generic cloaked silhouette so the head shape leaks nothing
  const rows = ["................", "................", ".....kkkkkk.....", "....kkkkkkkk....", "...kkkkkkkkkk...",
    "...kkkkkkkkkk...", "...kkkkkkkkkk...", "....kkkkkkkk....", ".....kkkkkk.....", ...BODY];
  cv.width = 16; cv.height = rows.length;
  const g = cv.getContext("2d");
  rows.forEach((row, y) => [...row].forEach((c, x) => { if (c !== ".") { g.fillStyle = "#0d0a14"; g.fillRect(x, y, 1, 1); } }));
  g.fillStyle = "#d9a441";
  [[7,3],[8,3],[9,4],[8,5],[8,7]].forEach(([x, y]) => g.fillRect(x, y + 1, 1, 1));
}

/* ---------- state ---------- */
const $ = (s, el = document) => el.querySelector(s);
const KEY = "ai-utaawase-picks-v1";
let D, cur = 0, picks = {}, openJudge = null;
try { picks = JSON.parse(localStorage.getItem(KEY)) || {}; } catch (e) {}
const save = () => { try { localStorage.setItem(KEY, JSON.stringify(picks)); } catch (e) {} };
const winner = r => r.judgments.filter(j => j.pick === "left").length * 2 > r.judgments.length ? "left" : "right";

/* ---------- render ---------- */
function render() {
  const r = D.rounds[cur], pick = picks[r.ban], done = !!pick;
  $("#ban").textContent = `第${r.ban}番`;
  $("#dai").textContent = r.dai;
  $("#daiyomi").textContent = `${r.bu}・${r.yomi}`;

  for (const side of ["left", "right"]) {
    const el = $(`.side.${side}`), p = r[side], card = $(".card", el);
    $(".waka", el).textContent = p.waka;
    $(".yomi", el).textContent = p.yomi;
    card.disabled = done;
    card.classList.toggle("mine", pick === side);
    card.classList.toggle("won", done && winner(r) === side);
    card.onclick = () => { picks[r.ban] = side; openJudge = null; save(); render(); };
    if (done) drawSprite($("canvas", el), p.model, side); else hiddenSprite($("canvas", el));
    $(".name", el).textContent = done ? NAMES[p.model] : "";
  }

  const J = $("#judges"); J.innerHTML = "";
  D.judges.forEach(jd => {
    const b = document.createElement("button");
    b.className = "judge" + (openJudge === jd.id ? " sel" : "");
    b.disabled = !done;
    const cv = document.createElement("canvas"); drawSprite(cv, jd.model, "judge", { hat: true });
    const jm = r.judgments.find(j => j.judge === jd.id);
    const flag = document.createElement("span");
    flag.className = "flag" + (done && jm ? " " + jm.pick : "");
    flag.textContent = done && jm ? (jm.pick === "left" ? "左" : "右") : "";
    const nm = document.createElement("span"); nm.className = "jname"; nm.textContent = NAMES[jd.model];
    b.append(cv, flag, nm);
    b.onclick = () => { openJudge = openJudge === jd.id ? null : jd.id; render(); };
    J.append(b);
  });
  const H = $("#hanshi"), jm = done && r.judgments.find(j => j.judge === openJudge);
  H.hidden = !jm;
  if (jm) {
    H.innerHTML = "";
    const w = document.createElement("span"); w.className = "who " + jm.pick; w.textContent = jm.pick === "left" ? "左勝" : "右勝";
    H.append(w, document.createTextNode(jm.comment));
  }

  const S = $("#strip"); S.innerHTML = "";
  D.rounds.forEach((x, i) => {
    const b = document.createElement("button");
    b.textContent = x.ban;
    b.className = (i === cur ? "cur " : "") + (picks[x.ban] ? winner(x) : "");
    b.onclick = () => { cur = i; openJudge = null; render(); };
    S.append(b);
  });

  const seen = D.rounds.filter(x => picks[x.ban]);
  const c = (f) => seen.filter(f).length;
  $("#tally").innerHTML =
    `<span><span class="k">判</span><b class="l">左${c(x => winner(x) === "left")}</b>－<b class="r">${c(x => winner(x) === "right")}右</b></span>` +
    `<span><span class="k">私</span><b class="l">左${c(x => picks[x.ban] === "left")}</b>－<b class="r">${c(x => picks[x.ban] === "right")}右</b></span>`;
}

/* ---------- statistics (only over rounds the viewer has judged) ---------- */
function stats() {
  const seen = D.rounds.filter(x => picks[x.ban]);
  const B = $("#statsBody"); B.innerHTML = "";
  const table = (head, rows) => {
    const t = document.createElement("table");
    const tr = cells => { const r = document.createElement("tr"); cells.forEach((c, i) => {
      const td = document.createElement(cells === head ? "th" : "td");
      if (c instanceof Node) td.append(c); else td.textContent = c; r.append(td); }); return r; };
    t.append(tr(head), ...rows.map(tr)); B.append(t);
  };
  const label = (model, robe, hat) => {
    const s = document.createElement("span"), cv = document.createElement("canvas");
    drawSprite(cv, model, robe, { hat }); s.append(cv, NAMES[model]); return s;
  };
  const frac = (a, b) => b ? `${a}/${b}` : "–";

  // per model (as poet)
  const entries = seen.flatMap(r => ["left", "right"].map(side => ({ r, side, model: r[side].model })));
  table(["歌人", "首", "勝", "票", "私"], MODELS.map(m => {
    const es = entries.filter(e => e.model === m);
    return [label(m, "judge"), es.length,
      frac(es.filter(e => winner(e.r) === e.side).length, es.length),
      frac(es.reduce((n, e) => n + e.r.judgments.filter(j => j.pick === e.side).length, 0), es.reduce((n, e) => n + e.r.judgments.length, 0)),
      frac(es.filter(e => picks[e.r.ban] === e.side).length, es.length)];
  }));

  // per judge
  table(["判者", "左", "右", "多数", "私", ...MODELS.map(m => NAMES[m])], D.judges.map(jd => {
    const js = seen.map(r => ({ r, j: r.judgments.find(j => j.judge === jd.id) })).filter(x => x.j);
    return [label(jd.model, "judge", true),
      js.filter(x => x.j.pick === "left").length, js.filter(x => x.j.pick === "right").length,
      frac(js.filter(x => x.j.pick === winner(x.r)).length, js.length),
      frac(js.filter(x => x.j.pick === picks[x.r.ban]).length, js.length),
      ...MODELS.map(m => { // votes given to each model's poems (mirror matches excluded)
        const ms = js.filter(x => (x.r.left.model === m) !== (x.r.right.model === m));
        return frac(ms.filter(x => x.r[x.j.pick].model === m).length, ms.length); })];
  }));

  const n = document.createElement("div"); n.className = "dim"; n.textContent = `${seen.length}/${D.rounds.length}`;
  B.append(n);
  $("#stats").showModal();
}

/* ---------- boot ---------- */
fetch("data/utaawase.json").then(r => r.json()).then(d => {
  D = d;
  const first = D.rounds.findIndex(x => !picks[x.ban]);
  cur = first < 0 ? 0 : first;
  $("#prev").onclick = () => { cur = (cur + D.rounds.length - 1) % D.rounds.length; openJudge = null; render(); };
  $("#next").onclick = () => { cur = (cur + 1) % D.rounds.length; openJudge = null; render(); };
  $("#statsBtn").onclick = stats;
  $("#statsClose").onclick = () => $("#stats").close();
  $("#resetBtn").onclick = () => { if (confirm("↺ ?")) { picks = {}; save(); cur = 0; openJudge = null; render(); } };
  document.addEventListener("keydown", e => { if (e.key === "ArrowLeft") $("#prev").click(); if (e.key === "ArrowRight") $("#next").click(); });
  render();
});
