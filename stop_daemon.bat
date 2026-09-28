@echo off
chcp 65001 > nul
title Fon Agentini To'xtatish
cd /d D:\agent

echo Fon agenti to'xtatilmoqda...

if exist "logs\daemon.pid" (
    set /p PID=<logs\daemon.pid
    taskkill /F /PID %PID% 2>nul
    del "logs\daemon.pid" 2>nul
    echo [OK] Fon agenti (PID: %PID%) to'xtatildi.
) else (
    echo [!] Fon agenti ishlamayapti yoki daemon.pid fayli topilmadi.
    echo Barcha fonda qolgan python daemon jarayonlari tekshirilmoqda...
    wmic process where "commandline like '%%python%%--daemon%%'" call terminate 2>nul
    echo Bajarildi.
)

pause
