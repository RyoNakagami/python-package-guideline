"""
lint-rules.py

_book/rules-catalog.json を schema-config.yml の許可リスト・制約に照らして検証する。

入力は catalog (= rules を持つ章だけ) なので、rules を持たない章
(index.qmd, glossary.qmd 等) は検証対象に入らず、誤検知しない。

使い方:
    uv run python scripts/lint-rules.py
    uv run python scripts/lint-rules.py --catalog path/to/rules-catalog.json

違反があれば一覧を表示して終了コード 1。warning のみなら 0。
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

SCHEMA_CONFIG = Path(__file__).parent / "schema-config.yml"
DEFAULT_CATALOG = Path("_book/rules-catalog.json")


# ---------------------------------------------------------------------------
# 設定読み込み
# ---------------------------------------------------------------------------


def load_schema_config() -> dict:
    """許可リストと制約を schema-config.yml から読む (build-catalog と共有)。"""
    with SCHEMA_CONFIG.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


# ---------------------------------------------------------------------------
# 検証結果
# ---------------------------------------------------------------------------


class Report:
    """エラー (致命) と warning (非致命) を蓄積する。"""

    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, where: str, msg: str) -> None:
        self.errors.append(f"[ERROR] {where}: {msg}")

    def warn(self, where: str, msg: str) -> None:
        self.warnings.append(f"[WARN]  {where}: {msg}")

    def print_and_exit(self) -> int:
        for w in self.warnings:
            print(w, file=sys.stderr)
        for e in self.errors:
            print(e, file=sys.stderr)
        n_e, n_w = len(self.errors), len(self.warnings)
        print(f"\nlint: {n_e} error(s), {n_w} warning(s)", file=sys.stderr)
        return 1 if n_e else 0


# ---------------------------------------------------------------------------
# 個別チェック
# ---------------------------------------------------------------------------


def check_rules(catalog: dict, schema: dict, rep: Report) -> None:
    rules = catalog.get("rules", [])
    rule_ids = {r["id"] for r in rules if r.get("id")}

    valid_phases = set(schema["phases"])
    valid_severity = set(schema["severities"])
    valid_rule_types = set(schema["rule_types"])
    valid_relation = set(schema["relation_types"])
    valid_maturity = set(schema["maturities"])
    valid_categories = set(schema["categories"])
    c = schema["constraints"]
    rule_id_re = re.compile(c["rule_id_pattern"])
    smin, smax = c["statement_min_len"], c["statement_max_len"]

    seen_ids: set[str] = set()

    for r in rules:
        rid = r.get("id", "")
        where = f"rule {rid or '(no id)'} (章 {r.get('chapter_slug')})"

        # id 形式
        if not rid:
            rep.error(where, "id が無い")
            continue
        if not rule_id_re.match(rid):
            rep.error(where, f"id 形式不正 (期待 {c['rule_id_pattern']})")
        # id 重複
        if rid in seen_ids:
            rep.error(where, "id が重複")
        seen_ids.add(rid)
        # category 許可
        cat = rid.split("-")[0] if "-" in rid else ""
        if cat and cat not in valid_categories:
            rep.error(where, f"未登録カテゴリ {cat!r} (許可: {sorted(valid_categories)})")

        # statement
        stmt = (r.get("statement") or "").strip()
        if not stmt:
            rep.error(where, "statement が空")
        elif len(stmt) < smin:
            rep.error(where, f"statement が短すぎ ({len(stmt)} < {smin})")
        elif len(stmt) > smax:
            rep.error(where, f"statement が長すぎ ({len(stmt)} > {smax})")

        # severity
        sev = r.get("severity")
        if sev not in valid_severity:
            rep.error(where, f"severity 不正 {sev!r}")

        # maturity
        mat = r.get("maturity", "stable")
        if mat not in valid_maturity:
            rep.error(where, f"maturity 不正 {mat!r}")

        # rule_type
        rt = r.get("rule_type")
        if rt not in valid_rule_types:
            rep.error(where, f"rule_type 不正 {rt!r}")

        # phase
        for p in r.get("phase", []):
            if p not in valid_phases:
                rep.error(where, f"phase 不正 {p!r}")
        if not r.get("phase"):
            rep.error(where, "phase が空")

        # rationale
        if not (r.get("rationale") or "").strip():
            rep.error(where, "rationale が空")

        # applies_to.primary
        applies = r.get("applies_to", {})
        if not applies.get("primary"):
            rep.error(where, "applies_to.primary が空")

        # related_rules
        for rel in r.get("related_rules", []):
            rel_id = rel.get("id")
            rel_type = rel.get("type")
            if rel_type not in valid_relation:
                rep.error(where, f"related type 不正 {rel_type!r}")
            # 段階移行中は参照先が未移行のことがあるため warning に留める
            if rel_id not in rule_ids:
                rep.warn(where, f"related の参照先 {rel_id!r} が catalog に未登録 (未移行章?)")

        # exceptions
        for exc in r.get("exceptions", []):
            ref = exc.get("ref_rule")
            if not exc.get("condition"):
                rep.error(where, "exception の condition が空")
            if ref not in rule_ids:
                rep.error(where, f"exception の ref_rule {ref!r} が catalog に不在")


def check_tldr(catalog: dict, schema: dict, rep: Report) -> None:
    tldr_max = schema["constraints"]["tldr_max_len"]
    for r in catalog.get("rules", []):
        where = f"rule {r.get('id')} (章 {r.get('chapter_slug')})"
        tldr = (r.get("tldr") or "").strip()
        if not tldr:
            rep.error(where, "TL;DR にこの Rule ID の行が無い")
        elif len(tldr) > tldr_max:
            rep.warn(where, f"tldr が長い ({len(tldr)} > {tldr_max})")


def check_slugs(catalog: dict, schema: dict, rep: Report) -> None:
    slug_re = re.compile(schema["constraints"]["slug_pattern"])
    seen: dict[str, str] = {}
    for slug, ch in catalog.get("chapters", {}).items():
        where = f"chapter {slug}"
        if not slug_re.match(slug):
            rep.error(where, f"slug が kebab-case でない ({slug_re.pattern})")
        if slug in seen:
            rep.error(where, "slug が重複")
        seen[slug] = ch.get("path", "")


def check_mcp_blocks(catalog: dict, rep: Report) -> None:
    rule_ids = {r["id"] for r in catalog.get("rules", []) if r.get("id")}
    blocks = catalog.get("mcp_blocks", {})

    # label 一意性は dict のキーで保証されるが、念のため空でないことを確認
    for label, b in blocks.items():
        where = f"block {label}"
        if not label.strip():
            rep.error(where, "label が空")
        # whitespace / slash / quote を含まない
        if re.search(r"""[\s/\\'"]""", label):
            rep.error(where, "label に空白/スラッシュ/クォートが含まれる")
        # rules 属性の参照先が実在
        if not b.get("rule_ids"):
            rep.error(where, "rules 属性が空")
        for rid in b.get("rule_ids", []):
            if rid not in rule_ids:
                rep.error(where, f"参照先ルール {rid!r} が catalog に不在")
        if not (b.get("content") or "").strip():
            rep.warn(where, "content が空")

    # 各ルールの mcp_block_labels が実在する label を指すか
    for r in catalog.get("rules", []):
        where = f"rule {r.get('id')}"
        for label in r.get("mcp_block_labels", []):
            if label not in blocks:
                rep.error(where, f"mcp_block_labels の {label!r} が mcp_blocks に不在")


def check_catalog_meta(catalog: dict, rep: Report) -> None:
    if not catalog.get("rules"):
        rep.warn("catalog", "ルールが 0 件 (移行未着手の可能性)")
    if not catalog.get("site_url"):
        rep.warn("catalog", "site_url が空 (chapter_url が相対パスになる)")


# ---------------------------------------------------------------------------
# メイン
# ---------------------------------------------------------------------------


def main() -> int:
    ap = argparse.ArgumentParser(description="rules-catalog.json を検証する")
    ap.add_argument(
        "--catalog",
        type=Path,
        default=DEFAULT_CATALOG,
        help=f"検証対象の catalog (既定: {DEFAULT_CATALOG})",
    )
    args = ap.parse_args()

    if not args.catalog.exists():
        print(
            f"ERROR: {args.catalog} が存在しません。先に build-rules-catalog.py を実行してください。",
            file=sys.stderr,
        )
        return 1
    if not SCHEMA_CONFIG.exists():
        print(f"ERROR: {SCHEMA_CONFIG} が存在しません。", file=sys.stderr)
        return 1

    schema = load_schema_config()
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))

    rep = Report()
    check_catalog_meta(catalog, rep)
    check_rules(catalog, schema, rep)
    check_tldr(catalog, schema, rep)
    check_slugs(catalog, schema, rep)
    check_mcp_blocks(catalog, rep)

    code = rep.print_and_exit()
    if code == 0 and not rep.warnings:
        print("lint: OK", file=sys.stderr)
    return code


if __name__ == "__main__":
    sys.exit(main())
