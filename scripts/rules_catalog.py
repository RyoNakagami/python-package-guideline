"""rules_catalog.py

book/ 配下の .qmd を直接パースして rules-catalog の dict を組み立てる純粋ロジック層。

I/O (ファイル読み書き・stderr 出力) は CLI 層 (build-rules-catalog.py) に分離し，
ここでは「テキスト → catalog dict」「front matter / 本文の抽出・正規化」だけを担う。
これにより in-memory のテキストを渡すだけで全挙動を pytest で検証できる。

book プロジェクトは gfm 並列出力に非対応のため，.md を経由せず .qmd を直接読む。
front matter (rules 等) と本文 (TL;DR / allowed-mcp-read) の両方を抽出する。

許可リスト・制約 (enum, Rule ID 形式等) の SST は scripts/schema-config.yml であり，
catalog に対する検証は scripts/lint-rules.py が担う。本モジュールは抽出・組み立てに専念し，
構築段階で気付ける軽微な異常 (slug 欠落・ID 形式・block の dangling 参照等) のみ
warning として返す。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

# ---------------------------------------------------------------------------
# 定数
# ---------------------------------------------------------------------------

CATALOG_VERSION = "1.3"

# Rule ID 形式の既定パターン。SST は schema-config.yml の constraints.rule_id_pattern。
# CLI 層が schema-config から読んで build_catalog に渡すが，
# 単体でも動くよう同値の既定をここに置く。
DEFAULT_RULE_ID_PATTERN = r"^[A-Z]+-[A-Z]+-\d{3}$"

# allowed-mcp-read ブロック: label と rules 属性を持つ
# ::: の数 (3 個以上) と ::: と { の間のスペースは任意 (Quarto はどちらも許容)
MCP_BLOCK_RE = re.compile(
    r":::+\s*\{\.allowed-mcp-read\s+"
    r'label="([^"]+)"\s+'
    r'rules="([^"]+)"\}'
    r"(.*?):::",
    re.DOTALL,
)


# ---------------------------------------------------------------------------
# front matter / 本文の抽出・正規化 (純粋関数)
# ---------------------------------------------------------------------------


def split_front_matter(text: str) -> tuple[dict | None, str]:
    """先頭 YAML front matter と本文を分離する。

    Returns:
        (front_matter_dict or None, body_str)
    """
    if not text.startswith("---"):
        return None, text
    try:
        end = text.index("\n---", 3)
    except ValueError:
        return None, text
    fm_raw = text[3:end]
    body = text[end + 4 :]  # "\n---" の後ろ
    try:
        fm = yaml.safe_load(fm_raw)
    except yaml.YAMLError:
        return None, body
    return (fm if isinstance(fm, dict) else None), body


def normalize_applies_to(raw) -> dict:
    """applies-to を {primary, contextual} に正規化する (B-1)。

    旧形式 (フラットな配列) は全て primary 扱い。
    """
    if isinstance(raw, dict):
        return {
            "primary": list(raw.get("primary", []) or []),
            "contextual": list(raw.get("contextual", []) or []),
        }
    return {"primary": list(raw or []), "contextual": []}


def normalize_related(raw) -> list[dict]:
    """related-rules を [{id, type}] に正規化する (B-5)。

    旧形式 (ID 文字列の配列) は type=prerequisite 扱い。
    """
    out: list[dict] = []
    for item in raw or []:
        if isinstance(item, dict):
            out.append({"id": item.get("id"), "type": item.get("type", "prerequisite")})
        else:
            out.append({"id": item, "type": "prerequisite"})
    return out


def html_url(site_url: str, qmd_path: Path) -> str:
    """qmd のパスから book プロジェクトの公開 HTML URL を組み立てる。

    book/004_testing/posts/fixture-design.qmd
      -> {site_url}/book/004_testing/posts/fixture-design.html
    """
    rel = qmd_path.with_suffix(".html").as_posix()
    return f"{site_url}/{rel}" if site_url else f"/{rel}"


def extract_mcp_blocks(body: str, slug: str) -> list[dict]:
    """本文から allowed-mcp-read ブロックを抽出する。"""
    blocks: list[dict] = []
    for m in MCP_BLOCK_RE.finditer(body):
        blocks.append(
            {
                "label": m.group(1).strip(),
                "rule_ids": [r.strip() for r in m.group(2).split(",") if r.strip()],
                "content": m.group(3).strip(),
                "chapter_slug": slug,
            }
        )
    return blocks


def extract_tldr_by_rule(body: str, rule_ids: list[str]) -> dict[str, str]:
    """## TL;DR セクションから各 Rule ID を含む箇条書き行を抽出する。"""
    tldr: dict[str, str] = {}
    m = re.search(r"##\s*TL;DR\s*\n(.*?)(?=\n##\s|\n---|\Z)", body, re.DOTALL)
    if not m:
        return tldr
    section = m.group(1)
    for rid in rule_ids:
        line_m = re.search(
            rf"[-*]\s*\*\*{re.escape(rid)}\*\*.*?(?=\n[-*]\s|\Z)",
            section,
            re.DOTALL,
        )
        if line_m:
            tldr[rid] = line_m.group(0).strip()
    return tldr


