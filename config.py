"""
YouTube-NotebookLM 자동화 시스템 설정
"""
import os
from pathlib import Path
from datetime import datetime

# ============================================================
# 프로젝트 경로
# ============================================================
BASE_DIR = Path(__file__).parent
OUTPUT_DIR = BASE_DIR / "output"
TEMPLATES_DIR = BASE_DIR / "templates"

# ============================================================
# YouTube 채널 목록
# ============================================================
YOUTUBE_CHANNELS = [
    {"handle": "@ai.yeongseon", "name": "AI 연선", "url": "https://www.youtube.com/@ai.yeongseon"},
    {"handle": "@digital_ggultip", "name": "디지털꿀팁", "url": "https://www.youtube.com/@digital_ggultip"},
    {"handle": "@speech-cog", "name": "말하는인지", "url": "https://www.youtube.com/@speech-cog"},
    {"handle": "@greenkokki", "name": "그린코끼", "url": "https://www.youtube.com/@greenkokki"},
    {"handle": "@Smarthacker-Hub", "name": "스마트해커 허브", "url": "https://www.youtube.com/@Smarthacker-Hub"},
    {"handle": "@designingi", "name": "디자인잉", "url": "https://www.youtube.com/@designingi"},
    {"handle": "@elanvitalai", "name": "엘란비탈AI", "url": "https://www.youtube.com/@elanvitalai"},
    {"handle": "@omd_eunhwan", "name": "오은환", "url": "https://www.youtube.com/@omd_eunhwan"},
    {"handle": "@careerhackeralex", "name": "커리어해커 알렉스", "url": "https://www.youtube.com/@careerhackeralex"},
]

# ============================================================
# Gemini API 설정
# ============================================================
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"

# ============================================================
# NotebookLM 설정
# ============================================================
NOTEBOOKLM_NOTEBOOK_URL = os.environ.get("NOTEBOOKLM_NOTEBOOK_URL", "")

# ============================================================
# 실행 설정
# ============================================================
HOURS_LOOKBACK = 24  # 최근 N시간 이내 영상만 수집
MAX_VIDEOS_PER_CHANNEL = 5  # 채널당 최대 수집 영상 수
TRANSCRIPT_LANGUAGES = ["ko", "en"]  # 자막 우선순위 (한국어 > 영어)

# ============================================================
# 출력 설정
# ============================================================
def get_today_output_dir():
    """오늘 날짜 기반 출력 디렉토리 반환"""
    today = datetime.now().strftime("%Y-%m-%d")
    output_dir = OUTPUT_DIR / today
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "channel_summaries").mkdir(exist_ok=True)
    return output_dir
