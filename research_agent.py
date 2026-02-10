"""
리서치 에이전트: YouTube 채널 모니터링 및 트랜스크립트 추출
- scrapetube로 최근 영상 목록 수집 (API 키 불필요)
- youtube-transcript-api로 자막 추출 (API 키 불필요)
- 채널별 요약 마크다운 생성
"""
import json
import logging
from datetime import datetime, timezone, timedelta
from pathlib import Path

import scrapetube
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import (
    TranscriptsDisabled,
    NoTranscriptFound,
)

from config import (
    YOUTUBE_CHANNELS,
    HOURS_LOOKBACK,
    MAX_VIDEOS_PER_CHANNEL,
    TRANSCRIPT_LANGUAGES,
    get_today_output_dir,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# 1. 최근 영상 수집
# ─────────────────────────────────────────────
def fetch_recent_videos(channel_handle: str, max_results: int = MAX_VIDEOS_PER_CHANNEL):
    """scrapetube으로 채널의 최근 영상 목록을 가져옵니다."""
    logger.info(f"📡 채널 스캔 중: {channel_handle}")
    try:
        # scrapetube는 채널 URL에서 직접 영상 목록을 가져옴
        videos = scrapetube.get_channel(
            channel_url=f"https://www.youtube.com/{channel_handle}",
            limit=max_results,
            sort_by="newest",
        )
        results = []
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=HOURS_LOOKBACK)

        for video in videos:
            video_id = video.get("videoId", "")
            title = video.get("title", {})
            if isinstance(title, dict):
                title = title.get("runs", [{}])[0].get("text", "제목 없음")

            # 게시 시간 텍스트 파싱 (예: "1 hour ago", "3 hours ago", "1 day ago")
            published_text = ""
            time_text = video.get("publishedTimeText", {})
            if isinstance(time_text, dict):
                published_text = time_text.get("simpleText", "")

            # 24시간 이내 판단
            is_recent = _is_within_hours(published_text, HOURS_LOOKBACK)

            if is_recent:
                view_count = video.get("viewCountText", {})
                if isinstance(view_count, dict):
                    view_count = view_count.get("simpleText", "조회수 없음")

                length_text = video.get("lengthText", {})
                if isinstance(length_text, dict):
                    length_text = length_text.get("simpleText", "")

                results.append({
                    "video_id": video_id,
                    "title": title,
                    "published_text": published_text,
                    "view_count": view_count if isinstance(view_count, str) else "",
                    "duration": length_text if isinstance(length_text, str) else "",
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                })

        logger.info(f"  → {len(results)}개 최근 영상 발견")
        return results

    except Exception as e:
        logger.error(f"  ❌ 채널 스캔 실패 ({channel_handle}): {e}")
        return []


def _is_within_hours(published_text: str, hours: int) -> bool:
    """YouTube의 상대 시간 텍스트를 파싱하여 N시간 이내인지 판단합니다."""
    if not published_text:
        return False

    text = published_text.lower().strip()

    # "N minutes/hours ago" 또는 한국어 "N시간 전", "N분 전"
    # Streamed N hours ago 도 포함
    text = text.replace("streamed ", "").replace("premiered ", "")

    # 영어 패턴
    if "just now" in text or "moment" in text:
        return True
    if "second" in text or "초" in text:
        return True
    if "minute" in text or "분" in text:
        return True

    # 시간 단위
    if "hour" in text or "시간" in text:
        try:
            num = int("".join(c for c in text if c.isdigit()) or "0")
            return num <= hours
        except ValueError:
            return False

    # 일 단위
    if "day" in text or "일" in text:
        try:
            num = int("".join(c for c in text if c.isdigit()) or "0")
            return num * 24 <= hours
        except ValueError:
            return False

    # 주 단위
    if "week" in text or "주" in text:
        try:
            num = int("".join(c for c in text if c.isdigit()) or "0")
            return num * 24 * 7 <= hours
        except ValueError:
            return False

    return False


# ─────────────────────────────────────────────
# 2. 트랜스크립트 추출
# ─────────────────────────────────────────────
def extract_transcript(video_id: str) -> dict:
    """YouTube 영상의 자막(트랜스크립트)을 추출합니다."""
    logger.info(f"  📝 트랜스크립트 추출 중: {video_id}")
    try:
        ytt_api = YouTubeTranscriptApi()
        transcript = ytt_api.fetch(
            video_id,
            languages=TRANSCRIPT_LANGUAGES,
        )
        full_text = " ".join([entry.text for entry in transcript])
        duration_sec = max([e.start + e.duration for e in transcript], default=0)

        logger.info(f"    ✅ {len(full_text)}자 추출 완료 (약 {int(duration_sec // 60)}분)")
        return {
            "success": True,
            "text": full_text,
            "char_count": len(full_text),
            "segment_count": len(transcript),
            "duration_minutes": round(duration_sec / 60, 1),
        }

    except (TranscriptsDisabled, NoTranscriptFound) as e:
        logger.warning(f"    ⚠️ 자막 없음 ({video_id}): {type(e).__name__}")
        return {"success": False, "text": "", "error": str(e)}

    except Exception as e:
        logger.error(f"    ❌ 트랜스크립트 추출 실패 ({video_id}): {e}")
        return {"success": False, "text": "", "error": str(e)}


