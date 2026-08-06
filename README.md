# 全球航运数据门户

聚合 **全球港口 · 主干航线 · 中国进出口贸易** 数据的轻量信息门户网站。

- 纯静态前端（HTML/CSS/JS，无构建步骤），数据为 JSON 文件
- 自动抓取（UN/LOCODE 港口库、Drewry WCI 运价）+ 人工维护（SCFI/CCFI/NCFI、海关贸易、航线、链接库）
- 所有数据点附权威来源链接

## 目录结构

```
site/
├── index.html           # 首页仪表盘（关键指标 + WCI 最新一期）
├── ports.html           # 港口地图（Leaflet 可视化 + 1.7 万+ 港口搜索）
├── routes.html          # 航线运价（指数卡片 + WCI 分航线图 + 主干航线）
├── trade.html           # 中国进出口贸易（月度数据 + 贸易伙伴）
├── sources.html         # 数据源导航（30+ 权威链接分类）
├── assets/              # css / js
├── data/
│   ├── ports.json       # 全球港口库（自动生成，1.7万+ 条，47 个 TOP 港）
│   ├── wci.json         # Drewry WCI 运价（自动抓取）
│   ├── manual/          # 人工维护数据（见下）
│   └── cache/           # 抓取缓存（UN/LOCODE CSV）
├── scripts/
│   ├── update_all.py    # 一键更新（抓取 + 校验）
│   ├── fetch_unlocode.py# 抓取 UN/LOCODE → ports.json
│   ├── fetch_wci.py     # 抓取 Drewry WCI → wci.json
│   ├── check_site.py    # 站点静态检查
│   └── deploy.sh        # 部署到 GitHub Pages
└── docs/data-sources.md # 数据源可行性报告
```

## 人工维护数据（data/manual/）

| 文件 | 内容 | 更新频率 |
|---|---|---|
| `top_ports.json` | 47 个主要港口（中文名/吞吐量/坐标/locode） | 低频 |
| `rates.json` | SCFI / CCFI / NCFI 最新一期数值 | 每周五 |
| `trade.json` | 中国月度进出口（海关总署）、贸易伙伴占比 | 每月 |
| `routes.json` | 10 条全球主干航线清单 | 低频 |
| `sources.json` | 权威数据源链接库 | 低频 |

> 说明：上海/宁波航运交易所官网历史数据需登录，SCFI/CCFI/NCFI 采用人工录入最新一期数值；海关总署官网直连被反爬，月度进出口数据人工录入。字段留 `null` 时页面显示"待更新"。

## 使用

```bash
# 1. 本地预览
cd site && python3 -m http.server 8000
# 浏览器打开 http://localhost:8000

# 2. 一键更新数据（联网）
python3 scripts/update_all.py
#   离线模式（UN/LOCODE 用缓存）
python3 scripts/update_all.py --offline

# 3. 静态检查
python3 scripts/check_site.py
```

## 一键打开

- **macOS**：双击 `打开网站.command` —— 线上可访问则直接打开 GitHub Pages，否则自动启动本地服务器并打开浏览器
- 或手动本地预览：`cd site && python3 -m http.server 8000` 后访问 http://localhost:8000

## 线上部署

已部署到 GitHub Pages：**https://henrychen-nb.github.io/shipping-data-portal/**

```bash
# 网络可直连 github.com 时，推送到 gh-pages 分支（传统方式）
./scripts/deploy.sh git@github.com:HenryChen-nb/shipping-data-portal.git "站点更新"
# 网络只能访问 api.github.com 时，用 REST API 上传到 main 分支（当前环境采用）
python3 scripts/deploy_api.py HenryChen-nb/shipping-data-portal <token>
```

## 数据来源

UN/LOCODE（开放数据）、Drewry WCI、上海航运交易所、宁波航运交易所、海关总署、商务部、国家统计局、交通运输部、船讯网、World Shipping Council、UNCTAD 等，完整清单见 [docs/data-sources.md](docs/data-sources.md) 与站内"数据源"页。

## 已知限制

- 官方指数/海关数据需登录或被反爬，采用人工维护 + 权威外链策略（详见 docs/data-sources.md）
- 地图瓦片与图表库来自 CDN（OpenStreetMap / ECharts），需联网加载
- WCI 解析依赖 Drewry 页面文本格式，官网改版后需适配 `fetch_wci.py`
