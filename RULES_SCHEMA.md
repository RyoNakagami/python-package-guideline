# RULES_SCHEMA.md

- `python-package-guidline` の各 `.qmd` が従う front matter スキーマと章構成規約
- このファイルがSST: `build-rules-catalog.py`，`lint-rules.py`・MCP サーバーの型定義は，すべてここに従う

---

## 0. このファイルの位置づけ

| 参照者 | このファイルから何を得るか |
| --- | --- |
| Author | front matter の書き方，TL;DR / allowed-mcp-read の規約 |
| `scripts/build-rules-catalog.py` | 抽出すべきフィールドと正規化ルール |
| `scripts/lint-rules.py` | 検証すべき制約 |
| MCP サーバー (`src/catalog/types.ts`) | 型定義の根拠 |

スキーマを変更するときは必ずこのファイルを先に更新し，4 者を追従させる．

---

## 1. 章ファイルの全体構成

各 `.qmd` は次の順で構成する．

```
front matter (YAML)        ← 機械可読のルール定義
  ↓
## TL;DR                   ← LAYER 1．agent が最初に読む散文
  ↓
本文 (見出し + 散文)        ← allowed-mcp-read ブロックを含む
  ↓
## Anti-pattern            ← allowed-mcp-read ブロック (任意)
  ↓
## Related                 ← 関連章へのリンク
```

front matter の `rules` (機械可読) → `## TL;DR` (散文) → `allowed-mcp-read` (詳細) が，
すべて Rule ID で一貫して紐付く 3 段構造になる．

---

## 2. front matter スキーマ

### 2.1 完全な例

```yaml
---
title: "src layout vs flat layout"        # 既存．Quarto の表示タイトル
slug: src-layout                          # 必須・kebab-case・ファイル内一意
phase: [init, packaging]                  # 必須・enum 配列・空不可
applies-to:                               # 必須・2 段階 glob
  primary:                                #   このルールが直接対象とするファイル (高スコア)
    - pyproject.toml
    - "src/**"
  contextual:                             #   周辺で参照されうるファイル (低スコア)
    - tests/
rule-type: structural                     # 必須・enum
rules:                                    # 必須・配列・空不可
  - id: PKG-LAYOUT-001                    #   必須・^[A-Z]+-[A-Z]+-\d{3}$
    statement: 新規パッケージは src/ layout を採用する  # 必須・10〜200 文字・1 文
    severity: required                    #   必須・enum
    maturity: stable                      #   任意・enum (既定 stable)
    rationale: |                          #   必須・複数行可
      テストが install 済みパッケージに対して実行され，
      import 漏れを早期検出できる．
    exceptions:                           #   任意・条件付き例外の配列
      - condition: C 拡張モジュールを含む  #     必須 (exceptions 内)・自然言語
        ref_rule: PKG-CEXT-001            #     必須 (exceptions 内)・例外時に従う Rule ID
  - id: PKG-LAYOUT-002
    statement: tests/ は src/ の外に置く
    severity: required
    rationale: テストコードをパッケージに含めない目的
related-rules:                            # 任意・種別付き関連ルール
  - id: PKG-VERSION-001                   #   必須 (related 内)・Rule ID
    type: prerequisite                    #   必須 (related 内)・enum
  - id: PKG-TESTPYPI-001
    type: prerequisite
---
```

### 2.2 フィールド一覧

| フィールド | 必須 | 型 | 制約 |
| --- | --- | --- | --- |
| `title` | 必須 | string | Quarto の既存フィールド |
| `slug` | 必須 | string | kebab-case (`^[a-z0-9]+(-[a-z0-9]+)*$`)，catalog 全体で一意 |
| `phase` | 必須 | enum[] | 空不可．§4.1 の許可リスト |
| `applies-to` | 必須 | object | `primary` (必須・1 件以上) と `contextual` (任意) |
| `rule-type` | 必須 | enum | §4.3 の許可リスト |
| `rules` | 必須 | object[] | 空不可．各要素は §2.3 |
| `related-rules` | 任意 | object[] | 各要素は `{id, type}`．§4.4 |

