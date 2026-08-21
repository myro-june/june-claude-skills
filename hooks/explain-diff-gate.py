#!/usr/bin/env python3
"""explain-diff-gate.py — PR 생성 전 diff 설명서 생성을 강제하는 PreToolUse 게이트.

동작 모드:
  (인자 없음)        PreToolUse 훅 모드. stdin JSON에서 gh pr create /
                     mcp__github__create_pull_request 를 감지하면 마커 검증.
                     설명서 없음/stale → exit 2 (차단, stderr 메시지가 Claude에 전달).
  --info             현재 레포의 base/브랜치/변경파일/출력경로를 JSON으로 출력.
                     diff설명 스킬이 게이트와 동일한 diff 범위를 잡기 위해 사용.
  --mark [--html P]  현재 diff 내용 해시로 마커 기록 (설명서 생성 직후 호출).
                     --html이 주어지면 먼저 무결성 검사를 통과해야 기록된다.
  --check-html P     설명서 HTML 무결성 검사만 단독 실행.
                     퀴즈 존재/data-answer 유효 범위/보기 2개 이상/해설의 본문
                     점프 링크(.jump) 존재/모든 내부 앵커(#) 대상 id 존재/정답
                     위치 분산에 더해, "누가 봐도 이해" 대리지표(핵심 요약 .tldr,
                     섹션 요지 .section-lead, 용어 사전 .glossary, .term 하한,
                     코드블록마다 .code-lead, 문단·문장 길이 상한)를 검사하고,
                     구조·시각 사양(상단 목차 .toc, 4섹션 id, flash #ff443a
                     2~3초, 점프 라벨 "본문에서 확인", .lab/.warnbox, pre-wrap,
                     smooth scroll, .term 2px dotted, glossary 내 .term,
                     .section-lead=<p>)까지 강제한다. 실패 시 exit 1 + 오류 목록.
  --check            현재 디렉토리 기준 마커 신선도 검사만 실행 (훅 모드와
                     동일 판정, stdin 불필요). gh 래퍼(~/.local/bin/gh) 등
                     Claude Code 밖 강제 지점이 호출한다. 실패 시 exit 2.
  --html-path        현재 브랜치 마커에 기록된 설명서 HTML 경로를 stdout에 출력.
                     PR 생성 성공 후 설명서를 띄우는 gh 래퍼가 호출한다.
                     마커/파일이 없으면 아무것도 출력하지 않고 exit 1.

신선도 판정: HEAD sha가 아니라 "base 대비 변경 파일 경로 + 워크트리 blob 해시"의
sha256을 쓴다. 같은 내용이면 커밋 전후로 해시가 동일하므로,
설명서 생성(커밋 전) → 커밋 → PR 흐름에서 stale 오판이 없다.

우회: Bash 명령 안에 SKIP_EXPLAIN=1 이 있으면 통과.
"""
import datetime
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT = os.path.expanduser("~/.claude/explain-diff")
SKILL_NAME = "diff설명"  # 사용자 레벨 스킬 등록명 (~/.claude/skills/diff설명)
SKILL_MD = os.path.expanduser("~/.claude/skills/diff설명/SKILL.md")
TEMPLATE_HTML = os.path.expanduser("~/.claude/skills/diff설명/template.html")
REQUIRED_SECTION_IDS = ("s-bg", "s-intuition", "s-code", "s-quiz")  # 4섹션 구조 앵커
MIN_TOC_LINKS = 3  # 상단 목차(.toc) 안 내부 앵커 하한
MIN_GLOSSARY_TERMS = 3  # 용어 사전(.glossary) 안 .term 하한
FLASH_COLOR = "#ff443a"  # 점프 하이라이트 샛빨간 배경 (SKILL.md Step 3)
MIN_QUIZZES = 5  # SKILL.md Step 3 사양
MIN_BOXES = 5  # 비유(🔎)/예시(▶) 블록 — SKILL.md "쉬운 설명 원칙"
MIN_SECTION_LEADS = 4  # 섹션 첫머리 한 줄 요지(.section-lead) — 분량/밀도 완화
MIN_TERMS = 5  # .term 용어 풀이 하한(구 "1개 이상") — 용어를 반드시 풀도록 상향
MAX_PARA_CHARS = 450  # 산문 <p> 한 문단 글자수 상한 — 밀도
MAX_SENTENCE_CHARS = 130  # 한 문장 글자수 상한 — 눈높이(비개발자도 읽힘)
# 코드 요약(.code-lead)은 개수 하한이 아니라 "<pre> 코드블록 수 이상"으로 강제한다
# — 코드를 한 줄도 안 읽어도 흐름이 이어지게 하려면 모든 코드블록에 요약이 필요하다.
PR_CMD_RE = re.compile(r"(?:^|[\s;&|(])(?:rtk\s+)?gh\s+pr\s+create\b")


