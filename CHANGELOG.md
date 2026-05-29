# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