### 2.3 rules[] の各要素

| フィールド | 必須 | 型 | 制約 |
|---|---|---|---|
| `id` | 必須 | string | `^[A-Z]+-[A-Z]+-\d{3}$`，catalog 全体で一意・不変 |
| `statement` | 必須 | string | 10〜200 文字．1 文で言い切る |
| `severity` | 必須 | enum | §4.2 の許可リスト |
| `maturity` | 任意 | enum | §4.5．既定 `stable` |
| `rationale` | 必須 | string | なぜそうするかの技術的根拠．複数行可 |
| `exceptions` | 任意 | object[] | 各要素は `{condition, ref_rule}` |

### 2.4 exceptions[] の各要素

| フィールド | 必須 | 型 | 制約 |
|---|---|---|---|
| `condition` | 必須 | string | 例外が成立する条件 (自然言語) |
| `ref_rule` | 必須 | string | 例外時に従う Rule ID．catalog に実在すること |

### 2.5 applies-to の 2 段階 glob

| キー | 必須 | 意味 | スコア重み (既定) |
|---|---|---|---|
| `primary` | 必須 (1 件以上) | このルールが直接対象とするファイル | 10 |
| `contextual` | 任意 | 周辺で参照されうるファイル | 3 |

glob は micromatch 記法 (`src/**`, `**/test_*.py`, `.github/workflows/*.yml` など)．

**後方互換**: `applies-to` がフラットな配列で書かれている場合，全て `primary` 扱いとする
(旧形式の章を段階移行できるようにするため)．

---

## 3. TL;DR と allowed-mcp-read の規約

### 3.1 ## TL;DR (LAYER 1)

front matter の `rules` を散文化したセクション．agent が最初に読む．

規約:
- `## TL;DR` という見出しで始める
- 各ルールを `- **<Rule ID>** (<severity>): <要点>` の箇条書きにする
- 全 Rule ID を必ず 1 行以上で含む
- 各行は statement + rationale を 1〜2 文で要約．120 文字以内を推奨

例:

```markdown
## TL;DR

- **PKG-LAYOUT-001** (required): 新規パッケージは src/ layout を採用する．
  テストが install 済みパッケージに対して実行され import 漏れを早期検出できる．
- **PKG-LAYOUT-002** (required): tests/ は src/ の外に置く．
  テストコードをパッケージに含めないため．
```

### 3.2 allowed-mcp-read ブロック (LAYER 2)

本文中の重要なコード例・意思決定フローを，ルールに紐付けて切り出すブロック．
agent が TL;DR で足りないとき `get_rule_detail` 経由で読む．

構文:

```markdown
:::{.allowed-mcp-read label="<label>" rules="<ID>[,<ID>...]"}
内容 (コードブロック，散文どちらでも可)
:::
```

| 属性 | 必須 | 意味 |
|---|---|---|
| `label` | 必須 | ブロックの一意名．catalog 全体で一意．命名は §3.3 |
| `rules` | 必須 | 紐付く Rule ID．カンマ区切りで複数可．front matter の `rules` に実在すること |

1 ブロックを複数ルールから参照してよい (例: Anti-pattern は複数ルール違反を示す)．

### 3.3 label 命名規則

```
<slug 由来の短い接頭辞>-<内容を表す名詞句>

例:
fixture-basic-example
fixture-scope-decision
fixture-session-mutable-antipattern
src-layout-example
```

- 内容を表す名詞句で，catalog 全体で一意
- slug の接頭辞は付けてよいが冗長なら省略可
- whitespace / スラッシュ / クォートを含めない

### 3.4 ブロックを置く・置かない基準

| 置く | 置かない |
|---|---|
| good/bad のコード対比 | 歴史的背景・trivial な説明 |
| 意思決定フロー・選択基準 | 他章の説明の繰り返し |
| 設定ファイルのスニペット | Related リンク一覧 |
| 「なぜ」の核心 | TL;DR で代替できる内容 |

