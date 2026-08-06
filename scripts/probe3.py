#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三轮探测：UN/LOCODE 镜像、统计局国家数据 API、SSE/NCFI 指数页内容。"""
import json
import re
import time
from pathlib import Path

import requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
H = {"User-Agent": UA, "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8"}

OUT = Path(__file__).resolve().parent.parent / "data" / "probe_report3.json"


def probe(name, cat, url, headers=None, expect_json=False):
    try:
        r = requests.get(url, headers=headers or H, timeout=30, allow_redirects=True)
        body = r.text[:60000]
        info = {"ok": r.status_code < 400 and len(r.content) > 100,
                "status": r.status_code, "final": r.url, "note": ""}
        if expect_json:
            try:
                j = r.json()
                info["json_sample"] = json.dumps(j, ensure_ascii=False)[:400]
            except Exception as e:  # noqa: BLE001
                info["note"] = f"JSON解析失败: {e}"
                info["json_sample"] = body[:200]
        else:
            m = re.search(r"<title[^>]*>(.*?)</title>", body, re.S | re.I)
            if m:
                info["title"] = m.group(1).strip()[:100]
            plain = re.sub(r"<script.*?</script>|<style.*?</style>", " ", body, flags=re.S | re.I)
            plain = re.sub(r"<[^>]+>", " ", plain)
            plain = re.sub(r"\s+", " ", plain).strip()
            info["text_sample"] = plain[:300]
        return {"name": name, "category": cat, "url": url, **info}
    except Exception as e:  # noqa: BLE001
        return {"name": name, "category": cat, "url": url, "ok": False,
                "status": None, "error": f"{type(e).__name__}: {e}"}


def main():
    results = []
    # 1. UN/LOCODE GitHub 镜像 (datasets/un-locode)
    results.append(probe("un-locode-gh", "港口-基础",
                         "https://raw.githubusercontent.com/datasets/un-locode/main/README.md"))
    results.append(probe("un-locode-gh-csv", "港口-基础",
                         "https://raw.githubusercontent.com/datasets/un-locode/main/data/code-list.csv"))
    # 2. 统计局国家数据 API：海关月度进出口总额 (dbcode=hgyd, zb=A0801)
    url_stats = ("https://data.stats.gov.cn/easyquery.htm?m=QueryData&dbcode=hgyd"
                 "&rowcode=zb&colcode=sj&wds=[]"
                 '&dfwds=[{"wdcode":"zb","valuecode":"A0801"}]')
    results.append(probe("stats-hgyd", "中国贸易", url_stats, expect_json=True))
    # 3. 统计局国家数据 API：海关月度进出口(美元计价 dbcode=hgyd, zb=A0802 出口 A0803 进口)
    url_export = url_stats.replace('"A0801"', '"A0802"')
    results.append(probe("stats-hgyd-exp", "中国贸易", url_export, expect_json=True))
    # 4. SSE 首页内容（找 SCFI/CCFI 数值）
    results.append(probe("sse-home", "运价指数", "https://www.sse.net.cn/"))
    # 5. 宁波 NCFI 指数发布页面
    results.append(probe("nbse-ncfi-page", "运价指数",
                         "https://www.nbse.net.cn/web/nbse/front/index/index.jsp"))
    results.append(probe("nbse-home", "运价指数", "https://www.nbse.net.cn/"))
    # 6. 交通运输部统计信息栏目
    results.append(probe("mot-stats", "港口-中国", "https://www.mot.gov.cn/tongjishuju/"))
    # 7. 商务部统计资料栏目
    results.append(probe("mofcom-stats", "中国贸易",
                         "http://www.mofcom.gov.cn/article/tongjiziliao/"))
    # 8. 世界银行开放数据 API（港口吞吐量等宏观数据，备用）
    results.append(probe("worldbank-api", "港口-吞吐量",
                         "https://api.worldbank.org/v2/country/CN/indicator/IS.SHP.GOOD.TU?format=json",
                         expect_json=True))
    # 9. Drewry WCI 页面
    results.append(probe("drewry-wci", "运价指数",
                         "https://www.drewry.co.uk/supply-chain-advisors/supply-chain-expertise/"
                         "world-container-index-assessed-by-drewry"))
    OUT.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print("\n===== 摘要 =====")
    for r in results:
        mark = "OK " if r.get("ok") else "FAIL"
        extra = (r.get("title") or r.get("json_sample") or r.get("text_sample")
                 or r.get("error") or "")
        print(f"{mark} {r['name']:18s} [{r['category']}] status={r.get('status')} {extra[:90]}")
    print(f"\n报告已写入 {OUT}")


if __name__ == "__main__":
    main()