def _git(args, cwd):
    # core.quotepath=off: 한글 등 non-ASCII 경로가 "\354..." 로 이스케이프되면
    # 파일 존재 확인과 blob 해시가 깨져 stale 감지가 누락된다.
    r = subprocess.run(
        ["git", "-c", "core.quotepath=off"] + args,
        cwd=cwd, capture_output=True, text=True,
    )
    return r.stdout.strip() if r.returncode == 0 else None


def repo_top(cwd):
    return _git(["rev-parse", "--show-toplevel"], cwd)


def default_base(top):
    """(base_rev, branch) — base는 기본 브랜치와의 merge-base.
    기본 브랜치 위이거나 base를 못 찾으면 HEAD(=워킹트리 변경만)."""
    ref = _git(["symbolic-ref", "--short", "refs/remotes/origin/HEAD"], top)
    if not ref:
        for c in ("origin/main", "origin/master", "main", "master"):
            if _git(["rev-parse", "--verify", "--quiet", c], top) is not None:
                ref = c
                break
    branch = _git(["branch", "--show-current"], top) or "detached"
    if not ref or ref.rsplit("/", 1)[-1] == branch:
        return "HEAD", branch
    mb = _git(["merge-base", ref, "HEAD"], top)
    return (mb or "HEAD"), branch


def changed_files(top, base):
    files = set()
    for out in (
        _git(["diff", "--name-only", base], top),
        _git(["ls-files", "-o", "--exclude-standard"], top),
    ):
        if out:
            files.update(l for l in out.splitlines() if l.strip())
    return sorted(f for f in files if not f.startswith(".omc/"))


def content_hash(top, base, files):
    h = hashlib.sha256()
    for f in files:
        p = os.path.join(top, f)
        if os.path.isfile(p):
            blob = _git(["hash-object", "--", f], top) or "unreadable"
        else:
            blob = "deleted"
        h.update(f"{f}\0{blob}\n".encode())
    return h.hexdigest()


def repo_slug(top):
    return os.path.basename(top) + "-" + hashlib.sha256(top.encode()).hexdigest()[:8]


def marker_path(top, branch):
    b = re.sub(r"[^A-Za-z0-9._가-힣-]", "_", branch or "detached")
    return os.path.join(ROOT, repo_slug(top), f".marker-{b}.json")


def collect(cwd):
    """공통 상태 수집. git 레포가 아니면 None."""
    top = repo_top(cwd)
    if not top:
        return None
    base, branch = default_base(top)
    files = changed_files(top, base)
    return {
        "top": top,
        "branch": branch,
        "base": base,
        "files": files,
        "hash": content_hash(top, base, files),
        "marker": marker_path(top, branch),
        "out_dir": os.path.join(ROOT, repo_slug(top)),
    }


def cmd_info(cwd):
    st = collect(cwd)
    if st is None:
        print(json.dumps({"error": "not a git repository"}))
        return 1
    date = datetime.date.today().isoformat()
    b = re.sub(r"[^A-Za-z0-9._가-힣-]", "_", st["branch"])
    st["suggested_html"] = os.path.join(st["out_dir"], f"{date}-{b}.html")
    print(json.dumps(st, ensure_ascii=False, indent=2))
    return 0


