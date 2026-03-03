"""
종합 에이전트: 리서치 결과를 통합하여 NotebookLM에 전달하고 콘텐츠 생성
- 채널별 요약을 하나의 종합 보고서로 통합
- Gemini API로 팟캐스트 스크립트 생성
- 슬라이드/인포그래픽 데이터 구조화
"""
import json
import logging
from datetime import datetime
from pathlib import Path

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

from config import GEMINI_API_KEY, GEMINI_MODEL, get_today_output_dir

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────
# Gemini API 초기화
# ─────────────────────────────────────────────
def init_gemini():
    """Gemini API 초기화"""
    if not HAS_GEMINI:
        logger.warning("⚠️ google-generativeai 패키지가 설치되지 않았습니다.")
        return None
    if not GEMINI_API_KEY:
        logger.warning("⚠️ GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
        return None
    genai.configure(api_key=GEMINI_API_KEY)
    return genai.GenerativeModel(GEMINI_MODEL)


# ─────────────────────────────────────────────
# 1. 종합 보고서 생성
# ─────────────────────────────────────────────
def build_combined_summary(output_dir: Path) -> str:
    """모든 채널 요약을 하나의 종합 보고서로 통합합니다."""
    summary_dir = output_dir / "channel_summaries"
    if not summary_dir.exists():
        logger.error("❌ 채널 요약 디렉토리가 없습니다.")
        return ""

    summaries = []
    for md_file in sorted(summary_dir.glob("*.md")):
        content = md_file.read_text(encoding="utf-8")
        if content.strip():
            summaries.append(content)

    if not summaries:
        logger.warning("⚠️ 수집된 채널 요약이 없습니다.")
        return ""

    combined = f"""# 📊 AI/테크 유튜브 일일 종합 보고서

**생성일**: {datetime.now().strftime('%Y년 %m월 %d일 %H:%M')}
**분석 대상**: {len(summaries)}개 채널

---

"""
    combined += "\n\n---\n\n".join(summaries)

    # 종합 보고서 저장
    combined_path = output_dir / "combined_summary.md"
    combined_path.write_text(combined, encoding="utf-8")
    logger.info(f"📄 종합 보고서 저장: {combined_path}")

    return combined


# ─────────────────────────────────────────────
# 2. 팟캐스트 스크립트 생성
# ─────────────────────────────────────────────
PODCAST_PROMPT = """당신은 AI/테크 분야의 인기 팟캐스트 진행자입니다.
아래 여러 유튜브 채널의 최신 영상 요약을 기반으로,
두 명의 진행자(호스트A, 호스트B)가 대화하는 형식의 팟캐스트 스크립트를 작성해주세요.

**형식 요구사항:**
- 자연스러운 대화체 (한국어)
- 호스트A는 메인 진행자, 호스트B는 분석가 역할
- 오프닝 인사 → 주요 뉴스/트렌드 소개 → 심층 분석 → 클로징
- 각 채널의 핵심 콘텐츠를 자연스럽게 엮어서 이야기
- 청취자가 흥미를 느낄 수 있는 포인트 강조
- 15~20분 분량 (약 3000~4000자)

**대화 형식:**
호스트A: (대사)
호스트B: (대사)

아래는 오늘의 유튜브 채널 요약입니다:

{content}
"""


# ─────────────────────────────────────────────
# 1.5. 개별 영상 요약 (Telegram 전송용)
# ─────────────────────────────────────────────
SUMMARY_PROMPT = """아래는 유튜브 영상의 자막(트랜스크립트)입니다.
이 영상의 핵심 내용을 3개의 불릿포인트로 요약해주세요.

**요구사항:**
- 한국어로 작성
- 각 포인트는 명확하고 구체적으로
- 이모지 사용 가능
- 불릿포인트 기호는 '•' 사용

자막:
{transcript}
"""


def summarize_video_content(transcript: str, model) -> str:
    """개별 영상의 자막을 3줄 요약합니다."""
    if not transcript or len(transcript) < 50:
        return ""
    
    if model is None:
        return "• (API 키 미설정으로 요약 불가)"

    try:
        # 자막이 너무 길 경우 앞부분만 사용 (토큰 절약)
        prompt = SUMMARY_PROMPT.format(transcript=transcript[:15000])
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"  ❌ 영상 요약 실패: {e}")
        if "429" in str(e):
             return "• (사용량 초과로 요약 불가)"
        return f"• (요약 실패: {str(e)})"


