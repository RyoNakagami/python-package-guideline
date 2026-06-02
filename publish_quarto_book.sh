#!/bin/bash
# ------------------------------------------------
# Script: publish_quarto_book.sh
# Purpose: Automatically publish Quarto book to GitHub Pages
# ------------------------------------------------

set -e  # Exit immediately if a command exits with a non-zero status

# Stage 1: Render and lint
echo "▶ Stage 1: rendering book and checking rules..."
uv run quarto render
uv run python scripts/lint-rules.py
echo "✅ Stage 1 passed."

# Stage 2: Confirm before publishing
read -r -p "Publish to GitHub Pages? [y/N] " reply
if [[ ! "$reply" =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 0
fi

# Publish Quarto book to gh-pages without prompt and without opening browser
PRE_COMMIT_ALLOW_NO_CONFIG=1 uv run quarto publish gh-pages --no-prompt --no-browser

echo "✅ Quarto book published to gh-pages successfully."
