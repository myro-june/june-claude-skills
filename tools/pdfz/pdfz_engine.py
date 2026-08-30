#!/usr/bin/env python3
"""
pdfz 엔진 — PDF를 "예산(기본 5MB) 미만 최대 화질"로 압축하고, 실제 뷰어(PDFKit)로 검증한다.

전략(스마트 방식):
  1) Ghostscript 텍스트 유지 압축(/ebook) 시도
       → PDFKit 전 페이지 검증 통과 + 용량<예산 이면 채택 (텍스트 살림)
  2) 실패(뷰어에서 페이지 깨짐) 또는 예산 초과 → 이미지 모드
       → 예산 미만에서 최대 dpi를 탐색해 렌더 → img2pdf 조립
  3) 최종물을 PDFKit로 재검증 (안전망)

검증 방식: mutool로 페이지를 하나씩 추출 → sips(=macOS PDFKit)로 렌더 →
           원본 페이지 렌더 대비 결과가 사실상 백지면(내용 소실) 실패로 판정.
           mutool은 깨진 걸 그냥 그려버리므로 검증에는 반드시 sips(PDFKit)를 쓴다.

출력(stdout): "<method>\t<orig_bytes>\t<final_bytes>"  (성공)
             "FAIL: <reason>"                          (실패)
"""
import sys, os, subprocess, tempfile, glob, shutil, math

def _find(name, *fallbacks):
    for p in fallbacks:
        if os.path.exists(p):
            return p
    return shutil.which(name)

GS = _find("gs", "/opt/homebrew/bin/gs", "/usr/local/bin/gs")
MUTOOL = _find("mutool", "/opt/homebrew/bin/mutool", "/usr/local/bin/mutool")
SIPS = _find("sips", "/usr/bin/sips")

try:
    import img2pdf
except Exception as e:
    print(f"FAIL: img2pdf 로드 실패 ({e})")
    sys.exit(0)

# --- 검증 파라미터 ---
VERIFY_WIDTH = 500      # 페이지 렌더 가로 px (작게=빠름, 백지 판별엔 충분)
CONTENT_FLOOR = 6000    # 원본 페이지 렌더가 이 bytes 초과여야 '내용 있는 페이지'로 간주
BLANK_RATIO = 0.40      # 결과 렌더가 원본의 이 비율 미만이면 '내용 소실'로 판정
MAX_DPI = 250
MIN_DPI = 72

def run(cmd):
    return subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)

def log(*a):
    print(*a, file=sys.stderr)

def page_count(pdf):
    for cmd in ([MUTOOL, "info", pdf] if MUTOOL else None, ["pdfinfo", pdf]):
        if not cmd:
            continue
        try:
            out = subprocess.run(cmd, capture_output=True, text=True).stdout
            for line in out.splitlines():
                s = line.strip()
                if s.startswith("Pages:"):
                    return int(s.split(":", 1)[1].strip())
        except Exception:
            pass
    return 0

def render_page_bytes(pdf, page, tmpd, tag):
    """페이지 1장을 추출→PDFKit(sips)로 렌더한 PNG의 바이트 수(내용량 프록시)."""
    pg = os.path.join(tmpd, f"{tag}_{page}.pdf")
    png = os.path.join(tmpd, f"{tag}_{page}.png")
    run([MUTOOL, "merge", "-o", pg, pdf, str(page)])
    if not os.path.exists(pg):
        return -1
    run([SIPS, "-s", "format", "png", "--resampleWidth", str(VERIFY_WIDTH), pg, "--out", png])
    return os.path.getsize(png) if os.path.exists(png) else -1

_orig_cache = {}

def verify(original, candidate, tmpd, npages):
    """원본 대비 결과에서 내용이 소실된 페이지가 있으면 (False, 페이지번호)."""
    if not (MUTOOL and SIPS):
        return True, None  # 검증 도구 없으면 통과 처리(설치가 보장하지만 방어적으로)
    for p in range(1, npages + 1):
        if p not in _orig_cache:
            _orig_cache[p] = render_page_bytes(original, p, tmpd, "orig")
        o = _orig_cache[p]
        c = render_page_bytes(candidate, p, tmpd, "cand")
        if o > CONTENT_FLOOR and (c < 0 or c < o * BLANK_RATIO):
            log(f"  검증 실패: p{p} 원본 {o}B → 결과 {c}B")
            return False, p
    return True, None

def gs_textmode(inp, out):
    run([GS, "-sDEVICE=pdfwrite", "-dCompatibilityLevel=1.5", "-dPDFSETTINGS=/ebook",
         "-dNOPAUSE", "-dQUIET", "-dBATCH", "-dDetectDuplicateImages=true",
         f"-sOutputFile={out}", inp])
    return os.path.getsize(out) if os.path.exists(out) else 0

