#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 3D 星球版记忆宫殿演示页（单文件、零依赖）。"""
import json
import os
import sys
from datetime import datetime

PALACE_DIR = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
OUT = sys.argv[2] if len(sys.argv) > 2 else os.path.join(os.path.dirname(os.path.abspath(__file__)), "site", "index.html")

with open(os.path.join(PALACE_DIR, "palace.json"), encoding="utf-8") as f:
    palace = json.load(f)

items = {}
idir = os.path.join(PALACE_DIR, "items")
for name in os.listdir(idir):
    if name.endswith(".json"):
        with open(os.path.join(idir, name), encoding="utf-8") as f:
            items[name[:-5]] = json.load(f)

META = {
    "c_df499c164c": {"author": "赫尔曼·黑塞", "publisher": "天津人民出版社", "year": "1919", "color": "#d9a24c", "pos": [-18, -18]},
    "c_1ee75e7cd6": {"author": "赫尔曼·黑塞", "publisher": "天津人民出版社", "year": "1906", "color": "#a7bd8b", "pos": [440, 106]},
    "c_5e35f97e1b": {"author": "赫尔曼·黑塞", "publisher": "天津人民出版社", "year": "1919", "color": "#e2b492", "pos": [229, -352]},
    "c_7e8f6a2ace": {"author": "亨利·戴维·梭罗", "publisher": "中国华侨出版社", "year": "1849", "color": "#8fb9cf", "pos": [-317, 370]},
    "c_e8d16f5ee4": {"author": "厄尼斯特·海明威", "publisher": "天津人民出版社", "year": "1929", "color": "#c96b5c", "pos": [-370, -106]},
}

books = []
for i, cell in enumerate(palace.get("cells", [])):
    if cell.get("kind") != "book":
        continue
    d = items.get(cell["id"], {})
    m = META.get(cell["id"], {})
    chs = d.get("chapters", [])
    sections = [s for ch in chs for s in ch.get("sections", [])]
    books.append({
        "id": cell["id"],
        "title": cell.get("title") or "未命名",
        "author": m.get("author", ""),
        "publisher": m.get("publisher", ""),
        "year": m.get("year", ""),
        "color": m.get("color", "#b9c7d0"),
        "pos": m.get("pos", [0, 0]),
        "chapters": [{"title": ch.get("title", ""), "sections": [s.get("title", "") for s in ch.get("sections", [])]} for ch in chs],
        "sectionCount": len(sections),
        "cards": d.get("cards", []),
        "inspirations": d.get("inspirations", []),
    })

data = {"books": books, "now": datetime.now().strftime("%Y.%m.%d")}

TEMPLATE = r"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>记忆宫殿 · Memory Palace</title>
<meta name="description" content="一座建在星图上的记忆宫殿：每本书是一颗星，联想把它们连起来。">
<meta name="theme-color" content="#7ea7c4">
<script>
  try {
    var saved = localStorage.getItem("palace-theme");
  } catch (e) {}
