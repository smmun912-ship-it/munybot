# YouTube-NotebookLM 자동화 에이전트

매일 오전 7시 15분(KST), 9개 AI/테크 유튜브 채널의 최신 영상을 자동 수집하여 **종합 팟캐스트 스크립트**, **슬라이드**, **인포그래픽**을 생성하고 텔레그램으로 알림을 보냅니다.

## 🚀 기능

- 📡 9개 유튜브 채널 자동 스캔 (API 키 불필요)
- 📝 한국어 트랜스크립트 자동 추출
- 🎙️ AI 팟캐스트 스크립트 생성 (Gemini)
- 📊 Reveal.js 슬라이드 자동 생성
- 🎨 인포그래픽 자동 생성
- 📲 텔레그램으로 결과 알림
- 🌐 GitHub Pages로 웹 호스팅
- 📂 NotebookLM 호환 문서 생성 (NotebookLM 수동 업로드 필요)

## ⚠️ NotebookLM 연동 안내

현재 Google NotebookLM은 공식 API를 제공하지 않아 **자동 파일 업로드가 불가능**합니다.
이 에이전트는 NotebookLM에 최적화된 형태의 **소스 파일(종합 보고서, 팟캐스트 스크립트 등)**을 로컬에 생성해줍니다.

**사용 방법:**
1. 생성된 `output/YYYY-MM-DD/combined_summary.md` 파일을 다운로드
2. [NotebookLM](https://notebooklm.google.com/)에 접속
3. 새 노트북 생성 후 '소스 추가' -> '파일 업로드'로 해당 파일 업로드
4. NotebookLM의 기능을 통해 팟캐스트 청취 및 질의응답 진행

## ⚙️ 설정

### 1. GitHub Secrets 등록

Repository → Settings → Secrets and variables → Actions → New repository secret:

| Secret 이름 | 값 |
|---|---|
| `GEMINI_API_KEY` | Google AI Studio에서 발급받은 API 키 |
| `TELEGRAM_BOT_TOKEN` | @BotFather에서 발급받은 봇 토큰 |
| `TELEGRAM_CHAT_ID` | 본인의 텔레그램 Chat ID |
| `GITHUB_PAGES_URL` | 예: `https://username.github.io/youtube-notebooklm-agent` |

### 2. GitHub Pages 활성화

Repository → Settings → Pages → Source: **Deploy from a branch** → Branch: `main`, Folder: `/docs`

### 3. 수동 실행 테스트

Actions 탭 → "YouTube Daily Digest" → "Run workflow" 클릭

## 📂 출력물

| 파일 | 설명 |
|------|------|
| `output/YYYY-MM-DD/combined_summary.md` | 종합 보고서 |
| `output/YYYY-MM-DD/podcast_script.md` | 팟캐스트 스크립트 |
| `output/YYYY-MM-DD/slides.html` | Reveal.js 슬라이드 |
| `output/YYYY-MM-DD/infographic.html` | 인포그래픽 |
| `docs/` | GitHub Pages (최신 결과) |
