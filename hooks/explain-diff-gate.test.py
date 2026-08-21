#!/usr/bin/env python3
"""explain-diff-gate.test.py — check_html 26항 검사기의 회귀 테스트.

왜 있나: 26항 전부 「없음 = 통과」형 검사라, 파서 리팩터·마크업 변형으로
한 항목이 조용히 무력화돼도 아무도 모른다(RTK-CUSTOM "잡을 수 없는 검사는
통과가 아니라 미실행"). 정상 fixture 1개가 통과하고, 항목별 위반 mutation이
각각 정확히 잡히는지를 고정한다.

실행: python3 ~/.claude/hooks/explain-diff-gate.test.py
"""
import importlib.util
import os
import sys
import tempfile
import unittest

HOOK = os.path.join(os.path.dirname(os.path.abspath(__file__)), "explain-diff-gate.py")
spec = importlib.util.spec_from_file_location("explain_diff_gate", HOOK)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def quiz(n, answer, jump='<a class="jump" href="#s-bg">📍 본문에서 확인</a>'):
    return (
        f'<div class="quiz" data-answer="{answer}">'
        f"<p><strong>Q{n}.</strong> 질문.</p>"
        f"<button>보기1</button><button>보기2</button><button>보기3</button>"
        f'<div class="explain">해설. {jump}</div>'
        f"</div>"
    )


# 26항 전부 통과하는 최소 정상 문서 (template.html 골격 준용).
VALID = f"""<!doctype html>
<html lang="ko">
<head>
<style>
  html {{ scroll-behavior: smooth; }}
  .term {{ border-bottom: 2px dotted #d05; }}
  pre {{ white-space: pre-wrap; }}
  @keyframes flashbg {{ 0% {{ background: #ff443a; }} 100% {{ background: transparent; }} }}
  .flash {{ animation: flashbg 2.5s ease-out; }}
</style>
</head>
<body>
<div class="tldr"><p>무엇을. 왜. 결과.</p></div>
<nav class="toc">
  <a href="#s-bg">배경</a>
  <a href="#s-intuition">직관</a>
  <a href="#s-code">코드</a>
  <a href="#s-quiz">퀴즈</a>
</nav>
<h2 id="s-bg">배경</h2>
<p class="section-lead">요지 하나.</p>
<p>짧은 문단이다. <span class="term" title="풀이">용어A</span>와 <span class="term" title="풀이">용어B</span>를 소개한다.</p>
<div class="glossary"><dl>
  <dt><span class="term" title="풀이">용어1</span></dt><dd>풀이.</dd>
  <dt><span class="term" title="풀이">용어2</span></dt><dd>풀이.</dd>
  <dt><span class="term" title="풀이">용어3</span></dt><dd>풀이.</dd>
</dl></div>
<h2 id="s-intuition">직관</h2>
<p class="section-lead">요지 둘.</p>
<div class="diagram"><div class="node">입력</div></div>
<div class="box"><span class="lab">🔎 비유</span> 택배 비유.</div>
<div class="box"><span class="lab">🔎 비유</span> 시험 비유.</div>
<div class="box warnbox"><span class="lab">▶ 예시로 따라가기</span> 100 - 8 = 92.</div>
<div class="box"><span class="lab">🔎 비유</span> 가계부 비유.</div>
<div class="box"><span class="lab">🔎 비유</span> 우편함 비유.</div>
<h2 id="s-code">코드</h2>
<p class="section-lead">요지 셋.</p>
<p class="code-lead">이 코드가 하는 일 한 줄.</p>
<pre>let x = 1;</pre>
<h2 id="s-quiz">퀴즈</h2>
<p class="section-lead">요지 넷.</p>
{quiz(1, 0)}
{quiz(2, 1)}
{quiz(3, 2)}
{quiz(4, 0)}
{quiz(5, 1)}
<script>
  document.querySelectorAll('a.jump').forEach(function (a) {{
    a.addEventListener('click', function () {{
      var t = document.getElementById(a.getAttribute('href').slice(1));
      if (t) {{ t.classList.remove('flash'); void t.offsetWidth; t.classList.add('flash'); }}
    }});
  }});
</script>
</body>
</html>
"""


