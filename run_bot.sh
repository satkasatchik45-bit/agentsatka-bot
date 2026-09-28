#!/usr/bin/env bash
set -e

cd "$(dirname "$0")"

echo "========================================================"
echo "       ANTIGRAVITY AVTONOM AGENT (TELEGRAM BOT)"
echo "========================================================"

if ! command -v python3 &> /dev/null; then
    echo "[XATOLIK] Python3 topilmadi!"
    exit 1
fi

echo "[1/2] Kutubxonalar tekshirilmoqda..."
pip install -r requirements.txt

echo "[2/2] Agent boti ishga tushirilmoqda..."
python3 main.py
