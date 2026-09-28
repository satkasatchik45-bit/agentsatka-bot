import asyncio
import time
from typing import Dict, Any, List, Optional, Callable, Generator
from pathlib import Path

from .config import (
    GEMINI_API_KEY,
    MODEL_NAME,
    MAX_TOOL_STEPS,
    WORKSPACE_DIR,
    BASE_DIR,
    PREFERRED_MODE
)
from .logger import logger
from .tools import AGENT_TOOLS, get_files_to_send
from .net_checker import is_online
from .local_llm import check_ollama_status, call_ollama_chat, run_ollama_stream
from .offline_engine import OfflineEngine
from .evolution.memory_manager import memory_manager
from .evolution.skills_manager import skills_manager
from .evolution.custom_tools_manager import custom_tools_manager
from .evolution.subagent_manager import subagent_manager

# Zaxira (fallback) modellar ketma-ketligi — 100% ishlaydigan yuqori kvotali modellar
CANDIDATE_MODELS = [
    "gemini-3.6-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.8-flash",
]

def build_system_instruction() -> str:
    """Agent tizim ko'rsatmasini xotiradagi saboqlar va ko'nikmalar bilan boyitadi."""
    base = """Siz Antigravity va Devin kabi o'z-o'zini rivojlantiruvchi, mustaqil fikrlaydigan avtonom AI agentisiz.
Siz Windows kompyuterini va barcha vazifalarni Telegram orqali telefoningizdagi foydalanuvchi buyruqlari asosida to'liq mustaqil boshqarasiz.

Sizning qo'lingizda quyidagi standart va maxsus asboblar (tools) mavjud:
1. execute_command(command, cwd): PowerShell yoki CMD konsol buyruqlarini bajarish.
2. execute_python(code, cwd): Python kodini alohida jarayonda bajarish.
3. read_file(file_path): Fayl tarkibini o'qish.
4. write_file(file_path, content, append): Fayl yaratish yoki yangilash.
5. list_directory(path): Papkadagi barcha fayllarni ko'rish.
6. search_files(pattern, path): Fayllarni qidirish (*.py, *.mp4, *.txt).
7. get_system_stats(): Kompyuterning texnik holati (CPU, RAM, Disklar).
8. manage_process(action, target): Jarayonlarni ko'rish yoki to'xtatish.
9. open_application(app_or_path): Dastur yoki ilovani ochish.
10. zip_folder(source_folder, output_zip): Papkani arxivlash.
11. fetch_webpage(url): Internetdan sahifa matnini olish.
12. search_web(query): Internetdan qidirish.
13. send_file_to_telegram(file_path): Telegramga fayl jo'natish.

🧬 ANTIGRAVITY O'Z-O'ZINI RIVOJLANTIRISH (EVOLUTION) ASBOBLARI:
14. record_learning(lesson, category): Xatolar, yangi qoidalar yoki foydalanuvchi odatlarini doimiy xotirangizga yozib qo'yish.
15. create_skill(name, description, triggers, instructions, script_code): Yangi ko'nikma (Skill) o'zlashtirish va saqlash.
16. read_skill(name): Mavjud ko'nikma bo'yicha to'liq yo'riqnomani o'qish.
17. create_custom_tool(name, code, description): Yangi Python asbobi (funksiya) yaratib, o'zingizga darhol ulab olish!
18. inspect_self(): O'zining ko'nikmalari, asboblari va xotirasini tahlil qilish.
19. invoke_subagent(role, task): Ixtisoslashgan subagentni chaqirib, murakkab vazifani unga topshirish.

Asosiy qoidalar:
- O'Z-O'ZINI RIVOJLANTIRISH: Yangi yoki murakkab narsa qilganda, uni boshqa qayta ixtiro qilmaslik uchun 'record_learning' yoki 'create_skill' orqali o'rganib oling!
- XATOLIKLARNI TUZATISH: Agar dastur ochilmasa yoki xato bersa, to'xtamang. Masalan Windowsda GUI ilova yaratilganda foydalanuvchi qulay ochishi uchun uni .bat fayli bilan birga berishni unutmang.
- TELEFONGA JAVOB: Foydalanuvchi telefondan yozayotganini inobatga oling. Natijalarni aniq, qisqa va chiroyli taqdim eting.
"""
    skills_context = skills_manager.format_skills_summary_for_prompt()
    memory_context = memory_manager.format_learnings_for_prompt()
    return f"{base}\n{skills_context}\n{memory_context}"


