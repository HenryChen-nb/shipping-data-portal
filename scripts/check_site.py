#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""站点静态检查：HTML 资源引用完整性 + 数据 JSON 合法性。

用法：python3 scripts/check_site.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
errors = []
ok_count = 0


def check(cond, msg):
    global ok_count
    if cond:
        ok_count += 1
    else:
        errors.append(msg)


def main() -> int:
    # 1. HTML 资源引用完整性
    for html in sorted(ROOT.glob("*.html")):
        text = html.read_text(encoding="utf-8")
        refs = set()
        refs.update(re.findall(r'(?:href|src)="(assets/[^"]+)"', text))
        refs.update(re.findall(r'(?:href|src)="(data/[^"]+)"', text))
        for ref in sorted(refs):
            p = ROOT / ref
            check(p.exists(), f"{html.name} 引用的资源不存在: {ref}")
        check("<title>" in text, f"{html.name} 缺少 <title>")
        check('class="nav"' in text, f"{html.name} 缺少导航栏")
        check("common.js" in text, f"{html.name} 缺少 common.js")

    # 2. 数据 JSON 合法性 + 必要字段
    json_checks = [
        ("data/ports.json", ("updated_at", "ports")),
        ("data/wci.json", ("updated_at", "wci_composite", "routes")),
        ("data/manual/rates.json", ("indices",)),
        ("data/manual/trade.json", ("monthly",)),
        ("data/manual/routes.json", ("routes",)),
        ("data/manual/sources.json", ("categories",)),
    ]
    for rel, fields in json_checks:
        p = ROOT / rel
        check(p.exists(), f"数据文件缺失: {rel}")
        if not p.exists():
            continue
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            check(False, f"{rel} JSON 解析失败: {e}")
            continue
        for f in fields:
            check(f in data, f"{rel} 缺少字段: {f}")

    # 3. 数据一致性：TOP 港口都有坐标与吞吐量
    ports = json.loads((ROOT / "data/ports.json").read_text(encoding="utf-8"))
    tops = [p for p in ports["ports"] if p.get("top")]
    check(len(tops) >= 40, f"TOP 港口数量异常: {len(tops)}")
    for p in tops:
        check("lat" in p and "lon" in p, f"TOP 港口缺坐标: {p['locode']}")
        check("teu_2024" in p, f"TOP 港口缺吞吐量: {p['locode']}")
        check("name_cn" in p, f"TOP 港口缺中文名: {p['locode']}")

    wci = json.loads((ROOT / "data/wci.json").read_text(encoding="utf-8"))
    check(len(wci["routes"]) >= 3, f"WCI 航线数据过少: {len(wci['routes'])} 条")

    print(f"检查项通过: {ok_count}，失败: {len(errors)}")
    for e in errors:
        print(f"  [FAIL] {e}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
