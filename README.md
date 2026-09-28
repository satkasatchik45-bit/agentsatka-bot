# 🤖 Antigravity AI Agent (CLI & Doimiy Fon Agenti)

Kompyuteringizni (Windows) qora oynada (Terminal/CLI) va doimiy fonda (Daemon) **mustaqil boshqaruvchi**, qadam-baqadam nima qilayotganini ko'rsatib boruvchi, **internetsiz ham, internet bilan ham to'liq ishlaydigan** shaxsiy avtonom sun'iy intellekt agenti.

---

## 🌟 Asosiy Imkoniyatlar

1. **🖥️ Qora oynadagi interaktiv Terminal (CLI):**
   - Zamonaviy qora konsol oynasida har bir amalni qadam-baqadam vizual ko'rsatib boradi:
     - `🧠 [1-qadam: Tahlil va Reja]` — Agent vazifani qanday tushungani va rejasini aytadi.
     - `⚙️ [2-qadam: Asbob chaqiruvi]` — Qaysi tizim asbobi yoki buyrug'i ishlatilayotgani.
     - `👁️ [Kuzatuv/Observation]` — Asbob qaytargan natijani o'rganadi.
     - `✨ [Yakuniy Natija]` — Chiroyli o'zbek tilida tayyor hisobot beradi.

2. **⚡ Ikki tomonlama intellekt (Dual-Mode):**
   - **🔴 INTERNETSIZ (100% Offline Rejim):**
     - Internet uzilganda ham kompyuteringiz ichidagi **barcha** ishlarni to'liq mustaqil bajara oladi.
     - O'zbek tilidagi buyruqlarni tahlil qiluvchi maxsus mahalliy miya (`OfflineEngine`) bilan jihozlangan.
     - Agar kompyuteringizda **Ollama** (masalan `qwen2.5` yoki `llama3`) o'rnatilgan bo'lsa, unga avtomatik ulanadi!
   - **🟢 INTERNET BILAN (Online Rejim):**
     - Internet mavjud bo'lganda va `.env` faylida kalit bo'lsa, eng zamonaviy **Google Gemini 2.5 Flash** modeliga ulanadi.
     - Internetdan ma'lumot qidirish (`search_web`) va veb-saytlarni tahlil qilish (`fetch_webpage`) imkoniyatlari ochiladi.
     - Internet to'satdan uzilsa ham, dastur to'xtab qolmaydi — avtomatik tarzda internetsiz mahalliy rejimga o'tadi!

3. **🔄 Doimiy Fon Agenti (24/7 Background Service):**
   - Orqa fonda jimjit ishlaydi va `D:\agent\tasks\inbox` papkasini kuzatadi.
   - Siz istalgan vaqtda konsoldan `agent do "vazifa matni"` buyrug'ini bersangiz yoki inbox papkasiga fayl tashlasangiz, agent uni orqa fonda avtonom bajaradi.
   - Natijani `D:\agent\tasks\results` papkasiga `.md` hisobot qilib yozadi va `D:\agent\logs\agent.log` fayliga to'liq qayd etadi.
   - Vazifa tugaganda Windows bildirishnomasi (balon xabar) orqali xabar beradi.

4. **🛠️ Kompyuterni boshqarish asboblari:**
   - **PowerShell / CMD:** Istalgan konsol buyruqlarini barcha disklarda (`C:`, `D:`) bajarish.
   - **Fayllar va Jildlar:** Yaratish, o'qish, tahrirlash, qidirish, ro'yxatini ko'rish, arxivlash (ZIP).
   - **Tizim diagnostikasi:** CPU, RAM, Disklar bo'sh joyi, Tarmoq kartalari, Uptime.
   - **Jarayonlar:** Ko'p xotira (RAM) yeyotgan dasturlarni ko'rish va to'xtatish (kill).
   - **Dasturlarni ishga tushirish:** Kalkulyator, bloknot, brauzer, fayl menejeri (explorer) va h.k.
   - **Python Interpreter:** Murakkab hisob-kitoblar va avtomatlashtirish skriptlarini yozish va bajarish.

---

## 📂 Loyiha Tuzilishi (`D:\agent\`)

