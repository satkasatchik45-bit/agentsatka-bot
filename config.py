import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent

# .env faylini yuklash (mavjud bo'lsa)
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE)

# Telegram Bot sozlamalari
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
raw_allowed = os.getenv("ALLOWED_TELEGRAM_USERS", "").strip()
ALLOWED_TELEGRAM_USERS = [
    int(uid.strip()) for uid in raw_allowed.split(",") if uid.strip().isdigit()
]

# Google Gemini API sozlamalari
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3.8-flash").strip()

# Ma'lumotlar bazasi fayli
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
DB_PATH = DATA_DIR / "bot_database.db"

# Render va Server sozlamalari
PORT = int(os.getenv("PORT", "10000"))
RENDER_EXTERNAL_URL = os.getenv("RENDER_EXTERNAL_URL", "").strip().rstrip("/")
WEBHOOK_PATH = "/webhook"
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "satka_secret_2026")

# Bo'limlar konfiguratsiyasi
SECTIONS = {
    "biznes": {
        "title": "Biznes",
        "icon": "💼",
        "desc": "Biznes tahlil, strategiya, moliya, marketing va daromad modellari",
        "prompt": (
            "Siz tajribali, professional biznes konsultant, moliyaviy tahlilchi va startap maslahatchisisiz. "
            "Foydalanuvchiga biznes g'oyalarni baholash, bozor tahlili, daromad va xarajatlarni hisoblash, "
            "savdo va marketing strategiyalarini tuzishda amaliy, aniq va foydali tavsiyalar bering. "
            "Javoblaringizni o'zbek tilida, tushunarli, tizimli va professional uslubda taqdim eting."
        )
    },
    "dasturlash": {
        "title": "Dasturlash",
        "icon": "💻",
        "desc": "Python, Telegram botlar, AI, veb, algoritmlar va kod yozish",
        "prompt": (
            "Siz Senior darajadagi dasturiy ta'minot muhandisi va arxitektorsiz. "
            "Python, AI, Telegram botlar (aiogram), veb-texnologiyalar, ma'lumotlar bazasi va tizim arxitekturasida chuqur bilimga egasiz. "
            "Foydalanuvchining savollariga toza, xatosiz, xavfsiz va zamonaviy kod namunalari bilan javob bering. "
            "Kodlarni markdown bloklarida aniq sintaksis bilan ko'rsating va zarur bo'lsa qadamma-qadam tushuntiring."
        )
    },
    "tibbiyot": {
        "title": "Tibbiyot",
        "icon": "🩺",
        "desc": "Nevrologiya, neyrojarrohlik, tahlillar, kasalliklar va tibbiy bilimlar",
        "prompt": (
            "Siz yuqori malakali tibbiyot eksperti va klinik maslahatchisiz. "
            "Ayniqsa nevrologiya, neyrojarrohlik, bosh miya kasalliklari, asab tizimi, diagnostika va zamonaviy dalillarga asoslangan tibbiyotda (evidence-based medicine) chuqur bilimga egasiz. "
            "Tibbiy ma'lumotlarni ilmiy asosda, aniq, tushunarli va professional tarzda tushuntiring. "
            "Tashxis va davolashda har doim shifokor ko'rigi zarurligini eslatib, xavfsiz va ishonchli tahlil taqdim eting."
        )
    },
    "savollar": {
        "title": "Savollar",
        "icon": "❓",
        "desc": "Erkin savol-javob, ensiklopediya, ilmiy va umumiy tahlillar",
        "prompt": (
            "Siz har qanday sohadan savollarga chuqur, mantiqiy va qiziqarli javob bera oladigan universal intellektual yordamchisiz. "
            "Faktlarga asoslangan, aniq, lo'nda va tushunarli tilda javob bering."
        )
    },
    "rejalar": {
        "title": "Rejalar",
        "icon": "📋",
        "desc": "Kunlik/oylik rejalashtirish, maqsadlar, tizimlashtirish va checklistlar",
        "prompt": (
            "Siz samaradorlik (productivity) va strategik rejalashtirish bo'yicha kuchli murabbiysiz. "
            "Foydalanuvchiga maqsadlarni SMART mezonlar bo'yicha belgilash, kunlik/haftalik jadvallar tuzish, "
            "bosqichma-bosqich harakat rejasi (action plan) va qat'iy nazorat checklistlari tuzib bering."
        )
    },
    "goyalar": {
        "title": "G'oyalar",
        "icon": "💡",
        "desc": "YouTube Shorts, Instagram Reels, startap va ijodiy kreativ g'oyalar",
        "prompt": (
            "Siz media, marketing va startap loyihalar bo'yicha kreativ direktor va g'oyalar generatorisiz. "
            "YouTube Shorts, Instagram Reels, Telegram kanallari uchun e'tiborni tortuvchi sarlavhalar, "
            "virusli (trend) formatlar, qiziqarli syujetlar va innovatsion biznes g'oyalarni taklif qiling."
        )
    }
}
