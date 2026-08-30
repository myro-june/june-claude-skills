# pdfz — macOS PDF 용량 압축 (Finder 우클릭)

PDF를 **Finder에서 우클릭 → "PDF 압축"** 한 번으로 용량을 줄이는 macOS 유틸리티.
원본 옆에 `<이름>_압축.pdf` 를 만들고 결과를 알림으로 보여준다.

## 동작 방식 (자동 판단)

| 단계 | 처리 | 결과 |
|------|------|------|
| 1차 | Ghostscript `/ebook` 압축 시도 | **15% 이상** 줄면 채택 → **텍스트 유지** |
| 2차 | 1차 효과가 미미하면 자동 전환 | 200dpi 이미지화(JPEG) → **모양 100% 보존**, 페이지 크기 유지 |
| 예외 | 이미 최적화돼 더 안 줄면 | 원본 유지 + 알림 |

즉 보통 PDF는 텍스트를 살린 채 줄고, 폰트가 비표준으로 박혀 gs가 못 줄이는 PDF(예: 일부 macOS 생성 문서)만 자동으로 이미지화된다.

> ⚠️ 이미지화된 PDF는 텍스트 선택/복사가 안 되고, 채용사이트의 자동 파싱(ATS)이 글자를 못 읽는다. 사람이 보거나 이메일/출력 용도엔 문제없다.

## 요구사항

- macOS
- [Homebrew](https://brew.sh) — Ghostscript 설치에 사용
- Ghostscript, Python 3 — `install.sh`가 없으면 자동 설치/구성

## 설치

```bash
git clone https://github.com/myro-june/june-claude-skills.git
cd june-claude-skills/tools/pdfz
./install.sh
```

설치되는 것:

| 위치 | 내용 |
|------|------|
| `~/.local/share/pdfz/pdfz.sh` | 압축 엔진 |
| `~/.local/share/pdfz/venv/`   | 이미지화 폴백용 파이썬 환경 (img2pdf) |
| `~/Library/Services/PDF 압축.workflow` | Finder Quick Action |

## 사용법

1. Finder에서 **PDF 우클릭** (여러 개 선택 가능)
2. **빠른 동작(Quick Actions) → PDF 압축**
3. 원본 옆에 `<이름>_압축.pdf` 생성, 완료 알림 표시 (예: `6.3MB → 1.5MB (−77%)`)

메뉴에 안 보이면 `시스템 설정 → 키보드 → 키보드 단축키 → 서비스` 에서 "PDF 압축"을 켠다.

### 터미널에서도

```bash
~/.local/share/pdfz/pdfz.sh 파일1.pdf 파일2.pdf
```

## 제거

```bash
cd june-claude-skills/tools/pdfz
./uninstall.sh
```

## 압축 강도 바꾸기

`pdfz.sh` 상단부의 값을 조정:

- 텍스트 유지 압축 화질: `-dPDFSETTINGS=/ebook` → `/screen`(작게) 또는 `/printer`(고화질)
- 이미지화 해상도/화질: `-r200`(dpi), `-dJPEGQ=85`(품질)
