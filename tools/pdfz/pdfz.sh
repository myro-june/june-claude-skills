#!/bin/zsh
# pdfz — PDF 용량 압축
#   1) 텍스트를 유지하는 Ghostscript 압축을 먼저 시도
#   2) 효과가 미미하면(폰트 깨진 PDF 등) 자동으로 이미지화(200dpi)로 전환
#   결과는 원본 옆에 "<이름>_압축.pdf" 로 저장하고 완료 알림을 띄운다.
emulate -L zsh
setopt no_nomatch

GS=/opt/homebrew/bin/gs
[[ -x "$GS" ]] || GS=$(command -v gs)
PYZ="$HOME/.local/share/pdfz/venv/bin/python"

human() { awk -v b="$1" 'BEGIN{printf "%.1fMB", b/1048576}'; }
notify() { osascript -e "display notification \"$2\" with title \"$1\" subtitle \"$3\"" >/dev/null 2>&1; }

if [[ -z "$GS" ]]; then
  notify "PDF 압축" "Ghostscript(gs)를 찾을 수 없습니다. 'brew install ghostscript' 필요" ""
  exit 1
fi

for f in "$@"; do
  case "${f:l}" in
    *.pdf) ;;
    *) continue ;;
  esac
  [[ -f "$f" ]] || continue

  dir="${f:h}"; name="${f:t:r}"
  out="$dir/${name}_압축.pdf"
  orig=$(stat -f%z "$f")
  method=""; final=0

  # 1) 텍스트 유지 압축 (Ghostscript /ebook)
  tmp="$(mktemp -t pdfz_XXXXXX).pdf"
  "$GS" -sDEVICE=pdfwrite -dCompatibilityLevel=1.5 -dPDFSETTINGS=/ebook \
        -dNOPAUSE -dQUIET -dBATCH -dDetectDuplicateImages=true \
        -sOutputFile="$tmp" "$f" 2>/dev/null
  gsz=$(stat -f%z "$tmp" 2>/dev/null || echo 0)

  if [[ "$gsz" -gt 1000 && "$gsz" -lt $(( orig * 85 / 100 )) ]]; then
    # 15% 이상 줄었으면 텍스트 살린 결과 채택
    mv -f "$tmp" "$out"
    method="텍스트 유지"; final=$gsz
  else
    rm -f "$tmp"
    # 2) 이미지화 폴백 (200dpi JPEG → PDF, 원본 페이지 크기 보존)
    td="$(mktemp -d -t pdfz)"
    "$GS" -sDEVICE=jpeg -dJPEGQ=85 -r200 -dNOPAUSE -dBATCH -dQUIET \
          -sOutputFile="$td/p%d.jpg" "$f" 2>/dev/null
    if [[ -x "$PYZ" ]] && ls "$td"/p*.jpg >/dev/null 2>&1; then
      "$PYZ" - "$out" "$td" <<'PY'
import sys, os, glob, img2pdf
out, td = sys.argv[1], sys.argv[2]
imgs = sorted(glob.glob(os.path.join(td, "p*.jpg")),
              key=lambda p: int("".join(c for c in os.path.basename(p) if c.isdigit()) or 0))
with open(out, "wb") as fo:
    fo.write(img2pdf.convert(imgs, layout_fun=img2pdf.get_fixed_dpi_layout_fun((200, 200))))
PY
      method="이미지화"; final=$(stat -f%z "$out" 2>/dev/null || echo 0)
    fi
    rm -rf "$td"
  fi

  if [[ "${final:-0}" -gt 0 ]]; then
    if [[ "$final" -ge "$orig" ]]; then
      # 더 커졌으면(이미 최적화된 PDF) 결과 폐기하고 원본 유지 안내
      rm -f "$out"
      notify "PDF 압축" "이미 최적화된 PDF라 더 줄지 않아 원본을 유지합니다" "${name}.pdf"
    else
      pct=$(( 100 - final * 100 / orig ))
      notify "PDF 압축 완료 (${method})" "$(human $orig) → $(human $final)  (−${pct}%)" "${name}_압축.pdf"
    fi
  else
    notify "PDF 압축 실패" "처리 중 오류가 발생했습니다" "${name}.pdf"
  fi
done