# ─────────────────────────────────────────────
# 3. 채널별 요약 마크다운 생성
# ─────────────────────────────────────────────
def generate_channel_summary(channel_info: dict, videos_data: list) -> str:
    """채널의 수집된 영상 데이터를 마크다운 형식으로 정리합니다."""
    lines = [
        f"# {channel_info['name']} ({channel_info['handle']})",
        f"",
        f"**수집 시각**: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"**채널 URL**: {channel_info['url']}",
        f"**수집된 영상 수**: {len(videos_data)}",
        f"",
        "---",
        "",
    ]

    for i, video in enumerate(videos_data, 1):
        lines.append(f"## {i}. {video['title']}")
        lines.append(f"")
        lines.append(f"- **URL**: {video['url']}")
        lines.append(f"- **게시 시점**: {video.get('published_text', 'N/A')}")
        lines.append(f"- **길이**: {video.get('duration', 'N/A')}")
        lines.append(f"- **조회수**: {video.get('view_count', 'N/A')}")
        lines.append(f"")

        if video.get("transcript"):
            lines.append(f"### 트랜스크립트")
            lines.append(f"")
            lines.append(video["transcript"])
            lines.append(f"")
        else:
            lines.append(f"> ⚠️ 자막을 추출할 수 없습니다.")
            lines.append(f"")

        lines.append("---")
        lines.append("")

    return "\n".join(lines)


# ─────────────────────────────────────────────
# 4. 메인 리서치 실행
# ─────────────────────────────────────────────
def run_research() -> dict:
    """모든 채널에서 최근 영상을 수집하고 트랜스크립트를 추출합니다."""
    output_dir = get_today_output_dir()
    summary_dir = output_dir / "channel_summaries"

    logger.info("=" * 60)
    logger.info("🔍 리서치 에이전트 시작")
    logger.info(f"📅 날짜: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info(f"📂 출력 디렉토리: {output_dir}")
    logger.info(f"🔎 최근 {HOURS_LOOKBACK}시간 이내 영상 수집")
    logger.info("=" * 60)

    all_results = {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "channels": [],
        "total_videos": 0,
        "total_transcripts": 0,
    }

    for channel in YOUTUBE_CHANNELS:
        logger.info(f"\n{'─' * 40}")
        logger.info(f"📺 {channel['name']}")
        logger.info(f"{'─' * 40}")

        # 1. 최근 영상 수집
        videos = fetch_recent_videos(channel["handle"])

        if not videos:
            logger.info(f"  ℹ️ 최근 {HOURS_LOOKBACK}시간 이내 새 영상 없음")
            continue

        # 2. 각 영상의 트랜스크립트 추출
        videos_with_transcripts = []
        for video in videos:
            transcript_result = extract_transcript(video["video_id"])
            video["transcript"] = transcript_result.get("text", "")
            video["transcript_success"] = transcript_result.get("success", False)
            videos_with_transcripts.append(video)

        # 3. 채널 요약 마크다운 생성 및 저장
        summary_md = generate_channel_summary(channel, videos_with_transcripts)
        safe_name = channel["handle"].replace("@", "").replace(".", "_").replace("-", "_")
        summary_path = summary_dir / f"{safe_name}.md"
        summary_path.write_text(summary_md, encoding="utf-8")
        logger.info(f"  💾 요약 저장: {summary_path.name}")

        # 통계 업데이트
        transcript_count = sum(1 for v in videos_with_transcripts if v.get("transcript_success"))
        channel_result = {
            "name": channel["name"],
            "handle": channel["handle"],
            "videos_found": len(videos),
            "transcripts_extracted": transcript_count,
            "summary_file": str(summary_path),
            "videos": [
                {
                    "title": v["title"],
                    "url": v["url"],
                    "has_transcript": v.get("transcript_success", False),
                }
                for v in videos_with_transcripts
            ],
        }
        all_results["channels"].append(channel_result)
        all_results["total_videos"] += len(videos)
        all_results["total_transcripts"] += transcript_count

    # 결과 JSON 저장
    results_path = output_dir / "research_results.json"
    results_path.write_text(json.dumps(all_results, ensure_ascii=False, indent=2), encoding="utf-8")

    logger.info(f"\n{'=' * 60}")
    logger.info(f"✅ 리서치 완료!")
    logger.info(f"  📊 총 {all_results['total_videos']}개 영상 / {all_results['total_transcripts']}개 트랜스크립트")
    logger.info(f"  📂 결과: {output_dir}")
    logger.info(f"{'=' * 60}")

    return all_results


if __name__ == "__main__":
    import sys

    # --test 모드: 첫 번째 채널만 테스트
    if "--test" in sys.argv:
        logger.info("🧪 테스트 모드 - 첫 번째 채널만 실행")
        from config import YOUTUBE_CHANNELS as channels
        test_channel = channels[0]
        videos = fetch_recent_videos(test_channel["handle"], max_results=2)
        if videos:
            for v in videos:
                transcript = extract_transcript(v["video_id"])
                print(f"\n📹 {v['title']}")
                print(f"   자막: {'✅' if transcript['success'] else '❌'} ({transcript.get('char_count', 0)}자)")
        else:
            print("ℹ️ 최근 24시간 이내 영상 없음 - 최근 영상으로 테스트합니다")
            # 최근 영상이 없어도 채널의 가장 최근 영상으로 테스트
            all_videos = scrapetube.get_channel(
                channel_url=f"https://www.youtube.com/{test_channel['handle']}",
                limit=1,
                sort_by="newest",
            )
            for v in all_videos:
                vid = v.get("videoId", "")
                title_data = v.get("title", {})
                title = title_data.get("runs", [{}])[0].get("text", "제목 없음") if isinstance(title_data, dict) else str(title_data)
                print(f"\n📹 {title} (ID: {vid})")
                transcript = extract_transcript(vid)
                print(f"   자막: {'✅' if transcript['success'] else '❌'} ({transcript.get('char_count', 0)}자)")
                if transcript["success"]:
                    print(f"   미리보기: {transcript['text'][:200]}...")
    else:
        run_research()
