/* 港口地图页逻辑 */
"use strict";

const COUNTRY_CN = {
  CN: "中国", SG: "新加坡", KR: "韩国", AE: "阿联酋", MY: "马来西亚", HK: "中国香港",
  NL: "荷兰", BE: "比利时", TW: "中国台湾", TH: "泰国", DE: "德国", VN: "越南",
  LK: "斯里兰卡", US: "美国", IN: "印度", BR: "巴西", GR: "希腊", ES: "西班牙",
  GB: "英国", CA: "加拿大", MX: "墨西哥", PA: "巴拿马", CO: "哥伦比亚", AU: "澳大利亚",
  ZA: "南非", BD: "孟加拉国", ID: "印度尼西亚", MA: "摩洛哥", FR: "法国", IT: "意大利",
  JP: "日本", RU: "俄罗斯", CL: "智利", PE: "秘鲁", EG: "埃及", SA: "沙特",
  TR: "土耳其", QA: "卡塔尔", KW: "科威特", OM: "阿曼", PH: "菲律宾", NZ: "新西兰",
};

let map = null;
let portData = null;
const topMarkers = [];

function countryCn(code) { return COUNTRY_CN[code] || code; }

function portName(p) { return p.name_cn || p.name_en; }

function radiusFor(teu) {
  if (!teu) return 8;
  if (teu >= 1500) return 22;
  if (teu >= 600) return 15;
  return 9;
}

function colorFor(teu) {
  if (!teu) return "#1d4a7a";
  if (teu >= 1500) return "#c53030";
  if (teu >= 600) return "#c9a227";
  return "#1d4a7a";
}

function renderDetail(p) {
  const d = document.getElementById("port-detail");
  const teu = p.teu_2024 ? fmtTeu(p.teu_2024) : "—";
  const coord = (p.lat !== undefined && p.lon !== undefined)
    ? `${p.lat.toFixed(4)}, ${p.lon.toFixed(4)}` : "无坐标";
  d.innerHTML = `
    <h3>${portName(p)}</h3>
    <p class="meta">${p.locode} · ${countryCn(p.country)} ${p.subdivision || ""}</p>
    <table class="data" style="margin-top:8px;">
      <tbody>
        <tr><td>英文名</td><td>${p.name_en}</td></tr>
        <tr><td>吞吐量</td><td><b>${teu}</b></td></tr>
        <tr><td>坐标</td><td>${coord}</td></tr>
        <tr><td>港口代码</td><td>${p.locode}</td></tr>
        ${p.note ? `<tr><td>备注</td><td>${p.note}</td></tr>` : ""}
      </tbody>
    </table>
    <p class="meta" style="margin-top:8px;">
      数据来源：<a class="ext" href="https://service.unece.org/trade/locode/" target="_blank">UN/LOCODE</a>
      · 吞吐量：人工维护（约数）
    </p>`;
}

function renderTopTable() {
  const tops = portData.ports.filter((p) => p.top && p.teu_2024 !== undefined)
    .sort((a, b) => b.teu_2024 - a.teu_2024);
  const tbody = document.querySelector("#top-table tbody");
  tbody.innerHTML = tops.map((p, i) => `
    <tr style="cursor:pointer;" onclick="focusPort('${p.locode}')">
      <td>${i + 1}</td>
      <td><b>${portName(p)}</b></td>
      <td>${p.locode}</td>
      <td>${countryCn(p.country)}</td>
      <td>${fmtTeu(p.teu_2024)}</td>
      <td>${p.note || ""}</td>
    </tr>`).join("");
}

function initMap() {
  map = L.map("map-full", { worldCopyJump: true }).setView([20, 90], 2);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 18,
    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>',
  }).addTo(map);

  portData.ports.filter((p) => p.top && p.lat !== undefined && p.lon !== undefined)
    .forEach((p) => {
      const m = L.circleMarker([p.lat, p.lon], {
        radius: radiusFor(p.teu_2024),
        color: "#fff", weight: 1.5,
        fillColor: colorFor(p.teu_2024), fillOpacity: 0.85,
      }).addTo(map);
      m.bindPopup(`
        <b>${portName(p)}</b> (${p.locode})<br>
        ${countryCn(p.country)} · ${p.teu_2024 ? fmtTeu(p.teu_2024) : "吞吐量—"}<br>
        <small>${p.name_en}</small>`);
      m.on("click", () => renderDetail(p));
      topMarkers.push({ locode: p.locode, marker: m });
    });
}

function focusPort(locode) {
  const p = portData.ports.find((x) => x.locode === locode);
  if (!p) return;
  if (p.lat !== undefined && p.lon !== undefined) {
    map.flyTo([p.lat, p.lon], 5);
  }
  renderDetail(p);
  const tm = topMarkers.find((x) => x.locode === locode);
  if (tm) tm.marker.openPopup();
  document.getElementById("port-detail").scrollIntoView({ behavior: "smooth", block: "start" });
}

function doSearch() {
  const q = (document.getElementById("port-search").value || "").trim().toLowerCase();
  const box = document.getElementById("search-results");
  const count = document.getElementById("search-count");
  if (!q) { box.innerHTML = ""; count.textContent = ""; return; }
  const hits = portData.ports.filter((p) =>
    (p.name_cn && p.name_cn.toLowerCase().includes(q)) ||
    (p.name_en && p.name_en.toLowerCase().includes(q)) ||
    (p.locode && p.locode.toLowerCase() === q) ||
    (p.locode && p.locode.toLowerCase().includes(q))
  ).slice(0, 60);
  count.textContent = `共 ${hits.length} 条`;
  if (!hits.length) { box.innerHTML = '<p class="empty">未找到匹配港口</p>'; return; }
  box.innerHTML = hits.map((p) => `
    <div style="padding:7px 4px;border-bottom:1px solid var(--border);cursor:pointer;font-size:13px;"
         onclick="focusPort('${p.locode}')">
      <b>${portName(p)}</b> <span class="meta">${p.locode} · ${countryCn(p.country)}</span>
      ${p.teu_2024 ? `<span class="tag cny">${fmtTeu(p.teu_2024)}</span>` : ""}
      <span class="meta" style="float:right;">${p.lat !== undefined ? "📍" : "无坐标"}</span>
    </div>`).join("");
}

async function init() {
  try {
    portData = await loadJSON("data/ports.json");
  } catch (e) {
    document.getElementById("data-time").innerHTML = `<b style="color:#c53030">数据加载失败：${e.message}</b>`;
    return;
  }
  showUpdateTime("data-time", portData.updated_at, `共 ${fmtInt(portData.total)} 个港口`);
  initMap();
  renderTopTable();
  document.getElementById("btn-search").addEventListener("click", doSearch);
  document.getElementById("port-search").addEventListener("keydown", (e) => {
    if (e.key === "Enter") doSearch();
  });
}

document.addEventListener("DOMContentLoaded", init);