</script>
<style>
  :root {
    --ink: #17262f; --ink-soft: #3c5567; --line: rgba(23,38,47,.16);
    --paper: #f7f4ec; --accent: #8c3b2e;
  }
  * { box-sizing: border-box; }
  html, body { margin: 0; padding: 0; height: 100%; overflow: hidden; }
  body {
    animation: fadein .9s ease both;
    background: #7ea7c4; color: var(--ink);
    font-family: "Songti SC", "Noto Serif SC", "Source Han Serif SC", "STSong", Georgia, serif;
    -webkit-font-smoothing: antialiased;
  }
  canvas { position: fixed; inset: 0; width: 100%; height: 100%; display: block; touch-action: none; cursor: grab; }
  canvas.dragging { cursor: grabbing; }
  canvas.linkmode { cursor: crosshair; }

  .brand { position: fixed; z-index: 5; left: 34px; top: 26px; pointer-events: none; color: #102028; }
  .brand h1 { margin: 0; font-size: 27px; font-weight: 500; letter-spacing: .02em; text-shadow: 0 1px 0 rgba(255,255,255,.35); }
  .brand p { margin: 4px 0 0; font-size: 11.5px; letter-spacing: .22em; color: rgba(16,32,40,.62); text-transform: uppercase; }

  .toolbar { position: fixed; z-index: 6; right: 26px; top: 24px; display: flex; gap: 8px; }
  .tool {
    font: inherit; font-size: 12px; letter-spacing: .08em; cursor: pointer;
    color: #16303c; background: rgba(247,244,236,.55); border: 1px solid rgba(23,38,47,.22);
    border-radius: 999px; padding: 7px 14px; backdrop-filter: blur(8px);
    transition: background .25s, border-color .25s, color .25s, transform .15s;
  }
  .tool:hover { background: rgba(247,244,236,.85); border-color: rgba(23,38,47,.4); }
  .tool:active { transform: scale(.97); }
  .tool.on { background: rgba(140,59,46,.9); border-color: rgba(140,59,46,.9); color: #fbf6ee; }

  .hintbar {
    position: fixed; z-index: 5; left: 34px; bottom: 22px;
    font-size: 12px; letter-spacing: .12em; color: rgba(16,32,40,.66);
    background: rgba(247,244,236,.5); border: 1px solid rgba(23,38,47,.14);
    border-radius: 999px; padding: 6px 16px; backdrop-filter: blur(8px); white-space: nowrap;
    transition: opacity .4s;
  }
  .hintbar.hidden { opacity: 0; }

  .tip {
    position: fixed; z-index: 7; pointer-events: none; padding: 7px 11px;
    background: rgba(20,34,42,.9); color: #f3eee2; border-radius: 8px;
    font-size: 12px; letter-spacing: .06em; opacity: 0; transform: translate(-50%, -130%) scale(.96);
    transition: opacity .18s, transform .18s; max-width: 240px; text-align: center; line-height: 1.5;
  }
  .tip.show { opacity: 1; transform: translate(-50%, -140%) scale(1); }

  .panel {
    position: fixed; z-index: 8; top: 24px; right: 24px; bottom: 24px; width: 372px;
    display: flex; flex-direction: column;
    background: rgba(248,245,237,.94); border: 1px solid rgba(23,38,47,.18); border-radius: 20px;
    box-shadow: 0 30px 80px rgba(10,26,36,.35); backdrop-filter: blur(14px) saturate(1.1);
    transform: translateX(calc(100% + 40px)); transition: transform .45s cubic-bezier(.22,.61,.36,1);
    overflow: hidden;
  }
  .panel.open { transform: none; }
  .panel-head { padding: 26px 26px 16px; border-bottom: 1px solid var(--line); position: relative; }
  .panel-head .kind { font-size: 10.5px; letter-spacing: .3em; color: var(--accent); }
  .panel-head h2 { margin: 8px 0 0; font-size: 32px; line-height: 1.18; letter-spacing: .02em; font-weight: 600; }
  .panel-head .by { margin: 8px 0 0; font-size: 13px; color: var(--ink-soft); }
  .panel-close {
    position: absolute; right: 18px; top: 18px; width: 34px; height: 34px; border-radius: 50%;
    border: 1px solid var(--line); background: transparent; color: var(--ink-soft);
    font: inherit; font-size: 20px; line-height: 1; cursor: pointer; transition: .25s;
  }
  .panel-close:hover { color: var(--accent); border-color: rgba(140,59,46,.5); transform: rotate(90deg); }
  .panel-body { padding: 18px 26px 30px; overflow: auto; }
  .facts { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 18px; }
  .fact { border: 1px solid var(--line); border-radius: 12px; padding: 10px 12px; }
  .fact b { display: block; font-size: 19px; font-weight: 600; letter-spacing: .01em; }
  .fact span { font-size: 10.5px; letter-spacing: .16em; color: rgba(23,38,47,.55); }
  .panel h3 { font-size: 11px; letter-spacing: .24em; color: rgba(23,38,47,.5); font-weight: 500; margin: 20px 0 10px; }
  .chapter { display: flex; gap: 12px; padding: 9px 0; border-bottom: 1px solid rgba(23,38,47,.08); font-size: 14.5px; }
  .chapter .n { color: rgba(23,38,47,.35); font-size: 11px; width: 22px; padding-top: 2px; font-variant-numeric: tabular-nums; }
  .muted { color: rgba(23,38,47,.5); font-size: 12.5px; line-height: 1.8; }
  .links { display: grid; gap: 8px; }
  .linkrow { display: flex; align-items: center; gap: 10px; font-size: 13px; }
  .linkrow i { width: 7px; height: 7px; border-radius: 50%; flex: 0 0 7px; }
  .clearlinks {
    margin-top: 12px; font: inherit; font-size: 11.5px; letter-spacing: .08em; cursor: pointer;
    background: none; border: 1px dashed var(--line); border-radius: 8px; color: rgba(23,38,47,.55);
    padding: 6px 10px;
  }
  .clearlinks:hover { color: var(--accent); border-color: rgba(140,59,46,.4); }
  .panel-foot { margin-top: 22px; padding-top: 14px; border-top: 1px solid var(--line); font-size: 11px; letter-spacing: .1em; color: rgba(23,38,47,.45); }

  .toast {
    position: fixed; z-index: 9; left: 50%; bottom: 70px; transform: translate(-50%, 10px);
    background: rgba(20,34,42,.92); color: #f3eee2; padding: 9px 16px; border-radius: 999px;
    font-size: 12.5px; letter-spacing: .08em; opacity: 0; transition: opacity .3s, transform .3s; pointer-events: none;
  }
  .toast.show { opacity: 1; transform: translate(-50%, 0); }

  @media (max-width: 720px) {
    .brand { left: 18px; top: 16px; }
    .brand h1 { font-size: 21px; }
    .brand p { font-size: 10px; letter-spacing: .18em; }
    .toolbar { right: 14px; top: 14px; gap: 6px; }
    .tool { font-size: 11px; padding: 6px 10px; }
    .tool.reset-label { display: none; }
    .hintbar { font-size: 11px; bottom: 14px; left: 18px; }
    .panel { left: 0; right: 0; top: auto; bottom: 0; width: auto; height: 68vh; border-radius: 20px 20px 0 0; transform: translateY(105%); }
    .panel.open { transform: none; }
    .panel-head h2 { font-size: 26px; }
  }
  @media (prefers-reduced-motion: reduce) {
    * { transition-duration: .001ms !important; animation-duration: .001ms !important; }
  }
</style>
</head>
<body>
<canvas id="scene"></canvas>

<div class="brand">
  <h1>Memory Palace</h1>
  <p>记忆宫殿 · __COUNT__ 本书</p>
</div>

<div class="toolbar">
  <button class="tool on" id="spinBtn">自动旋转</button>
  <button class="tool" id="linkBtn">连一条联想</button>
  <button class="tool" id="resetBtn">重置视角</button>
</div>

<div class="hintbar" id="hintbar">拖动旋转 · 滚轮缩放 · 点星球打开</div>
<div class="tip" id="tip"></div>
<div class="toast" id="toast"></div>

<aside class="panel" id="panel" aria-hidden="true">
  <div class="panel-head">
    <span class="kind">书</span>
    <h2 id="p-title"></h2>
    <p class="by" id="p-by"></p>
    <button class="panel-close" id="panelClose" aria-label="关闭">×</button>
  </div>
  <div class="panel-body" id="panelBody"></div>
</aside>

<script>
const DATA = __DATA__;

/* ---------------- 场景参数 ---------------- */
const canvas = document.getElementById("scene");
const ctx = canvas.getContext("2d");
const tip = document.getElementById("tip");
const toast = document.getElementById("toast");
const hintbar = document.getElementById("hintbar");
const panel = document.getElementById("panel");

let W = innerWidth, H = innerHeight, DPR = 1;

const fitDist = () => innerWidth < 720 ? 2750 : (innerWidth < 1100 ? 2350 : 1850);
const view = {
  yaw: 0.42, pitch: 1.0, dist: fitDist(),
  targetDist: fitDist(), targetPitch: 1.0,
  panX: 0, panY: 0,
  spin: !matchMedia('(prefers-reduced-motion: reduce)').matches, vYaw: 0, idle: 0,
};

const GRID = 120, EXT = 9;
const COLORS = {};
DATA.books.forEach(b => COLORS[b.id] = hexToRgb(b.color));

/* ---------------- 工具 ---------------- */
function hexToRgb(h) {
  const v = h.replace("#", "");
  return [parseInt(v.slice(0, 2), 16), parseInt(v.slice(2, 4), 16), parseInt(v.slice(4, 6), 16)];
}
function mix(c, target, amount) {
  const t = target === "#fff" ? [255, 255, 255] : [12, 20, 26];
  return c.map((v, i) => Math.round(v + (t[i] - v) * amount));
}
const rgba = (c, a) => "rgba(" + c[0] + "," + c[1] + "," + c[2] + "," + a + ")";

function project(x, y, z) {
  const cy = Math.cos(view.yaw), sy = Math.sin(view.yaw);
  const X = x * cy - z * sy;
  const Z = x * sy + z * cy;
  const cp = Math.cos(view.pitch), sp = Math.sin(view.pitch);
  const Y = y * cp + Z * sp;
  const Zc = Z * cp - y * sp;
  const d = Zc + view.dist;
  const s = 1500 / Math.max(d, 80);
  return { x: W / 2 + X * s + view.panX, y: H * 0.56 - Y * s + view.panY, s, d };
}

/* ---------------- 书本星球 ---------------- */
const nodes = DATA.books.map((b, i) => ({
  book: b,
  x: b.pos[0], z: b.pos[1], baseY: 74,
  r: (40 + (b.title.length > 3 ? 2 : 0)) * (innerWidth < 720 ? 1.35 : 1),
  phase: i * 1.7,
  color: COLORS[b.id],
}));

const PRESET_LINKS = [];
(function seedLinks() {
  const byAuthor = {};
  DATA.books.forEach(b => { (byAuthor[b.author] = byAuthor[b.author] || []).push(b.id); });
  Object.values(byAuthor).forEach(ids => {
    for (let i = 0; i < ids.length - 1; i++) PRESET_LINKS.push({ a: ids[i], b: ids[i + 1], why: "同一作者" });
  });
})();

const LINK_KEY = "palace-scene-links";
let localLinks = [];
try { localLinks = JSON.parse(localStorage.getItem(LINK_KEY) || "[]"); } catch (e) {}

function allLinks() { return PRESET_LINKS.concat(localLinks); }
function saveLinks() { try { localStorage.setItem(LINK_KEY, JSON.stringify(localLinks)); } catch (e) {} }

/* ---------------- 交互状态 ---------------- */
let hoverId = null, activeId = null, linkMode = false, linkFrom = null;
let pointers = new Map(), dragStart = null, lastMove = 0;
let projected = {};

/* ---------------- 绘制 ---------------- */
function fitView() {
  view.panX = 0; view.panY = 0;
  if (innerWidth >= 720) return;
  view.dist = view.targetDist = 2400;
  for (let i = 0; i < 30; i++) {
    const pts = nodes.map(n => project(n.x, n.baseY, n.z));
    const xs = pts.map(p => p.x), ys = pts.map(p => p.y);
    const w = Math.max(...xs) - Math.min(...xs), h = Math.max(...ys) - Math.min(...ys);
    if (w <= W - 100 && h <= H - 240) break;
    view.dist += 120; view.targetDist = view.dist;
  }
  const pts = nodes.map(n => project(n.x, n.baseY, n.z));
  const xs = pts.map(p => p.x), ys = pts.map(p => p.y);
  view.panX = Math.max(-W * 0.3, Math.min(W * 0.3, W / 2 - (Math.min(...xs) + Math.max(...xs)) / 2));
  view.panY = Math.max(-100, Math.min(100, H * 0.5 - (Math.min(...ys) + Math.max(...ys)) / 2));
}

function resize() {
  DPR = Math.min(2, devicePixelRatio || 1);
  W = innerWidth; H = innerHeight;
  view.dist = view.targetDist = fitDist();
  view.pitch = view.targetPitch = 1.0;
  fitView();
  canvas.width = Math.round(W * DPR);
  canvas.height = Math.round(H * DPR);
  ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
}
addEventListener("resize", resize);

function drawBackground() {
  const g = ctx.createLinearGradient(0, 0, 0, H);
  g.addColorStop(0, "#9dbfd8");
  g.addColorStop(0.42, "#7fa7c4");
  g.addColorStop(1, "#6289a8");
  ctx.fillStyle = g;
  ctx.fillRect(0, 0, W, H);

  const vg = ctx.createRadialGradient(W / 2, H * 0.42, Math.min(W, H) * 0.2, W / 2, H * 0.5, Math.max(W, H) * 0.78);
  vg.addColorStop(0, "rgba(255,255,255,.10)");
  vg.addColorStop(0.55, "rgba(255,255,255,0)");
  vg.addColorStop(1, "rgba(16,38,54,.20)");
  ctx.fillStyle = vg;
  ctx.fillRect(0, 0, W, H);
}

function drawGrid() {
  ctx.lineWidth = 1.15;
  const seg = 22;
  for (let axis = 0; axis < 2; axis++) {
    for (let k = -EXT; k <= EXT; k++) {
      const fixed = k * GRID;
      let prev = null;
      for (let i = 0; i <= seg; i++) {
        const t = -EXT * GRID + (i / seg) * 2 * EXT * GRID;
        const p = axis === 0 ? project(fixed, 0, t) : project(t, 0, fixed);
        if (prev) {
          const midS = (prev.s + p.s) / 2;
          let a = 0.52 * Math.max(0.22, Math.min(1, midS * 1.55));
          if (Math.abs(t) > (EXT - 0.5) * GRID) a *= 0.65;
          ctx.strokeStyle = "rgba(255,255,255," + a.toFixed(3) + ")";
          ctx.beginPath();
          ctx.moveTo(prev.x, prev.y);
          ctx.lineTo(p.x, p.y);
          ctx.stroke();
        }
        prev = p;
      }
    }
  }
}

function drawArcs(t) {
  const links = allLinks();
  links.forEach((ln, idx) => {
    const A = nodes.find(n => n.book.id === ln.a), B = nodes.find(n => n.book.id === ln.b);
    if (!A || !B) return;
    const hot = (hoverId && (ln.a === hoverId || ln.b === hoverId)) || (activeId && (ln.a === activeId || ln.b === activeId));
    const ay = A.baseY + Math.sin(t * 0.0011 + A.phase) * 7;
    const by = B.baseY + Math.sin(t * 0.0011 + B.phase) * 7;
    const mx = (A.x + B.x) / 2, mz = (A.z + B.z) / 2;
    const dxs = B.x - A.x, dzs = B.z - A.z;
    const arcLen = Math.hypot(dxs, dzs) || 1;
    const nx = -dzs / arcLen, nz = dxs / arcLen;
    const side = arcLen * 0.42 * ((ln.why === "你的联想") ? 1 : 0.85);
    const apex = 110 + arcLen * 0.18 + (ln.why === "你的联想" ? 40 : 0);
    const qx = mx + nx * side, qy = apex + 40, qz = mz + nz * side;

    const N = 36;
    const pts = [];
    for (let i = 0; i <= N; i++) {
      const u = i / N, w = 1 - u;
      const x = w * w * A.x + 2 * w * u * qx + u * u * B.x;
      const y = w * w * ay + 2 * w * u * qy + u * u * by;
      const z = w * w * A.z + 2 * w * u * qz + u * u * B.z;
      pts.push(project(x, y, z));
    }
    ctx.save();
    ctx.lineCap = "round";
    ctx.beginPath();
    pts.forEach((p, i) => i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y));
    ctx.strokeStyle = hot ? "rgba(255,252,240,.98)" : "rgba(248,252,255,.8)";
    ctx.lineWidth = hot ? 2.6 : 1.7;
    ctx.shadowColor = hot ? "rgba(255,240,200,.9)" : "rgba(225,242,255,.75)";
    ctx.shadowBlur = hot ? 18 : 12;
    ctx.stroke();
    ctx.shadowBlur = 0;

    const prog = ((t * 0.00016) + idx * 0.27) % 1;
    const ip = Math.min(N, Math.max(0, Math.round(prog * N)));
    const pp = pts[ip];
    ctx.beginPath();
    ctx.arc(pp.x, pp.y, hot ? 3.4 : 2.2, 0, Math.PI * 2);
    ctx.fillStyle = hot ? "rgba(255,250,235,.98)" : "rgba(255,253,246,.85)";
    ctx.shadowColor = "rgba(255,244,210,.95)";
    ctx.shadowBlur = hot ? 14 : 8;
    ctx.fill();
    ctx.shadowBlur = 0;

    if (hot) {
      const dash = t * 0.00035 + idx * 0.2;
      ctx.setLineDash([2, 26]);
      ctx.lineDashOffset = -dash * 260;
      ctx.strokeStyle = "rgba(255,255,255,.95)";
      ctx.lineWidth = 2.4;
      ctx.stroke();
      ctx.setLineDash([]);
    }
    ctx.restore();
  });
}

function drawFloorRing(n) {
  const p = project(n.x, 0, n.z);
  const r = n.r * 1.55;
  ctx.save();
  ctx.beginPath();
  for (let i = 0; i <= 30; i++) {
    const a = (i / 30) * Math.PI * 2;
    const q = project(n.x + Math.cos(a) * r, 0, n.z + Math.sin(a) * r);
    i ? ctx.lineTo(q.x, q.y) : ctx.moveTo(q.x, q.y);
  }
  ctx.closePath();
  ctx.strokeStyle = "rgba(255,255,255,.55)";
  ctx.lineWidth = 1;
  ctx.stroke();
  ctx.fillStyle = "rgba(30,60,80,.10)";
  ctx.fill();
  ctx.restore();
}

function drawOrb(n, t) {
  const bob = Math.sin(t * 0.0011 + n.phase) * 7;
  const y = n.baseY + bob;
  const p = project(n.x, y, n.z);
  const hovered = hoverId === n.book.id || activeId === n.book.id;
  const R = n.r * p.s * (hovered ? 1.13 : 1);
  projected[n.book.id] = { x: p.x, y: p.y, r: R, s: p.s };

  drawFloorRing(n);

  // 光晕
  const glow = ctx.createRadialGradient(p.x, p.y, R * 0.2, p.x, p.y, R * 3.0);
  glow.addColorStop(0, rgba(n.color, hovered ? 0.7 : 0.46));
  glow.addColorStop(0.55, rgba(n.color, 0.12));
  glow.addColorStop(1, rgba(n.color, 0));
  ctx.fillStyle = glow;
  ctx.beginPath();
  ctx.arc(p.x, p.y, R * 3.0, 0, Math.PI * 2);
  ctx.fill();

  // 球体
  const g = ctx.createRadialGradient(p.x - R * 0.36, p.y - R * 0.42, R * 0.12, p.x, p.y, R * 1.04);
  g.addColorStop(0, rgba(mix(n.color, "#fff", 0.55), 1));
  g.addColorStop(0.45, rgba(n.color, 1));
  g.addColorStop(0.85, rgba(mix(n.color, "#000", 0.22), 1));
  g.addColorStop(1, rgba(mix(n.color, "#000", 0.5), 1));
  ctx.beginPath();
  ctx.arc(p.x, p.y, R, 0, Math.PI * 2);
  ctx.fillStyle = g;
  ctx.fill();

  // 球面纹理
  ctx.save();
  ctx.beginPath();
  ctx.arc(p.x, p.y, R - 0.6, 0, Math.PI * 2);
  ctx.clip();
  for (let i = 0; i < 3; i++) {
    const off = (i - 1) * R * 0.42;
    ctx.beginPath();
    ctx.ellipse(p.x, p.y + off, R * 1.02, R * 0.18, (i - 1) * 0.12, 0, Math.PI * 2);
    ctx.strokeStyle = rgba(mix(n.color, i % 2 ? "#fff" : "#000", 0.12), 0.5);
    ctx.lineWidth = R * 0.12;
    ctx.stroke();
  }
  ctx.restore();

  // 高光
  ctx.beginPath();
  ctx.arc(p.x - R * 0.34, p.y - R * 0.4, R * 0.26, 0, Math.PI * 2);
  ctx.fillStyle = "rgba(255,255,255,.45)";
  ctx.fill();

  // 名称
  const floor = project(n.x, 0, n.z);
  const fs = Math.max(14, 19 * p.s);
  ctx.save();
  ctx.textAlign = "center";
  ctx.textBaseline = "top";
  ctx.shadowColor = "rgba(255,255,255,.55)";
  ctx.shadowBlur = 6;
  ctx.fillStyle = hovered ? "rgba(10,26,34,.98)" : "rgba(16,32,42,.82)";
  if ("letterSpacing" in ctx) ctx.letterSpacing = "1.5px";
  ctx.font = "600 " + fs + "px 'Songti SC','Noto Serif SC',serif";
  ctx.fillText(n.book.title, floor.x, floor.y + 14 * p.s);
  ctx.shadowBlur = 0;
  ctx.fillStyle = "rgba(20,38,48,.55)";
  if ("letterSpacing" in ctx) ctx.letterSpacing = "0.6px";
  ctx.font = Math.max(10, fs * 0.68) + "px 'Songti SC','Noto Serif SC',serif";
  ctx.fillText(n.book.author, floor.x, floor.y + 14 * p.s + fs * 1.32);
  ctx.restore();
}

function render(t) {
  ctx.clearRect(0, 0, W, H);
  drawBackground();
  drawGrid();
  drawArcs(t);
  const order = nodes.map(n => ({ n, d: project(n.x, n.baseY, n.z).d })).sort((a, b) => b.d - a.d);
  order.forEach(o => drawOrb(o.n, t));
  requestAnimationFrame(render);
}

/* ---------------- 交互 ---------------- */
function hitTest(x, y) {
  let best = null, bestD = Infinity;
  Object.keys(projected).forEach(id => {
    const p = projected[id];
    const d = Math.hypot(x - p.x, y - p.y);
    if (d < Math.max(34, p.r * 1.6) && d < bestD) { best = id; bestD = d; }
  });
  return best;
}

canvas.addEventListener("pointerdown", e => {
  try { canvas.setPointerCapture(e.pointerId); } catch (err) {}
  pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
  dragStart = { x: e.clientX, y: e.clientY, yaw: view.yaw, pitch: view.pitch, dist: view.targetDist, moved: 0 };
  view.spin = false;
  setSpinBtn(false);
  if (pointers.size === 2) {
    const [a, b] = [...pointers.values()];
    dragStart.pinch = Math.hypot(a.x - b.x, a.y - b.y);
    dragStart.pinchDist = view.targetDist;
  }
});

canvas.addEventListener("pointermove", e => {
  const pt = pointers.get(e.pointerId);
  if (pt) {
    pt.x = e.clientX; pt.y = e.clientY;
    if (pointers.size === 2 && dragStart && dragStart.pinch) {
      const [a, b] = [...pointers.values()];
      const d = Math.hypot(a.x - b.x, a.y - b.y);
      view.targetDist = Math.max(1050, Math.min(3600, dragStart.pinchDist * dragStart.pinch / Math.max(d, 1)));
      return;
    }
    if (dragStart) {
      const dx = e.clientX - dragStart.x, dy = e.clientY - dragStart.y;
      dragStart.moved = Math.max(dragStart.moved, Math.hypot(dx, dy));
      view.yaw = dragStart.yaw + dx * 0.0055;
      view.pitch = Math.max(0.5, Math.min(1.28, dragStart.pitch - dy * 0.0022));
      if (dragStart.moved > 4) canvas.classList.add("dragging");
    }
    return;
  }
  const id = hitTest(e.clientX, e.clientY);
  canvas.style.cursor = id ? "pointer" : (linkMode ? "crosshair" : "grab");
  setHover(id, e.clientX, e.clientY);
});

canvas.addEventListener("pointerup", e => {
  pointers.delete(e.pointerId);
  canvas.classList.remove("dragging");
  if (dragStart && dragStart.moved < 6) {
    const id = hitTest(e.clientX, e.clientY);
    if (id) handleNodeClick(id);
    else if (panel.classList.contains("open")) closePanel();
  }
  dragStart = null;
});

canvas.addEventListener("pointercancel", () => { pointers.clear(); dragStart = null; canvas.classList.remove("dragging"); });

canvas.addEventListener("wheel", e => {
  e.preventDefault();
  view.targetDist = Math.max(1050, Math.min(3600, view.targetDist * Math.exp(e.deltaY * 0.0012)));
}, { passive: false });

canvas.addEventListener("pointerleave", () => setHover(null));

function setHover(id, x, y) {
  if (hoverId === id) { if (id) placeTip(x, y); return; }
  hoverId = id;
  if (!id) { tip.classList.remove("show"); return; }
  const n = nodes.find(n => n.book.id === id);
  const b = n.book;
  tip.innerHTML = "<b>" + esc(b.title) + "</b><br>" + esc(b.author) + (b.sectionCount ? " · " + b.sectionCount + " 节" : "");
  placeTip(x, y);
  tip.classList.add("show");
}

function placeTip(x, y) { tip.style.left = x + "px"; tip.style.top = y + "px"; }

function handleNodeClick(id) {
  if (linkMode) {
    if (!linkFrom) {
      linkFrom = id;
      activeId = id;
      showToast("再点一颗星，连成联想");
      return;
    }
    if (linkFrom === id) { linkFrom = null; activeId = null; return; }
    const exists = allLinks().some(l => (l.a === linkFrom && l.b === id) || (l.a === id && l.b === linkFrom));
    if (!exists) {
      localLinks.push({ a: linkFrom, b: id, why: "你的联想" });
      saveLinks();
      showToast("连上了");
    } else {
      showToast("这两颗星已经连着");
    }
    linkFrom = null;
    activeId = null;
    setLinkMode(false);
    return;
  }
  activeId = id;
  openPanel(id);
}

function openPanel(id) {
  const n = nodes.find(n => n.book.id === id);
  if (!n) return;
  const b = n.book;
  document.getElementById("p-title").textContent = b.title;
  document.getElementById("p-by").textContent = [b.author, b.publisher, b.year].filter(Boolean).join(" · ");
  const related = allLinks().filter(l => l.a === id || l.b === id).map(l => {
    const other = l.a === id ? l.b : l.a;
    const ob = DATA.books.find(x => x.id === other);
    return { title: ob ? ob.title : "", why: l.why, color: ob ? ob.color : "#888" };
  });
  const chs = b.chapters.map((c, i) => '<div class="chapter"><span class="n">' + String(i + 1).padStart(2, "0") + '</span><span>' + esc(c.title) + '</span></div>').join("");
  document.getElementById("panelBody").innerHTML =
    '<div class="facts">' +
      '<div class="fact"><b>' + (b.chapters.length || "—") + '</b><span>章</span></div>' +
      '<div class="fact"><b>' + b.sectionCount + '</b><span>节</span></div>' +
      '<div class="fact"><b>' + b.cards.length + '</b><span>卡片</span></div>' +
    '</div>' +
    '<h3>目录</h3>' +
    (chs || '<p class="muted">目录还没生成。翻开这本书之后，章节会出现在这里。</p>') +
    '<h3>联想</h3>' +
    (related.length ? '<div class="links">' + related.map(r => '<div class="linkrow"><i style="background:' + r.color + '"></i><span>' + esc(r.title) + '</span><span class="muted">' + esc(r.why) + '</span></div>').join("") + '</div>' : '<p class="muted">还没有连接。点右上角「连一条联想」，再点两颗星。</p>') +
    (localLinks.length ? '<button class="clearlinks" id="clearLinks">清除我连的线</button>' : '') +
    '<p class="panel-foot">' + esc(b.publisher) + ' · 进度会随阅读记录更新</p>';
  view.spin = false;
  setSpinBtn(false);
  panel.classList.add("open");
  panel.setAttribute("aria-hidden", "false");
  const clr = document.getElementById("clearLinks");
  if (clr) clr.addEventListener("click", () => {
    localLinks = []; saveLinks(); showToast("已清除"); openPanel(id);
  });
  document.getElementById("hintbar").classList.add("hidden");
}

function closePanel() {
  panel.classList.remove("open");
  panel.setAttribute("aria-hidden", "true");
  activeId = null;
  document.getElementById("hintbar").classList.remove("hidden");
}

document.getElementById("panelClose").addEventListener("click", closePanel);
addEventListener("keydown", e => { if (e.key === "Escape") closePanel(); });

/* ---------------- 按钮 ---------------- */
const spinBtn = document.getElementById("spinBtn");
const linkBtn = document.getElementById("linkBtn");
function setSpinBtn(on) { spinBtn.classList.toggle("on", on); spinBtn.textContent = on ? "自动旋转" : "已暂停"; }
spinBtn.addEventListener("click", () => { view.spin = !view.spin; setSpinBtn(view.spin); });

function setLinkMode(on) {
  linkMode = on;
  linkBtn.classList.toggle("on", on);
  linkBtn.textContent = on ? "选两颗星" : "连一条联想";
  canvas.classList.toggle("linkmode", on);
  if (!on) { linkFrom = null; }
}
linkBtn.addEventListener("click", () => setLinkMode(!linkMode));

document.getElementById("resetBtn").addEventListener("click", () => {
  view.targetDist = fitDist(); view.dist = fitDist();
  view.pitch = 1.0; view.targetPitch = 1.0;
  view.yaw = 0.42;
  view.spin = true; setSpinBtn(true);
  closePanel();
  setLinkMode(false);
});

let toastTimer = null;
function showToast(msg) {
  toast.textContent = msg;
  toast.classList.add("show");
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => toast.classList.remove("show"), 1800);
}

function esc(s) { return String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c])); }

/* ---------------- 主循环 ---------------- */
let lastTick = null;
function tick(t) {
  const dt = lastTick == null ? 16 : Math.min(64, t - lastTick);
  lastTick = t;
  if (view.spin) view.yaw += dt * 0.000055;
  view.pitch += (view.targetPitch - view.pitch) * 0.08;
  view.dist += (view.targetDist - view.dist) * 0.10;
  requestAnimationFrame(tick);
}

resize();
requestAnimationFrame(render);
requestAnimationFrame(tick);
setTimeout(() => hintbar.classList.add("hidden"), 9000);
</script>
</body>
</html>
"""

html = (TEMPLATE
        .replace("__COUNT__", str(len(books)))
        .replace("__DATA__", json.dumps(data, ensure_ascii=False)))

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("written", OUT, len(html), "bytes;", len(books), "books")