def render_images(inp, out, dpi, q, tmpd):
    for f in glob.glob(os.path.join(tmpd, "img_*.jpg")):
        os.remove(f)
    run([GS, "-sDEVICE=jpeg", f"-dJPEGQ={q}", f"-r{dpi}", "-dNOPAUSE", "-dBATCH", "-dQUIET",
         f"-sOutputFile={os.path.join(tmpd, 'img_%d.jpg')}", inp])
    imgs = sorted(glob.glob(os.path.join(tmpd, "img_*.jpg")),
                  key=lambda p: int("".join(c for c in os.path.basename(p) if c.isdigit()) or 0))
    if not imgs:
        return 0
    with open(out, "wb") as fo:
        fo.write(img2pdf.convert(imgs, layout_fun=img2pdf.get_fixed_dpi_layout_fun((dpi, dpi))))
    return os.path.getsize(out)

def image_mode(inp, out, budget, tmpd):
    """예산 미만에서 최대 dpi(화질) 탐색. q=90 고정, 필요 시 q 하향."""
    q = 90
    def size_at(dpi):
        return render_images(inp, out, dpi, q, tmpd)

    s150 = size_at(150)
    best = 150 if s150 <= budget else None

    if best is not None:
        # 위로 10dpi씩 오르며 예산 안에서 최대치
        d = 150
        while d + 10 <= MAX_DPI:
            if size_at(d + 10) <= budget:
                best = d = d + 10
            else:
                break
        # +5 미세조정
        if best + 5 <= MAX_DPI and size_at(best + 5) <= budget:
            best += 5
    else:
        # 150도 초과 → 아래로 내려가며 예산 진입
        d = 150
        while d - 10 >= MIN_DPI:
            d -= 10
            if size_at(d) <= budget:
                best = d
                break
        if best is None:
            best = MIN_DPI
            # 최저 dpi로도 초과면 q를 낮춰 마지막 시도
            for qq in (80, 70, 60):
                q = qq
                if size_at(MIN_DPI) <= budget:
                    break

    final = render_images(inp, out, best, q, tmpd)
    return best, q, final

def main():
    if len(sys.argv) < 3:
        print("FAIL: 사용법 pdfz_engine.py <in.pdf> <out.pdf>")
        return
    inp, out = sys.argv[1], sys.argv[2]
    # macOS Finder·Notion 등은 용량을 '십진 MB'(1MB=1,000,000바이트)로 표시/제한한다.
    # 이진(1,048,576)으로 잡으면 Finder에선 5MB를 넘겨 보이므로, 십진 MB로 계산하고
    # 100KB 안전 마진을 둬 확실히 그 아래로 떨어뜨린다.
    budget = int(float(os.environ.get("PDFZ_MAX_MB", "5")) * 1_000_000) - 100_000
    if not GS:
        print("FAIL: ghostscript(gs) 없음")
        return
    if not os.path.isfile(inp):
        print("FAIL: 입력 파일 없음")
        return

    orig_size = os.path.getsize(inp)
    npages = page_count(inp)
    if npages <= 0:
        print("FAIL: 페이지 수 확인 불가 (손상 PDF?)")
        return

    with tempfile.TemporaryDirectory(prefix="pdfz_") as tmpd:
        method = None
        # 1) 텍스트 유지(gs) 시도
        gs_out = os.path.join(tmpd, "gs.pdf")
        gs_size = gs_textmode(inp, gs_out)
        if 1000 < gs_size < orig_size and gs_size <= budget:
            ok, bad = verify(inp, gs_out, tmpd, npages)
            if ok:
                shutil.copyfile(gs_out, out)
                method = "텍스트유지"
            else:
                log(f"  gs 결과 p{bad} 깨짐 → 이미지 모드로 전환")
        elif gs_size > budget:
            log(f"  gs 결과 {gs_size} > 예산 {budget} → 이미지 모드")

        # 2) 이미지 모드 (예산 내 최대 화질)
        if method is None:
            dpi, q, _ = image_mode(inp, out, budget, tmpd)
            if not os.path.exists(out):
                print("FAIL: 이미지 변환 실패")
                return
            # 3) 안전망 재검증
            ok, bad = verify(inp, out, tmpd, npages)
            method = f"이미지{dpi}dpi" + ("" if ok else f"(경고:p{bad})")

        final_size = os.path.getsize(out)
    print(f"{method}\t{orig_size}\t{final_size}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"FAIL: 예외 {e}")
