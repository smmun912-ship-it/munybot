"""
인포그래픽 생성기: JSON 데이터 → 시각적 HTML 인포그래픽
"""
import json
import logging
from pathlib import Path
from datetime import datetime

from config import get_today_output_dir

logger = logging.getLogger(__name__)

INFOGRAPHIC_TEMPLATE = """<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{headline}</title>
    <link href="https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@300;400;700;900&display=swap" rel="stylesheet">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Noto Sans KR', sans-serif;
            background: linear-gradient(135deg, #0f0c29 0%, #302b63 50%, #24243e 100%);
            min-height: 100vh;
            color: #e8e8e8;
            padding: 40px 20px;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
        }}
        
        /* ─── Header ─── */
        .header {{
            text-align: center;
            margin-bottom: 50px;
        }}
        
        .header .badge {{
            display: inline-block;
            background: rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.15);
            border-radius: 20px;
            padding: 6px 18px;
            font-size: 0.8em;
            color: #a5b4fc;
            margin-bottom: 20px;
        }}
        
        .header h1 {{
            font-size: 2.6em;
            font-weight: 900;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            line-height: 1.3;
            margin-bottom: 10px;
        }}
        
        .header .subtitle {{
            font-size: 1.1em;
            color: rgba(255,255,255,0.5);
            font-weight: 300;
        }}
        
        /* ─── Stats Grid ─── */
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 50px;
        }}
        
        .stat-card {{
            background: rgba(255,255,255,0.05);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(255,255,255,0.1);
            border-radius: 16px;
            padding: 24px;
            text-align: center;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .stat-card:hover {{
            transform: translateY(-4px);
            box-shadow: 0 12px 40px rgba(102, 126, 234, 0.2);
        }}
        
        .stat-card .icon {{
            font-size: 2em;
            margin-bottom: 8px;
        }}
        
        .stat-card .value {{
            font-size: 1.8em;
            font-weight: 900;
            color: #a5b4fc;
        }}
        
        .stat-card .label {{
            font-size: 0.85em;
            color: rgba(255,255,255,0.5);
            margin-top: 4px;
        }}
        
        /* ─── Topics ─── */
        .section-title {{
            font-size: 1.4em;
            font-weight: 700;
            color: #a5b4fc;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .section-title::after {{
            content: '';
            flex: 1;
            height: 1px;
            background: linear-gradient(90deg, rgba(165,180,252,0.3) 0%, transparent 100%);
        }}
        
        .topics {{
            display: flex;
            flex-direction: column;
            gap: 16px;
            margin-bottom: 50px;
        }}
        
        .topic-card {{
            background: rgba(255,255,255,0.04);
            border: 1px solid rgba(255,255,255,0.08);
            border-radius: 16px;
            padding: 24px;
            border-left: 3px solid #667eea;
            transition: background 0.3s ease;
        }}
        
        .topic-card:nth-child(2) {{ border-left-color: #764ba2; }}
        .topic-card:nth-child(3) {{ border-left-color: #f093fb; }}
        .topic-card:nth-child(4) {{ border-left-color: #42a5f5; }}
        .topic-card:nth-child(5) {{ border-left-color: #66bb6a; }}
        
        .topic-card:hover {{
            background: rgba(255,255,255,0.07);
        }}
        
        .topic-card h3 {{
            font-size: 1.15em;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        
        .topic-card p {{
            font-size: 0.9em;
            color: rgba(255,255,255,0.6);
            line-height: 1.6;
            margin-bottom: 12px;
        }}
        
        .keywords {{
            display: flex;
            flex-wrap: wrap;
            gap: 6px;
        }}
        
        .keyword {{
            background: rgba(102, 126, 234, 0.15);
            border: 1px solid rgba(102, 126, 234, 0.3);
            border-radius: 12px;
            padding: 3px 12px;
            font-size: 0.75em;
            color: #a5b4fc;
        }}
        
        /* ─── Trending ─── */
        .trending {{
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
            margin-bottom: 50px;
        }}
        
        .trend-tag {{
            background: linear-gradient(135deg, rgba(102,126,234,0.2) 0%, rgba(118,75,162,0.2) 100%);
            border: 1px solid rgba(102,126,234,0.3);
            border-radius: 20px;
            padding: 8px 20px;
            font-size: 0.9em;
            color: #c5cae9;
            transition: all 0.3s ease;
            cursor: default;
        }}
        
        .trend-tag:hover {{
            background: linear-gradient(135deg, rgba(102,126,234,0.4) 0%, rgba(118,75,162,0.4) 100%);
            transform: scale(1.05);
        }}
        
        /* ─── Takeaway ─── */
        .takeaway {{
            background: linear-gradient(135deg, rgba(102,126,234,0.1) 0%, rgba(118,75,162,0.1) 100%);
            border: 1px solid rgba(102,126,234,0.2);
            border-radius: 20px;
            padding: 30px 36px;
            text-align: center;
        }}
        
        .takeaway .label {{
            font-size: 0.8em;
            color: #a5b4fc;
            text-transform: uppercase;
            letter-spacing: 2px;
            margin-bottom: 12px;
        }}
        
        .takeaway .text {{
            font-size: 1.15em;
            font-weight: 400;
            line-height: 1.7;
            color: rgba(255,255,255,0.85);
        }}
        
        /* ─── Footer ─── */
        .footer {{
            text-align: center;
            margin-top: 40px;
            color: rgba(255,255,255,0.25);
            font-size: 0.8em;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="badge">📊 Daily AI/Tech Insight</div>
            <h1>{headline}</h1>
            <div class="subtitle">{subheadline}</div>
        </div>

        <div class="stats-grid">
{stats_html}
        </div>

        <div class="section-title">🔥 주요 토픽</div>
        <div class="topics">
{topics_html}
        </div>

        <div class="section-title">📈 트렌딩 키워드</div>
        <div class="trending">
{trending_html}
        </div>

        <div class="takeaway">
            <div class="label">💡 Today's Takeaway</div>
            <div class="text">{takeaway}</div>
        </div>

        <div class="footer">
            AI/테크 유튜브 일일 종합 인포그래픽 | {date} | Auto-generated
        </div>
    </div>
</body>
</html>
"""


