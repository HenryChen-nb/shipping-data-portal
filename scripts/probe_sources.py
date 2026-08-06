#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""数据源可用性探测脚本：测试候选免费源的 HTTP 可达性与内容结构。
用法：python3 scripts/probe_sources.py
输出：data/probe_report.json + 终端摘要
"""
import json
import re
import sys
import time
from pathlib import Path

import requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")
TIMEOUT = 20

# (名称, 类别, url, 说明)
SOURCES = [
    ("unece-locode", "港口-基础", "https://service.unece.org/trade/locode/",
     "联合国港口代码开放数据(首页，含全量 CSV 下载入口)"),
    ("portscom", "港口-基础", "https://ports.com/", "全球港口数据库"),
    ("sse-scfi", "运价指数", "https://www.sse.net.cn/", "上海航运交易所 SCFI/CCFI"),
    ("nbse-ncfi", "运价指数", "https://www.nbse.net.cn/", "宁波航运交易所 NCFI"),
    ("customs-stat", "中国贸易", "http://www.customs.gov.cn/customs/302249/zfxxgk/2799825/302274/302277/index.html",
     "海关总署-统计数据发布栏目"),
    ("mot-port", "港口-中国", "https://www.mot.gov.cn/", "交通运输部(港口吞吐量等)"),
    ("shipxy", "船舶动态AIS", "https://www.shipxy.com/", "船讯网 AIS(外链)"),
    ("worldshipping", "港口-吞吐量", "https://www.worldshipping.org/", "世界航运理事会(港口排名报告)"),
    ("freightos-fbx", "运价指数", "https://fbx.freightos.com/", "FBX 波罗的海运价指数"),
    ("seaintelligence", "航线-准班率", "https://www.sea-intelligence.com/", "Sea-Intelligence 准班率"),
    ("eesea", "航线-船期", "https://www.eesea.com/", "eeSea 船期/挂靠(部分免费)"),
    ("linerlytica", "港口-拥堵", "https://linerlytica.com/", "Linerlytica 集装箱市场报告"),
    ("gzw-ssc", "运价指数", "https://www.21cshipping.com/", "中国水运报/上海国际航运研究中心"),
    ("scio-stats", "中国贸易", "http://www.scio.gov.cn/", "国务院新闻办(贸易发布会)"),
    ("ndrc-belt", "航线-政策", "https://www.ndrc.gov.cn/", "发改委(一带一路/港口建设)"),
]

OUT = Path(__file__).resolve().parent.parent / "data" / "probe_report.json"


def probe(name: str, category: str, url: str, note: str) -> dict:
    result = {"name": name, "category": category, "url": url, "note": note,
              "ok": False, "status": None, "final_url": None,
              "content_type": None, "title": None, "error": None,
              "sample": None, "elapsed_s": None}
    try:
        t0 = time.time()
        resp = requests.get(url, headers={"User-Agent": UA}, timeout=TIMEOUT,
                            allow_redirects=True)
        result["elapsed_s"] = round(time.time() - t0, 1)
        result["status"] = resp.status_code
        result["final_url"] = resp.url
        result["content_type"] = resp.headers.get("Content-Type")
        result["ok"] = resp.status_code < 400 and len(resp.content) > 200
        text = resp.text[:20000]
        m = re.search(r"<title[^>]*>(.*?)</title>", text, re.S | re.I)
        if m:
            result["title"] = m.group(1).strip()[:120]
        # 提取可读文本片段
        plain = re.sub(r"<script.*?</script>|<style.*?</style>", " ", text, flags=re.S | re.I)
        plain = re.sub(r"<[^>]+>", " ", plain)
        plain = re.sub(r"\s+", " ", plain).strip()
        result["sample"] = plain[:160]
    except Exception as e:  # noqa: BLE001
        result["error"] = f"{type(e).__name__}: {e}"
    return result


def main() -> int:
    results = []
    for name, cat, url, note in SOURCES:
        print(f"[{name}] {url} ...", flush=True)
        results.append(probe(name, cat, url, note))
        time.sleep(0.5)  # 礼貌间隔
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n===== 摘要 =====")
    for r in results:
        mark = "OK " if r["ok"] else "FAIL"
        extra = r["title"] or r["error"] or r["sample"] or ""
        print(f"{mark} {r['name']:22s} [{r['category']}] status={r['status']} {extra[:80]}")
    print(f"\n报告已写入 {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