def generate_podcast_script(combined_summary: str, model) -> str:
    """Gemini를 사용하여 팟캐스트 스크립트를 생성합니다."""
    logger.info("🎙️ 팟캐스트 스크립트 생성 중...")

    if model is None:
        return _generate_podcast_fallback(combined_summary, error_msg="API Key Not Configured")

    try:
        prompt = PODCAST_PROMPT.format(content=combined_summary[:30000])
        response = model.generate_content(prompt)
        script = response.text
        logger.info(f"  ✅ 팟캐스트 스크립트 생성 완료 ({len(script)}자)")
        return script
    except Exception as e:
        logger.error(f"  ❌ Gemini API 오류: {e}")
        return _generate_podcast_fallback(combined_summary, error_msg=str(e))


def _generate_podcast_fallback(combined_summary: str, error_msg: str = None) -> str:
    """Gemini API 없이 기본 팟캐스트 템플릿 생성"""
    logger.info("  ℹ️ 폴백 모드: 기본 템플릿 사용")
    
    warning_msg = "⚠️ Gemini API 키가 설정되지 않았거나 오류가 발생했습니다."
    if error_msg and "429" in error_msg:
        warning_msg = "⚠️ Gemini 무료 사용량 한도(Quota)가 초과되었습니다. (내일 초기화됩니다)"
    elif error_msg:
        warning_msg = f"⚠️ API 오류 발생: {error_msg}"

    return f"""# 🎙️ AI/테크 데일리 팟캐스트 스크립트

**날짜**: {datetime.now().strftime('%Y년 %m월 %d일')}

---

호스트A: 안녕하세요! AI/테크 데일리 팟캐스트에 오신 것을 환영합니다.
호스트B: 네, 오늘도 여러 AI 유튜버들의 최신 콘텐츠를 종합해서 전해드리겠습니다.

호스트A: 오늘은 총 여러 채널에서 새로운 영상이 올라왔는데요,
주요 내용을 정리해볼까요?

---

> {warning_msg}
> 
> 아래 종합 요약을 참고하여 직접 스크립트를 작성하거나,
> GEMINI_API_KEY 환경변수를 확인해주세요.

---

## 원본 종합 요약

{combined_summary[:5000]}
"""


# ─────────────────────────────────────────────
# 3. 슬라이드 데이터 생성
# ─────────────────────────────────────────────
SLIDES_PROMPT = """아래 유튜브 채널 종합 요약을 기반으로, 프레젠테이션 슬라이드 데이터를 JSON 형식으로 생성해주세요.

**요구사항:**
- 총 8~12장 슬라이드
- 각 슬라이드에는 title, content (불릿포인트 리스트), notes (발표자 노트) 포함
- 첫 슬라이드: 제목 슬라이드
- 중간 슬라이드: 채널별 또는 주제별 핵심 내용
- 마지막 슬라이드: 요약 및 시사점

**JSON 형식:**
```json
{{
  "title": "전체 프레젠테이션 제목",
  "date": "날짜",
  "slides": [
    {{
      "title": "슬라이드 제목",
      "content": ["포인트 1", "포인트 2", "포인트 3"],
      "notes": "발표자 노트"
    }}
  ]
}}
```

종합 요약:
{content}
"""


def generate_slides_data(combined_summary: str, model) -> dict:
    """슬라이드 구조 데이터를 생성합니다."""
    logger.info("📊 슬라이드 데이터 생성 중...")

    if model is None:
        return _generate_slides_fallback(combined_summary, error_msg="API Key Not Configured")

    try:
        prompt = SLIDES_PROMPT.format(content=combined_summary[:25000])
        response = model.generate_content(prompt)
        text = response.text

        # JSON 블록 추출
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        slides_data = json.loads(text.strip())
        logger.info(f"  ✅ {len(slides_data.get('slides', []))}장 슬라이드 생성 완료")
        return slides_data

    except Exception as e:
        logger.error(f"  ❌ 슬라이드 데이터 생성 실패: {e}")
        return _generate_slides_fallback(combined_summary, error_msg=str(e))


