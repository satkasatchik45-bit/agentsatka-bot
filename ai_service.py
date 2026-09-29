import os
import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

try:
    from .config import GEMINI_API_KEY, MODEL_NAME, SECTIONS, SAVDO_INSTRUCTION
    from .database import get_page_messages, add_message, get_evolution_stats
except ImportError:
    from config import GEMINI_API_KEY, MODEL_NAME, SECTIONS, SAVDO_INSTRUCTION
    from database import get_page_messages, add_message, get_evolution_stats

logger = logging.getLogger("ai_service")

# Barqaror va tezkor Gemini modellar ketma-ketligi (Multimodal: Matn, Audio, Video, Rasm, PDF)
FALLBACK_MODELS = [
    "gemini-2.5-flash",
    "gemini-flash-lite-latest",
    "gemini-flash-latest",
    "gemini-3.7-flash",
    "gemini-3.5-flash",
    "gemini-3.1-flash-lite"
]

class AIService:
    def __init__(self):
        self.client = None
        if GEMINI_API_KEY:
            try:
                self.client = genai.Client(api_key=GEMINI_API_KEY)
                logger.info("Gemini AI Client muvaffaqiyatli ishga tushirildi.")
            except Exception as e:
                logger.error(f"Gemini AI Clientni ishga tushirishda xatolik: {e}")

    def is_available(self) -> bool:
        return self.client is not None

    def generate_response(
        self,
        user_message: str,
        section_key: str,
        page_id: int,
        media_bytes: Optional[bytes] = None,
        mime_type: Optional[str] = None
    ) -> str:
        """Berilgan bo'lim va sahifa uchun ixtisoslashgan AI javobini hosil qiladi (Matn, Ovoz, Video, Rasm, Fayl)."""
        if not self.is_available():
            return (
                "⚠️ Sun'iy intellekt kaliti (GEMINI_API_KEY) o'rnatilmagan yoki noto'g'ri. "
                "Iltimos, sozlamalarni tekshiring."
            )

        sec_config = SECTIONS.get(section_key, SECTIONS.get("savollar", {}))
        system_prompt = sec_config.get("prompt", "Siz aqlli kiber yordamchisiz.")

        # #savdo, #hisobot-savdo, #jadval teglari tekshiruvi
        msg_lower = user_message.lower() if user_message else ""
        if any(tag in msg_lower for tag in ["#savdo", "#hisobot-savdo", "#jadval", "savdo hisob"]):
            system_prompt = f"{system_prompt}\n\n{SAVDO_INSTRUCTION}"

        # Ushbu sahifadagi avvalgi xabarlarni yuklash (faqat shu sahifa konteksti)
        recent_messages = get_page_messages(page_id, limit=12)

        # Gemini API uchun contents ro'yxatini shakllantirish
        contents = []

        # Avvalgi suhbat tarixini qo'shish
        for m in recent_messages:
            role = "user" if m["role"] == "user" else "model"
            contents.append(
                types.Content(
                    role=role,
                    parts=[types.Part.from_text(text=m["content"])]
                )
            )

        # Yangi foydalanuvchi xabari (va media: audio, video, rasm, hujjat)
        user_parts = []
        if media_bytes and mime_type:
            user_parts.append(
                types.Part.from_bytes(data=media_bytes, mime_type=mime_type)
            )
        
        effective_message = user_message.strip() if user_message else ""
        if not effective_message:
            if mime_type and mime_type.startswith("audio/"):
                effective_message = "Ushbu ovozli xabarni diqqat bilan eshitib, to'liq tahlil qiling va batafsil, aniq yozma javob bering."
            elif mime_type and mime_type.startswith("video/"):
                effective_message = "Ushbu videoni to'liq ko'rib chiqib, undagi nutq va tasvirlarni chuqur tahlil qilib, batafsil yozma xulosa va yechim bering."
            else:
                effective_message = "Ushbu fayl va materialni tahlil qilib bering."

        user_parts.append(types.Part.from_text(text=effective_message))
        contents.append(types.Content(role="user", parts=user_parts))

        # Modellar bo'yicha ketma-ket urinish (fallback tizimi)
        last_error = None
        for model in FALLBACK_MODELS:
            try:
                response = self.client.models.generate_content(
                    model=model,
                    contents=contents,
                    config=types.GenerateContentConfig(
                        system_instruction=system_prompt,
                        temperature=0.7,
                        max_output_tokens=3500
                    )
                )

                if response and response.text:
                    ai_text = response.text.strip()
                    # Suhbat tarixiga yozish
                    stored_user_text = user_message.strip() if user_message else f"[{mime_type or 'Media'}]"
                    add_message(page_id, "user", stored_user_text)
                    add_message(page_id, "assistant", ai_text)
                    return ai_text

            except Exception as e:
                err_str = str(e)
                logger.warning(f"Model '{model}' xatolik berdi: {err_str[:120]}")
                last_error = err_str
                continue

        return f"❌ Javob olishda xatolik yuz berdi: {last_error or 'Nomaʼlum xatolik'}"

    def synthesize_evolution(self, user_id: int) -> str:
        """Agent o'z-o'zini rivojlantirish va takomillashtirish tahlilini tuzadi"""
        if not self.is_available():
            return "AI xizmati hozircha faol emas."
        try:
            stats = get_evolution_stats()
            prompt = (
                f"Siz @agentsatka_bot — avtonom, o'zini-o'zi rivojlantiruvchi kiber sun'iy intellekt agentsiz. "
                f"Sizning joriy darajangiz: {stats.get('level', 1)} ({stats.get('title', 'Kiber Agent')}), "
                f"Jami to'plangan tajriba (XP): {stats.get('total_xp', 0)} XP, "
                f"Bajarilgan vazifalar soni: {stats.get('total_tasks', 0)} ta.\n\n"
                f"O'zingizning ishingizni, nutqni tushunish, audio/video tahlil, biznes, dasturlash va tibbiyot "
                f"bo'limlaridagi mahoratingizni tahlil qiling. O'zbek tilida 3-4 banddan iborat qisqa, salobatli va "
                f"aniq avtonom rivojlanish hisobotini yozib bering."
            )
            for model in FALLBACK_MODELS:
                try:
                    resp = self.client.models.generate_content(
                        model=model,
                        contents=prompt
                    )
                    if resp and resp.text:
                        return resp.text.strip()
                except Exception:
                    continue
            return "Agent o'z-o'zini tahlil qilish jarayonida. Har bir savol va vazifa orqali tizim mukammallashib bormoqda."
        except Exception as e:
            return f"Evolyutsiya tahlilida vaqtinchalik xatolik: {e}"

ai_service = AIService()