1 章あたり 2〜5 ブロックが目安．

---

## 4. 許可リスト (enum 定義)

### 4.1 phase

| 値 | 説明 | 主な applies-to.primary の例 |
|---|---|---|
| `init` | プロジェクト初期化 | `pyproject.toml`, `README.md`, `.gitignore` |
| `packaging` | パッケージング構造 | `pyproject.toml`, `src/**`, `MANIFEST.in` |
| `develop` | 開発中の日常作業 | `src/**/*.py` |
| `test` | テスト記述 | `tests/**`, `conftest.py` |
| `release` | リリース・公開 | `pyproject.toml`, `dist/` |
| `ci` | CI/CD 設定 | `.github/workflows/*.yml` |
| `docs` | ドキュメント | `docs/`, `README.md` |

### 4.2 severity

| 値 | 意味 | MCP 側の扱い |
|---|---|---|
| `required` | 必ず従う | rerank/budget で絶対に落とさない．違反コードを生成しない |
| `recommended` | 強く推奨 | rerank/budget の対象．違反時は明示的に断る |
| `forbidden` | 禁止 | rerank/budget で絶対に落とさない．`must_not` に分離 |

### 4.3 rule-type

| 値 | 意味 |
|---|---|
| `structural` | ディレクトリ構造，ファイル配置 |
| `naming` | 命名規約 |
| `dependency` | 依存管理 |
| `process` | 手順，ワークフロー |
| `config` | 設定ファイルの書き方 |
| `style` | コーディングスタイル |

### 4.4 related-rules の type

| 値 | 意味 | MCP デフォルト展開 |
|---|---|---|
| `prerequisite` | 前提知識．高確率で必要 | する (1-hop) |
| `exception` | 例外時のみ関連 | しない (例外条件ヒット時のみ) |
| `contrasts` | 対比．通常は不要 | しない |
| `extends` | 発展．深掘り時のみ | しない |

### 4.5 maturity

| 値 | 意味 | MCP 側の扱い |
|---|---|---|
| `stable` (既定) | 十分に検証済み | 優先的に提示 |
| `draft` | 執筆中・議論中 | 提示するが rerank で末尾に寄せる |
| `experimental` | 試験的 | 明示要求時のみ |

### 4.6 difficulty

`beginner` / `intermediate` / `advanced`．任意フィールド．順位付けには使わない (参考情報)．

---

## 5. Rule ID 命名規則

### 5.1 形式

```
<CATEGORY>-<TOPIC>-<NNN>

正規表現: ^[A-Z]+-[A-Z]+-\d{3}$
```

- `CATEGORY`: 3-5 文字の大文字．§5.2 の許可リスト
- `TOPIC`: 3-10 文字の大文字．カテゴリ内の主題
- `NNN`: 3 桁通し番号 (001 起点)

### 5.2 CATEGORY 許可リスト

| プレフィックス | 領域 |
|---|---|
| `PKG` | パッケージング全般 (layout, version, deps, build) |
| `TEST` | テスト (pytest, fixture, mock, coverage) |
| `CI` | CI/CD (GitHub Actions, workflow) |
| `GIT` | Git 運用 (tag, branch, commit) |
| `DEV` | 開発環境・ツール (lint, format, type) |
| `UV` | uv によるパッケージ・環境管理 |

新カテゴリが必要になったらこの表に追記してから使う．

### 5.3 不変原則

- 一度発行した Rule ID は**意味を変えない**．章のリネーム・分割でも ID は維持
- 廃止したルールの ID は**再利用しない** (番号スキップ可)
- ID はコード中のコメント (`# Follows PKG-LAYOUT-001`) から参照されるため，
  ID を変えると既存コードの参照が壊れる

### 5.4 新規採番手順

