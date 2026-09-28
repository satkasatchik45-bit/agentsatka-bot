import os
from pathlib import Path
from dotenv import load_dotenv

# Loyiha ildiz papkasi (D:\agent)
BASE_DIR = Path(__file__).resolve().parent.parent

# .env faylni yuklash
ENV_FILE = BASE_DIR / ".env"
load_dotenv(ENV_FILE)

# Asosiy jildlar
raw_ws = os.getenv("WORKSPACE_DIR", "workspace")
p_ws = Path(raw_ws)
WORKSPACE_DIR = (BASE_DIR / p_ws).resolve() if not p_ws.is_absolute() else p_ws.resolve()
LOGS_DIR = Path(os.getenv("LOGS_DIR", str(BASE_DIR / "logs"))).resolve()
TASKS_DIR = Path(os.getenv("TASKS_DIR", str(BASE_DIR / "tasks"))).resolve()

TASKS_INBOX = TASKS_DIR / "inbox"
TASKS_COMPLETED = TASKS_DIR / "completed"
TASKS_RESULTS = TASKS_DIR / "results"

for d in [WORKSPACE_DIR, LOGS_DIR, TASKS_DIR, TASKS_INBOX, TASKS_COMPLETED, TASKS_RESULTS]:
    d.mkdir(parents=True, exist_ok=True)

# Google Gemini API sozlamalari
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
MODEL_NAME = os.getenv("MODEL_NAME", "gemini-3.8-flash").strip()

# Mahalliy LLM (Ollama, LM Studio) sozlamalari
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434").strip()
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.2:3b").strip()

# Ish tartibi: 'auto' (avtomatik: internet bo'lsa Gemini, bo'lmasa Mahalliy),
# 'cloud' (faqat bulut), 'local' (faqat ollama), 'offline' (faqat internetsiz mahalliy tizim)
PREFERRED_MODE = os.getenv("PREFERRED_MODE", "auto").strip().lower()

# Telegram sozlamalari (mavjud imkoniyat)
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
raw_allowed = os.getenv("ALLOWED_TELEGRAM_USERS", "").strip()
ALLOWED_TELEGRAM_USERS = [int(uid.strip()) for uid in raw_allowed.split(",") if uid.strip().isdigit()]

# Xavfsizlik va cheklovlar
MAX_TOOL_STEPS = int(os.getenv("MAX_TOOL_STEPS", "20"))
COMMAND_TIMEOUT = int(os.getenv("COMMAND_TIMEOUT", "90"))  # sekund
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").strip().upper()
