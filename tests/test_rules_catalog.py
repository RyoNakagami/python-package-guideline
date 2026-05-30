"""scripts/rules_catalog.py の純粋ロジックに対する pytest。

pythonpath = ["scripts"] (pyproject.toml) により scripts/ から直接 import できる。
"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent

import pytest

from rules_catalog import (
    DEFAULT_RULE_ID_PATTERN,
    QmdSource,
    build_catalog,
    extract_mcp_blocks,
    extract_tldr_by_rule,
    html_url,
    load_site_url,
    normalize_applies_to,
    normalize_related,
    rule_id_pattern_from_schema,
    split_front_matter,
)


# ---------------------------------------------------------------------------
# split_front_matter
# ---------------------------------------------------------------------------


def test_split_front_matter_extracts_dict_and_body():
    text = "---\ntitle: hi\nslug: x\n---\n\n## TL;DR\nbody\n"
    fm, body = split_front_matter(text)
    assert fm == {"title": "hi", "slug": "x"}
    assert body.lstrip().startswith("## TL;DR")


def test_split_front_matter_no_front_matter():
    fm, body = split_front_matter("## just body\ntext")
    assert fm is None
    assert body == "## just body\ntext"


def test_split_front_matter_unterminated_returns_none():
    fm, body = split_front_matter("---\ntitle: hi\nno closing fence")
    assert fm is None
    assert body == "---\ntitle: hi\nno closing fence"


def test_split_front_matter_non_dict_yaml_returns_none():
    # YAML がスカラ/配列の場合は dict でないので None
    fm, _ = split_front_matter("---\n- a\n- b\n---\nbody")
    assert fm is None


def test_split_front_matter_invalid_yaml_returns_none_with_body():
    fm, body = split_front_matter("---\n: : bad\n---\nbody")
    assert fm is None
    # body は閉じフェンス "\n---" の直後から (先頭の改行を含む) を返す
    assert body == "\nbody"


# ---------------------------------------------------------------------------
# normalize_applies_to
# ---------------------------------------------------------------------------


def test_normalize_applies_to_new_form():
    raw = {"primary": ["pyproject.toml", "src/**"], "contextual": ["tests/"]}
    assert normalize_applies_to(raw) == {
        "primary": ["pyproject.toml", "src/**"],
        "contextual": ["tests/"],
    }


def test_normalize_applies_to_legacy_flat_list_is_primary():
    assert normalize_applies_to(["a", "b"]) == {
        "primary": ["a", "b"],
        "contextual": [],
    }


def test_normalize_applies_to_none():
    assert normalize_applies_to(None) == {"primary": [], "contextual": []}


def test_normalize_applies_to_dict_missing_keys():
    assert normalize_applies_to({}) == {"primary": [], "contextual": []}


# ---------------------------------------------------------------------------
# normalize_related
# ---------------------------------------------------------------------------


def test_normalize_related_legacy_string_ids():
    assert normalize_related(["PKG-A-001", "PKG-B-002"]) == [
        {"id": "PKG-A-001", "type": "prerequisite"},
        {"id": "PKG-B-002", "type": "prerequisite"},
    ]


def test_normalize_related_dict_form_keeps_type():
    raw = [{"id": "PKG-A-001", "type": "contrasts"}, {"id": "PKG-B-002"}]
    assert normalize_related(raw) == [
        {"id": "PKG-A-001", "type": "contrasts"},
        {"id": "PKG-B-002", "type": "prerequisite"},
    ]


def test_normalize_related_none():
    assert normalize_related(None) == []


# ---------------------------------------------------------------------------
# html_url
# ---------------------------------------------------------------------------


def test_html_url_with_site_url():
    url = html_url("https://x.io/book", Path("book/004_testing/posts/f.qmd"))
    assert url == "https://x.io/book/book/004_testing/posts/f.html"


def test_html_url_without_site_url_is_root_relative():
    url = html_url("", Path("book/a/b.qmd"))
    assert url == "/book/a/b.html"


# ---------------------------------------------------------------------------
# extract_tldr_by_rule
# ---------------------------------------------------------------------------


def test_extract_tldr_by_rule_picks_matching_lines():
    body = dedent(
        """\
        ## TL;DR

        - **PKG-LAYOUT-001** (required): src layout を採用する。
        - **PKG-LAYOUT-002** (required): tests は外に置く。

        ## 本文
        無関係
        """
    )
    tldr = extract_tldr_by_rule(body, ["PKG-LAYOUT-001", "PKG-LAYOUT-002"])
    assert "src layout" in tldr["PKG-LAYOUT-001"]
    assert "tests は外" in tldr["PKG-LAYOUT-002"]


def test_extract_tldr_by_rule_no_section_returns_empty():
    assert extract_tldr_by_rule("## 本文\nfoo", ["PKG-A-001"]) == {}


def test_extract_tldr_by_rule_missing_id_omitted():
    body = "## TL;DR\n\n- **PKG-A-001**: ある。\n"
    tldr = extract_tldr_by_rule(body, ["PKG-A-001", "PKG-B-002"])
    assert "PKG-A-001" in tldr
    assert "PKG-B-002" not in tldr


# ---------------------------------------------------------------------------
# extract_mcp_blocks
# ---------------------------------------------------------------------------


def test_extract_mcp_blocks_parses_label_rules_content():
    body = dedent(
        """\
        前文
        :::{.allowed-mcp-read label="src-layout-example" rules="PKG-A-001, PKG-B-002"}
        コード例
        :::
        後文
        """
    )
    blocks = extract_mcp_blocks(body, slug="src-layout")
    assert len(blocks) == 1
    b = blocks[0]
    assert b["label"] == "src-layout-example"
    assert b["rule_ids"] == ["PKG-A-001", "PKG-B-002"]
    assert b["content"] == "コード例"
    assert b["chapter_slug"] == "src-layout"


def test_extract_mcp_blocks_none_present():
    assert extract_mcp_blocks("本文だけ", slug="x") == []


def test_extract_mcp_blocks_accepts_four_colons():
    # Quarto は :::: のような 3 個以上のコロンも許容する
    body = '::::{.allowed-mcp-read label="lbl" rules="PKG-A-001"}\nコード\n:::'
    blocks = extract_mcp_blocks(body, slug="s")
    assert len(blocks) == 1
    assert blocks[0]["label"] == "lbl"


def test_extract_mcp_blocks_accepts_space_before_brace():
    # ::: と { の間のスペースも許容する
    body = '::: {.allowed-mcp-read label="lbl" rules="PKG-A-001"}\nコード\n:::'
    blocks = extract_mcp_blocks(body, slug="s")
    assert len(blocks) == 1
    assert blocks[0]["label"] == "lbl"


# ---------------------------------------------------------------------------
# load_site_url
# ---------------------------------------------------------------------------


def test_load_site_url_strips_trailing_slash():
    yml = "book:\n  site-url: https://x.io/guide/\n"
    assert load_site_url(yml) == "https://x.io/guide"


def test_load_site_url_missing_returns_empty():
    assert load_site_url("project:\n  type: book\n") == ""


def test_load_site_url_invalid_yaml_returns_empty():
    assert load_site_url(": : not valid") == ""


# ---------------------------------------------------------------------------
# rule_id_pattern_from_schema
# ---------------------------------------------------------------------------


def test_rule_id_pattern_from_schema_reads_constraint():
    yml = "constraints:\n  rule_id_pattern: '^X-\\d+$'\n"
    assert rule_id_pattern_from_schema(yml) == r"^X-\d+$"


def test_rule_id_pattern_from_schema_missing_falls_back():
    assert rule_id_pattern_from_schema("phases: [init]\n") == DEFAULT_RULE_ID_PATTERN


def test_rule_id_pattern_from_schema_invalid_falls_back():
    assert rule_id_pattern_from_schema(": : bad") == DEFAULT_RULE_ID_PATTERN


# ---------------------------------------------------------------------------
# build_catalog (end-to-end)
# ---------------------------------------------------------------------------

CHAPTER_QMD = dedent(
    """\
    ---
    title: "src layout vs flat layout"
    slug: src-layout
    phase: [init, packaging]
    applies-to:
      primary:
        - pyproject.toml
        - "src/**"
      contextual:
        - tests/
    rule-type: structural
    rules:
      - id: PKG-LAYOUT-001
        statement: 新規パッケージは src/ layout を採用する
        severity: required
        rationale: import 漏れを早期検出できる。
      - id: PKG-LAYOUT-002
        statement: tests/ は src/ の外に置く
        severity: required
        rationale: テストをパッケージに含めない。
    related-rules:
      - id: PKG-VERSION-001
        type: prerequisite
    ---

    ## TL;DR

    - **PKG-LAYOUT-001** (required): src/ layout を採用する。
    - **PKG-LAYOUT-002** (required): tests/ は外に置く。

    ## 本文

    :::{.allowed-mcp-read label="src-layout-example" rules="PKG-LAYOUT-001"}
    例コード
    :::
    """
)


def _src(path: str, text: str) -> QmdSource:
    return QmdSource(rel_path=Path(path), text=text)


def test_build_catalog_happy_path():
    result = build_catalog(
        [_src("book/pkg/layout.qmd", CHAPTER_QMD)],
        site_url="https://x.io/guide",
    )
    cat = result.catalog

    assert cat["version"] == "1.3"
    assert cat["site_url"] == "https://x.io/guide"
    assert cat["generated_at"] is None  # CLI 層で上書きされる前提
    assert result.warnings == []

    # chapters
    assert set(cat["chapters"]) == {"src-layout"}
    chap = cat["chapters"]["src-layout"]
    assert chap["path"] == "book/pkg/layout.qmd"
    assert chap["url"] == "https://x.io/guide/book/pkg/layout.html"
    assert chap["phase"] == ["init", "packaging"]
    assert chap["mcp_block_labels"] == ["src-layout-example"]

    # rules
    assert len(cat["rules"]) == 2
    r1 = next(r for r in cat["rules"] if r["id"] == "PKG-LAYOUT-001")
    assert r1["severity"] == "required"
    assert r1["maturity"] == "stable"  # 既定値
    assert r1["chapter_slug"] == "src-layout"
    assert r1["related_rules"] == [{"id": "PKG-VERSION-001", "type": "prerequisite"}]
    assert r1["mcp_block_labels"] == ["src-layout-example"]
    assert "src/ layout を採用する" in r1["tldr"]
    # vector_text は statement + rationale + tldr の連結
    assert "新規パッケージは src/ layout" in r1["vector_text"]
    assert "import 漏れ" in r1["vector_text"]

    r2 = next(r for r in cat["rules"] if r["id"] == "PKG-LAYOUT-002")
    assert r2["mcp_block_labels"] == []  # ブロックに紐付かない

    # 集約
    assert cat["phases"] == ["init", "packaging"]
    assert cat["categories"] == ["PKG"]
    assert cat["mcp_blocks"]["src-layout-example"]["content"] == "例コード"
    # phase_inference: glob -> sorted phases
    assert cat["phase_inference"]["pyproject.toml"] == ["init", "packaging"]
    assert cat["phase_inference"]["tests/"] == ["init", "packaging"]


def test_build_catalog_skips_chapters_without_rules():
    no_rules = "---\ntitle: index\nslug: idx\n---\n\n本文のみ\n"
    result = build_catalog([_src("book/index.qmd", no_rules)])
    assert result.catalog["rules"] == []
    assert result.catalog["chapters"] == {}
    assert result.warnings == []


def test_build_catalog_warns_on_missing_slug():
    qmd = dedent(
        """\
        ---
        title: t
        rules:
          - id: PKG-A-001
            statement: x
            severity: required
            rationale: y
        ---
        ## TL;DR
        - **PKG-A-001**: x
        """
    )
    result = build_catalog([_src("book/a.qmd", qmd)])
    assert result.catalog["rules"] == []  # slug 無しはスキップ
    assert any("slug" in w for w in result.warnings)


def test_build_catalog_warns_on_bad_rule_id_but_keeps_rule():
    qmd = dedent(
        """\
        ---
        title: t
        slug: bad-id
        rules:
          - id: not_a_valid_id
            statement: x
            severity: required
            rationale: y
        ---
        ## TL;DR
        - **not_a_valid_id**: x
        """
    )
    result = build_catalog([_src("book/a.qmd", qmd)])
    assert len(result.catalog["rules"]) == 1
    assert any("形式不正" in w for w in result.warnings)


def test_build_catalog_warns_on_duplicate_block_label():
    # dedent と f-string を混ぜると block の差し込み行が共通インデントを
    # 崩すため，dedent 後に連結する。
    block = ':::{.allowed-mcp-read label="dup" rules="PKG-A-001"}\nx\n:::'
    head = dedent(
        """\
        ---
        title: t
        slug: s
        rules:
          - id: PKG-A-001
            statement: x
            severity: required
            rationale: y
        ---
        ## TL;DR
        - **PKG-A-001**: x

        """
    )
    qmd = f"{head}{block}\n\n{block}\n"
    result = build_catalog([_src("book/a.qmd", qmd)])
    assert list(result.catalog["mcp_blocks"]) == ["dup"]  # 2 個目は無視
    assert any("重複" in w for w in result.warnings)


def test_build_catalog_warns_on_dangling_block_rule_ref():
    qmd = dedent(
        """\
        ---
        title: t
        slug: s
        rules:
          - id: PKG-A-001
            statement: x
            severity: required
            rationale: y
        ---
        ## TL;DR
        - **PKG-A-001**: x

        :::{.allowed-mcp-read label="b" rules="PKG-A-001,PKG-GHOST-999"}
        x
        :::
        """
    )
    result = build_catalog([_src("book/a.qmd", qmd)])
    assert any("PKG-GHOST-999" in w for w in result.warnings)


def test_build_catalog_warns_when_tldr_missing():
    qmd = dedent(
        """\
        ---
        title: t
        slug: s
        rules:
          - id: PKG-A-001
            statement: x
            severity: required
            rationale: y
        ---
        ## 本文
        TL;DR なし
        """
    )
    result = build_catalog([_src("book/a.qmd", qmd)])
    assert any("TL;DR" in w for w in result.warnings)
    assert result.catalog["rules"][0]["tldr"] == ""


def test_build_catalog_sorts_sources_by_path():
    # 入力順に依存せず path 順で安定処理されることを確認
    a = CHAPTER_QMD.replace("src-layout", "alpha").replace("PKG-LAYOUT", "PKG-ALPHA")
    z = CHAPTER_QMD.replace("src-layout", "zeta").replace("PKG-LAYOUT", "PKG-ZETA")
    out1 = build_catalog([_src("book/z.qmd", z), _src("book/a.qmd", a)])
    out2 = build_catalog([_src("book/a.qmd", a), _src("book/z.qmd", z)])
    assert out1.catalog["rules"] == out2.catalog["rules"]


def test_build_catalog_honors_custom_rule_id_pattern():
    # 既定パターンには合致するが，カスタムパターン (X- 始まり) には不一致 → warning
    result = build_catalog(
        [_src("book/pkg/layout.qmd", CHAPTER_QMD)],
        rule_id_pattern=r"^X-[A-Z]+-\d{3}$",
    )
    assert any("形式不正" in w for w in result.warnings)
    # ルール自体は (形式不正でも) catalog に残る
    assert len(result.catalog["rules"]) == 2


def test_build_catalog_legacy_applies_to_flat_list():
    qmd = dedent(
        """\
        ---
        title: t
        slug: s
        applies-to:
          - pyproject.toml
        rules:
          - id: PKG-A-001
            statement: x
            severity: required
            rationale: y
        ---
        ## TL;DR
        - **PKG-A-001**: x
        """
    )
    result = build_catalog([_src("book/a.qmd", qmd)])
    rule = result.catalog["rules"][0]
    assert rule["applies_to"] == {"primary": ["pyproject.toml"], "contextual": []}


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-v"]))
