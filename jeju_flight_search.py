"""
제주도 항공편 검색 모듈
Gemini + Google Search 그라운딩으로 서울↔제주 항공권 가격을 실시간 검색합니다.
"""
import logging
import re
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

DEPARTURE_AIRPORTS = {
    "GMP": "김포",
    "ICN": "인천",
}
DESTINATION_NAME = "제주"

# Naver Flights 딥링크 (API 실패 시 fallback)
def get_naver_url(origin: str, dep_date: str) -> str:
    d = dep_date.replace("-", "")
    return f"https://flight.naver.com/flights/domestic/{origin}-CJU-{d}-1-0-0"


def _search_with_gemini(query: str) -> str:
    """Gemini + Google Search 그라운딩으로 검색합니다."""
    import google.generativeai as genai
    from config import GEMINI_API_KEY, GEMINI_MODEL

    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        tools=[{"google_search": {}}],
    )
    response = model.generate_content(query)
    return response.text


def search_jeju_flights(dep_date: str, origin: str = "GMP") -> str:
    """
    Gemini Search로 제주 항공편 정보를 가져옵니다.

    Args:
        dep_date: 출발일 (YYYY-MM-DD)
        origin:   출발 공항 코드 (GMP=김포, ICN=인천)

    Returns:
        요약 텍스트 (실패 시 None)
    """
    origin_name = DEPARTURE_AIRPORTS.get(origin, origin)
    date_kor = datetime.strptime(dep_date, "%Y-%m-%d").strftime("%Y년 %m월 %d일")

    query = (
        f"{date_kor} {origin_name}공항에서 제주도 가는 국내선 항공편 가격을 알려줘. "
        f"항공사별 최저 가격(원)과 출발·도착 시간을 목록으로 정리해줘. "
        f"가격이 없으면 일반적인 가격대를 알려줘."
    )

    try:
        result = _search_with_gemini(query)
        return result.strip()
    except Exception as e:
        logger.warning(f"[Gemini 항공편 검색 실패] {origin}→CJU {dep_date}: {e}")
        return None


def build_flight_report(days_ahead: int = 1, origins: list = None) -> str:
    """텔레그램 HTML 형식의 제주 항공편 리포트를 생성합니다."""
    if origins is None:
        origins = list(DEPARTURE_AIRPORTS.keys())

    dep_date = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
    date_kor = datetime.strptime(dep_date, "%Y-%m-%d").strftime("%m월 %d일")
    lines = [
        "✈️ <b>제주도 항공권</b>",
        f"📅 {date_kor} 출발 기준",
        "",
    ]

    for origin in origins:
        origin_name = DEPARTURE_AIRPORTS.get(origin, origin)
        naver_url = get_naver_url(origin, dep_date)

        lines.append(f"🛫 <b>{origin_name} → 제주</b>")

        result = search_jeju_flights(dep_date, origin)
        if result:
            # Gemini 응답에서 HTML 태그 제거 후 줄 단위로 들여쓰기
            for line in result.splitlines():
                line = line.strip()
                if line:
                    # 기본 마크다운 강조(**)를 HTML <b>로 변환
                    line = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", line)
                    lines.append(f"  {line}")
        else:
            lines.append(f'  → <a href="{naver_url}">네이버 항공권에서 확인하기</a>')

        lines.append("")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    import os
    logging.basicConfig(level=logging.INFO)

    # 로컬 테스트: GEMINI_API_KEY 환경변수 필요
    if not os.environ.get("GEMINI_API_KEY"):
        print("⚠️  GEMINI_API_KEY 환경변수를 설정하세요.")
        sys.exit(1)

    dep = sys.argv[1] if len(sys.argv) > 1 else (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    for origin, name in DEPARTURE_AIRPORTS.items():
        print(f"\n=== {name} → 제주 ({dep}) ===")
        result = search_jeju_flights(dep, origin)
        if result:
            print(result)
        else:
            print(f"검색 실패. URL: {get_naver_url(origin, dep)}")
