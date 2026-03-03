import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path

# Adjust path to import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Inject Credentials for Test (from run_daily.bat)
# MUST happen before importing config
os.environ["GEMINI_API_KEY"] = "AIzaSyAWDSFTfSGMfZ5GNFIXe6u6AaRF2Utc83g"

from config import YOUTUBE_CHANNELS, get_today_output_dir
from research_agent import fetch_recent_videos, extract_transcript, generate_channel_summary
from synthesis_agent import run_synthesis
from slide_generator import generate_slides_html
from infographic_generator import generate_infographic_html
from telegram_notifier import send_telegram_message, build_daily_report

# Setup Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ManualTest")

# Ensure UTF-8 Output
if sys.stdout.encoding != 'utf-8':
    sys.stdout.reconfigure(encoding='utf-8')

# Inject Credentials for Test (from run_daily.bat)
os.environ["GEMINI_API_KEY"] = "AIzaSyAWDSFTfSGMfZ5GNFIXe6u6AaRF2Utc83g"
# Note: Telegram tokens are missing locally. Sending will likely fail but generation will work.

def run_manual_test():
    logger.info("🧪 Manual Test Started: Picking 1 video for end-to-end test")

    # 1. Pick a target channel (e.g., the first one)
    target_channel = YOUTUBE_CHANNELS[0]
    logger.info(f"📍 Target Channel: {target_channel['name']} ({target_channel['handle']})")

    # 2. Fetch LATEST video (Force 1 result, ignore time limit logic by manually calling scrapetube or using fetch with modification? 
    # Actually fetch_recent_videos checks time. 
    # We will manually fetch using scrapetube here to bypass the time check in fetch_recent_videos)
    
    import scrapetube
    videos = list(scrapetube.get_channel(channel_url=target_channel['url'], limit=1, sort_by="newest"))
    
    if not videos:
        logger.error("❌ No videos found in channel.")
        return

    video_data = videos[0]
    video_id = video_data['videoId']
    title_runs = video_data.get("title", {}).get("runs", [{}])
    title = title_runs[0].get("text", "No Title") if title_runs else "No Title"
    
    logger.info(f"🎬 Found Video: {title} ({video_id})")

    # 3. Extract Transcript
    transcript_result = extract_transcript(video_id)
    transcript_text = transcript_result.get("text", "")
    
    # 4. Construct 'research_results' mock
    # Need to simulate the structure expected by synthesis_agent
    
    video_info = {
        "video_id": video_id,
        "title": title,
        "url": f"https://www.youtube.com/watch?v={video_id}",
        "published_text": "Manual Test",
        "duration": "N/A",
        "view_count": "N/A",
        "transcript": transcript_text,
        "transcript_success": transcript_result.get("success", False)
    }

    output_dir = get_today_output_dir()
    summary_md = generate_channel_summary(target_channel, [video_info])
    
    # Save channel summary
    safe_name = target_channel["handle"].replace("@", "").replace(".", "_").replace("-", "_")
    summary_path = output_dir / "channel_summaries" / f"{safe_name}.md"
    summary_path.write_text(summary_md, encoding="utf-8")

    research_results = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "channels": [{
            "name": target_channel["name"],
            "handle": target_channel["handle"],
            "videos_found": 1,
            "transcripts_extracted": 1 if transcript_result.get("success") else 0,
            "summary_file": str(summary_path),
            "videos": [{
                "title": title,
                "url": video_info["url"],
                "has_transcript": video_info["transcript_success"],
                "transcript": video_info["transcript"]
            }]
        }],
        "total_videos": 1,
        "total_transcripts": 1 if transcript_result.get("success") else 0
    }
    
    # Save research results json
    results_path = output_dir / "research_results.json"
    results_path.write_text(json.dumps(research_results, ensure_ascii=False, indent=2), encoding="utf-8")

    # 5. Run Synthesis
    logger.info("🧠 Running Synthesis Agent...")
    synthesis_results = run_synthesis(research_results)

    # 6. Generate Outputs
    logger.info("🎨 Generating HTML Outputs...")
    generate_slides_html()
    generate_infographic_html()

    # 7. Telegram Notification
    logger.info("📲 Sending Telegram Notification...")
    report = build_daily_report()
    print("\n--- Message Preview ---")
    print(report)
    print("-----------------------\n")
    
    success = send_telegram_message(report)
    if success:
        logger.info("✅ Test Completed Successfully!")
    else:
        logger.error("❌ Telegram Send Failed.")

if __name__ == "__main__":
    run_manual_test()