```text
D:\agent\
│
├── start_cli.bat             <-- Qora oynada (Terminalda) agentni ochish
├── agent.bat                 <-- Tezkor buyruq vositasi (masalan: agent "vazifa" yoki agent do "vazifa")
├── start_daemon.bat          <-- Doimiy fon agentini monitoring oynasida ochish
├── start_daemon_hidden.vbs   <-- Doimiy fon agentini butunlay yashirin (oynasiz) ishga tushirish
├── stop_daemon.bat           <-- Ishlayotgan fon agentini xavfsiz to'xtatish
├── setup_ollama.bat          <-- Internetsiz Ollama (Qwen/Llama3) o'rnatish yordamchisi
├── run_telegram_bot.bat      <-- Telegram bot rejimida ishga tushirish (agar kerak bo'lsa)
├── main.py                   <-- Asosiy yagona ishga tushiruvchi
├── .env                      <-- Sozlamalar va API kalitlar
├── requirements.txt          <-- Python kutubxonalari
│
├── tasks/                    <-- Fon vazifalari almashish hududi
│   ├── inbox/                <-- Yangi topshiriqlar tushadigan jild
│   ├── completed/            <-- Bajarilgan topshiriqlar arxivi
│   └── results/              <-- Natijaviy hisobotlar (.md)
│
├── logs/                     <-- Jurnallar
│   └── agent.log             <-- Barcha qadamlar va amallar tarixi
│
├── workspace/                <-- Agentning asosiy ishchi papkasi
│
└── agent/                    <-- Dastur kodlari
    ├── cli.py                <-- Qora oynadagi zamonaviy CLI interfeys
    ├── core.py               <-- Asosiy boshqaruvchi universal miya
    ├── offline_engine.py     <-- 100% Internetsiz ishlovchi o'zbekcha NLP miya
    ├── local_llm.py          <-- Mahalliy Ollama / LM Studio moduli
    ├── net_checker.py        <-- Tarmoqni tezkor aniqlovchi
    ├── system_info.py        <-- CPU, RAM, Disklar holati moduli
    ├── tools.py              <-- Tizim asboblari
    ├── daemon.py             <-- Fon xizmati (Daemon)
    └── bot.py                <-- Telegram boti
```

---

## 🚀 Ishga Tushirish va Foydalanish

### 1. Qora oynada (Terminal CLI) ishga tushirish:
`D:\agent` papkasidagi **`start_cli.bat`** faylini sichqoncha bilan ikki marta bosing (yoki CMD da `agent` deb yozing).

Qora oyna ochiladi va quyidagicha interaktiv muhit paydo bo'ladi:
```text
Antigravity (D:\agent) ❯ 
```
Endi istalgan buyruqni o'zbek tilida yozishingiz mumkin!

### 2. Tezkor buyruqlar:
- `agent "D diskdagi bo'sh joyni ko'rsat"` — Terminal ochmasdan to'g'ridan-to'g'ri natijani oladi.
- `agent status` — Kompyuter tizim holatini chiqaradi.
- `agent do "D diskdagi ovoz fayllarini qidir"` — Topshiriqni fon agentiga yuboradi.

### 3. Doimiy Fon Agenti (Daemon) rejimida ishlatish:
- **Oddiy rejim:** `start_daemon.bat` ni bosing. Kichkina oyna ochiladi va u 24/7 fonda vazifalar kutib turadi.
- **Yashirin rejim:** `start_daemon_hidden.vbs` ni bosing. Hech qanday oyna ochilmaydi, agent to'liq fonda ishlayveradi.
- **To'xtatish:** `stop_daemon.bat` ni bosing.

---

## 💬 Namunaviy Buyruqlar (O'zbek tilida)

1. **Fayllar va disklar:**
   - *"D diskdagi barcha rasmlarni topib ber"*
   - *"D diskda yangi eslatma.txt faylini yarat va ichiga Dars soat 18:00 da deb yoz"*
   - *"D diskdagi papkalar ro'yxatini ko'rsat"*
   - *"D:/agent papkasini arxivlab zip qilib ber"*
   - *"D:/agent/README.md faylini o'qib ber"*

2. **Kompyuter diagnostikasi:**
   - *"kompyuterimning tizim holatini tekshir"*
   - *"qancha bo'sh joy bor?"*
   - *"eng ko'p xotira yeyotgan dasturlarni ko'rsat"*
   - *"tarmoq holatini tekshir"*

3. **Dasturlar va konsol:**
   - *"kalkulyatorni och"*
   - *"bloknotni och"*
   - *"powershell: Get-Service | Where-Object {$_.Status -eq 'Running'}"*

4. **Dasturlash va hisob-kitob:**
   - *"1 dan 50 gacha bo'lgan sonlar kvadratini chiqaruvchi Python kod yoz va ishga tushir"*
   - *"(1450000 * 0.12) hisoblab ber"*

---

## 🦙 Internetsiz Mahalliy AI (Ollama) Ulash

Agar siz internetsiz ham xuddi ChatGPT kabi erkin suhbatlashuvchi sun'iy intellekt modelidan foydalanmoqchi bo'lsangiz:
1. `D:\agent\setup_ollama.bat` faylini bosing.
2. U sizga Ollama o'rnatish va bepul `qwen2.5:3b` modelini yuklab olishga yordam beradi.
3. Model yuklangach, bizning agent unga **avtomatik ulanadi** va internetsiz ham eng aqlli rejimda ishlaydi!

---

## 🌐 Internet Borligida Google Gemini API dan Foydalanish

Agar internet ulangan bo'lsa va yuqori darajadagi Gemini AI imkoniyatlaridan foydalanmoqchi bo'lsangiz:
1. https://aistudio.google.com/app/apikey manziliga kiring va bepul API kalit oling.
2. `D:\agent\.env` faylini oching va quyidagi qatorga kalitingizni qo'ying:
   ```env
   GEMINI_API_KEY=AIzaSy...
   ```
3. Agent internet mavjudligini avtomatik sezadi va eng yuqori darajada ishlaydi!

---

*Loyiha to'liq `D:\agent` manzilida sozlandi va foydalanishga tayyor.*
