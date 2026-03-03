import logging
import sys
import os

# Adjust path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("ResearchOnly")

from research_agent import run_research

if __name__ == "__main__":
    logger.info("🧪 Running Research Agent Only (Production Logic)...")
    results = run_research()
    
    print("\n\n📊 RESULTS SUMMARY:")
    print(f"Total Videos Found: {results['total_videos']}")
    print(f"Total Transcripts: {results['total_transcripts']}")
    
    if results['total_videos'] > 0:
        print("\nVideos Detail:")
        for ch in results['channels']:
            if ch['videos_found'] > 0:
                print(f"  📺 {ch['name']}: {ch['videos_found']} videos")
                for v in ch['videos']:
                    print(f"     - {v['title']}")
    else:
        print("❌ No videos found matching the criteria.")
