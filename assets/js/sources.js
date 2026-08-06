/* 数据源导航页逻辑 */
"use strict";

async function init() {
  let sources;
  try {
    sources = await loadJSON("data/manual/sources.json");
  } catch (e) {
    document.getElementById("data-time").innerHTML = `<b style="color:#c53030">数据加载失败：${e.message}</b>`;
    return;
  }
  showUpdateTime("data-time", sources.updated_at, "人工维护");
  const box = document.getElementById("source-cats");
  box.innerHTML = (sources.categories || []).map((cat) => `
    <div class="card" style="margin-bottom:16px;">
      <h3>${cat.category}</h3>
      <div class="grid cols-2" style="gap:10px;">
        ${(cat.items || []).map((it) => `
          <div style="padding:8px 10px;border:1px solid var(--border);border-radius:8px;">
            <a class="ext" href="${it.url}" target="_blank" style="font-weight:600;">${it.name}</a>
            <p class="meta" style="font-size:12px;margin-top:2px;">${it.desc || ""}</p>
          </div>`).join("")}
      </div>
    </div>`).join("");
}

document.addEventListener("DOMContentLoaded", init);
