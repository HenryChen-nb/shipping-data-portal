# 数据源可行性报告（阶段 1 产出）

> 探测日期：2026-08（脚本：`scripts/probe_sources.py` / `scripts/probe3.py` / `scripts/probe5_nav.py`，原始日志见 `docs/probe_logs/`）
> 结论先行：**免费源中能稳定自动抓取的只有 2 类（UN/LOCODE 港口库、Drewry WCI 运价）；中国官方指数/海关数据均需登录或反爬，采用"人工维护 JSON + 权威外链"策略。**

## 一、数据源矩阵

### A 类：自动抓取（已实测可用）

| 数据源 | 内容 | 方式 | 更新频率 |
|---|---|---|---|
| UN/LOCODE（GitHub 镜像 `datasets/un-locode`） | 全球港口/口岸代码库：代码、中英名、经纬度、国家、功能 | 全量 CSV 下载 → 过滤港口功能 | 一次性建库，季度刷新 |
| Drewry WCI（`drewry.co.uk`） | 全球集装箱运价指数最新一期（综合 + 8 条分航线） | HTML 解析 | 每周 |
| 上海航运交易所官网（`sse.net.cn`） | 20+ 航运指数**导航/简介**（CCFI/SCFI/CBFI/远东干散货等） | 仅外链（历史数值需登录） | - |
| 中远海运集运（`lines.coscoshipping.com`） | 船公司航线与服务 | 仅外链 | - |

### B 类：人工维护（JSON 半自动，脚本只做合并/校验）

| 数据 | 更新频率 | 数据来源（官网链接） |
|---|---|---|
| SCFI / CCFI / NCFI 最新数值 | 每周五 | 上海航运交易所、宁波航运交易所 |
| 中国海关月度进出口总值/国别 | 每月 | 海关总署（官网直连被反爬 412/SSL，人工录入） |
| 交通运输部港口吞吐量 | 每月 | 交通运输部官网 |
| 主干航线清单（8~10 条） | 低频 | 船公司航线表整理 |

### C 类：权威外链库（不抓取，链接展示）

AIS/船舶动态：船讯网、MarineTraffic、VesselFinder、HiFleet
航线/船期：Maersk、MSC、CMA CGM、中远海运、eeSea、Sea-Intelligence
指数/运价：上海航运交易所、宁波航运交易所、FBX、Drewry、波罗的海交易所
吞吐量/行业报告：UNCTAD、World Shipping Council、Linerlytica、中国港口网
中国贸易：海关总署、商务部、国家统计局、交通运输部

### D 类：探测失败/放弃（附原因）

| 源 | 原因 |
|---|---|
| service.unece.org（官方） | Cloudflare JS 挑战 403 |
| ports.com | 连接超时 |
| 海关总署 www.customs.gov.cn | https 证书异常 / http 返回 412 |
| 国家统计局数据 API data.stats.gov.cn | 403（反爬） |
| World Bank API | 502/超时 |
| 国新办 scio.gov.cn | 521 |
| 波罗的海交易所 | Cloudflare 验证 |
| 21cshipping.com / china-ports.org.cn / data.mofcom.gov.cn | 连接失败/SSL |

## 二、抓取策略

1. **港口库**：`fetch_unlocode.py` 下载 UN/LOCODE CSV，过滤 `Function` 含港口(1)或联运(6)的条目，与人工维护的 TOP 港口清单（含吞吐量、中文名）合并 → `data/ports.json`
2. **运价**：`fetch_wci.py` 解析 Drewry WCI 页面 → `data/wci.json`；SCFI/CCFI/NCFI 人工维护 → `data/manual/rates.json`
3. **贸易**：人工维护 → `data/manual/trade.json`（含海关官网链接）
4. **航线/链接**：人工维护 → `data/manual/routes.json`、`data/manual/sources.json`
5. **总入口**：`update_all.py` 依次执行抓取 + 合并人工数据，产出前端可读的全部 `data/*.json`

## 三、风险备注

- SCFI/CCFI 等官方指数历史序列需官网登录，本方案仅维护"最新一期"数值，历史走势依赖前端本地累积或外链
- 人工数据条目字段含 `updated_at`，前端展示"数据更新时间"，避免误导
- 所有数据点附 `source_url` 权威链接，可追溯