def check_html(path):
    """설명서 HTML 무결성 검사. 오류 문자열 목록 반환 (빈 리스트 = 통과)."""
    import html.parser

    class Scan(html.parser.HTMLParser):
        def __init__(self):
            super().__init__()
            self.ids = set()
            self.internal_hrefs = []  # href="#..." 앵커명
            self.quizzes = []  # {'answer', 'buttons', 'jumps'}
            self.terms = 0  # .term 용어 풀이 span
            self.diagrams = 0  # .diagram HTML/CSS 다이어그램
            self.boxes = 0  # .box 비유/예시 블록
            self.code_leads = 0  # .code-lead 코드 요약 문장
            self.section_leads = 0  # .section-lead 섹션 첫머리 한 줄 요지
            self.pres = 0  # <pre> 코드 블록 수
            self.tldr = False  # .tldr 핵심 요약(TL;DR) 블록
            self.glossary = False  # .glossary 용어 사전 블록
            self.paras = []  # 산문 <p> 텍스트 (문단/문장 길이 검사)
            self._p_depth = 0  # <p> 중첩 깊이 (0이면 문단 밖)
            self._p_buf = []  # 현재 <p> 안에서 모으는 텍스트
            self.labs = 0  # .lab 라벨 (비유 🔎 / 예시 ▶)
            self.warnboxes = 0  # .warnbox 예시 블록
            self.toc_links = 0  # 목차(.toc) 안 내부 앵커 수
            self._toc_tag = None
            self._toc_depth = 0
            self.glossary_terms = 0  # .glossary 안 .term 수
            self._gloss_tag = None
            self._gloss_depth = 0
            self.jump_texts = []  # .jump 링크 표시 텍스트 (라벨 규격 검사)
            self._in_jump = False
            self._jump_buf = []
            self.bad_lead_tags = 0  # <p>가 아닌 태그에 붙은 .section-lead

        def handle_starttag(self, tag, attrs):
            d = dict(attrs)
            if d.get("id"):
                self.ids.add(d["id"])
            cls = (d.get("class") or "").split()
            if self._toc_tag and tag == self._toc_tag:
                self._toc_depth += 1
            if self._gloss_tag and tag == self._gloss_tag:
                self._gloss_depth += 1
            if "toc" in cls and self._toc_tag is None:
                self._toc_tag = tag
                self._toc_depth = 1
            if "glossary" in cls and self._gloss_tag is None:
                self._gloss_tag = tag
                self._gloss_depth = 1
            if "lab" in cls:
                self.labs += 1
            if "warnbox" in cls:
                self.warnboxes += 1
            if "section-lead" in cls and tag != "p":
                self.bad_lead_tags += 1
            if "term" in cls:
                self.terms += 1
                if self._gloss_tag and self._gloss_depth > 0:
                    self.glossary_terms += 1
            if "diagram" in cls:
                self.diagrams += 1
            if "box" in cls:
                self.boxes += 1
            if "code-lead" in cls:
                self.code_leads += 1
            if "section-lead" in cls:
                self.section_leads += 1
            if "tldr" in cls:
                self.tldr = True
            if "glossary" in cls:
                self.glossary = True
            if tag == "pre":
                self.pres += 1
            if tag == "p":
                self._p_depth += 1
                self._p_buf = []
            if "quiz" in cls:
                self.quizzes.append(
                    {"answer": d.get("data-answer"), "buttons": 0, "jumps": 0}
                )
            elif self.quizzes and tag == "button":
                self.quizzes[-1]["buttons"] += 1
            if tag == "a":
                href = d.get("href") or ""
                if href.startswith("#"):
                    self.internal_hrefs.append(href[1:])
                    if self._toc_tag and self._toc_tag != "__closed__" and self._toc_depth > 0:
                        self.toc_links += 1
                    if "jump" in cls and self.quizzes:
                        self.quizzes[-1]["jumps"] += 1
                if "jump" in cls:
                    self._in_jump = True
                    self._jump_buf = []

        def handle_data(self, data):
            # <p> 안에 있는 동안의 텍스트만 모은다(자식 span 텍스트 포함).
            if self._p_depth > 0:
                self._p_buf.append(data)
            if self._in_jump:
                self._jump_buf.append(data)

        def handle_endtag(self, tag):
            if tag == "a" and self._in_jump:
                self.jump_texts.append("".join(self._jump_buf).strip())
                self._in_jump = False
            if self._toc_tag and tag == self._toc_tag and self._toc_depth > 0:
                self._toc_depth -= 1
                if self._toc_depth == 0:
                    self._toc_tag = "__closed__"
            if self._gloss_tag and tag == self._gloss_tag and self._gloss_depth > 0:
                self._gloss_depth -= 1
                if self._gloss_depth == 0:
                    self._gloss_tag = "__closed__"
            if tag == "p" and self._p_depth > 0:
                self._p_depth -= 1
                if self._p_depth == 0:
                    txt = "".join(self._p_buf).strip()
                    if txt:
                        self.paras.append(txt)

    s = Scan()
    with open(path, encoding="utf-8") as fp:
        raw = fp.read()
    s.feed(raw)

    errs = []
    if not s.quizzes:
        errs.append("퀴즈(.quiz)가 하나도 없습니다")
    elif len(s.quizzes) < MIN_QUIZZES:
        errs.append(
            f"퀴즈가 {len(s.quizzes)}문제뿐입니다 (사양: {MIN_QUIZZES}문제)"
        )
    answers = []
    for i, q in enumerate(s.quizzes, 1):
        try:
            a = int(q["answer"])
        except (TypeError, ValueError):
            errs.append(f"Q{i}: data-answer가 없거나 숫자가 아닙니다")
            continue
        if q["buttons"] < 2:
            errs.append(f"Q{i}: 보기가 {q['buttons']}개뿐입니다 (최소 2개)")
        if not 0 <= a < max(q["buttons"], 1):
            errs.append(f"Q{i}: data-answer={a}가 보기 개수({q['buttons']}) 범위 밖입니다")
        answers.append(a)
        if q["jumps"] == 0:
            errs.append(
                f"Q{i}: 해설에 본문 점프 링크(.jump)가 없습니다 — "
                f"본문에 근거 문단이 없는 퀴즈는 금지 (근거를 본문에 먼저 추가할 것)"
            )
    for anchor in s.internal_hrefs:
        if anchor and anchor not in s.ids:
            errs.append(f"내부 링크 #{anchor}의 대상 id가 문서에 없습니다 (깨진 앵커)")
    if len(answers) >= 3 and len(set(answers)) < 2:
        errs.append("정답 위치가 전부 같은 번호입니다 — 무작위 분산 규칙 위반")
    # 아래 3개는 2026-08-10/12 설명서가 통째로 빠뜨린 채 통과한 항목이다.
    # 마크업 존재만으로는 못 잡으므로 스타일/스크립트 원문까지 함께 본다.
    if ".flash" not in raw or "classList.add('flash')" not in raw:
        errs.append(
            "점프 링크 하이라이트가 없습니다 — .flash 애니메이션 정의와 "
            "classList.add('flash') 호출이 모두 있어야 합니다"
        )
    if s.terms < MIN_TERMS:
        errs.append(
            f"용어 풀이(.term 점선 밑줄)가 {s.terms}개뿐입니다 (최소 {MIN_TERMS}개) — "
            f"전문·도메인 용어는 첫 등장 시 .term으로 괄호 풀이를 붙일 것"
        )
    if s.diagrams == 0:
        errs.append("다이어그램(.diagram)이 없습니다 — HTML/CSS로 1개 이상 그릴 것")
    if s.boxes < MIN_BOXES:
        errs.append(
            f"비유/예시 블록(.box)이 {s.boxes}개뿐입니다 (최소 {MIN_BOXES}개) — "
            f"개념마다 실생활 비유(🔎) 또는 미니 예시(▶)를 붙일 것"
        )
    # 코드 블록마다 요약 한 줄: <pre> 개수 이상의 .code-lead 를 요구한다.
    # 코드를 한 줄도 안 읽어도 흐름이 이어지게 하기 위함(비개발자 독자 기준).
    if s.pres and s.code_leads < s.pres:
        errs.append(
            f"코드 요약(.code-lead) {s.code_leads}개가 코드 블록(<pre>) {s.pres}개보다 "
            f"적습니다 — 모든 코드 블록 위에 '이 코드가 하는 일' 한 줄(.code-lead)을 붙여 "
            f"코드를 건너뛰어도 흐름이 이어지게 할 것"
        )
    # 아래 5개는 2026-08-18 추가 — 분량(2)·용어(3)·눈높이(4)를 셀 수 있게 만든 대리지표.
    # "누가 봐도 이해"가 목표이므로 구조(요약·요지·용어사전)와 밀도(문단·문장)를 강제한다.
    if not s.tldr:
        errs.append(
            "핵심 요약(.tldr) 블록이 없습니다 — 문서 맨 위에 "
            "'무엇을 / 왜 / 결과'를 3줄 이내로 먼저 요약할 것"
        )
    if s.section_leads < MIN_SECTION_LEADS:
        errs.append(
            f"섹션 요지(.section-lead)가 {s.section_leads}개뿐입니다 "
            f"(최소 {MIN_SECTION_LEADS}개) — 각 섹션 첫 줄에 한 줄 요지를 붙일 것"
        )
    if not s.glossary:
        errs.append(
            "용어 사전(.glossary) 블록이 없습니다 — 도메인 용어를 한곳에 모아 "
            "'용어 — 한 줄 풀이'로 정리할 것"
        )
    long_paras = [p for p in s.paras if len(p) > MAX_PARA_CHARS]
    if long_paras:
        errs.append(
            f"너무 긴 문단이 {len(long_paras)}개입니다 (>{MAX_PARA_CHARS}자) — "
            f"3~4문장으로 쪼갤 것. 예: \"{long_paras[0][:40]}…\""
        )
    long_sents = []
    for p in s.paras:
        for sent in re.split(r"(?<=[.!?。…])\s+", p):
            sent = sent.strip()
            if len(sent) > MAX_SENTENCE_CHARS:
                long_sents.append(sent)
    if long_sents:
        errs.append(
            f"너무 긴 문장이 {len(long_sents)}개입니다 (>{MAX_SENTENCE_CHARS}자) — "
            f"한 문장에 한 가지 생각만 담고 끊을 것. 예: \"{long_sents[0][:40]}…\""
        )
    # ── 구조·시각 사양 검사 (2026-08-21 추가) ─────────────────────────────
    # SKILL.md 「스타일 요구사항」 중 기계가 볼 수 있는 항목을 전부 강제한다.
    # 배경: 08-21 설명서가 게이트 표 항목만 지키고 목차·4섹션·flash 색·라벨 등
    # 표 밖 사양 ~9건을 이탈한 채 통과했다 (08-10/12와 동일 패턴 3번째).
    if s.toc_links < MIN_TOC_LINKS:
        errs.append(
            f"상단 목차(.toc) 안 내부 앵커가 {s.toc_links}개입니다 (최소 {MIN_TOC_LINKS}개) — "
            f'<nav class="toc"> 블록에 섹션 앵커 링크를 넣을 것'
        )
    missing_ids = [i for i in REQUIRED_SECTION_IDS if i not in s.ids]
    if missing_ids:
        errs.append(
            "4섹션 구조 id가 없습니다: "
            + ", ".join(f"#{i}" for i in missing_ids)
            + " — Background(s-bg)·Intuition(s-intuition)·Code(s-code)·Quiz(s-quiz)"
            " 골격을 지킬 것 (template.html에서 시작하면 자동 충족)"
        )
    if FLASH_COLOR not in raw.lower():
        errs.append(
            f"점프 하이라이트가 샛빨간 배경({FLASH_COLOR} 계열)이 아닙니다 — "
            f"@keyframes 시작 배경색을 {FLASH_COLOR}로 할 것"
        )
    m_flash = re.search(r"\.flash\s*\{[^}]*?([0-9]*\.?[0-9]+)s", raw)
    if not m_flash:
        errs.append(
            ".flash 애니메이션 지속시간을 찾을 수 없습니다 — "
            "`.flash { animation: ... 2.5s ... }` 형태로 쓸 것"
        )
    elif not 2.0 <= float(m_flash.group(1)) <= 3.5:
        errs.append(
            f".flash 지속시간이 {m_flash.group(1)}s입니다 — 2~3초(권장 2.5s)로 할 것"
        )
    bad_jumps = [t for t in s.jump_texts if "본문에서 확인" not in t]
    if bad_jumps:
        errs.append(
            f"점프 링크 라벨이 규격(📍 본문에서 확인)과 다른 것이 {len(bad_jumps)}개입니다"
            f' — 예: "{bad_jumps[0][:20]}…"'
        )
    if s.boxes and s.labs < s.boxes:
        errs.append(
            f".lab 라벨({s.labs}개)이 .box 블록({s.boxes}개)보다 적습니다 — "
            '비유는 <span class="lab">🔎 비유</span>, '
            '예시는 <span class="lab">▶ 예시로 따라가기</span> 라벨을 붙일 것'
        )
    if s.warnboxes == 0:
        errs.append(
            "예시 블록(.warnbox)이 없습니다 — 예시는 .box.warnbox + ▶ 라벨로 "
            "구체 값이 흐르게 쓸 것"
        )
    if s.pres and "pre-wrap" not in raw:
        errs.append(
            "<pre>에 white-space: pre-wrap이 없습니다 — 가로 스크롤 방지 규칙"
        )
    if not re.search(r"scroll-behavior\s*:\s*smooth", raw):
        errs.append(
            "부드러운 스크롤(scroll-behavior: smooth)이 없습니다 — html 셀렉터에 지정할 것"
        )
    if s.terms and not re.search(r"\.term\s*\{[^}]*2px\s+dotted", raw):
        errs.append(
            ".term 스타일이 2px dotted 점선 밑줄이 아닙니다 — border-bottom: 2px dotted"
        )
    if s.glossary and s.glossary_terms < MIN_GLOSSARY_TERMS:
        errs.append(
            f"용어 사전(.glossary) 안 .term이 {s.glossary_terms}개입니다 "
            f"(최소 {MIN_GLOSSARY_TERMS}개) — 사전의 용어명마다 .term을 붙일 것"
        )
    if s.bad_lead_tags:
        errs.append(
            f'.section-lead가 <p>가 아닌 태그에 {s.bad_lead_tags}개 붙어 있습니다 — '
            f'<p class="section-lead">로 쓸 것'
        )
    return errs