def load_site_url(quarto_yml_text: str) -> str:
    """_quarto.yml のテキストから book.site-url を読む。GH Pages の公開先 URL。"""
    try:
        cfg = yaml.safe_load(quarto_yml_text)
    except yaml.YAMLError:
        return ""
    if not isinstance(cfg, dict):
        return ""
    return (cfg.get("book", {}) or {}).get("site-url", "").rstrip("/")


def rule_id_pattern_from_schema(schema_config_text: str) -> str:
    """schema-config.yml のテキストから constraints.rule_id_pattern を読む。

    欠落・パース不能なら DEFAULT_RULE_ID_PATTERN にフォールバックする。
    """
    try:
        cfg = yaml.safe_load(schema_config_text)
    except yaml.YAMLError:
        return DEFAULT_RULE_ID_PATTERN
    if not isinstance(cfg, dict):
        return DEFAULT_RULE_ID_PATTERN
    return (cfg.get("constraints", {}) or {}).get(
        "rule_id_pattern", DEFAULT_RULE_ID_PATTERN
    )


# ---------------------------------------------------------------------------
# catalog 組み立て (純粋関数)
# ---------------------------------------------------------------------------


@dataclass
class QmdSource:
    """1 つの .qmd の入力。パスはリポジトリルートからの相対 (.qmd)。"""

    rel_path: Path
    text: str


@dataclass
class BuildResult:
    """catalog 組み立て結果。catalog は JSON 化対象，warnings は人向けの警告。

    generated_at は意図的に含めない (純粋性を保つため CLI 層で付与する)。
    """

    catalog: dict
    warnings: list[str] = field(default_factory=list)


def empty_catalog(site_url: str) -> dict:
    return {
        "version": CATALOG_VERSION,
        "generated_at": None,  # CLI 層が ISO8601 を上書きする (純粋性のため None)
        "site_url": site_url,
        "rules": [],
        "chapters": {},
        "mcp_blocks": {},  # label -> block
        "phase_inference": {},  # glob -> [phase]
        "phases": [],
        "categories": [],
    }


