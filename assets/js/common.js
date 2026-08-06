/* 公共工具：数据加载、格式化、导航高亮 */
"use strict";

/** 加载 JSON（data/ 下相对路径） */
async function loadJSON(path) {
  const resp = await fetch(path, { cache: "no-store" });
  if (!resp.ok) throw new Error(`加载失败 ${path}: HTTP ${resp.status}`);
  return resp.json();
}

/** 千分位格式化 */
function fmtInt(n) {
  if (n === null || n === undefined || isNaN(n)) return "—";
  return Number(n).toLocaleString("zh-CN");
}

/** 万TEU 格式化 */
function fmtTeu(n) {
  if (n === null || n === undefined) return "—";
  return `${Number(n).toLocaleString("zh-CN")} 万 TEU`;
}

/** 变化率 → 带颜色标签的 HTML */
function deltaHtml(pct, suffix = "%") {
  if (pct === null || pct === undefined) return '<span class="meta">—</span>';
  if (pct === 0) return `<span class="delta flat">持平</span>`;
  const cls = pct > 0 ? "up" : "down";
  const sign = pct > 0 ? "+" : "";
  return `<span class="delta ${cls}">${sign}${pct}${suffix}</span>`;
}

/** 顶部导航高亮当前页 */
function highlightNav() {
  const path = location.pathname.split("/").pop() || "index.html";
  document.querySelectorAll("header.nav a.page").forEach((a) => {
    if (a.getAttribute("href") === path) a.classList.add("active");
  });
}

/** 页面底部注入数据来源说明 */
function injectFooter() {
  const f = document.createElement("footer");
  f.innerHTML = `数据来源：UN/LOCODE、Drewry WCI、上海/宁波航运交易所、海关总署等，详见
    <a href="sources.html">数据源导航</a> · 数据更新时间见各页面顶部`;
  document.body.appendChild(f);
}

/** 展示数据更新时间（data.updated_at + 说明） */
function showUpdateTime(containerId, updatedAt, extra = "") {
  const c = document.getElementById(containerId);
  if (!c) return;
  const t = updatedAt || "未知";
  c.innerHTML = `数据更新时间：<b>${t}</b>${extra ? ` · ${extra}` : ""}`;
}

document.addEventListener("DOMContentLoaded", () => {
  highlightNav();
  injectFooter();
});
