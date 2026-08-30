# pdfz — macOS PDF 용량 압축 (Finder 우클릭)

PDF를 **Finder에서 우클릭 → "PDF 압축"** 한 번으로 줄이는 macOS 유틸리티.
원본 옆에 `<이름>_압축저화질.pdf` 를 만들고 결과를 알림으로 보여준다.

핵심은 **"실제 뷰어(PDFKit)로 검증"** 한다는 것. 압축 결과가 Preview·노션 등에서
깨지지(페이지 백지) 않는지 확인하고, 깨졌으면 자동으로 안전한 방식으로 다시 만든다.

## 동작 방식 (스마트 모드)

```
1) Ghostscript 텍스트 유지 압축(/ebook) 시도
      └ PDFKit로 전 페이지 검증 + 용량<예산 통과?
           → YES: 채택  (텍스트 선택 가능 + 최소 용량)   [일반 문서·이력서]
           → NO : 2)로
2) 이미지 모드 — 예산 미만에서 최대 dpi(화질)를 탐색해 렌더
                                                      [디자인·포폴 등]
3) 최종물 PDFKit 재검증 (안전망) → 알림
```

- **용량 예산**: 기본 **5MB**. macOS Finder·노션은 십진(1MB=1,000,000B)으로 표시하므로
  그 기준으로 계산하고 안전마진을 둔다. `PDFZ_MAX_MB` 환경변수로 조정.
- **검증**: `mutool`로 페이지를 하나씩 추출 → `sips`(=macOS PDFKit)로 렌더 →
  원본 대비 백지가 된 페이지가 있으면 실패로 보고 이미지 모드로 전환.
  (mutool의 자체 렌더러는 깨진 걸 그려버려서 검증엔 반드시 PDFKit을 쓴다.)

> ⚠️ 이미지 모드로 만들어진 PDF는 텍스트 선택·복사가 안 된다(ATS 파싱 불가).
> 사람이 보거나 이메일·출력·노션 업로드 용도엔 문제없다.

## 요구사항

- macOS
- [Homebrew](https://brew.sh)
- Ghostscript, mupdf-tools(mutool), Python 3 — `install.sh`가 없으면 자동 설치/구성

## 설치

```bash
git clone https://github.com/myro-june/june-claude-skills.git
cd june-claude-skills/tools/pdfz
./install.sh
```

설치되는 것:

| 위치 | 내용 |
|------|------|
| `~/.local/share/pdfz/pdfz.sh` | Quick Action/CLI 래퍼 |
| `~/.local/share/pdfz/pdfz_engine.py` | 압축·검증 엔진 |
| `~/.local/share/pdfz/venv/` | 파이썬 환경 (img2pdf) |
| `~/Library/Services/PDF 압축.workflow` | Finder Quick Action |

## 사용법

1. Finder에서 **PDF 우클릭** (여러 개 선택 가능)
2. **빠른 동작(Quick Actions) → PDF 압축**
3. 원본 옆에 `<이름>_압축저화질.pdf` 생성, 완료 알림 (예: `9.5MB → 4.9MB (−49%, 이미지160dpi)`)

메뉴에 안 보이면 `시스템 설정 → 키보드 → 키보드 단축키 → 서비스`에서 "PDF 압축"을 켠다.

### 터미널에서도

```bash
~/.local/share/pdfz/pdfz.sh 파일1.pdf 파일2.pdf
# 예산을 바꾸려면(예: 3MB 미만):
PDFZ_MAX_MB=3 ~/.local/share/pdfz/pdfz.sh 파일.pdf
```

## 제거

```bash
cd june-claude-skills/tools/pdfz
./uninstall.sh
```

## 조정 포인트

- **용량 예산**: `PDFZ_MAX_MB`(기본 5). Finder/노션 표시 기준(십진 MB).
- **이미지 화질**: `pdfz_engine.py`의 `q=90`(JPEG 품질), `MAX_DPI`(상한).
- **검증 민감도**: `BLANK_RATIO`(원본 대비 이 비율 미만이면 소실로 판정), `VERIFY_WIDTH`.
