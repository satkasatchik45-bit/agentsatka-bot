@echo off
chcp 65001 >nul
title Antigravity AI Agent - Telegram Bot

echo ========================================================
echo        ANTIGRAVITY AVTONOM AGENT (TELEGRAM BOT)
echo ========================================================
echo.

cd /d "%~dp0"

where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [XATOLIK] Python kompyuteringizda topilmadi!
    echo Iltimos, Python 3.10+ o'rnating: https://www.python.org/
    pause
    exit /b 1
)

echo [1/2] Kutubxonalar tekshirilmoqda...
python -m pip install -q -r requirements.txt

echo [2/2] Agent Telegram boti ishga tushirilmoqda...
echo.
echo ========================================================
echo Botni to'xtatish uchun klaviaturada Ctrl + C bosing.
echo ========================================================
echo.

python main.py

if %errorlevel% neq 0 (
    echo.
    echo [OGOHLANTIRISH] Dastur xatolik bilan to'xtadi.
    pause
)
