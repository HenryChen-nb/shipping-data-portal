#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一键更新脚本：抓取自动数据 + 校验人工数据。

步骤：
  1. 抓取 UN/LOCODE 港口库（--offline 时用缓存）
  2. 抓取 Drewry WCI 运价
  3. 校验 data/manual/*.json 可解析且字段完整
用法：
  python3 scripts/update_all.py
  python3 scripts/update_all.py --offline
"""
import argparse
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
MANUAL = ROOT / "data" / "manual"

# 人工数据文件 -> 必填顶层字段
MANUAL_CHECKS = {
    "top_ports.json": ["ports"],
    "rates.json": ["indices"],
    "trade.json": ["monthly"],
    "routes.json": ["routes"],
    "sources.json": ["categories"],
}


def run(script: str, extra: list) -> int:
    print(f"\n=== 运行 {script} {' '.join(extra)} ===")
    return subprocess.call([sys.executable, str(SCRIPTS / script), *extra])


def validate_manual() -> bool:
    ok = True
    for name, fields in MANUAL_CHECKS.items():
        p = MANUAL / name
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:  # noqa: BLE001
            print(f"  [FAIL] {name} 解析失败: {e}")
            ok = False
            continue
        missing = [f for f in fields if f not in data]
        if missing:
            print(f"  [FAIL] {name} 缺少字段: {missing}")
            ok = False
        else:
            print(f"  [OK] {name} 字段完整")
    return ok


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--offline", action="store_true", help="UN/LOCODE 使用本地缓存")
    ap.add_argument("--skip-fetch", action="store_true", help="跳过网络抓取，仅校验人工数据")
    args = ap.parse_args()

    code = 0
    if not args.skip_fetch:
        code |= run("fetch_unlocode.py", ["--offline"] if args.offline else [])
        code |= run("fetch_wci.py", [])
    else:
        print("跳过网络抓取")

    print("\n=== 校验人工数据 ===")
    if not validate_manual():
        code |= 1

    # 汇总
    summary = {"updated_at": __import__("datetime").datetime.now().strftime("%Y-%m-%d %H:%M"),
               "files": {}}
    for p in sorted((ROOT / "data").glob("*.json")):
        try:
            summary["files"][p.name] = p.stat().st_size
        except OSError:
            pass
    (ROOT / "data" / "manifest.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    print("\n=== 更新完成 ===")
    if code:
        print("有步骤失败，请检查上方输出")
    else:
        print("全部成功")
    return code


if __name__ == "__main__":
    sys.exit(main())
