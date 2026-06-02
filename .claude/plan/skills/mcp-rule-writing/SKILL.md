---
name: mcp-rule-writing
description: |
  Quarto Book (python-package-guideline 等) の章に「ルール」を追加・編集するときに使う．
  .qmd の front matter (rules)，## TL;DR，allowed-mcp-read ブロックを，schema-config.yml に
  準拠した形で生成する．「ルールを追加」「この章をルール化」「front matter を書いて」
  「Rule ID を採番」「TL;DR を書いて」のような依頼，または book/**/*.qmd を編集して
  ルールを足す作業で必ず発火する．catalog (rules-catalog.json) を読む MCP サーバーとは別物で，
  これは「ルールを書く側」を助ける Skill．
---

# mcp-rule-writing — Quarto Book にルールを書くための Skill

この Book は，各章の front matter に機械可読な「ルール」を持ち，
それを `build-rules-catalog.py` が `rules-catalog.json` に変換し，
`quarto-book-mcp` が Claude Code に配信する．この Skill は**ルールを書く側**を助ける．

## 役割分担 (重要)

| 主体 | 担当 |
|---|---|
| Claude Code (この Skill) | front matter / TL;DR / allowed-mcp-read を**書く**，Rule ID を採番，スキーマ自己点検 |
| RyoNak (人間) | `uv run quarto render` と `uv run python scripts/lint-rules.py` を**実行**，lint 結果を判断，コミット |

Claude Code の責務は「スキーマ準拠のルールを書く」ところまで．
render (catalog 生成) と lint (検証) は人間が実行する．Claude Code は書き終えたら
その実行を**促す**だけで，勝手に走らせない．

ルールを追加・編集するときは，必ず `scripts/schema-config.yml` の制約に準拠させる．
スキーマの単一の真実源は `RULES_SCHEMA.md` と `scripts/schema-config.yml`．

## 章の構造 (必ずこの順)

```
front matter (YAML)   ← 機械可読なルール定義
## TL;DR              ← LAYER 1．各 Rule ID を 1 行で要約 (2段検索の段階2 / agent が最初に読む)
本文                   ← allowed-mcp-read ブロックを含む
## Related            ← 関連章リンク (任意)
```

## front matter スキーマ (準拠必須)

```yaml
---
title: "章のタイトル"
slug: kebab-case-unique           # ^[a-z0-9]+(-[a-z0-9]+)*$ ，catalog 全体で一意
phase: [test]                     # 下記 enum から 1 つ以上．空不可
applies-to:
  primary:                        # このルールが直接対象とするファイル (高スコア)．1 件以上
    - "tests/**/test_*.py"
    - "tests/conftest.py"
  contextual:                     # 周辺で参照されるファイル (低スコア)．任意
    - "src/**"
rule-type: structural             # 下記 enum
rules:
  - id: TEST-FIXTURE-001          # ^[A-Z]+-[A-Z]+-\d{3}$ ，catalog 全体で一意・不変
    statement: 複数テストで共有する fixture は conftest.py に置く   # 10〜200 字・1 文・規範
    severity: required            # required / recommended / forbidden
    maturity: stable              # stable(既定) / draft / experimental
    rationale: |                  # なぜそうするかの技術的根拠．空不可
      pytest が conftest.py を自動ロードするため明示的 import が不要になる．
    exceptions:                   # 任意．条件付き例外
      - condition: 単一テストファイル内でしか使わない fixture
        ref_rule: TEST-FIXTURE-002
related-rules:                    # 任意．章レベル (全ルールが同じ related を持つ)
  - id: TEST-CONF-001
    type: prerequisite            # prerequisite / exception / contrasts / extends
---
```

## 許可リスト (scripts/schema-config.yml と一致させる)

- **phase**: `init` `packaging` `develop` `test` `release` `ci` `docs`
- **severity**: `required` `recommended` `forbidden`
- **rule_type**: `structural` `naming` `dependency` `process` `config` `style`
- **relation type**: `prerequisite` `exception` `contrasts` `extends`
- **maturity**: `stable` `draft` `experimental`
- **category** (Rule ID の接頭辞): `PKG` `TEST` `CI` `GIT` `DEV` `UV`

## 制約 (constraints)

