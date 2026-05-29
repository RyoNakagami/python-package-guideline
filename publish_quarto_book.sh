#!/bin/bash
# ------------------------------------------------
# Script: publish_quarto_book.sh
# Purpose: Automatically publish Quarto book to GitHub Pages
# ------------------------------------------------

set -e  # Exit immediately if a command exits with a non-zero status

# Publish Quarto book to gh-pages without prompt and without opening browser
PRE_COMMIT_ALLOW_NO_CONFIG=1 uv run quarto publish gh-pages --no-prompt --no-browser

echo "✅ Quarto book published to gh-pages successfully."
