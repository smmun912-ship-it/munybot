@echo off
chcp 65001 >nul
echo ========================================
echo  YouTube-NotebookLM 일일 자동화 실행
echo  %date% %time%
echo ========================================

REM 프로젝트 디렉토리로 이동
cd /d "c:\Users\Moon\Antigravity works\youtube-notebooklm-agent"

REM Gemini API 키 설정 (여기에 키를 입력하세요)
set GEMINI_API_KEY=AIzaSyAWDSFTfSGMfZ5GNFIXe6u6AaRF2Utc83g

REM Windows 인코딩 설정
set PYTHONIOENCODING=utf-8

REM 파이썬 실행
python main.py

REM 결과 확인
if %errorlevel% equ 0 (
    echo.
    echo ✅ 자동화 완료!
) else (
    echo.
    echo ❌ 오류 발생. 로그를 확인하세요.
)

pause
