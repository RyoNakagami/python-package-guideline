# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2026-06-02

### Changed

- **BREAKING**: Moved the rules catalog tooling out of this repository into the `scripts` git submodule (`https://github.com/RyoNakagami/quarto-mcp-book-scripts.git`). Cloning now requires `git submodule update --init` to obtain the scripts.
- Relocated `schema-config.yml` from `scripts/` to the repository root.

### Removed

- In-tree scripts now provided by the `scripts` submodule: `scripts/rules_catalog.py`, `scripts/build-rules-catalog.py`, and `scripts/lint-rules.py`.

### Fixed

- Corrected the documented catalog schema version in `RULES_SCHEMA.md` to `1.0`.

## [1.0.0] - 2026-06-02

### Added

- MCP rules catalog system: `scripts/rules_catalog.py` (core catalog builder), `scripts/build-rules-catalog.py` (CLI entry point), `scripts/lint-rules.py` (rule linter), and `scripts/schema-config.yml`.
- `RULES_SCHEMA.md` documenting the full rules schema for MCP skill definitions.
- Test suite for the rules catalog (`tests/test_rules_catalog.py`).
- MCP rule-writing skill (`.claude/plan/skills/mcp-rule-writing/SKILL.md`) with authoring and publish pre-flight guidelines.
- Testing chapter (`book/004_testing/index.qmd`, `book/004_testing/posts/test.qmd`).
- Packaging chapter covering src-layout vs flat-layout (`book/posts/src-layout-vs-flat-layout.qmd`).
- `pytest` and `ruff` as development dependencies in `pyproject.toml`.

### Changed

- Restructured book content directories: moved `posts/` under `book/` and reorganised chapter numbering in `_quarto.yml`.
- Expanded `index.qmd` with updated chapter overview and navigation.
- Improved `publish_quarto_book.sh` with additional pre-flight checks.

## [0.1.0]

### Added

- Quarto book scaffolding with `_quarto.yml` configuration and `index.qmd` entry point.
- Quarto extensions: `pseudocode`, `reveal_vspace`, `shield_badge`, and `custom-numbered-blocks`.
- Appendix glossary (`posts/999_appendix/glossary.qmd`) with a custom glossary generator.
- Project documentation: branch strategy, commit rules, and versioning policy under `docs/`.
- Light/dark theming (`include/light.scss`, `include/dark.scss`, `include/custom.scss`, `styles.css`) plus MathJax, web font, and Google Tag Manager includes.
- Bibliography support via `references.bib`, `references.qmd`, and `reference.csl`.
- `uv`-managed Python environment (`pyproject.toml`, `uv.lock`) requiring Python >= 3.13.
- Pre-commit configuration and VS Code code snippets.
- `publish_quarto_book.sh` script for publishing the book.
- GitHub issue/PR templates, repository metadata, and label/PR-posting workflows.
