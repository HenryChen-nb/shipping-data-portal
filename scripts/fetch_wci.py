#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取 Drewry World Container Index (WCI) 最新一期并生成 data/wci.json。

页面文本段落含结构化描述，如：
  "World Container Index (WCI) ... decreased 3% to $4,255 per 40ft container"
  "spot rates from Shanghai to Los Angeles declined 2% to $5,739 per 40ft container"
用法：python3 scripts/fetch_wci.py
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "wci.json"
URL = ("https://www.drewry.co.uk/supply-chain-advisors/supply-chain-expertise/"
       "world-container-index-assessed-by-drewry")
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")

# 航线名 -> 中文名
ROUTE_CN = {
    "Los Angeles": "上海-洛杉矶",
    "New York": "上海-纽约",
    "Genoa": "上海-热那亚",
    "Rotterdam": "上海-鹿特丹",
}

CHANGE_WORDS = r"(?:decreased|declined|increased|rose|fell|held steady|remained steady|up|down)"
NUM = r"\$([\d,]+)"


def _num(s: str):
    return int(s.replace(",", ""))


def parse(text: str) -> dict:
    # 评估段落：从 "Our detailed assessment" 到 "Spot freight rates"
    m = re.search(r"Our detailed assessment for ([^.]*?)(?:\s*The Drewry|\.\s*The Drewry)", text)
    if not m:
        m = re.search(r"Our detailed assessment for ([^\n]{0,200})", text)
    assessed = m.group(1).strip() if m else ""
    date_m = re.search(r"(\d{1,2}\s+[A-Z][a-z]{2}\s+\d{4})", assessed)
    assessed_on = date_m.group(1) if date_m else ""

    # 综合指数：WCI ... changed X% to $Y 或 held steady at $Y
    comp = None
    comp_change = None
    m = re.search(
        r"World Container Index \(WCI\)[^.]*?"
        r"(?:decreased|declined|increased|rose|fell)\s*(\d+)%\s*to\s*\$([\d,]+)", text)
    if m:
        comp = _num(m.group(2))
        comp_change = -int(m.group(1)) if "dec" in m.group(0) or "fell" in m.group(0) else int(m.group(1))
    else:
        m = re.search(r"World Container Index \(WCI\)[^.]*?held steady at \$([\d,]+)", text)
        if m:
            comp = _num(m.group(1))
            comp_change = 0

    # 评估段落（分航线解析只在此范围内进行，避免导航文本干扰）
    am = re.search(r"Our detailed assessment for .*?Spot freight rates by major route", text, re.S)
    seg = am.group(0) if am else text

    # 分航线：把句子按逗号/and/while 切分为子句，子句内恰含一条航线一个数值时配对
    # （解决同句含多条航线、数值前后语序不一的问题）
    def _clause_rate(anchor):
        """anchor: 航线名在 seg 中的位置。返回 (rate, change_pct) 或 None。"""
        s = max(seg.rfind(".", 0, anchor), seg.rfind(";", 0, anchor))  # 句首
        s = s + 1 if s >= 0 else 0
        e = seg.find(".", anchor)
        if e < 0:
            e = len(seg)
        sent = seg[s:e]
        # 计算每个子句在 sent 中的起始偏移（逗号前后均为数字时为千位分隔符，不切分）
        parts = list(re.split(r"((?<!\d),(?!\d)|;|\band\b|\bwhile\b)", sent))
        offset = 0
        for i in range(0, len(parts), 2):
            clause = parts[i]
            if anchor >= s + offset and anchor < s + offset + len(clause):
                break
            offset += len(clause) + (len(parts[i + 1]) if i + 1 < len(parts) else 0)
        rate_m = re.search(r"\$([\d,]+)", clause)
        if not rate_m:
            return None
        chg = None
        cm = re.search(r"(decreased|declined|increased|rose|fell)\s*(\d+)%", clause)
        if cm:
            chg = -int(cm.group(2)) if ("dec" in cm.group(1) or cm.group(1) == "fell") else int(cm.group(2))
        elif "held steady" in clause or "remained steady" in clause:
            chg = 0
        return _num(rate_m.group(1)), chg

    routes = []
    for en, cn in ROUTE_CN.items():
        for mpos in re.finditer(re.escape(en), seg):
            r = _clause_rate(mpos.start())
            if r:
                routes.append({"route": f"Shanghai-{en}", "route_cn": cn,
                               "rate_usd": r[0], "change_pct": r[1]})
                break
    return {"assessed_on": assessed_on, "assessed_text": assessed,
            "wci_composite": comp, "wci_change_pct": comp_change, "routes": routes}


def main() -> int:
    print(f"抓取 {URL}")
    r = requests.get(URL, headers={"User-Agent": UA}, timeout=60)
    r.raise_for_status()
    text = re.sub(r"\s+", " ", r.text)
    # 提取正文文本（去掉 script/style）
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(text, "html.parser")
    for tag in soup(["script", "style"]):
        tag.decompose()
    body = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))

    data = parse(body)
    if not data["routes"]:
        print("警告：未解析到分航线数据，保留原始文本片段供排查")
        data["raw_sample"] = body[:2000]

    data["updated_at"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    data["source"] = "Drewry World Container Index (WCI)"
    data["source_url"] = URL
    OUT.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"评估日期: {data['assessed_on']}")
    print(f"WCI 综合: {data.get('wci_composite')} (变化 {data.get('wci_change_pct')}%)")
    for rt in data["routes"]:
        print(f"  {rt['route_cn']:10s} ${rt['rate_usd']} ({rt['change_pct']}%)")
    print(f"已写出 {OUT}")
    return 0 if data["routes"] else 1


if __name__ == "__main__":
    sys.exit(main())