def cmd_check_html(path):
    if not os.path.isfile(path):
        print(f"파일 없음: {path}", file=sys.stderr)
        return 1
    errs = check_html(path)
    if errs:
        print("[check-html] 무결성 검사 실패:", file=sys.stderr)
        for e in errs:
            print(f"  - {e}", file=sys.stderr)
        return 1
    print("html check OK")
    return 0


def cmd_mark(cwd, html):
    st = collect(cwd)
    if st is None:
        print("not a git repository", file=sys.stderr)
        return 1
    if not st["files"]:
        print("no changes vs base — nothing to mark", file=sys.stderr)
        return 1
    if html:
        if not os.path.isfile(html):
            print(f"--html 파일 없음: {html} — 마커 기록 거부", file=sys.stderr)
            return 1
        errs = check_html(html)
        if errs:
            print("[mark] 설명서 무결성 검사 실패 — 마커 기록 거부:", file=sys.stderr)
            for e in errs:
                print(f"  - {e}", file=sys.stderr)
            print("오류를 고친 뒤 --mark를 다시 실행하세요.", file=sys.stderr)
            return 1
    os.makedirs(os.path.dirname(st["marker"]), exist_ok=True)
    with open(st["marker"], "w") as fp:
        json.dump(
            {
                "branch": st["branch"],
                "hash": st["hash"],
                "html": html,
                "created": datetime.datetime.now().isoformat(timespec="seconds"),
                "files": st["files"],
            },
            fp,
            ensure_ascii=False,
            indent=2,
        )
    print(f"marked: {st['marker']} ({len(st['files'])} files)")
    return 0