| 項目 | 制約 |
|---|---|
| statement 長さ | 10〜200 文字．1 文で言い切る規範文 |
| tldr 長さ | 120 文字以内 (## TL;DR の各行) |
| Rule ID | `^[A-Z]+-[A-Z]+-\d{3}$` (例 `PKG-LAYOUT-001`) |
| slug | `^[a-z0-9]+(-[a-z0-9]+)*$` (kebab-case) |
| rationale | 空にしない |
| applies-to.primary | 1 件以上 |

## Rule ID 採番の手順

1. カテゴリ (`PKG`/`TEST`/`CI`/`GIT`/`DEV`/`UV`) と TOPIC を決める (例 `TEST-FIXTURE`)
2. `RULES_SCHEMA.md` の採番台帳，または既存の `book/**/*.qmd` を grep して
   `<CATEGORY>-<TOPIC>-` の最大番号を確認する
3. 最大 + 1 を採番 (3 桁ゼロ詰め，例 `001`)
4. **一度発行した Rule ID は意味を変えない・再利用しない** (コードのコメントから参照されるため)

採番前に必ず既存 ID を確認する:

```bash
grep -rhoE '[A-Z]+-[A-Z]+-[0-9]{3}' book/ | sort -u
```

## ## TL;DR の書き方 (2段検索の段階2で使われる)

- `## TL;DR` 見出しで始める
- 各ルールを `- **<Rule ID>** (<severity>): <要点>` の形で 1 行
- 全 Rule ID を必ず含める (lint が網羅を検証)
- 各行は statement + 理由を 1〜2 文に圧縮．120 字以内
- statement (段階1) と tldr (段階2) は粒度を変える:
  statement = 短い規範文 / tldr = 要点 + 理由の散文

例:

```markdown
## TL;DR

- **TEST-FIXTURE-001** (required): 共有 fixture は conftest.py に置く．
  pytest が自動ロードし import 不要になるため．
- **TEST-FIXTURE-002** (recommended): 重いリソースは scope="module" 以上を検討．
  function スコープは毎テスト再生成され遅いため．
```

## allowed-mcp-read ブロックの書き方

本文中の重要なコード例・意思決定フローを，Rule ID に紐付けて切り出す．
agent が `get_rule_detail` で取得する LAYER 2．

```markdown
::: {.allowed-mcp-read label="fixture-basic-example" rules="TEST-FIXTURE-001"}
```python
@pytest.fixture()
def db_connection():
    conn = create_connection()
    yield conn
    conn.close()
```
:::
```

- `label`: catalog 全体で一意．空白/スラッシュ/クォートを含めない
- `rules`: 紐付く Rule ID．カンマ区切りで複数可 (1 ブロックを複数ルールで共有してよい)
- `:::` と `{` の間のスペースは有無どちらでも可 (catalog 生成は両対応)
- 1 章あたり 2〜5 ブロックが目安．good/bad のコード対比，意思決定フロー，設定スニペットに使う

## ルールを持たない章

カテゴリ扉ページ (`index.qmd`) や用語集 (`glossary.qmd`) は `rules` を書かない．
`build-rules-catalog.py` が自動でスキップする．`slug` も不要．

## 書いた後の検証 (人間が実行する)

ルールを書き終えたら，**RyoNak (人間) が**以下を実行して確認する．
これらは Claude Code が自動実行するものではない．render は副作用が大きく，
lint の結果 (error を直すか warning を許容するか) は人間が判断するため．

Claude Code は，ルールを書き終えたら**この 2 コマンドの実行を人間に促す**だけでよい．

```bash
uv run quarto render                     # post-render で catalog 生成
uv run python scripts/lint-rules.py      # スキーマ違反を検出
```

lint の error は 0 にする．related の dangling 参照は warning (段階移行中は許容)．
Claude Code が事前にスキーマ準拠を点検しておけば，人間の lint で error が出にくい．

## 自己点検チェックリスト (Claude Code が生成・編集直後に確認)

人間が render/lint する前に，Claude Code 側でこれを点検しておく．
ここを通しておけば，人間の lint で error が出にくくなる．

- [ ] slug は kebab-case で catalog 全体に一意
- [ ] Rule ID は `^[A-Z]+-[A-Z]+-\d{3}$`，カテゴリは許可リスト内，重複なし
- [ ] statement は 10〜200 字の 1 文・規範文 (「〜する/しない」)
- [ ] severity / maturity / rule-type / phase が許可リスト内
- [ ] rationale が空でない
- [ ] applies-to.primary が 1 件以上
- [ ] ## TL;DR が全 Rule ID を含み，各行 120 字以内
- [ ] allowed-mcp-read の label が一意，rules 属性が front matter の id に実在
- [ ] exceptions の ref_rule が実在する Rule ID

## やってはいけないこと

- 既存 Rule ID の意味変更・再利用 (参照が壊れる)
- statement に複数の規範を詰め込む (1 ルール 1 規範．分けて別 ID にする)
- TL;DR に Rule ID を書き忘れる (lint error)
- 許可リストにない phase / severity / category を使う
- schema-config.yml と RULES_SCHEMA.md を片方だけ更新する (両方同時に)
