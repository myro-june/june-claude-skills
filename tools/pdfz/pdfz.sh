#!/bin/zsh
# pdfz — PDF 용량 압축 (Finder Quick Action / CLI 공용 래퍼)
#   실제 로직은 pdfz_engine.py 가 담당:
#     텍스트 유지(gs) 시도 → PDFKit 검증 → 안 되면 이미지 모드(예산 내 최대 화질) → 재검증
#   결과는 원본 옆 "<이름>_압축.pdf" 로 저장하고 알림을 띄운다.
#   용량 예산은 PDFZ_MAX_MB(기본 5)로 조정.
emulate -L zsh
setopt no_nomatch

PREFIX="$HOME/.local/share/pdfz"
PYZ="$PREFIX/venv/bin/python"
ENGINE="$PREFIX/pdfz_engine.py"
TAB=$'\t'

notify() { osascript -e "display notification \"$2\" with title \"$1\" subtitle \"$3\"" >/dev/null 2>&1; }
human()  { awk -v b="$1" 'BEGIN{printf "%.1fMB", b/1048576}'; }

if [[ ! -x "$PYZ" || ! -f "$ENGINE" ]]; then
  notify "PDF 압축" "설치가 필요합니다 (install.sh 실행)" ""
  exit 1
fi

for f in "$@"; do
  case "${f:l}" in
    *.pdf) ;;
    *) continue ;;
  esac
  [[ -f "$f" ]] || continue

  dir="${f:h}"; name="${f:t:r}"; out="$dir/${name}_압축저화질.pdf"

  res="$("$PYZ" "$ENGINE" "$f" "$out" 2>/dev/null)"

  if [[ "$res" == FAIL:* ]]; then
    notify "PDF 압축 실패" "${res#FAIL: }" "${name}.pdf"
    continue
  fi
  if [[ ! -f "$out" ]]; then
    notify "PDF 압축 실패" "결과 파일이 생성되지 않음" "${name}.pdf"
    continue
  fi

  method="${res%%${TAB}*}"
  rest="${res#*${TAB}}"
  orig="${rest%%${TAB}*}"
  final="${rest##*${TAB}}"
  [[ "$orig" == <-> ]]  || orig=$(stat -f%z "$f")
  [[ "$final" == <-> ]] || final=$(stat -f%z "$out")

  if (( final >= orig )); then
    rm -f "$out"
    notify "PDF 압축" "이미 최적화된 PDF라 더 줄지 않아 원본을 유지합니다" "${name}.pdf"
  else
    pct=$(( 100 - final * 100 / orig ))
    notify "PDF 압축 완료 (${method})" "$(human $orig) → $(human $final)  (−${pct}%)" "${name}_압축저화질.pdf"
  fi
done