def errs_of(html_text):
    with tempfile.NamedTemporaryFile(
        "w", suffix=".html", encoding="utf-8", delete=False
    ) as fp:
        fp.write(html_text)
        path = fp.name
    try:
        return gate.check_html(path)
    finally:
        os.unlink(path)


class CheckHtmlRegression(unittest.TestCase):
    """각 mutation이 정확히 해당 항목의 오류를 낸다 — 검사기 무력화 감지."""

    def assert_err(self, mutated, keyword, msg=None):
        errs = errs_of(mutated)
        self.assertTrue(
            any(keyword in e for e in errs),
            msg or f"'{keyword}' 오류가 나와야 하는데 없음. 실제: {errs}",
        )

    # ── 기준선 ──────────────────────────────────────────────────────
    def test_00_valid_passes(self):
        self.assertEqual([], errs_of(VALID))

    # ── 퀴즈 계열 (항목 1~6) ────────────────────────────────────────
    def test_01_no_quiz(self):
        m = VALID
        for n, a in ((1, 0), (2, 1), (3, 2), (4, 0), (5, 1)):
            m = m.replace(quiz(n, a), "")
        self.assert_err(m, "하나도 없습니다")

    def test_01b_quiz_under_five(self):
        self.assert_err(VALID.replace(quiz(5, 1), ""), "문제뿐입니다")

    def test_02_bad_data_answer(self):
        self.assert_err(
            VALID.replace('data-answer="0"', 'data-answer="x"', 1), "data-answer"
        )

    def test_02b_answer_out_of_range(self):
        self.assert_err(
            VALID.replace('data-answer="0"', 'data-answer="9"', 1), "범위 밖"
        )

    def test_03_too_few_buttons(self):
        m = VALID.replace(
            "<button>보기1</button><button>보기2</button><button>보기3</button>",
            "<button>보기1</button>",
            1,
        )
        self.assert_err(m, "보기가")

    def test_04_quiz_without_jump(self):
        self.assert_err(
            VALID.replace(quiz(1, 0), quiz(1, 0, jump="")), "점프 링크(.jump)가 없습니다"
        )

    def test_05_broken_anchor(self):
        self.assert_err(
            VALID.replace("</body>", '<a href="#nope">x</a></body>'), "깨진 앵커"
        )

    def test_06_answers_not_distributed(self):
        m = VALID
        for n, a in ((2, 1), (3, 2), (4, 0), (5, 1)):
            m = m.replace(quiz(n, a), quiz(n, 0))
        self.assert_err(m, "무작위 분산")

    # ── 눈높이 대리지표 계열 (항목 7~16) ────────────────────────────
    def test_07_flash_js_missing(self):
        self.assert_err(VALID.replace("classList.add('flash')", ""), "하이라이트")

    def test_08_terms_under_min(self):
        m = VALID.replace('<span class="term" title="풀이">용어A</span>', "용어A")
        m = m.replace('<span class="term" title="풀이">용어B</span>', "용어B")
        self.assert_err(m, "용어 풀이")

    def test_09_no_diagram(self):
        self.assert_err(
            VALID.replace('<div class="diagram"><div class="node">입력</div></div>', ""),
            "다이어그램",
        )

    def test_10_boxes_under_min(self):
        self.assert_err(
            VALID.replace(
                '<div class="box"><span class="lab">🔎 비유</span> 우편함 비유.</div>', ""
            ),
            "비유/예시 블록",
        )

    def test_11_code_lead_fewer_than_pre(self):
        self.assert_err(
            VALID.replace('<p class="code-lead">이 코드가 하는 일 한 줄.</p>', ""),
            "코드 요약",
        )

    def test_12_no_tldr(self):
        self.assert_err(
            VALID.replace('<div class="tldr"><p>무엇을. 왜. 결과.</p></div>', ""),
            "핵심 요약",
        )

    def test_13_section_leads_under_min(self):
        self.assert_err(
            VALID.replace('<p class="section-lead">요지 넷.</p>', ""), "섹션 요지"
        )

    def test_14_no_glossary(self):
        start = '<div class="glossary">'
        m = VALID[: VALID.index(start)] + VALID[VALID.index("</dl></div>") + len("</dl></div>") :]
        self.assert_err(m, "용어 사전(.glossary) 블록이 없습니다")

    def test_15_long_paragraph(self):
        self.assert_err(
            VALID.replace("</body>", "<p>" + "가" * 500 + ".</p></body>"), "너무 긴 문단"
        )

    def test_16_long_sentence(self):
        self.assert_err(
            VALID.replace("</body>", "<p>" + "가" * 140 + ".</p></body>"), "너무 긴 문장"
        )

    # ── 구조·시각 사양 계열 (항목 17~26, 2026-08-21 추가분) ─────────
    def test_17_toc_missing(self):
        start = '<nav class="toc">'
        m = VALID[: VALID.index(start)] + VALID[VALID.index("</nav>") + len("</nav>") :]
        self.assert_err(m, "상단 목차")

    def test_18_section_id_missing(self):
        m = VALID.replace('id="s-bg"', 'id="s-background"')
        self.assert_err(m, "4섹션 구조 id")

    def test_19_flash_color_not_red(self):
        self.assert_err(VALID.replace("#ff443a", "#ffe08a"), "샛빨간")

    def test_20_flash_duration_out_of_range(self):
        self.assert_err(VALID.replace("flashbg 2.5s", "flashbg 5s"), "지속시간")

    def test_21_jump_label_off_spec(self):
        self.assert_err(
            VALID.replace("📍 본문에서 확인", "→ 확인", 1), "라벨이 규격"
        )

    def test_22_lab_fewer_than_boxes(self):
        self.assert_err(
            VALID.replace('<span class="lab">🔎 비유</span> 택배 비유.', "택배 비유.", 1),
            ".lab 라벨",
        )

    def test_23_no_warnbox(self):
        self.assert_err(
            VALID.replace('class="box warnbox"', 'class="box"'), "(.warnbox)"
        )

    def test_24_no_pre_wrap(self):
        self.assert_err(
            VALID.replace("pre { white-space: pre-wrap; }", ""), "pre-wrap"
        )

    def test_25a_no_smooth_scroll(self):
        self.assert_err(
            VALID.replace("html { scroll-behavior: smooth; }", ""), "scroll-behavior"
        )

    def test_25b_term_style_not_2px_dotted(self):
        self.assert_err(
            VALID.replace("2px dotted", "1px dotted"), "2px dotted"
        )

    def test_26a_glossary_terms_under_min(self):
        m = VALID
        for i in (1, 2, 3):
            m = m.replace(
                f'<dt><span class="term" title="풀이">용어{i}</span></dt>', f"<dt>용어{i}</dt>"
            )
        # 본문 .term 5개 하한도 같이 깨지므로, glossary 전용 오류를 특정해 확인
        self.assert_err(m, "용어 사전(.glossary) 안 .term")

    def test_26b_section_lead_not_p(self):
        m = VALID.replace(
            '<p class="section-lead">요지 넷.</p>',
            '<div class="section-lead">요지 넷.</div>',
        )
        self.assert_err(m, "<p>가 아닌")


class TemplateSmoke(unittest.TestCase):
    """template.html 골격이 검사기가 요구하는 고정 사양을 담고 있는지 (드리프트 감지)."""

    def setUp(self):
        if not os.path.isfile(gate.TEMPLATE_HTML):
            self.skipTest(f"template 없음: {gate.TEMPLATE_HTML}")
        with open(gate.TEMPLATE_HTML, encoding="utf-8") as fp:
            self.raw = fp.read()

    def test_required_section_ids(self):
        for sid in gate.REQUIRED_SECTION_IDS:
            self.assertIn(f'id="{sid}"', self.raw, f"template에 #{sid} 골격 누락")

    def test_flash_spec(self):
        self.assertIn(gate.FLASH_COLOR, self.raw.lower())
        self.assertIn("classList.add('flash')", self.raw)

    def test_style_invariants(self):
        self.assertIn("scroll-behavior: smooth", self.raw)
        self.assertIn("pre-wrap", self.raw)
        self.assertIn("2px dotted", self.raw)
        self.assertIn("본문에서 확인", self.raw)


if __name__ == "__main__":
    unittest.main(verbosity=1)
