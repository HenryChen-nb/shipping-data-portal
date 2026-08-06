#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""抓取 UN/LOCODE 港口库并生成 data/ports.json。

数据源：datasets/un-locode（GitHub 镜像，CDN 优先）
- 全量 CSV -> 过滤 Function 含 Port(位置1=1)
- 合并 data/manual/top_ports.json（人工 TOP 港口，含中文名/吞吐量）
用法：
  python3 scripts/fetch_unlocode.py            # 联网下载并生成
  python3 scripts/fetch_unlocode.py --offline  # 使用本地缓存 data/cache/un-locode.csv
"""
import argparse
import csv
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache" / "un-locode.csv"
OUT = ROOT / "data" / "ports.json"
TOP_PORTS = ROOT / "data" / "manual" / "top_ports.json"

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
URLS = [
    "https://cdn.jsdelivr.net/gh/datasets/un-locode@main/data/code-list.csv",
    "https://raw.githubusercontent.com/datasets/un-locode/main/data/code-list.csv",
]


def download() -> Path:
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    for url in URLS:
        print(f"  下载 {url}")
        try:
            r = requests.get(url, headers={"User-Agent": UA}, timeout=120, stream=True)
            if r.status_code != 200:
                print(f"  HTTP {r.status_code}，尝试下一个源")
                continue
            with open(CACHE, "wb") as f:
                for chunk in r.iter_content(chunk_size=1 << 16):
                    f.write(chunk)
            print(f"  已保存 {CACHE} ({CACHE.stat().st_size/1e6:.1f} MB)")
            return CACHE
        except Exception as e:  # noqa: BLE001
            print(f"  失败: {type(e).__name__}: {e}")
    raise SystemExit("所有下载源均失败")


def parse_coord(coord: str):
    """'4230N 00131E' -> (42.5, 1.5167)；'51.95N 004.14E' -> (51.95, 4.14)"""
    if not coord:
        return None
    m = re.match(r"^\s*([\d.]+)\s*([NS])\s+([\d.]+)\s*([EW])\s*$", coord, re.I)
    if not m:
        return None
    lat_s, lat_d, lon_s, lon_d = m.groups()
    try:
        lat = float(lat_s) / 100 if "." not in lat_s else float(lat_s)
        lon = float(lon_s) / 100 if "." not in lon_s else float(lon_s)
    except ValueError:
        return None
    if lat_d.upper() == "S":
        lat = -lat
    if lon_d.upper() == "W":
        lon = -lon
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        return None
    return (round(lat, 4), round(lon, 4))


def load_top():
    with open(TOP_PORTS, encoding="utf-8") as f:
        return json.load(f)["ports"]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="使用本地缓存")
    args = ap.parse_args()

    if args.offline:
        if not CACHE.exists():
            raise SystemExit(f"缓存不存在: {CACHE}")
        print("离线模式，使用缓存")
    else:
        download()

    print("解析 CSV ...")
    ports = []
    country_set = set()
    with open(CACHE, encoding="utf-8", errors="replace") as f:
        rd = csv.DictReader(f)
        for row in rd:
            fn = (row.get("Function") or "").ljust(7)
            if not fn or fn[0] != "1":  # 仅保留 Port 功能
                continue
            locode = (row.get("Country", "") + row.get("Location", "")).strip().upper()
            if len(locode) != 5:
                continue
            coord = parse_coord(row.get("Coordinates") or "")
            country = row.get("Country", "").strip().upper()
            country_set.add(country)
            p = {
                "locode": locode,
                "country": country,
                "name_en": (row.get("NameWoDiacritics") or row.get("Name") or "").strip(),
                "subdivision": (row.get("Subdivision") or "").strip(),
            }
            if coord:
                p["lat"], p["lon"] = coord
            ports.append(p)
    print(f"  Port 功能条目: {len(ports)}，涉及国家/地区: {len(country_set)}")

    # 合并 TOP 港口
    top = load_top()
    by_locode = {p["locode"]: p for p in ports}
    top_out = []
    unmatched = []
    for t in top:
        locode = t["locode"].strip().upper()
        p = by_locode.get(locode)
        if p is None:
            # 尝试按英文名首词匹配
            key = t["name_en"].split()[0].lower()
            p = next((x for x in ports if x["name_en"].lower().startswith(key)
                      and x["country"] == locode[:2]), None)
        if p is None:
            unmatched.append(t)
            continue
        p["top"] = True
        p["name_cn"] = t["name_cn"]
        p["teu_2024"] = t["teu_2024"]
        if t.get("note"):
            p["note"] = t["note"]
        # CSV 缺坐标时采用人工坐标
        if "lat" not in p and t.get("lat") is not None:
            p["lat"], p["lon"] = t["lat"], t["lon"]
        top_out.append(p)

    # 无匹配的 TOP 港口作为附加条目（保留人工坐标；无坐标则前端隐藏地图点）
    extra = []
    for t in unmatched:
        e = {
            "locode": t["locode"].upper(), "country": t["locode"][:2],
            "name_en": t["name_en"], "name_cn": t["name_cn"],
            "top": True, "teu_2024": t["teu_2024"], "note": t.get("note", ""),
        }
        if t.get("lat") is not None and t.get("lon") is not None:
            e["lat"], e["lon"] = t["lat"], t["lon"]
        else:
            e["no_coord"] = True
        extra.append(e)
    print(f"  TOP 港口匹配: {len(top_out)}，未匹配(附加): {len(extra)}")
    if extra:
        print("  未匹配清单:", [e["name_cn"] for e in extra])

    data = {
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "source": "UN/LOCODE (datasets/un-locode GitHub 镜像) + 人工 TOP 清单",
        "source_url": "https://github.com/datasets/un-locode",
        "total": len(ports) + len(extra),
        "top_count": len(top_out) + len(extra),
        "ports": ports + extra,
    }
    OUT.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    print(f"已写出 {OUT} ({OUT.stat().st_size/1e6:.2f} MB)")


if __name__ == "__main__":
    sys.exit(main())
