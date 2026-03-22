#!/usr/bin/env python3
"""从 backend/app.py 导出与 GET /api/locations 一致的 locations.json，供 GitHub Pages 静态站使用。"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
FRONTEND = ROOT / "frontend"
sys.path.insert(0, str(BACKEND))

from app import OVERSEAS, PROVINCES  # noqa: E402


def main() -> None:
    provinces = []
    for pk, pv in PROVINCES.items():
        cities = [{"code": ck, "name": cv["name"]} for ck, cv in pv["cities"].items()]
        provinces.append({"code": pk, "name": pv["name"], "cities": cities})
    countries = []
    for ck, cv in OVERSEAS.items():
        cities = [{"code": cc, "name": ccv["name"]} for cc, ccv in cv["cities"].items()]
        countries.append({"code": ck, "name": cv["name"], "cities": cities})
    data = {"provinces": provinces, "countries": countries}
    out = FRONTEND / "locations.json"
    out.write_text(json.dumps(data, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print("Wrote", out)


if __name__ == "__main__":
    main()
