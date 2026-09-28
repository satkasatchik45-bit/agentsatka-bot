# ☁️ Kompyuter o'chirilgan holatda ham Agentni 24/7 ishlatish bo'yicha qo'llanma

Siz bergan talablardan biri:
> *"faqat kompyuterim o'chirilgan holatda ham ishlatishim buyruqlarni bajarishi imkoni bo'lsin, telefonda telegramdan boshqarganda ham ishlasin."*

Kompyuter jismonan o'chirilganda undagi protsessor va dasturlar to'xtaydi. Shuning uchun agentingiz **kompyuteringiz o'chiq bo'lsa ham kecha-yu kunduz (24/7)** ishlab turishi uchun uni **Bulutli xizmatlarga (Cloud)** joylashtirish kerak.

Agentimiz dasturiy jihatdan bulutda ishlashga 100% moslab tayyorlangan:
- Ichida avtomatik **health-check server** bor (Render/Railway kabi bepul xizmatlar o'chirib qo'ymasligi uchun).
- **Dockerfile** va **render.yaml** tayyor.

Quyida uni 5-10 daqiqa ichida mutlaqo bepul bulutga o'rnatish yo'llari keltirilgan.

---

## 🥇 1-USUL: Render.com (Eng oson va 100% Bepul tavsiya)

Render.com — dasturlarni bepul bulutda ishlatish uchun dunyodagi eng mashhur xizmatlardan biri.

### 1-qadam: Kodni GitHub ga yuklash
1. [github.com](https://github.com) ga kiring va yangi repository oching (masalan, `my-telegram-agent`).
2. `D:\agent` papkasidagi fayllarni GitHub ga yuklang (Git orqali yoki GitHub saytidan "Upload files" tugmasi orqali).
*(Muhim: `.env` faylini yuklamang, undagi kalitlarni keyingi qadamda kiritasiz).*

### 2-qadam: Render.com da hisob ochish
1. [render.com](https://render.com) saytiga kiring va GitHub orqali ro'yxatdan o'ting (Sign In with GitHub).

### 3-qadam: Yangi servis yaratish
1. Boshqaruv panelida **"New +"** tugmasini bosing va **"Web Service"** ni tanlang.
2. O'zingiz ochgan `my-telegram-agent` GitHub omborini tanlang va **"Connect"** tugmasini bosing.
3. Sozlamalarni shunday to'ldiring:
   - **Name:** `antigravity-agent`
   - **Region:** Frankfurt yoki Singapur (istalgan yaqin server)
   - **Branch:** `main` (yoki `master`)
   - **Runtime:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python main.py`
   - **Instance Type:** `Free` ($0/oy)

### 4-qadam: Sozlamalar va API kalitlarni kiritish
Quyiroqqa tushib **"Environment Variables"** (Muhit o'zgaruvchilari) bo'limini toping va kalitlaringizni qo'shing:
- `TELEGRAM_BOT_TOKEN` = Sizning bot tokeningiz
- `GEMINI_API_KEY` = Sizning Gemini API kalitingiz
- `ALLOWED_TELEGRAM_USERS` = Sizning Telegram ID raqamingiz

### 5-qadam: Ishga tushirish (Deploy)
**"Create Web Service"** tugmasini bosing!
Render 1-2 daqiqada kutubxonalarni o'rnatadi va botni ishga tushiradi.

🎉 **Bo'ldi! Endi kompyuteringizni butunlay o'chirib qo'yishingiz mumkin.**
Botingiz Render serverlarida 24 soat uzluksiz ishlab turadi va telefoningizdan Telegram orqali yozganingizda darhol javob qaytaradi!

---

## 🥈 2-USUL: Railway.app (Juda tez va qulay)

1. [railway.app](https://railway.app) saytiga kiring (GitHub bilan kiring).
2. **"New Project"** -> **"Deploy from GitHub repo"** ni bosing va repozitoriyangizni tanlang.
3. Loyiha sozlamalarida (Variables bo'limida) `.env` dagi kalitlarni kiriting:
   - `TELEGRAM_BOT_TOKEN`
   - `GEMINI_API_KEY`
   - `ALLOWED_TELEGRAM_USERS`
4. Railway avtomatik ravishda `Procfile` yoki `Dockerfile` ni ko'radi va bir necha soniyada botni 24/7 ishga tushiradi.

---

## 🥉 3-USUL: Shaxsiy VPS Server (Ubuntu / Debian)

Agar sizda arzon VPS (masalan, Hetzner, DigitalOcean yoki Uztelecom serveri) bo'lsa:

1. Serverga kiring:
   ```bash
   ssh root@server_ip
   ```
2. Loyihani yuklab oling yoki `D:\agent` papkasini serverga ko'chiring:
   ```bash
   git clone <sizning_repo> agent
   cd agent
   ```
3. Docker orqali bir buyruq bilan 24/7 fonda ishga tushirish:
   ```bash
   docker compose up -d --build
   ```
4. Yoki to'g'ridan-to'g'ri Python va `systemd` orqali fonda yoqib qo'yish:
   ```bash
   pip install -r requirements.txt
   nohup python3 main.py > agent.log 2>&1 &
   ```

---

## 📱 4-USUL: Eski Android telefon orqali (Kompyutersiz va Server sotib olmasdan)

Agar sizda uyda ortiqcha eski Android smartfon bo'lsa:
1. Google Play yoki F-Droid dan **Termux** dasturini o'rnating.
2. Quyidagi buyruqlarni bering:
   ```bash
   pkg update
   pkg install python git
   ```
3. Loyihani yuklab olib, `.env` faylini to'ldiring va:
   ```bash
   python main.py
   ```
4. Telefonni zaryadkaga ulab, Wi-Fi ga ulab qo'ysangiz, u uy ichida mini-server sifatida 24/7 ishlab turadi!

---

## 🔍 Xulosa

- **Hozir test qilish va o'rganish uchun:** Kompyuteringizda `D:\agent\run_bot.bat` ni yoqib ko'ring.
- **Doimiy kompyutersiz ishlatish uchun:** Kodni GitHub ga joylab, **Render.com** (1-usul) ga ulang. Bu eng ishonchli va mutlaqo bepul yo'ldir!
