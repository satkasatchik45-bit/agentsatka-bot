---
name: windows_apps
description: Windows muhitida qulay GUI dasturlar, kalkulyatorlar va skriptlar yaratish, ularni 1-klikda ochiluvchi .bat orqali ishga tushirish
triggers: ['kalkulyator', 'calculator', 'gui', 'dastur', 'app', 'oyna', 'tkinter']
---

# Ko'nikma: Windows GUI va Ilovalar Yaratish

## 🎯 Maqsad
Foydalanuvchi Windows kompyuterida osongina foydalana oladigan grafik (GUI) dasturlar (masalan, Kalkulyator, eslatma dasturi, o'yin, valyuta hisoblagich) yaratish.

## 📋 Muhim Qoidalar va Algoritm
1. **Fayl assotsiatsiyasi muammosi:** Foydalanuvchida `.py` fayllar dastur sifatida to'g'ridan-to'g'ri ochilmasligi, "Qaysi dasturda ochishni xohlaysiz?" degan oyna chiqishi mumkin.
2. **Yechim (Ikkita fayl qoidasi):**
   - 1-fayl: `Dastur.py` (Tkinter asosidagi toza, zamonaviy GUI kodi).
   - 2-fayl: `Dasturni_Boshlash.bat` (Foydalanuvchi sichqoncha bilan ikki marta bosganda dasturni `pythonw.exe` orqali konsolsiz, silliq ochib beruvchi fayl).
3. **.bat fayli namunasi:**
   ```bat
   @echo off
   start pythonw.exe "%~dp0Dastur.py"
   ```
4. **Foydalanuvchiga taqdim etish:**
   - Dastur kodi va .bat faylini ishchi papkada yaratish.
   - Ikkala faylni ham foydalanuvchiga Telegram orqali yuborish.
   - Foydalanuvchiga: *"Ushbu dasturni ochish uchun .bat fayliga ikki marta bosing"* deb aniq yo'riqnoma berish.
