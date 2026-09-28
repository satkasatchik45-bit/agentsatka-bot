@echo off
chcp 65001 > nul
cd /d D:\agent
python main.py %*
if %ERRORLEVEL% NEQ 0 (
    if "%~1"=="" pause
)
