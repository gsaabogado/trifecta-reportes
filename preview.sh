#!/bin/bash
# Auto-preview: converts docx to PDF and opens in Skim with auto-reload.
# Usage: ./preview.sh report_output_es.docx
#
# Skim auto-reloads PDFs by default. Just re-run this script (or the
# generate command) and Skim picks up the new PDF automatically.

DOCX="${1:?Usage: ./preview.sh <file.docx>}"
DIR="$(dirname "$DOCX")"
BASE="$(basename "$DOCX" .docx)"
PDF="$DIR/$BASE.pdf"

echo "Converting: $DOCX → $PDF"
/opt/homebrew/bin/soffice --headless --convert-to pdf --outdir "$DIR" "$DOCX" 2>/dev/null

if [ -f "$PDF" ]; then
    echo "Opening in Skim (auto-reload enabled)..."
    open -a Skim "$PDF"
    echo "Done. Re-run generate + this script to refresh."
else
    echo "ERROR: PDF conversion failed."
    exit 1
fi
