/* 航线运价页逻辑 */
"use strict";

function renderIndexCards(rates, wci) {
  const box = document.getElementById("index-cards");
  const cards = [];
  // 人工指数
  (rates.indices || []).forEach((i) => {
    const hasVal = i.latest !== null && i.latest !== undefined;
    cards.push(`
      <div class="card">
        <h3>${i.name_cn}</h3>
        <div class="big">${hasVal ? fmtInt(i.latest) : "待更新"}</div>
        <div class="unit">${i.unit} · ${i.period}</div>
        <div class="meta">${hasVal ? deltaHtml(i.change_pct) : "请更新 data/manual/rates.json"}</div>
        <div class="meta"><a class="ext" href="${i.source_url}" target="_blank">来源 ↗</a></div>
      </div>`);
  });
  // WCI 综合
  cards.push(`
    <div class="card">
      <h3>WCI 综合运价（Drewry）</h3>
      <div class="big">$${fmtInt(wci.wci_composite)}</div>
      <div class="unit">美元/40尺箱 · 周度</div>
      <div class="meta">${deltaHtml(wci.wci_change_pct)} · 评估日 ${wci.assessed_on || "—"}</div>
      <div class="meta"><a class="ext" href="${wci.source_url}" target="_blank">来源 ↗</a></div>
    </div>`);
  box.innerHTML = cards.join("");
}

function renderWciChart(wci) {
  const chart = echarts.init(document.getElementById("wci-chart"));
  const names = (wci.routes || []).map((r) => r.route_cn);
  const values = (wci.routes || []).map((r) => r.rate_usd);
  chart.setOption({
    tooltip: { trigger: "axis", valueFormatter: (v) => `$${fmtInt(v)}` },
    grid: { left: 60, right: 20, top: 30, bottom: 40 },
    xAxis: { type: "category", data: names, axisLabel: { fontSize: 12 } },
    yAxis: { type: "value", axisLabel: { formatter: "$${value}" } },
    series: [{
      type: "bar",
      data: values,
      itemStyle: { color: "#1d4a7a", borderRadius: [4, 4, 0, 0] },
      label: { show: true, position: "top", formatter: (p) => fmtInt(p.value) },
    }],
  });
  window.addEventListener("resize", () => chart.resize());
}

function renderRouteCards(routes) {
  const box = document.getElementById("route-cards");
  box.innerHTML = (routes.routes || []).map((r) => `
    <div class="card">
      <h3>${r.name_cn}</h3>
      <p class="meta">${r.name_en} · 航程约 ${r.transit_days}</p>
      <p style="font-size:13px;margin:6px 0;"><b>途经：</b>${r.via}</p>
      <p style="font-size:13px;margin:6px 0;"><b>主要挂靠港：</b>
        ${(r.key_ports_cn || []).map((p) => `<span class="tag">${p}</span>`).join("")}
      </p>
      <p style="font-size:13px;margin:6px 0;"><b>主要船公司：</b>${(r.carriers || []).join("、")}</p>
      <p class="meta">运价参考：${r.rate_ref}${r.note ? ` · ${r.note}` : ""}</p>
    </div>`).join("");
}

async function init() {
  let wci, rates, routes;
  try {
    [wci, rates, routes] = await Promise.all([
      loadJSON("data/wci.json"),
      loadJSON("data/manual/rates.json"),
      loadJSON("data/manual/routes.json"),
    ]);
  } catch (e) {
    document.getElementById("data-time").innerHTML = `<b style="color:#c53030">数据加载失败：${e.message}</b>`;
    return;
  }
  showUpdateTime("data-time", [wci.updated_at, rates.updated_at, routes.updated_at].filter(Boolean).join(" / "));
  renderIndexCards(rates, wci);
  renderWciChart(wci);
  renderRouteCards(routes);
}

document.addEventListener("DOMContentLoaded", init);
