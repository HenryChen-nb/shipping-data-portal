#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第五轮：解析 sse/nbse/mot 首页导航链接，找指数与统计栏目真实路径。"""
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
OUT = Path(__file__).resolve().parent.parent / "data" / "nav_links.json"

TARGETS = {
    "sse": "https://www.sse.net.cn/",
    "nbse": "https://www.nbse.net.cn/",
    "mot": "https://www.mot.gov.cn/",
}

KEYWORDS = ["指数", "SCFI", "CCFI", "NCFI", "统计", "吞吐量", "运价", "公告",
            "数据", "新闻", "信息", "发布"]


def main():
    nav = {}
    for key, url in TARGETS.items():
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=30)
            soup = BeautifulSoup(r.text, "html.parser")
            links = []
            for a in soup.find_all("a", href=True):
                text = a.get_text(strip=True)
                href = a["href"]
                if not text:
                    continue
                full = href if href.startswith("http") else (
                    url.rstrip("/") + ("/" + href.lstrip("/") if not href.startswith("#") else ""))
                links.append({"text": text, "href": full})
            # 按关键词过滤
            hit = [l for l in links if any(k in l["text"] for k in KEYWORDS)]
            nav[key] = {"url": url, "title": (soup.title.get_text(strip=True) if soup.title else ""),
                        "total_links": len(links), "keyword_links": hit[:40]}
            print(f"\n=== {key} ({len(links)} 链接) ===")
            for l in hit[:40]:
                print(f"  {l['text'][:40]:42s} -> {l['href'][:90]}")
        except Exception as e:  # noqa: BLE001
            nav[key] = {"url": url, "error": str(e)}
            print(f"\n=== {key} 失败: {e}")
        time.sleep(0.5)
    OUT.write_text(__import__("json").dumps(nav, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n导航链接已写入 {OUT}")


if __name__ == "__main__":
    main()
