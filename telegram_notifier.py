"""
텔레그램 봇 알림: 매일 결과를 텔레그램으로 전송
"""
import os
import json
import logging
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path

from config import get_today_output_dir

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Windows 콘솔 출력 인코딩 설정
import sys
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
PAGES_URL = os.environ.get("PAGES_URL", "")


def send_telegram_message(text: str, parse_mode: str = "HTML") -> bool:
    """텔레그램으로 메시지를 전송합니다."""
    if not BOT_TOKEN or not CHAT_ID:
        logger.warning("⚠️ TELEGRAM_BOT_TOKEN 또는 TELEGRAM_CHAT_ID가 설정되지 않았습니다.")
        return False

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = urllib.parse.urlencode({
        "chat_id": CHAT_ID,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": "false",
    }).encode("utf-8")

    try:
        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read())
            if result.get("ok"):
                logger.info("✅ 텔레그램 메시지 전송 성공")
                return True
            else:
                logger.error(f"❌ 텔레그램 오류: {result}")
                return False
    except Exception as e:
        logger.error(f"❌ 텔레그램 전송 실패: {e}")
        return False


def build_daily_report() -> str:
    """오늘의 결과를 텔레그램 메시지 형식으로 생성합니다."""
    output_dir = get_today_output_dir()
    today = datetime.now().strftime("%Y년 %m월 %d일")

    # 리서치 결과 로드
    results_path = output_dir / "research_results.json"
    if results_path.exists():
        results = json.loads(results_path.read_text(encoding="utf-8"))
    else:
        return f"📊 <b>AI/테크 데일리 다이제스트</b>\n📅 {today}\n\n⚠️ 오늘의 결과가 없습니다."

    total_videos = results.get("total_videos", 0)
    total_transcripts = results.get("total_transcripts", 0)
    channels = results.get("channels", [])

    # 메시지 구성
    lines = [
        f"📊 <b>AI/테크 데일리 다이제스트</b>",
        f"📅 {today}",
        "",
        f"🎬 수집 영상: <b>{total_videos}개</b>",
        f"📝 트랜스크립트: <b>{total_transcripts}개</b>",
        "",
    ]

    if channels:
        lines.append("📺 <b>채널별 요약:</b>")
        for ch in channels:
            video_count = ch.get("videos_found", 0)
            lines.append(f"  • {ch['name']}: {video_count}개 영상")
            for v in ch.get("videos", [])[:2]:
                emoji = "✅" if v.get("has_transcript") else "⚠️"
                title = v['title'][:45]
                url = v.get('url', '')
                summary = v.get('summary', '')

                if url:
                    lines.append(f"    {emoji} <a href='{url}'>{title}</a>")
                else:
                    lines.append(f"    {emoji} {title}")
                
                if summary:
                    summary_lines = summary.strip().split('\n')
                    for line in summary_lines:
                        lines.append(f"    {line}")
                    lines.append("")  # Add empty line after summary
        lines.append("")

    # 링크 추가 (수집된 영상이 있을 때만)
    # User Request: Remove slides/infographics links

    if total_videos == 0:
        lines.insert(4, "ℹ️ 최근 24시간 내 새 영상이 없습니다.")

    return "\n".join(lines)


if __name__ == "__main__":
    report = build_daily_report()
    print(report)
    print("---")
    success = send_telegram_message(report)
    if not success:
        logger.info("ℹ️ 텔레그램 전송 실패 - 토큰/Chat ID를 확인하세요.")
