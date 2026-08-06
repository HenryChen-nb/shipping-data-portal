/* 贸易数据页逻辑 */
"use strict";

function renderTradeTable(trade) {
  const tbody = document.getElementById("trade-table");
  const months = (trade.monthly || []).slice().reverse();
  tbody.innerHTML = months.map((m) => {
    const has = m.total !== null && m.total !== undefined;
    return `<tr>
      <td>${m.month}</td>
      <td>${has ? fmtInt(m.export) : "待更新"}</td>
      <td>${has ? fmtInt(m.import) : "待更新"}</td>
      <td><b>${has ? fmtInt(m.total) : "待更新"}</b></td>
    </tr>`;
  }).join("") || '<tr><td colspan="4" class="empty">暂无数据</td></tr>';
}

function renderPartnerTable(trade) {
  const tbody = document.getElementById("partner-table");
  tbody.innerHTML = (trade.partners || []).map((p) => `
    <tr>
      <td>${p.country}</td>
      <td>${p.share_pct !== null && p.share_pct !== undefined ? `${p.share_pct}%` : "待更新"}</td>
    </tr>`).join("") || '<tr><td colspan="2" class="empty">暂无数据</td></tr>';
}

function renderTradeChart(trade) {
  const chart = echarts.init(document.getElementById("trade-chart"));
  const months = (trade.monthly || []).slice().reverse();
  const hasData = months.some((m) => m.total !== null && m.total !== undefined);

  if (!hasData) {
    document.getElementById("trade-chart").innerHTML =
      `<div class="empty">暂无月度数据<br><span class="hint">请更新 data/manual/trade.json（来源：海关总署统计快讯）</span></div>`;
    return;
  }
  chart.setOption({
    tooltip: { trigger: "axis", valueFormatter: (v) => `${fmtInt(v)} 亿元` },
    legend: { data: ["出口", "进口"] },
    grid: { left: 70, right: 20, top: 40, bottom: 40 },
    xAxis: { type: "category", data: months.map((m) => m.month) },
    yAxis: { type: "value", name: "亿元" },
    series: [
      { name: "出口", type: "bar", data: months.map((m) => m.export), itemStyle: { color: "#1d4a7a" } },
      { name: "进口", type: "bar", data: months.map((m) => m.import), itemStyle: { color: "#c9a227" } },
    ],
  });
  window.addEventListener("resize", () => chart.resize());
}

async function init() {
  let trade;
  try {
    trade = await loadJSON("data/manual/trade.json");
  } catch (e) {
    document.getElementById("data-time").innerHTML = `<b style="color:#c53030">数据加载失败：${e.message}</b>`;
    return;
  }
  showUpdateTime("data-time", trade.updated_at, "人工维护，每月更新");
  document.getElementById("trade-source").href = trade.source_url || "#";
  renderTradeTable(trade);
  renderPartnerTable(trade);
  renderTradeChart(trade);
}

document.addEventListener("DOMContentLoaded", init);
