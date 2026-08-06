/* 首页仪表盘逻辑 */
"use strict";

function kpiCard(title, value, unit, extra) {
  return `<div class="card">
    <h3>${title}</h3>
    <div class="big">${value}</div>
    <div class="unit">${unit}</div>
    ${extra || ""}
  </div>`;
}

async function init() {
  let wci = null, ports = null, rates = null, routes = null, trade = null, manifest = null;
  try { [wci, ports, rates, routes, trade, manifest] = await Promise.all([
    loadJSON("data/wci.json"),
    loadJSON("data/ports.json"),
    loadJSON("data/manual/rates.json"),
    loadJSON("data/manual/routes.json"),
    loadJSON("data/manual/trade.json"),
    loadJSON("data/manifest.json"),
  ]); } catch (e) {
    document.getElementById("data-time").innerHTML = `<b style="color:#c53030">数据加载失败：${e.message}</b>`;
    return;
  }

  // 更新时间
  const times = [wci.updated_at, ports.updated_at, rates.updated_at,
                 trade.updated_at, routes.updated_at].filter(Boolean);
  showUpdateTime("data-time", times.join(" / "), "人工数据以 manual/ 内 updated_at 为准");

  // KPI 卡片
  const scfi = rates.indices.find((i) => i.code === "SCFI");
  const ccfi = rates.indices.find((i) => i.code === "CCFI");
  const idxVal = (idx) => (idx && idx.latest !== null && idx.latest !== undefined);
  const kpi = document.getElementById("kpi");
  kpi.innerHTML = [
    kpiCard("WCI 综合运价", wci.wci_composite ? `$${fmtInt(wci.wci_composite)}` : "—",
      "美元/40尺箱",
      `<div class="meta">${deltaHtml(wci.wci_change_pct)} · 评估日 ${wci.assessed_on || "—"}</div>`),
    kpiCard("SCFI 上海出口指数", idxVal(scfi) ? fmtInt(scfi.latest) : "待更新",
      "点 · 周度",
      idxVal(scfi) ? `<div class="meta">${deltaHtml(scfi.change_pct)}</div>` : `<div class="meta">每周五发布，人工维护</div>`),
    kpiCard("CCFI 中国出口指数", idxVal(ccfi) ? fmtInt(ccfi.latest) : "待更新",
      "点 · 周度",
      idxVal(ccfi) ? `<div class="meta">${deltaHtml(ccfi.change_pct)}</div>` : `<div class="meta">每周五发布，人工维护</div>`),
    kpiCard("全球港口数", fmtInt(ports.total), "个（UN/LOCODE）",
      `<div class="meta">TOP 主要港口 ${ports.top_count} 个</div>`),
  ].join("");

  // WCI 详情卡片
  const wciCard = document.getElementById("wci-card");
  const rows = (wci.routes || []).map((r) => `
    <tr>
      <td>${r.route_cn}</td>
      <td><b>$${fmtInt(r.rate_usd)}</b></td>
      <td>${deltaHtml(r.change_pct)}</td>
    </tr>`).join("");
  wciCard.innerHTML = `
    <div style="display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px;margin-bottom:12px;">
      <div>综合指数 <b style="font-size:20px;">$${fmtInt(wci.wci_composite)}</b> ${deltaHtml(wci.wci_change_pct)}</div>
      <div class="meta">评估日期：${wci.assessed_on || "—"} · 更新于 ${wci.updated_at || "—"}</div>
    </div>
    <table class="data">
      <thead><tr><th>航线</th><th>运价（美元/40尺箱）</th><th>周环比</th></tr></thead>
      <tbody>${rows || '<tr><td colspan="3" class="empty">暂无数据</td></tr>'}</tbody>
    </table>
    <p class="meta" style="margin-top:10px;">来源：<a class="ext" href="${wci.source_url}" target="_blank">Drewry World Container Index</a></p>`;
}

document.addEventListener("DOMContentLoaded", init);
