@echo off
chcp 65001 > nul
title Antigravity Doimiy Fon Agenti [Monitoring]
cd /d D:\agent

echo ======================================================================
echo           ANTIGRAVITY DOIMIY FON AGENTI ISHGA TUSHMOQDA...
echo ======================================================================
echo Bu oyna fonda doimiy ishlab turadi va D:\agent\tasks\inbox papkasini
echo doimiy nazorat qiladi. Yangi topshiriq tushganda darhol bajaradi.
echo.
echo Oynani minimallashtirib (kichraytirib) qo'yishingiz mumkin.
echo To'xtatish uchun: Ctrl+C yoki stop_daemon.bat ni bosing.
echo ======================================================================
echo.

python main.py --daemon
pause
