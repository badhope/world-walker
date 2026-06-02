"""
Regenerate data/cities/cities.yaml from any code-side seed data.

Use this when:
  - You want to add a new city
  - You want to update a metric value
  - You want to bump the version / last_updated date

Usage:
    python scripts/regen_cities_yaml.py
    python scripts/regen_cities_yaml.py --version 2025.06
    python scripts/regen_cities_yaml.py --out data/cities/cities_test.yaml
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Dict

import yaml

# Make backend importable when run from project root
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.data import city_data as cd  # noqa: E402


def _build_doc(version: str) -> Dict[str, Any]:
    """Build the YAML document from the in-memory city_data module."""
    return {
        "_meta": {
            "version": version,
            "last_updated": cd.DATA_SOURCE_INFO.get("last_updated", "2024-12-31"),
            "city_count": len(cd.CITY_DATA),
            "sources": cd.DATA_SOURCE_INFO.get("sources", []),
            "update_frequency": cd.DATA_SOURCE_INFO.get("update_frequency", "年度"),
            "license": cd.DATA_SOURCE_INFO.get("license", "内部使用 / Internal use only"),
        },
        "score_weights": cd.SCORE_WEIGHTS,
        "cities": cd.CITY_DATA,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default=str(ROOT / "data" / "cities" / "cities.yaml"),
        help="Output YAML path",
    )
    parser.add_argument(
        "--version",
        default=cd.DATA_SOURCE_INFO.get("version", "2024.12"),
        help="Version string to write into the YAML header",
    )
    args = parser.parse_args()

    doc = _build_doc(args.version)
    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as fh:
        yaml.dump(doc, fh, allow_unicode=True, sort_keys=False, default_flow_style=False)

    print(f"✅ Wrote {len(cd.CITY_DATA)} cities to {out_path}")
    print(f"   version: {args.version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