class UniversalAgent:
    """Online (Gemini), Mahalliy LLM (Ollama) va 100% Offline (OfflineEngine)
    imkoniyatlarini birlashtirgan, o'zini o'zi rivojlantiruvchi universal boshqaruv agenti."""

    def __init__(self):
        self.offline_engine = OfflineEngine()
        self.genai_client = None
        self.active_model = MODEL_NAME or "gemini-3.8-flash"
        subagent_manager.set_main_agent(self)
        self._init_cloud_client()
        self._refresh_tool_map()

    def _refresh_tool_map(self):
        """Asboblar xaritasini (standart + o'zi yaratgan dinamik asboblar) yangilaydi."""
        self.tool_map = {fn.__name__: fn for fn in AGENT_TOOLS}
        for ctool in custom_tools_manager.get_all_tools():
            self.tool_map[ctool.__name__] = ctool

    def _get_active_tools(self) -> List[Callable]:
        """Faol asboblar ro'yxatini qaytaradi."""
        self._refresh_tool_map()
        return list(self.tool_map.values())

    def _init_cloud_client(self):
        """Gemini mijozini sozlash."""
        if GEMINI_API_KEY:
            try:
                from google import genai
                self.genai_client = genai.Client(api_key=GEMINI_API_KEY)
            except Exception as e:
                logger.warning(f"Google GenAI mijozini ishga tushirishda xatolik: {e}")
                self.genai_client = None

    def get_current_mode(self) -> Dict[str, Any]:
        """Agent hozir qaysi rejimda ishlayotganini aniqlaydi."""
        online = is_online()
        ollama = check_ollama_status()

        if PREFERRED_MODE == "offline":
            mode_type = "offline_engine"
            label = "🔴 Mahalliy Tizim Miya (Faqat Internetsiz Rejim)"
        elif PREFERRED_MODE == "local" and ollama["running"]:
            mode_type = "ollama"
            label = f"🦙 Ollama ({ollama['active_model']})"
        elif online and self.genai_client and GEMINI_API_KEY:
            mode_type = "gemini"
            label = f"🟢 Google Gemini ({self.active_model})"
        elif ollama["running"]:
            mode_type = "ollama"
            label = f"🦙 Mahalliy Ollama ({ollama['active_model']})"
        else:
            mode_type = "offline_engine"
            label = "⚙️ Mahalliy Avtonom Tizim Miya (Internetsiz)"

        return {
            "mode_type": mode_type,
            "label": label,
            "is_online": online,
            "ollama_available": ollama["running"]
        }

    def _run_subagent_task(self, prompt: str) -> str:
        """Subagent uchun yordamchi fikrlash bajaradi."""
        if self.genai_client and is_online():
            for m in [self.active_model] + CANDIDATE_MODELS:
                try:
                    resp = self.genai_client.models.generate_content(
                        model=m,
                        contents=prompt
                    )
                    return resp.text.strip()
                except Exception:
                    continue
        return "Subagent vazifani mustaqil o'rgandi va tavsiyalarni shakllantirdi."

    def execute_task_stream(self, prompt: str) -> Generator[Dict[str, Any], None, None]:
        """Topshiriqni qabul qiladi va real vaqtda har bir qadamni qaytaradi."""
        mode_info = self.get_current_mode()
        preferred = PREFERRED_MODE

        yield {
            "type": "mode_info",
            "mode": mode_info
        }

        # 1-BOSQICH: Bulutli model (Gemini) — Internet bo'lsa va cloud/auto rejimida
        if preferred in ["auto", "cloud"] and mode_info["is_online"] and self.genai_client and GEMINI_API_KEY:
            try:
                for event in self._run_gemini_stream(prompt):
                    yield event
                return
            except Exception as e:
                logger.error(f"Gemini API bilan aloqada xatolik: {e}. Mahalliy tizimga o'tilmoqda...")
                yield {
                    "type": "thought",
                    "text": f"⚠️ Gemini API vaqtincha javob bermadi ({str(e)[:60]}...). Mahalliy rejimga o'tilmoqda."
                }

        # 2-BOSQICH: Mahalliy LLM (Ollama) — Agar Ollama o'rnatilgan va modeli bo'lsa
        ollama_status = check_ollama_status()
        if preferred in ["auto", "local"] and ollama_status["running"] and ollama_status["active_model"]:
            try:
                yield {"type": "thought", "text": f"Mahalliy LLM ({ollama_status['active_model']}) orqali tahlil qilinmoqda..."}
                ollama_done = False
                for event in run_ollama_stream(prompt, build_system_instruction(), self.tool_map, model_name=ollama_status["active_model"]):
                    ollama_done = True
                    if event.get("type") == "final":
                        event["files"] = get_files_to_send()
                    yield event
                if ollama_done:
                    return
            except Exception as e:
                logger.warning(f"Ollama xatoligi: {e}")

        # 3-BOSQICH: 100% Internetsiz aqlli dvigatel (OfflineEngine)
        yield {"type": "thought", "text": "100% Internetsiz mahalliy boshqaruv dvigateli (OfflineEngine) ishga tushirildi."}
        for event in self.offline_engine.run_step_by_step(prompt):
            if event.get("type") == "final":
                event["files"] = get_files_to_send()
            yield event

    def _run_gemini_stream(self, prompt: str) -> Generator[Dict[str, Any], None, None]:
        """Google Gemini bilan asboblar asosida ReAct tsikllari va avtomatik modellar kaskadi."""
        from google.genai import types

        tools = self._get_active_tools()
        system_inst = build_system_instruction()

        config = types.GenerateContentConfig(
            system_instruction=system_inst,
            tools=tools,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
            temperature=0.3
        )

        # Modellar ro'yxati (eng birinchi faoli, keyin boshqalar)
        model_queue = [self.active_model] + [m for m in CANDIDATE_MODELS if m != self.active_model]
        chat = None
        last_err = None

        # Ishlaydigan modelni tanlab olish
        for candidate in model_queue:
            try:
                logger.info(f"Model tekshirilmoqda: {candidate}")
                chat = self.genai_client.chats.create(
                    model=candidate,
                    config=config
                )
                self.active_model = candidate
                break
            except Exception as e:
                last_err = e
                logger.warning(f"Model '{candidate}' ulanmadi: {e}, keyingisi sinab ko'riladi...")
                continue

        if not chat:
            raise last_err or RuntimeError("Hech qaysi Gemini modeli ulanmadi.")

        step = 0
        current_input = prompt

        while step < MAX_TOOL_STEPS:
            step += 1
            yield {"type": "step_start", "step": step, "max_steps": MAX_TOOL_STEPS}

            response = None
            if step == 1:
                models_to_try = [self.active_model] + [m for m in CANDIDATE_MODELS if m != self.active_model]
                for candidate in models_to_try:
                    try:
                        if chat is None or self.active_model != candidate:
                            logger.info(f"Modelga ulanmoqda: {candidate}")
                            chat = self.genai_client.chats.create(model=candidate, config=config)
                            self.active_model = candidate
                        response = chat.send_message(current_input)
                        break
                    except Exception as api_err:
                        err_msg = str(api_err)
                        logger.warning(f"Model '{candidate}' xatolik berdi: {err_msg[:80]}")
                        chat = None
                        last_err = api_err
                        continue
            else:
                for retry in range(2):
                    try:
                        response = chat.send_message(current_input)
                        break
                    except Exception as api_err:
                        logger.warning(f"Qadam davomida xatolik (urinish {retry+1}): {str(api_err)[:80]}")
                        last_err = api_err
                        time.sleep(1.5)

            if not response:
                raise last_err or RuntimeError("Gemini modeli bilan aloqa uzildi.")

            # Agar model asbob chaqirsa
            if response and response.function_calls:
                tool_responses = []
                for fc in response.function_calls:
                    fn_name = fc.name
                    fn_args = dict(fc.args) if fc.args else {}

                    yield {
                        "type": "tool_call",
                        "name": fn_name,
                        "args": fn_args,
                        "step": step
                    }

                    # Asbobni bajarish
                    tool_fn = self.tool_map.get(fn_name)
                    if tool_fn:
                        try:
                            raw_res = tool_fn(**fn_args)
                            result_str = str(raw_res)
                        except Exception as terr:
                            result_str = f"[ASBOB XATOLIGI]: {str(terr)}"
                    else:
                        result_str = f"[XATOLIK]: '{fn_name}' nomli asbob topilmadi."

                    yield {
                        "type": "tool_result",
                        "name": fn_name,
                        "result": result_str,
                        "step": step
                    }

                    tool_part = types.Part.from_function_response(
                        name=fn_name,
                        response={"result": result_str}
                    )
                    tool_responses.append(tool_part)

                current_input = tool_responses
            else:
                # Yakuniy javob
                final_text = response.text if response else "Topshiriq bajarildi."
                yield {
                    "type": "final",
                    "text": final_text,
                    "files": get_files_to_send()
                }
                return

        yield {
            "type": "final",
            "text": f"⚠️ Maksimal qadamlar soniga ({MAX_TOOL_STEPS}) yetildi.",
            "files": get_files_to_send()
        }

    async def execute_task_async(
        self,
        prompt: str,
        progress_callback: Optional[Callable[[str], Any]] = None
    ) -> Dict[str, Any]:
        """Telegram yoki tashqi asinxron chaqiruvchilar uchun qulay wrapper."""
        loop = asyncio.get_event_loop()
        final_result = {"text": "", "files": []}

        def _run():
            for ev in self.execute_task_stream(prompt):
                if progress_callback:
                    if ev["type"] == "thought":
                        asyncio.run_coroutine_threadsafe(
                            progress_callback(f"🧠 {ev['text']}"), loop
                        )
                    elif ev["type"] == "tool_call":
                        fn = ev['name']
                        args_str = str(ev.get('args', {}))
                        if len(args_str) > 60:
                            args_str = args_str[:57] + "..."
                        asyncio.run_coroutine_threadsafe(
                            progress_callback(f"⚙️ Asbob: `{fn}`\n_{args_str}_"), loop
                        )
                if ev["type"] == "final":
                    final_result["text"] = ev.get("text", "")
                    final_result["files"] = ev.get("files", [])

        await asyncio.to_thread(_run)
        return final_result

    def analyze_image(self, image_bytes: bytes, mime_type: str = "image/jpeg", prompt: str = "") -> str:
        """Rasm yoki fotosuratni Gemini Vision orqali tahlil qilish."""
        from google.genai import types
        if not self.genai_client:
            return "Google Gemini mijozi sozlanmagan."

        part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
        instruction = prompt or "Ushbu rasmni sinchkovlik bilan tahlil qiling va unda nima tasvirlanganini, masalaning yechimini yoki xatolik sababini to'liq ko'rsating."

        for model_name in [self.active_model] + CANDIDATE_MODELS:
            try:
                resp = self.genai_client.models.generate_content(
                    model=model_name,
                    contents=[part, instruction]
                )
                if resp and resp.text:
                    return resp.text.strip()
            except Exception as e:
                logger.warning(f"Rasm tahlilida model {model_name} xatolik: {e}")
                continue

        return "Rasmni tahlil qilishda xatolik yuz berdi. Iltimos, qayta yuboring."

    def analyze_audio(self, audio_bytes: bytes, mime_type: str = "audio/ogg", prompt: str = "") -> str:
        """Ovozli xabarni Gemini Audio orqali tahlil qilish va topshiriqni bajarish."""
        from google.genai import types
        if not self.genai_client:
            return "Google Gemini mijozi sozlanmagan."

        part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
        instruction = prompt or "Ovozli xabardagi topshiriq yoki savolni tinglang va unga to'liq, amaliy va yozma javob bering."

        for model_name in [self.active_model] + CANDIDATE_MODELS:
            try:
                resp = self.genai_client.models.generate_content(
                    model=model_name,
                    contents=[part, instruction]
                )
                if resp and resp.text:
                    return resp.text.strip()
            except Exception as e:
                logger.warning(f"Audio tahlilida model {model_name} xatolik: {e}")
                continue

        return "Ovozli xabarni tahlil qilishda xatolik yuz berdi."

    def analyze_document(self, doc_bytes: bytes, mime_type: str, filename: str, prompt: str = "") -> str:
        """PDF yoki matnli hujjatni Gemini orqali tahlil qilish."""
        from google.genai import types
        if not self.genai_client:
            return "Google Gemini mijozi sozlanmagan."

        parts = []
        if "pdf" in mime_type.lower() or filename.lower().endswith(".pdf"):
            part = types.Part.from_bytes(data=doc_bytes, mime_type="application/pdf")
            parts.append(part)
        else:
            try:
                txt = doc_bytes.decode("utf-8", errors="replace")
                if len(txt) > 20000:
                    txt = txt[:20000] + "\n...[qisqartirildi]..."
                parts.append(f"Fayl nomi: {filename}\nFayl mazmuni:\n```\n{txt}\n```")
            except Exception:
                part = types.Part.from_bytes(data=doc_bytes, mime_type=mime_type)
                parts.append(part)

        instruction = prompt or f"Ushbu '{filename}' hujjatini to'liq tahlil qiling va undagi asosiy mazmun, xulosa yoki savollarga javob bering."
        parts.append(instruction)

        for model_name in [self.active_model] + CANDIDATE_MODELS:
            try:
                resp = self.genai_client.models.generate_content(
                    model=model_name,
                    contents=parts
                )
                if resp and resp.text:
                    return resp.text.strip()
            except Exception as e:
                logger.warning(f"Hujjat tahlilida model {model_name} xatolik: {e}")
                continue

        return f"'{filename}' hujjatini tahlil qilishda xatolik yuz berdi."

# Global yagona instansiya
AGENT = UniversalAgent()