def freshness(cwd):
    """마커 신선도 판정. (ok, reason) — 레포 아님/변경 없음이면 (True, None)."""
    st = collect(cwd)
    if st is None or not st["files"]:
        return True, None
    if os.path.isfile(st["marker"]):
        try:
            with open(st["marker"]) as fp:
                if json.load(fp).get("hash") == st["hash"]:
                    return True, None
            return False, "설명서가 stale합니다 (설명서 생성 이후 변경사항이 더 생겼습니다)"
        except Exception:
            return False, "마커 파일을 읽을 수 없습니다"
    return False, "이 브랜치의 변경사항에 대한 diff 설명서가 아직 없습니다"


def block_message(reason):
    # 스킬 이름 해석은 실패할 수 있으므로(08-21 실사고: 잘못된 접두 명칭으로 Unknown
    # skill) 항상 동작하는 SKILL.md 절대경로를 정본 안내로 삼는다. 폴백에서도
    # SKILL.md 전문을 읽게 해 "게이트 표 항목만 맞춘 문서"를 원천 차단한다.
    return (
        f"[explain-diff-gate] PR 생성 차단: {reason}.\n"
        f"1) `{SKILL_MD}` 전문을 Read하고 그대로 따라 설명서(HTML)를 생성하세요.\n"
        f"   (스킬 호출명은 `{SKILL_NAME}` — 이름 해석이 실패해도 위 SKILL.md 경로가 정본입니다.\n"
        f"    골격은 `{TEMPLATE_HTML}` 을 출력 경로로 복사해 채우면 구조 사양이 보장됩니다.)\n"
        f"2) `python3 ~/.claude/hooks/explain-diff-gate.py --mark --html <경로>` 로 마커를 기록하세요.\n"
        f"   ⚠️ --mark 는 반드시 단독 Bash 명령으로 — gh pr create 와 한 명령에 합치면\n"
        f"   이 훅이 명령 전체를 선차단해 --mark 자체가 실행되지 않습니다.\n"
        f"3) 그 다음 별도 명령으로 PR 생성을 재시도하세요.\n"
        f"긴급 우회가 필요하면 사용자 승인 하에 명령 앞에 SKIP_EXPLAIN=1 을 붙이세요.\n"
    )


