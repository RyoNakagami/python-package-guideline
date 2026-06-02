#!/usr/bin/env python3
"""
build-rules-catalog.py

book/ 配下の全 .qmd を直接パースして _book/rules-catalog.json を生成する CLI。

book プロジェクトは gfm 並列出力に非対応のため，.md を経由せず .qmd を直接読む。
front matter (rules 等) と本文 (TL;DR / allowed-mcp-read) の両方を .qmd から抽出する。

post-render フックから呼ばれる想定:
    project:
      post-render:
        - scripts/build-rules-catalog.py

抽出・正規化ロジックは scripts/rules_catalog.py に分離してあり (テスト対象)，
このファイルは I/O (読み込み・JSON 書き出し・stderr 出力) のみを担う。
許可リスト・制約の SST は scripts/schema-config.yml，catalog の検証は
scripts/lint-rules.py が担当する (build → lint の 2 段)。

rules フィールドを持たない章 (index.qmd, glossary.qmd 等) は自動スキップする。
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

# scripts/ を import パスに追加 (post-render フックは任意の cwd から呼ばれうる)
sys.path.insert(0, str(Path(__file__).resolve().parent))

from rules_catalog import (  # noqa: E402
    DEFAULT_RULE_ID_PATTERN,
    build_catalog,
    load_site_url,
    read_sources,
    rule_id_pattern_from_schema,
)

BOOK_DIR = Path("book")  # 章のルート (book/ 配下を再帰探索)
OUT = Path("_book/rules-catalog.json")  # 出力先 (resources で GH Pages にも公開)
QUARTO_YML = Path("_quarto.yml")
SCHEMA_CONFIG = Path(__file__).resolve().parent / "schema-config.yml"


def build() -> int:
    if not BOOK_DIR.exists():
        print(f"ERROR: {BOOK_DIR} が存在しません", file=sys.stderr)
        return 1

    site_url = ""
    if QUARTO_YML.exists():
        site_url = load_site_url(QUARTO_YML.read_text(encoding="utf-8"))

    rule_id_pattern = DEFAULT_RULE_ID_PATTERN
    if SCHEMA_CONFIG.exists():
        rule_id_pattern = rule_id_pattern_from_schema(
            SCHEMA_CONFIG.read_text(encoding="utf-8")
        )

    sources = read_sources(BOOK_DIR, root=Path("."))
    result = build_catalog(sources, site_url=site_url, rule_id_pattern=rule_id_pattern)

    catalog = result.catalog
    catalog["generated_at"] = datetime.now(timezone.utc).isoformat()

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(catalog, indent=2, ensure_ascii=False), encoding="utf-8")

    if result.warnings:
        print("WARNINGS:", file=sys.stderr)
        for w in result.warnings:
            print(f"  {w}", file=sys.stderr)

    print(
        f"Wrote {len(catalog['rules'])} rules, "
        f"{len(catalog['mcp_blocks'])} mcp_blocks, "
        f"{len(catalog['phase_inference'])} phase_inference entries "
        f"across {len(catalog['chapters'])} chapters"
    )
    print(f"site_url: {site_url or '(未設定)'}")
    return 0


if __name__ == "__main__":
    sys.exit(build())
