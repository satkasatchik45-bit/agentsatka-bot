@echo off
chcp 65001 > nul
title Antigravity Telegram Boti (@agentsatka_bot)
cd /d D:\agent

echo ======================================================================
echo           @agentsatka_bot AVTONOM AGENT ISHGA TUSHMOQDA...
echo ======================================================================
echo.

if exist "C:\Users\user\python_embed\python.exe" (
    "C:\Users\user\python_embed\python.exe" main.py --bot
) else (
    python main.py --bot
)
pause