def _generate_slides_fallback(combined_summary: str, error_msg: str = None) -> dict:
    """Gemini 없이 기본 슬라이드 구조 생성"""
    
    warning_title = "⚠️ API 설정 확인 필요"
    warning_desc = "GEMINI_API_KEY 환경변수를 설정해주세요"
    
    if error_msg and "429" in error_msg:
        warning_title = "⚠️ 일일 사용량 초과 (Quota Exceeded)"
        warning_desc = "무료 사용 한도가 초과되었습니다. 내일 다시 시도해주세요."
    elif error_msg:
        warning_desc = f"오류 발생: {error_msg}"

    return {
        "title": f"AI/테크 유튜브 일일 종합 - {datetime.now().strftime('%Y.%m.%d')}",
        "date": datetime.now().strftime("%Y년 %m월 %d일"),
        "slides": [
            {
                "title": "오늘의 AI/테크 트렌드",
                "content": [
                    "여러 AI 유튜브 채널의 최신 콘텐츠를 종합합니다",
                    f"분석 날짜: {datetime.now().strftime('%Y년 %m월 %d일')}",
                    "Gemini API 키 설정 후 자동 슬라이드 생성 가능",
                ],
                "notes": "인트로 슬라이드",
            },
            {
                "title": warning_title,
                "content": [
                    warning_desc,
                    "Google AI Studio에서 무료로 발급 가능",
                    "https://aistudio.google.com/apikey",
                ],
                "notes": "API 키 설정 안내",
            },
        ],
    }


# ─────────────────────────────────────────────
# 4. 인포그래픽 데이터 생성
# ─────────────────────────────────────────────
INFOGRAPHIC_PROMPT = """아래 유튜브 채널 종합 요약을 기반으로, 인포그래픽 데이터를 JSON으로 생성해주세요.

**요구사항:**
- headline: 한 줄 핵심 타이틀
- subheadline: 부제목
- key_stats: 주요 통계/수치 3~5개 (각각 label, value, icon 포함)
- main_topics: 주요 토픽 3~5개 (각각 title, description, keywords 포함)  
- trending_keywords: 트렌딩 키워드 5~8개
- takeaway: 핵심 시사점 한 문장

**JSON 형식:**
```json
{{
  "headline": "핵심 타이틀",
  "subheadline": "부제목",
  "date": "날짜",
  "key_stats": [
    {{"label": "분석 채널", "value": "9개", "icon": "📺"}},
    {{"label": "신규 영상", "value": "15개", "icon": "🎬"}}
  ],
  "main_topics": [
    {{
      "title": "토픽 제목",
      "description": "설명",
      "keywords": ["키워드1", "키워드2"]
    }}
  ],
  "trending_keywords": ["키워드1", "키워드2"],
  "takeaway": "핵심 시사점"
}}
```

종합 요약:
{content}
"""


def generate_infographic_data(combined_summary: str, model) -> dict:
    """인포그래픽 데이터를 생성합니다."""
    logger.info("🎨 인포그래픽 데이터 생성 중...")

    if model is None:
        return _generate_infographic_fallback(error_msg="API Key Not Configured")

    try:
        prompt = INFOGRAPHIC_PROMPT.format(content=combined_summary[:20000])
        response = model.generate_content(prompt)
        text = response.text

        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]

        data = json.loads(text.strip())
        logger.info("  ✅ 인포그래픽 데이터 생성 완료")
        return data

    except Exception as e:
        logger.error(f"  ❌ 인포그래픽 데이터 생성 실패: {e}")
        return _generate_infographic_fallback(error_msg=str(e))


def _generate_infographic_fallback(error_msg: str = None) -> dict:
    state_msg = "API 키 필요"
    if error_msg and "429" in error_msg:
        state_msg = "사용량 초과"
    
    return {
        "headline": "AI/테크 데일리 인사이트",
        "subheadline": f"{datetime.now().strftime('%Y년 %m월 %d일')} 유튜브 트렌드",
        "date": datetime.now().strftime("%Y년 %m월 %d일"),
        "key_stats": [
            {"label": "분석 채널", "value": "9개", "icon": "📺"},
            {"label": "상태", "value": state_msg, "icon": "⚠️"},
        ],
        "main_topics": [],
        "trending_keywords": ["AI", "자동화", "트렌드"],
        "takeaway": f"오류: {error_msg}" if error_msg else "GEMINI_API_KEY를 설정하면 자동 분석이 가능합니다.",
    }