def cmd_check(cwd):
    ok, reason = freshness(cwd)
    if ok:
        print("check OK")
        return 0
    sys.stderr.write(block_message(reason))
    return 2


def cmd_html_path(cwd):
    """현재 브랜치 마커의 설명서 HTML 경로 출력. 없으면 무출력 + exit 1."""
    st = collect(cwd)
    if st is None or not os.path.isfile(st["marker"]):
        return 1
    try:
        with open(st["marker"]) as fp:
            html = json.load(fp).get("html")
    except Exception:
        return 1
    if not html or not os.path.isfile(html):
        return 1
    print(html)
    return 0


def hook_main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        return 0
    tool = payload.get("tool_name", "")
    cwd = payload.get("cwd") or os.getcwd()
    if tool == "Bash":
        cmd = (payload.get("tool_input") or {}).get("command", "")
        if not PR_CMD_RE.search(cmd):
            return 0
        if "SKIP_EXPLAIN=1" in cmd:
            return 0
    elif tool != "mcp__github__create_pull_request":
        return 0

    ok, reason = freshness(cwd)
    if ok:
        return 0
    sys.stderr.write(block_message(reason))
    return 2


def main():
    argv = sys.argv[1:]
    cwd = os.getcwd()
    if not argv:
        return hook_main()
    if argv[0] == "--info":
        return cmd_info(cwd)
    if argv[0] == "--mark":
        html = None
        if "--html" in argv:
            i = argv.index("--html")
            html = argv[i + 1] if i + 1 < len(argv) else None
        return cmd_mark(cwd, html)
    if argv[0] == "--check-html":
        if len(argv) < 2:
            print("사용법: --check-html <html 경로>", file=sys.stderr)
            return 1
        return cmd_check_html(argv[1])
    if argv[0] == "--check":
        return cmd_check(cwd)
    if argv[0] == "--html-path":
        return cmd_html_path(cwd)
    print(f"unknown mode: {argv[0]}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