def generate_infographic_html(data: dict = None) -> str:
    """인포그래픽 데이터를 HTML로 변환합니다."""
    output_dir = get_today_output_dir()

    if data is None:
        json_path = output_dir / "infographic_data.json"
        if json_path.exists():
            data = json.loads(json_path.read_text(encoding="utf-8"))
        else:
            logger.error("❌ infographic_data.json이 없습니다.")
            return ""

    # Stats HTML
    stats_parts = []
    for stat in data.get("key_stats", []):
        stats_parts.append(f"""            <div class="stat-card">
                <div class="icon">{stat.get('icon', '📊')}</div>
                <div class="value">{stat.get('value', '-')}</div>
                <div class="label">{stat.get('label', '')}</div>
            </div>""")
    stats_html = "\n".join(stats_parts)

    # Topics HTML
    topics_parts = []
    for topic in data.get("main_topics", []):
        keywords_html = "\n".join(
            f'                    <span class="keyword">{kw}</span>'
            for kw in topic.get("keywords", [])
        )
        topics_parts.append(f"""            <div class="topic-card">
                <h3>{topic.get('title', '')}</h3>
                <p>{topic.get('description', '')}</p>
                <div class="keywords">
{keywords_html}
                </div>
            </div>""")
    topics_html = "\n".join(topics_parts)

    # Trending keywords HTML
    trending_parts = [
        f'            <div class="trend-tag">#{kw}</div>'
        for kw in data.get("trending_keywords", [])
    ]
    trending_html = "\n".join(trending_parts)

    full_html = INFOGRAPHIC_TEMPLATE.format(
        headline=data.get("headline", "AI/테크 데일리"),
        subheadline=data.get("subheadline", ""),
        date=data.get("date", datetime.now().strftime("%Y년 %m월 %d일")),
        stats_html=stats_html,
        topics_html=topics_html,
        trending_html=trending_html,
        takeaway=data.get("takeaway", ""),
    )

    html_path = output_dir / "infographic.html"
    html_path.write_text(full_html, encoding="utf-8")
    logger.info(f"🎨 인포그래픽 HTML 저장: {html_path}")

    return str(html_path)


if __name__ == "__main__":
    path = generate_infographic_html()
    if path:
        print(f"✅ 인포그래픽 생성 완료: {path}")
