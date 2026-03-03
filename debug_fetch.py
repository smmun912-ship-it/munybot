import logging
import scrapetube
import sys
from datetime import datetime, timezone, timedelta

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("DebugFetch")

# Ensure UTF-8 Output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Target Channel: @ai.yeongseon
CHANNEL_URL = "https://www.youtube.com/@ai.yeongseon"
HOURS_LOOKBACK = 24

def _is_within_hours(published_text: str, hours: int) -> bool:
    """Copy of the logic from research_agent.py for testing"""
    if not published_text:
        return False

    text = published_text.lower().strip()
    text = text.replace("streamed ", "").replace("premiered ", "")

    if "just now" in text or "moment" in text: return True
    if "second" in text or "초" in text: return True
    if "minute" in text or "분" in text: return True

    if "hour" in text or "시간" in text:
        try:
            num = int("".join(c for c in text if c.isdigit()) or "0")
            return num <= hours
        except ValueError: return False

    if "day" in text or "일" in text:
        try:
            num = int("".join(c for c in text if c.isdigit()) or "0")
            return num * 24 <= hours
        except ValueError: return False
        
    if "week" in text or "주" in text:
        try:
            num = int("".join(c for c in text if c.isdigit()) or "0")
            return num * 24 * 7 <= hours
        except ValueError: return False

    return False

def run_debug():
    logger.info(f"🔍 Scanning Channel: {CHANNEL_URL}")
    
    try:
        videos = scrapetube.get_channel(channel_url=CHANNEL_URL, limit=5, sort_by="newest")
        
        count = 0
        for video in videos:
            count += 1
            video_id = video.get("videoId", "")
            
            title_data = video.get("title", {})
            title = title_data.get("runs", [{}])[0].get("text", "No Title") if isinstance(title_data, dict) else str(title_data)
            
            time_text_data = video.get("publishedTimeText", {})
            published_text = time_text_data.get("simpleText", "N/A") if isinstance(time_text_data, dict) else str(time_text_data)
            
            is_recent = _is_within_hours(published_text, HOURS_LOOKBACK)
            
            print(f"\n[{count}] {title}")
            print(f"    ID: {video_id}")
            print(f"    Time Text: '{published_text}'")
            print(f"    Within {HOURS_LOOKBACK}h?: {'YES ✅' if is_recent else 'NO ❌'}")
            
    except Exception as e:
        logger.error(f"❌ Error: {e}")

if __name__ == "__main__":
    run_debug()
