import os
import logging
from typing import List, Dict, Any, Optional
from google import genai
from google.genai import types

try:
    from .config import GEMINI_API_KEY, MODEL_NAME, SECTIONS, SAVDO_INSTRUCTION
    from .database import get_page_messages, add_message
except ImportError:
    from config import GEMINI_API_KEY, MODEL_NAME, SECTIONS, SAVDO_INSTRUCTION
    from database import get_page_messages, add_message

logger = logging.getLogger("ai_service")

# Barqaror modellar ketma-ketligi
FALLBACK_MODELS = [
    MODEL_NAME or "gemini-3.8-flash",
    "gemini-3.6-flash",
    "gemini-3.1-flash-lite",
    "gemini-2.5-flash"
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
        image_bytes: Optional[bytes] = None,
        mime_type: Optional[str] = None
    ) -> str:
        """Berilgan bo'lim va sahifa uchun ixtisoslashgan AI javobini hosil qiladi."""
        if not self.is_available():
            return (
                "⚠️ Sun'iy intellekt kaliti (GEMINI_API_KEY) o'rnatilmagan yoki noto'g'ri. "
                "Iltimos, sozlamalarni tekshiring."
            )

        sec_config = SECTIONS.get(section_key, SECTIONS["savollar"])
        system_prompt = sec_config["prompt"]

        # #savdo, #hisobot-savdo, #jadval teglari tekshiruvi
        msg_lower = user_message.lower()
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

        # Yangi foydalanuvchi xabari (va rasm agar bo'lsa)
        user_parts = []
        if image_bytes and mime_type:
            user_parts.append(
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            )
        user_parts.append(types.Part.from_text(text=user_message))

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
                        max_output_tokens=3000
                    )
                )

                if response and response.text:
                    ai_text = response.text.strip()
                    # Suhbat tarixiga yozish
                    add_message(page_id, "user", user_message)
                    add_message(page_id, "assistant", ai_text)
                    return ai_text

            except Exception as e:
                err_str = str(e)
                logger.warning(f"Model '{model}' xatolik berdi: {err_str[:120]}")
                last_error = err_str
                continue

        return f"❌ Javob olishda xatolik yuz berdi: {last_error or 'Nomaʼlum xatolik'}"

ai_service = AIService()