def build_catalog(
    sources: list[QmdSource],
    site_url: str = "",
    rule_id_pattern: str = DEFAULT_RULE_ID_PATTERN,
) -> BuildResult:
    """QmdSource の列から catalog dict を組み立てる (副作用なし)。

    rules フィールドを持たない章 (index.qmd, glossary.qmd 等) は自動スキップする。
    site_url は呼び出し側 (_quarto.yml 由来)，rule_id_pattern は schema-config.yml 由来。
    """
    catalog = empty_catalog(site_url)
    rule_id_re = re.compile(rule_id_pattern)

    phases_seen: set[str] = set()
    categories_seen: set[str] = set()
    phase_inference: dict[str, set] = {}
    warnings: list[str] = []

    for src in sorted(sources, key=lambda s: s.rel_path.as_posix()):
        qmd = src.rel_path
        fm, body = split_front_matter(src.text)

        # rules を持たない章 (index.qmd, glossary.qmd 等) はスキップ
        if not fm or "rules" not in fm:
            continue

        slug = fm.get("slug")
        if not slug:
            warnings.append(f"{qmd}: 'slug' がありません")
            continue

        rule_ids_in_chapter = [r.get("id") for r in fm["rules"] if r.get("id")]
        chapter_url = html_url(site_url, qmd)
        applies = normalize_applies_to(fm.get("applies-to"))
        chapter_phases = fm.get("phase", []) or []

        # TL;DR 抽出
        tldr_map = extract_tldr_by_rule(body, rule_ids_in_chapter)
        if not tldr_map:
            warnings.append(f"{qmd}: ## TL;DR が無い、または Rule ID を含みません")

        # allowed-mcp-read ブロック抽出
        blocks = extract_mcp_blocks(body, slug)
        block_labels_by_rule: dict[str, list[str]] = {}
        for block in blocks:
            label = block["label"]
            if label in catalog["mcp_blocks"]:
                warnings.append(f"{qmd}: block label 重複 {label!r}")
                continue
            catalog["mcp_blocks"][label] = block
            for rid in block["rule_ids"]:
                if rid not in rule_ids_in_chapter:
                    warnings.append(
                        f"{qmd}: block {label!r} が未定義ルール {rid!r} を参照"
                    )
                block_labels_by_rule.setdefault(rid, []).append(label)

        # phase 推定テーブルへの寄与 (glob -> phase)
        for pattern in applies["primary"] + applies["contextual"]:
            phase_inference.setdefault(pattern, set()).update(chapter_phases)

        catalog["chapters"][slug] = {
            "slug": slug,
            "title": fm.get("title"),
            "path": qmd.as_posix(),  # .qmd パス (gfm 非生成のため)
            "url": chapter_url,
            "phase": chapter_phases,
            "applies_to": applies,
            "rule_type": fm.get("rule-type"),
            "mcp_block_labels": [b["label"] for b in blocks],
        }

        for rule in fm["rules"]:
            rule_id = rule.get("id", "")
            if not rule_id:
                warnings.append(f"{qmd}: id の無いルールがあります")
                continue
            if not rule_id_re.match(rule_id):
                warnings.append(f"{qmd}: Rule ID 形式不正 {rule_id!r}")

            related = normalize_related(fm.get("related-rules", []))
            exceptions = rule.get("exceptions", []) or []

            # ルール単位ベクター用テキスト (statement + rationale + tldr)
            vector_text = "\n".join(
                filter(
                    None,
                    [
                        rule.get("statement", ""),
                        rule.get("rationale", ""),
                        tldr_map.get(rule_id, ""),
                    ],
                )
            )

            catalog["rules"].append(
                {
                    "id": rule_id,
                    "statement": rule.get("statement"),
                    "severity": rule.get("severity"),
                    "maturity": rule.get("maturity", "stable"),
                    "rationale": rule.get("rationale", ""),
                    "tldr": tldr_map.get(rule_id, ""),
                    "phase": chapter_phases,
                    "applies_to": applies,
                    "rule_type": fm.get("rule-type"),
                    "chapter_slug": slug,
                    "chapter_path": qmd.as_posix(),
                    "chapter_url": chapter_url,
                    "related_rules": related,
                    "exceptions": exceptions,
                    "mcp_block_labels": block_labels_by_rule.get(rule_id, []),
                    "vector_text": vector_text,
                }
            )

            for p in chapter_phases:
                phases_seen.add(p)
            if "-" in rule_id:
                categories_seen.add(rule_id.split("-")[0])

    catalog["phases"] = sorted(phases_seen)
    catalog["categories"] = sorted(categories_seen)
    catalog["phase_inference"] = {
        k: sorted(v) for k, v in sorted(phase_inference.items())
    }

    return BuildResult(catalog=catalog, warnings=warnings)


def read_sources(book_dir: Path, root: Path) -> list[QmdSource]:
    """book_dir 配下の .qmd を再帰的に読み，root 相対の QmdSource にする。"""
    sources: list[QmdSource] = []
    for qmd in sorted(book_dir.rglob("*.qmd")):
        sources.append(
            QmdSource(
                rel_path=qmd.relative_to(root),
                text=qmd.read_text(encoding="utf-8"),
            )
        )
    return sources
