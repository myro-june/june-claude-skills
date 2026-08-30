#!/bin/bash
# pdfz 제거 — Quick Action과 엔진/venv를 삭제한다.
# (Ghostscript는 다른 곳에서도 쓸 수 있어 남겨둔다.)
set -uo pipefail

PREFIX="$HOME/.local/share/pdfz"
SERVICES="$HOME/Library/Services"
WORKFLOW_NAME="PDF 압축.workflow"

echo "▶ pdfz 제거"
rm -rf "$SERVICES/$WORKFLOW_NAME" && echo "✓ Quick Action 제거"
rm -rf "$PREFIX"                  && echo "✓ 엔진/venv 제거 ($PREFIX)"

/System/Library/CoreServices/pbs -flush >/dev/null 2>&1 || true
killall Finder 2>/dev/null || true

echo "✅ 제거 완료."
echo "   Ghostscript는 남겨뒀습니다. 필요 없으면: brew uninstall ghostscript"
