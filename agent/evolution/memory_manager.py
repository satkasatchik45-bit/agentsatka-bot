import json
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..logger import logger

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MEMORY_FILE = BASE_DIR / "memory" / "learned_knowledge.json"
HISTORY_FILE = BASE_DIR / "memory" / "task_history.json"

DEFAULT_LEARNINGS = [
    {
        "id": "learn_001",
        "timestamp": "2026-09-29 00:50:00",
        "category": "windows_apps",
        "lesson": "Windows muhitida GUI dasturlar (masalan, Kalkulyator yoki boshqa ilovalar) yaratilganda, foydalanuvchiga faqat .py fayl bermaslik kerak. Uni ishga tushiruvchi .bat skript ham yaratish yoki 'pythonw.exe' orqali orqa fonda xatosiz ochilishini ta'minlash lozim."
    },
    {
        "id": "learn_002",
        "timestamp": "2026-09-29 00:55:00",
        "category": "mobile_capabilities",
        "lesson": "Foydalanuvchi telefondan Telegram orqali murojaat qilganda, telefonning o'z tizim fayllariga bot to'g'ridan-to'g'ri tegina olmaydi, lekin telefonni keshdan tozalash bo'yicha aniq qadam-baqadam ko'rsatmalar berishi, Telegram keshini tozalash yo'llarini tushuntirishi yoki kompyuterga ulanganda ADB orqali tozalashi mumkin."
    },
    {
        "id": "learn_003",
        "timestamp": "2026-09-29 01:00:00",
        "category": "self_evolution",
        "lesson": "Xuddi Antigravity kabi, yangi murakkab mavzu yoki texnologiya uchraganda o'zim mustaqil yangi Skill yoki yangi Asbob (Tool) yaratib, uni xotiramga yozib qo'yishim shart."
    }
]

class MemoryManager:
    """Agentning doimiy xotirasi va o'zini o'zi o'rgatish (Self-Learning) tizimi."""

    def __init__(self):
        self.memory_path = MEMORY_FILE
        self.history_path = HISTORY_FILE
        self._ensure_storage()

    def _ensure_storage(self):
        self.memory_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.memory_path.exists():
            self._save_learnings(DEFAULT_LEARNINGS)
        if not self.history_path.exists():
            self.history_path.write_text("[]", encoding="utf-8")

    def _load_learnings(self) -> List[Dict[str, Any]]:
        try:
            txt = self.memory_path.read_text(encoding="utf-8")
            return json.loads(txt) if txt.strip() else []
        except Exception as e:
            logger.error(f"Xotirani o'qishda xatolik: {e}")
            return []

    def _save_learnings(self, data: List[Dict[str, Any]]):
        try:
            self.memory_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.error(f"Xotirani saqlashda xatolik: {e}")

    def record_learning(self, lesson: str, category: str = "tajriba") -> str:
        """Yangi xulosa, qoida yoki saboqni xotiraga yozadi."""
        learnings = self._load_learnings()
        new_id = f"learn_{int(time.time())}"
        timestr = time.strftime("%Y-%m-%d %H:%M:%S")

        entry = {
            "id": new_id,
            "timestamp": timestr,
            "category": category,
            "lesson": lesson.strip()
        }
        learnings.append(entry)
        self._save_learnings(learnings)
        logger.info(f"🧠 Yangi saboq o'rganildi [{category}]: {lesson[:60]}...")
        return f"✅ Yangi saboq xotiraga saqlandi (ID: {new_id}):\n_{lesson}_"

    def get_all_learnings(self) -> List[Dict[str, Any]]:
        """Barcha o'rganilgan saboqlar ro'yxatini qaytaradi."""
        return self._load_learnings()

    def format_learnings_for_prompt(self) -> str:
        """Agent tizim ko'rsatmasiga (system instruction) kiritish uchun saboqlarni matn formatida qaytaradi."""
        learnings = self._load_learnings()
        if not learnings:
            return ""

        lines = ["\n--- AGENTNING O'RGANGAN SABOQLARI VA XOTIRASI (Muvaffaqiyatsizliklardan olingan darslar) ---"]
        for idx, item in enumerate(learnings, 1):
            lines.append(f"{idx}. [{item.get('category', 'umumiy')}]: {item.get('lesson')}")
        lines.append("Har doim ushbu o'rganilgan darslarga amal qiling va oldingi xatolarni takrorlamang!\n")
        return "\n".join(lines)

    def log_task_execution(self, prompt: str, success: bool, steps_taken: int, notes: str = ""):
        """Bajarilgan topshiriq tarixini saqlaydi."""
        try:
            txt = self.history_path.read_text(encoding="utf-8")
            history = json.loads(txt) if txt.strip() else []
            history.append({
                "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                "prompt": prompt[:150],
                "success": success,
                "steps": steps_taken,
                "notes": notes
            })
            if len(history) > 100:
                history = history[-100:]
            self.history_path.write_text(json.dumps(history, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Vazifani qayd qilishda xatolik: {e}")

memory_manager = MemoryManager()
