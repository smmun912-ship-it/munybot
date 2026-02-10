"""
메인 오케스트레이터: 리서치 → 종합 → 출력물 생성 전체 파이프라인
"""
import sys
import logging
import traceback
from datetime import datetime

from config import get_today_output_dir

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(
            get_today_output_dir() / "pipeline.log",
            encoding="utf-8",
        ),
    ],
)
logger = logging.getLogger(__name__)


def run_pipeline():
    """전체 파이프라인 실행"""
    start_time = datetime.now()
    output_dir = get_today_output_dir()

    logger.info("╔" + "═" * 58 + "╗")
    logger.info("║  🚀 YouTube-NotebookLM 자동화 파이프라인 시작              ║")
    logger.info("║  " + f"📅 {start_time.strftime('%Y-%m-%d %H:%M:%S')}" + " " * 34 + "║")
    logger.info("╚" + "═" * 58 + "╝")

    results = {"success": False, "stages": {}}

    try:
        # ──────────────────────────────────────
        # Stage 1: 리서치 에이전트
        # ──────────────────────────────────────
        logger.info("\n" + "=" * 60)
        logger.info("📌 Stage 1/3: 리서치 에이전트")
        logger.info("=" * 60)

        from research_agent import run_research
        research_results = run_research()
        results["stages"]["research"] = {
            "success": True,
            "total_videos": research_results.get("total_videos", 0),
            "total_transcripts": research_results.get("total_transcripts", 0),
        }

        if research_results.get("total_videos", 0) == 0:
            logger.warning("⚠️ 최근 24시간 이내 새 영상이 없습니다.")
            logger.info("ℹ️ 종합 에이전트를 건너뜁니다.")
            results["success"] = True
            results["message"] = "새 영상 없음"
            return results

        # ──────────────────────────────────────
        # Stage 2: 종합 에이전트
        # ──────────────────────────────────────
        logger.info("\n" + "=" * 60)
        logger.info("📌 Stage 2/3: 종합 에이전트")
        logger.info("=" * 60)

        from synthesis_agent import run_synthesis
        synthesis_results = run_synthesis(research_results)
        results["stages"]["synthesis"] = {
            "success": synthesis_results.get("success", False),
        }

        # ──────────────────────────────────────
        # Stage 3: HTML 출력물 생성
        # ──────────────────────────────────────
        logger.info("\n" + "=" * 60)
        logger.info("📌 Stage 3/3: HTML 출력물 생성")
        logger.info("=" * 60)

        from slide_generator import generate_slides_html
        from infographic_generator import generate_infographic_html

        slides_path = generate_slides_html()
        infographic_path = generate_infographic_html()

        results["stages"]["output"] = {
            "success": True,
            "slides": slides_path,
            "infographic": infographic_path,
        }

        results["success"] = True

    except Exception as e:
        logger.error(f"\n❌ 파이프라인 오류: {e}")
        logger.error(traceback.format_exc())
        results["error"] = str(e)

    finally:
        elapsed = (datetime.now() - start_time).total_seconds()
        logger.info("\n" + "╔" + "═" * 58 + "╗")
        logger.info(f"║  {'✅' if results['success'] else '❌'} 파이프라인 {'완료' if results['success'] else '실패'}" + " " * 40 + "║")
        logger.info(f"║  ⏱️  소요 시간: {elapsed:.1f}초" + " " * 38 + "║")
        logger.info(f"║  📂 출력: {output_dir}" + " " * max(0, 38 - len(str(output_dir))) + "║")
        logger.info("╚" + "═" * 58 + "╝")

    return results


if __name__ == "__main__":
    results = run_pipeline()
    sys.exit(0 if results.get("success") else 1)