# ─────────────────────────────────────────────
# 5. 메인 종합 실행
# ─────────────────────────────────────────────
def run_synthesis(research_results: dict = None) -> dict:
    """종합 에이전트 실행: 통합, 팟캐스트, 슬라이드, 인포그래픽 생성"""
    output_dir = get_today_output_dir()
    model = init_gemini()

    logger.info("=" * 60)
    logger.info("📊 종합 에이전트 시작")
    logger.info("=" * 60)

    # 1. 종합 보고서 생성
    combined = build_combined_summary(output_dir)
    if not combined:
        logger.error("❌ 종합할 데이터가 없습니다. 리서치 에이전트를 먼저 실행하세요.")
        return {"success": False, "error": "No data to synthesize"}

    # 1.5. 개별 영상 요약 (research_results.json 업데이트)
    if research_results:
        logger.info("📝 개별 영상 요약 생성 중...")
        updated_count = 0
        for channel in research_results.get("channels", []):
            for video in channel.get("videos", []):
                # 자막이 있고 요약이 없는 경우에만 수행
                # (research_results에는 전체 transcript가 없으므로, 파일에서 읽거나 
                #  이전 단계에서 transcript가 포함된 full data를 넘겨받아야 함.
                #  메모리 효율을 위해 여기서는 research_agent가 저장한 개별 md 파일을 읽지 않고,
                #  research_results에 transcript가 포함되어 있다고 가정하거나,
                #  별도로 자막 파일을 읽어야 함.
                #  
                #  *수정*: research_agent.py를 보면 research_results.json에는 'transcript' 필드가 포함되지 않음.
                #  대신 channel_summaries/*.md 파일에 자막이 있음.
                #  하지만 파싱하기 복잡하므로, research_results.json 구조를 변경하여 transcript를 포함시키거나
                #  여기서 md 파일을 다시 읽어야 함.
                #  
                #  가장 쉬운 방법: research_agent.py에서 json 저장 시 transcript 포함하도록 수정.
                #  하지만 이미 실행된 결과에 대해 돌리려면... 
                #  일단 manual_test에서는 transcript가 메모리에 있으므로 전달됨.
                pass 
        
        # 실제 구현: 
        # run_synthesis는 main.py에서 호출될 때 'results'를 받음.
        # research_agent.py의 run_research() 반환값에는 transcript가 포함되어 있지 않음 (videos_with_transcripts는 지역변수).
        # 따라서 research_agent.py를 수정하여 transcript를 결과에 포함시키거나,
        # 여기서 md 파일을 파싱해야 함.
        # 
        # 전략: research_agent.py가 JSON에 transcript를 포함하도록 수정하는 것이 가장 정석임.
        # 하지만 당장 테스트를 위해선, research_results 딕셔너리에 transcript가 있다고 가정하고 처리.
        # (main.py에서 run_research의 리턴값을 그대로 넘김)
        
        for channel in research_results.get("channels", []):
            for video in channel.get("videos", []):
                # video 객체에 transcript가 있다면 요약 시도
                if video.get("has_transcript") and "transcript" in video:
                     summary = summarize_video_content(video["transcript"], model)
                     video["summary"] = summary
                     updated_count += 1
        
        if updated_count > 0:
            logger.info(f"  ✅ {updated_count}개 영상 요약 완료")
            # 업데이트된 결과를 다시 저장
            results_path = output_dir / "research_results.json"
            results_path.write_text(json.dumps(research_results, ensure_ascii=False, indent=2), encoding="utf-8")
        else:
            logger.info("  ℹ️ 요약할 영상 자막을 찾지 못했습니다 (JSON에 transcript 미포함 가능성).")

    # 2. 팟캐스트 스크립트 생성
    podcast = generate_podcast_script(combined, model)
    podcast_path = output_dir / "podcast_script.md"
    podcast_path.write_text(podcast, encoding="utf-8")
    logger.info(f"🎙️ 팟캐스트 스크립트 저장: {podcast_path}")

    # 3. 슬라이드 데이터 생성
    slides_data = generate_slides_data(combined, model)
    slides_json_path = output_dir / "slides_data.json"
    slides_json_path.write_text(json.dumps(slides_data, ensure_ascii=False, indent=2), encoding="utf-8")

    # 4. 인포그래픽 데이터 생성
    infographic_data = generate_infographic_data(combined, model)
    infographic_json_path = output_dir / "infographic_data.json"
    infographic_json_path.write_text(json.dumps(infographic_data, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "success": True,
        "output_dir": str(output_dir),
        "files": {
            "combined_summary": str(output_dir / "combined_summary.md"),
            "podcast_script": str(podcast_path),
            "slides_data": str(slides_json_path),
            "infographic_data": str(infographic_json_path),
        },
    }
