"""
슬라이드 생성기: JSON 데이터 → Reveal.js HTML 슬라이드
"""
import json
import logging
from pathlib import Path
from datetime import datetime

from config import get_today_output_dir

logger = logging.getLogger(__name__)

REVEAL_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.css">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/theme/night.css">
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700;900&display=swap');
        
        :root {{
            --r-main-font: 'Noto Sans KR', sans-serif;
            --r-heading-font: 'Noto Sans KR', sans-serif;
            --r-main-color: #e8e8e8;
            --r-heading-color: #ffffff;
            --r-link-color: #64b5f6;
            --accent-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --accent-blue: #42a5f5;
            --accent-purple: #ab47bc;
            --accent-green: #66bb6a;
        }}
        
        .reveal {{
            font-family: var(--r-main-font);
        }}
        
        .reveal .slides section {{
            text-align: left;
            padding: 40px;
        }}
        
        .reveal h1 {{
            font-size: 2.2em;
            font-weight: 900;
            background: var(--accent-gradient);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 0.3em;
        }}
        
        .reveal h2 {{
            font-size: 1.6em;
            font-weight: 700;
            color: var(--accent-blue);
            border-bottom: 2px solid rgba(100, 181, 246, 0.3);
            padding-bottom: 10px;
            margin-bottom: 30px;
        }}
        
        .reveal h3 {{
            font-size: 1.2em;
            color: var(--accent-purple);
        }}
        
        .reveal ul {{
            list-style: none;
            padding: 0;
        }}
        
        .reveal ul li {{
            padding: 8px 0 8px 30px;
            position: relative;
            font-size: 0.85em;
            line-height: 1.6;
        }}
        
        .reveal ul li::before {{
            content: '▸';
            position: absolute;
            left: 8px;
            color: var(--accent-blue);
            font-weight: bold;
        }}
        
        .title-slide h1 {{
            font-size: 2.8em;
            text-align: center;
        }}
        
        .title-slide .date {{
            text-align: center;
            color: rgba(255,255,255,0.6);
            font-size: 1.1em;
            margin-top: 20px;
        }}
        
        .slide-number {{
            font-family: 'Noto Sans KR', sans-serif !important;
            font-size: 14px !important;
            color: rgba(255,255,255,0.4) !important;
        }}
        
        .speaker-notes {{
            display: none;
        }}
    </style>
</head>
<body>
    <div class="reveal">
        <div class="slides">
{slides_html}
        </div>
    </div>
    <script src="https://cdn.jsdelivr.net/npm/reveal.js@5.1.0/dist/reveal.js"></script>
    <script>
        Reveal.initialize({{
            hash: true,
            slideNumber: true,
            transition: 'slide',
            backgroundTransition: 'fade',
            center: false,
            width: 1280,
            height: 720,
        }});
    </script>
</body>
</html>
"""


def generate_slides_html(slides_data: dict = None) -> str:
    """슬라이드 데이터를 Reveal.js HTML로 변환합니다."""
    output_dir = get_today_output_dir()

    if slides_data is None:
        json_path = output_dir / "slides_data.json"
        if json_path.exists():
            slides_data = json.loads(json_path.read_text(encoding="utf-8"))
        else:
            logger.error("❌ slides_data.json이 없습니다.")
            return ""

    title = slides_data.get("title", "AI/테크 데일리")
    date = slides_data.get("date", datetime.now().strftime("%Y년 %m월 %d일"))
    slides = slides_data.get("slides", [])

    slides_html_parts = []

    # 타이틀 슬라이드
    slides_html_parts.append(f"""
            <section class="title-slide">
                <h1>{title}</h1>
                <div class="date">{date}</div>
            </section>""")

    # 콘텐츠 슬라이드
    for slide in slides:
        slide_title = slide.get("title", "")
        content = slide.get("content", [])
        notes = slide.get("notes", "")

        items_html = "\n".join(f"                        <li>{item}</li>" for item in content)

        slides_html_parts.append(f"""
            <section>
                <h2>{slide_title}</h2>
                <ul>
{items_html}
                </ul>
                <aside class="notes">{notes}</aside>
            </section>""")

    # 엔딩 슬라이드
    slides_html_parts.append(f"""
            <section class="title-slide">
                <h1>감사합니다</h1>
                <div class="date">AI/테크 데일리 종합 | {date}</div>
            </section>""")

    full_html = REVEAL_TEMPLATE.format(
        title=title,
        slides_html="\n".join(slides_html_parts),
    )

    # HTML 파일 저장
    html_path = output_dir / "slides.html"
    html_path.write_text(full_html, encoding="utf-8")
    logger.info(f"📊 슬라이드 HTML 저장: {html_path}")

    return str(html_path)


if __name__ == "__main__":
    path = generate_slides_html()
    if path:
        print(f"✅ 슬라이드 생성 완료: {path}")
