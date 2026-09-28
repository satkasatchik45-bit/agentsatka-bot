@echo off
chcp 65001 > nul
title Ollama (Lokal AI) Holati
cd /d D:\agent

echo ======================================================================
echo       INTERNETSIZ LOKAL SUN'IY INTELLEKT (OLLAMA) HOLATI
echo ======================================================================
echo.

set OLLAMA_EXE=C:\Users\%USERNAME%\AppData\Local\Programs\Ollama\ollama.exe

if exist "%OLLAMA_EXE%" (
    echo [TABRIKLAYMIZ] Ollama kompyuteringizda muvaffaqiyatli sozlangan!
    echo.
    echo Mavjud modellar ro'yxati:
    "%OLLAMA_EXE%" list
    echo.
    echo Sizning agentingiz ushbu modelga 100%% INTERNETSIZ ulanadi!
    echo.
    echo Agar yangi yoki boshqa model yuklamoqchi bo'lsangiz:
    echo Masalan: "%OLLAMA_EXE%" pull llama3.2:1b
) else (
    echo [!] Ollama topilmadi.
    echo Rasmiy sahifa: https://ollama.com/download/windows
    start https://ollama.com/download/windows
)

echo.
pause
