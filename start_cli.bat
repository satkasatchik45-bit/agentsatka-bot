@echo off
chcp 65001 > nul
title Antigravity AI Agent [Terminal CLI]
cd /d D:\agent

echo ======================================================================
echo           ANTIGRAVITY AVTONOM AGENTI YUKLANMOQDA...
echo ======================================================================
echo.

python main.py %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Xatolik yuz berdi. Tugmani bosing...
    pause > nul
)
