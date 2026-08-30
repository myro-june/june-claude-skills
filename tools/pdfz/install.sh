#!/bin/bash
# pdfz 설치 — 새 맥에서도 "지금처럼 바로" 쓰기 위한 설치 스크립트.
#   1) Ghostscript 확인/설치 (Homebrew)
#   2) ~/.local/share/pdfz 에 엔진 + 파이썬 venv(img2pdf) 구성
#   3) ~/Library/Services 에 Finder Quick Action 설치 + 등록
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="$HOME/.local/share/pdfz"
SERVICES="$HOME/Library/Services"
WORKFLOW_NAME="PDF 압축.workflow"

echo "▶ pdfz 설치 시작"

# 0) macOS 확인
if [[ "$(uname)" != "Darwin" ]]; then
  echo "✗ 이 도구는 macOS 전용입니다."; exit 1
fi

# 1) Ghostscript
if command -v gs >/dev/null 2>&1 || [[ -x /opt/homebrew/bin/gs ]]; then
  echo "✓ Ghostscript 확인됨"
elif command -v brew >/dev/null 2>&1; then
  echo "· Ghostscript 설치 중 (brew)..."
  brew install ghostscript
else
  echo "✗ Ghostscript도 Homebrew도 없습니다."
  echo "  https://brew.sh 설치 후 'brew install ghostscript' 하거나 gs를 직접 설치한 뒤 다시 실행하세요."
  exit 1
fi

# 1-b) mutool (결과 검증용 페이지 추출) — mupdf-tools
if command -v mutool >/dev/null 2>&1 || [[ -x /opt/homebrew/bin/mutool ]]; then
  echo "✓ mutool 확인됨"
elif command -v brew >/dev/null 2>&1; then
  echo "· mupdf-tools 설치 중 (brew)..."
  brew install mupdf-tools
else
  echo "⚠ mutool 없음 — 결과 검증(페이지 손실 감지)이 생략됩니다."
fi

# 2) Python venv + img2pdf (이미지화 폴백용)
PY=""
for c in /opt/homebrew/bin/python3 python3; do
  if command -v "$c" >/dev/null 2>&1; then PY="$(command -v "$c")"; break; fi
done
if [[ -z "$PY" ]]; then
  echo "✗ python3가 필요합니다. 'brew install python' 후 다시 실행하세요."; exit 1
fi

mkdir -p "$PREFIX"
if [[ ! -x "$PREFIX/venv/bin/python" ]]; then
  echo "· 파이썬 가상환경 생성..."
  "$PY" -m venv "$PREFIX/venv"
fi
echo "· img2pdf 설치..."
"$PREFIX/venv/bin/pip" install -q --disable-pip-version-check img2pdf

# 3) 엔진 스크립트 배치
install -m 0755 "$SCRIPT_DIR/pdfz.sh" "$PREFIX/pdfz.sh"
install -m 0644 "$SCRIPT_DIR/pdfz_engine.py" "$PREFIX/pdfz_engine.py"
echo "✓ 엔진: $PREFIX/pdfz.sh + pdfz_engine.py"

# 4) Finder Quick Action 설치
mkdir -p "$SERVICES"
rm -rf "$SERVICES/$WORKFLOW_NAME"
cp -R "$SCRIPT_DIR/$WORKFLOW_NAME" "$SERVICES/$WORKFLOW_NAME"
echo "✓ Quick Action: $SERVICES/$WORKFLOW_NAME"

# 5) 서비스 등록 + Finder 반영
/System/Library/CoreServices/pbs -flush  >/dev/null 2>&1 || true
/System/Library/CoreServices/pbs -update >/dev/null 2>&1 || true
killall Finder 2>/dev/null || true

echo ""
echo "✅ 설치 완료!"
echo "   Finder에서 PDF 우클릭 → 빠른 동작(Quick Actions) → 'PDF 압축'"
echo "   (메뉴에 안 보이면: 시스템 설정 → 키보드 → 키보드 단축키 → 서비스 에서 체크)"