1. §5.5 の採番台帳で対象 `<CATEGORY>-<TOPIC>-` の最大番号を確認
2. 最大番号 + 1 を採番
3. 採番台帳に追記

### 5.5 採番台帳

> 発行済み Rule ID を記録する．章を書くたびに更新する．
> 初版では未発行のため，採番ルールのみ記載．実際の ID が発行され次第ここに追記する．

| Rule ID 範囲 | 用途 | 最大発行番号 |
|---|---|---|
| `PKG-LAYOUT-NNN` | パッケージレイアウト | (未発行) |
| `PKG-VERSION-NNN` | バージョニング | (未発行) |
| `PKG-DEPS-NNN` | 依存管理 | (未発行) |
| `PKG-TESTPYPI-NNN` | TestPyPI 公開 | (未発行) |
| `TEST-NAMING-NNN` | テスト命名 | (未発行) |
| `TEST-FIXTURE-NNN` | fixture 設計 | (未発行) |
| `TEST-PARAM-NNN` | parametrize | (未発行) |
| `TEST-MOCK-NNN` | mock / patch | (未発行) |
| `TEST-CONF-NNN` | conftest.py | (未発行) |
| `TEST-COV-NNN` | カバレッジ | (未発行) |
| `CI-NAMING-NNN` | workflow 命名 | (未発行) |
| `UV-INIT-NNN` | uv 初期化 | (未発行) |
| `GIT-TAG-NNN` | git tag 運用 | (未発行) |

新しい `<CATEGORY>-<TOPIC>` を起こしたらこの表に行を追加する．

---

## 6. lint で検証される制約

`scripts/lint-rules.py` が `rules-catalog.json` に対して検証する項目．
執筆者はこれらを満たすこと．

- Rule ID が正規表現 `^[A-Z]+-[A-Z]+-\d{3}$` にマッチ
- Rule ID が catalog 全体で重複なし
- `slug` が kebab-case で一意
- `phase` / `severity` / `rule-type` / `maturity` が許可リスト内
- `related-rules[].type` が許可リスト内
- `related-rules[].id` が catalog に実在 (dangling 参照なし)
- `exceptions[].ref_rule` が catalog に実在
- `statement` が 10〜200 文字
- `rationale` が空でない
- `applies-to.primary` が 1 件以上
- `## TL;DR` セクションが存在し，全 Rule ID を含む
- 各ルールに `tldr` が抽出される
- `tldr` が 120 文字以内
- `allowed-mcp-read` の `label` が catalog 全体で一意
- `allowed-mcp-read` の `rules` 属性 ID が front matter の `rules` に実在

---

## 7. catalog への変換 (build-rules-catalog.py が行うこと)

`scripts/build-rules-catalog.py` は各 `.qmd` の front matter と本文から
`_book/rules-catalog.json` を生成する．主な変換:

- `applies-to` を `{primary, contextual}` に正規化 (旧形式は primary 扱い)
- `related-rules` を `{id, type}` に正規化 (旧形式は type=prerequisite)
- `## TL;DR` から各 Rule ID の `tldr` を抽出
- `allowed-mcp-read` ブロックを抽出し `mcp_blocks` に格納，ルールに `mcp_block_labels` を付与
- 各ルールの `vector_text` (statement + rationale + tldr) を生成 (ベクター検索用)
- `applies-to` から `phase_inference` テーブル (glob → phase) を集約
- `chapter_url` を `_quarto.yml` の `site-url` から生成

catalog のスキーマバージョンは現在 `1.3`．

---

## 8. 変更管理

このスキーマを変更する場合:

1. このファイルを先に更新する
2. `scripts/build-rules-catalog.py` を追従
3. `scripts/lint-rules.py` を追従
4. MCP サーバーの `src/catalog/types.ts` を追従
5. catalog のスキーマバージョンを上げる
6. 既存章への影響を確認 (破壊的変更なら移行手順を記載)

スキーマの後方互換 (旧形式の受理) は `build-rules-catalog.py` の正規化関数で吸収する．
