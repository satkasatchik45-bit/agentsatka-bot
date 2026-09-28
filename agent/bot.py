import asyncio
import os
import sys
import platform
import time
from pathlib import Path
from typing import Optional

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, FSInputFile
from aiogram.enums import ParseMode

from .config import TELEGRAM_BOT_TOKEN, ALLOWED_TELEGRAM_USERS, WORKSPACE_DIR, MODEL_NAME
from .logger import logger
from .core import AGENT
from .tools import list_directory

bot: Optional[Bot] = None
dp = Dispatcher()

def save_user_to_env(user_id: int):
    try:
        import re
        env_path = Path(__file__).resolve().parent.parent / ".env"
        if env_path.exists():
            txt = env_path.read_text(encoding="utf-8")
            if "ALLOWED_TELEGRAM_USERS=" in txt:
                txt = re.sub(r'ALLOWED_TELEGRAM_USERS=.*', f'ALLOWED_TELEGRAM_USERS={user_id}', txt)
            else:
                txt += f"\nALLOWED_TELEGRAM_USERS={user_id}\n"
            env_path.write_text(txt, encoding="utf-8")
    except Exception as e:
        logger.warning(f".env ga saqlashda ogohlantirish: {e}")

def is_authorized(user_id: int) -> bool:
    """Foydalanuvchi botdan foydalanish huquqiga ega ekanligini tekshiradi."""
    global ALLOWED_TELEGRAM_USERS
    if not ALLOWED_TELEGRAM_USERS:
        # Birinchi murojaat qilgan foydalanuvchini avtomatik Administrator (Egasi) deb qabul qilish
        ALLOWED_TELEGRAM_USERS.append(user_id)
        save_user_to_env(user_id)
        logger.info(f"Yangi administrator avtomatik biriktirildi: {user_id}")
        return True
    return user_id in ALLOWED_TELEGRAM_USERS

async def send_chunked_message(message: Message, text: str):
    """Xabar uzun bo'lsa, Telegram chegarasi (4096 belgi) bo'yicha bo'lib yuboradi."""
    max_len = 3900
    if len(text) <= max_len:
        try:
            await message.answer(text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await message.answer(text)
        return

    # Bo'laklarga bo'lib yuborish
    chunks = [text[i:i + max_len] for i in range(0, len(text), max_len)]
    for chunk in chunks:
        try:
            await message.answer(chunk, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await message.answer(chunk)
        await asyncio.sleep(0.3)

@dp.message(CommandStart())
async def handle_start(message: Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.first_name

    if not is_authorized(user_id):
        if not ALLOWED_TELEGRAM_USERS:
            await message.answer(
                f"🛡 *Assalomu alaykum, {username}!* \n\n"
                f"Xavfsizlik yuzasidan ushbu shaxsiy agent faqat egasiga xizmat qiladi.\n\n"
                f"Sizning Telegram ID raqamingiz: `{user_id}`\n\n"
                f"Botni faollashtirish uchun `.env` faylida quyidagi qatorni yozing:\n"
                f"`ALLOWED_TELEGRAM_USERS={user_id}`\n"
                f"va botni qayta ishga tushiring.",
                parse_mode=ParseMode.MARKDOWN
            )
        else:
            await message.answer("⛔ Kechirasiz, siz ushbu shaxsiy botdan foydalana olmaysiz.")
        return

    await message.answer(
        f"👋 *Assalomu alaykum, {username}! Men sizning shaxsiy avtonom agentingizman.* 🤖\n\n"
        f"Men xuddi **Antigravity** kabi orqa fonda mustaqil fikrlayman, o'zimni o'zim rivojlantiraman, xatolardan saboq olaman va yangi asboblar yarata olaman!\n\n"
        f"🔹 *Vazifalarni orqa fonda bajarish* (kod, fayllar, tahlillar)\n"
        f"🔹 *Ko'nikmalar tizimi* — har bir yangi mavzuni skill sifatida o'zlashtirish\n"
        f"🔹 *Yangi asboblar yaratish* — kerak bo'lganda Python orqali yangi qurol yasash\n"
        f"🔹 *Doimiy xotira* — o'rganilgan barcha saboqlar esda qoladi\n\n"
        f"📌 *Asosiy buyruqlar:*\n"
        f"• `/help` - To'liq qo'llanma va namunalar\n"
        f"• `/skills` - Agentning barcha maxsus ko'nikmalari\n"
        f"• `/tools` - Faol asboblar (standart + o'zi yaratgan)\n"
        f"• `/memory` - Agent o'rgangan qoidalar va saboqlar\n"
        f"• `/learn <saboq>` - Agentga yangi qoida o'rgatish\n"
        f"• `/evolve` - Tizimni tahlil qilish va takomillashtirish\n"
        f"• `/status` - Server va AI modellari holati\n\n"
        f"Topshirig'ingizni yozishingiz mumkin!",
        parse_mode=ParseMode.MARKDOWN
    )

@dp.message(Command("help"))
async def handle_help(message: Message):
    if not is_authorized(message.from_user.id):
        return
    await message.answer(
        "📖 *Antigravity AI Agent - Foydalanish Qo'llanmasi:*\n\n"
        "Shunchaki telefoningizdan odatiy tilda vazifa bering:\n\n"
        "1️⃣ *Dastur yaratish va ochish:*\n"
        "_'Menga qulay kalkulyator GUI dasturini yaratib ber, kompyuterda bosib ochiladigan bo'lsin'_\n"
        "*(Agent Windows GUI ko'nikmasi orqali dastur bilan birga .bat faylini ham tayyorlab beradi)*\n\n"
        "2️⃣ *Telefon va maslahatlar:*\n"
        "_'Telefonimda kesh to'lib ketdi, qanday qilib Telegram va tizim keshini xavfsiz tozalayman?'_\n\n"
        "3️⃣ *O'z-o'zini rivojlantirish (Evolution):*\n"
        "• `/learn <qoida>` — Agentga yangi qoida o'rgatish\n"
        "• `/skills` — Ko'nikmalar ro'yxatini ko'rish\n"
        "• `/tools` — Barcha asboblarni ko'rish\n"
        "• `/evolve` — Tizim holatini ko'zdan kechirish\n\n"
        "4️⃣ *Fayllar bilan ishlash:*\n"
        "Istalgan faylni botga yuborishingiz va tahlil qilishni so'rashingiz mumkin.",
        parse_mode=ParseMode.MARKDOWN
    )

@dp.message(Command("status"))
async def handle_status(message: Message):
    if not is_authorized(message.from_user.id):
        return
    
    os_info = f"{platform.system()} {platform.release()} ({platform.machine()})"
    py_ver = sys.version.split()[0]
    
    from .evolution.skills_manager import skills_manager
    from .evolution.memory_manager import memory_manager
    from .evolution.custom_tools_manager import custom_tools_manager
    
    skills_cnt = len(skills_manager.discover_skills())
    mem_cnt = len(memory_manager.get_all_learnings())
    tools_cnt = len(AGENT.tool_map)
    custom_cnt = len(custom_tools_manager.list_tools_info())

    status_text = (
        f"📊 *Agent va Tizim Holati:*\n\n"
        f"🤖 *Faol AI Modeli:* `{AGENT.active_model}`\n"
        f"📚 *O'zlashtirilgan Skills:* `{skills_cnt} ta`\n"
        f"🧠 *Xotiradagi saboqlar:* `{mem_cnt} ta`\n"
        f"🛠 *Asboblar:* `{tools_cnt} ta` (shundan `{custom_cnt} ta` dinamik)\n"
        f"💻 *Tizim:* `{os_info}` | Python `{py_ver}`\n"
        f"📁 *Ishchi papka:* `{WORKSPACE_DIR}`\n"
        f"👤 *Admin ID:* `{message.from_user.id}`\n"
        f"🟢 *Agent holati:* Faol, o'rganishga tayyor"
    )
    await message.answer(status_text, parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("clear"))
async def handle_clear(message: Message):
    if not is_authorized(message.from_user.id):
        return
    await message.answer("🧹 *Xotira yangilandi!* Yangi topshiriqlarni kutmoqdaman.", parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("files"))
async def handle_files(message: Message):
    if not is_authorized(message.from_user.id):
        return
    res = list_directory(".")
    await message.answer(f"📁 *Ishchi papkadagi fayllar:*\n\n```\n{res}\n```", parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("skills"))
async def handle_skills(message: Message):
    if not is_authorized(message.from_user.id):
        return
    from .evolution.skills_manager import skills_manager
    skills = skills_manager.discover_skills()
    if not skills:
        await message.answer("📚 Hozircha maxsus ko'nikmalar yaratilmagan.", parse_mode=ParseMode.MARKDOWN)
        return
    lines = ["📚 *AGENTNING MAXSUS KO'NIKMALARI (SKILLS):*\n"]
    for name, data in skills.items():
        trig = f" (Kalit so'zlar: {', '.join(data['triggers'][:3])})" if data['triggers'] else ""
        lines.append(f"⭐ *{data['name']}*\n   _{data['description']}_{trig}\n")
    lines.append("💡 _Agent yangi murakkab vazifalarni bajargan sari o'ziga yangi ko'nikmalar yozib boradi._")
    await message.answer("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("tools"))
async def handle_tools(message: Message):
    if not is_authorized(message.from_user.id):
        return
    from .evolution.custom_tools_manager import custom_tools_manager
    all_tools = list(AGENT.tool_map.keys())
    custom = custom_tools_manager.list_tools_info()
    custom_names = [c["name"] for c in custom]
    builtin_names = [t for t in all_tools if t not in custom_names]

    lines = [
        f"🛠 *AGENT ASBOBLARI (JAMI: {len(all_tools)} ta):*\n",
        f"🔹 *Standart asboblar ({len(builtin_names)} ta):*",
        ", ".join(f"`{t}`" for t in builtin_names),
        f"\n🧬 *O'zi yaratgan dinamik asboblar ({len(custom_names)} ta):*",
        ", ".join(f"`{t}`" for t in custom_names) if custom_names else "_Hozircha yo'q (agent vazifaga qarab o'zi yaratadi)_",
        "\n💡 _Agent imkoniyati yetmagan paytda yangi Python funksiyasini yozib, o'ziga darhol yangi asbob qilib ulab oladi!_"
    ]
    await message.answer("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("memory"))
async def handle_memory(message: Message):
    if not is_authorized(message.from_user.id):
        return
    from .evolution.memory_manager import memory_manager
    learnings = memory_manager.get_all_learnings()
    if not learnings:
        await message.answer("🧠 Xotirada hali saboqlar yo'q.", parse_mode=ParseMode.MARKDOWN)
        return
    lines = [f"🧠 *AGENTNING DOIMIY XOTIRASI ({len(learnings)} ta saboq):*\n"]
    for idx, l in enumerate(learnings[-10:], 1):
        lines.append(f"{idx}. *[{l.get('category', 'umumiy')}]* ({l.get('timestamp', '')}):\n   _{l.get('lesson')}_\n")
    lines.append("💡 _Siz ham `/learn <saboq>` buyrug'i orqali agentga yangi qoidalarni o'rgatishingiz mumkin._")
    await message.answer("\n".join(lines), parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("learn"))
async def handle_learn(message: Message):
    if not is_authorized(message.from_user.id):
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.answer(
            "ℹ️ *Agentga yangi saboq o'rgatish uchun:*\n\n"
            "`/learn <o'rganilishi kerak bo'lgan qoida yoki ko'rsatma>`\n\n"
            "Masalan:\n`/learn Windows dasturlarni har doim .bat ishga tushiruvchisi bilan birga ber`",
            parse_mode=ParseMode.MARKDOWN
        )
        return
    from .evolution.memory_manager import memory_manager
    res = memory_manager.record_learning(args[1].strip(), category="foydalanuvchi_oqitdi")
    await message.answer(
        f"🎓 *Saboq qabul qilindi!*\n\n{res}\n\n"
        f"Endi agent keyingi barcha topshiriqlarda ushbu ko'rsatmaga qat'iy amal qiladi.",
        parse_mode=ParseMode.MARKDOWN
    )

@dp.message(Command("evolve"))
async def handle_evolve(message: Message):
    if not is_authorized(message.from_user.id):
        return
    from .evolution.self_evolver import self_evolver
    report = self_evolver.format_inspection_report()
    await message.answer(report, parse_mode=ParseMode.MARKDOWN)

@dp.message(F.photo)
async def handle_photo(message: Message):
    """Foydalanuvchi yuborgan rasm va skrinshotlarni tahlil qilish."""
    if not is_authorized(message.from_user.id):
        return

    caption = (message.caption or "").strip()
    status_msg = await message.answer("🔍 *Rasm yuklab olinmoqda va tahlil qilinmoqda...*", parse_mode=ParseMode.MARKDOWN)

    try:
        photo = message.photo[-1]
        file_info = await message.bot.get_file(photo.file_id)
        
        # Faylni yuklab olish
        import io
        stream = io.BytesIO()
        await message.bot.download_file(file_info.file_path, destination=stream)
        img_bytes = stream.getvalue()

        # Workspace ga ham saqlab qo'yish
        img_path = WORKSPACE_DIR / f"photo_{int(time.time())}.jpg"
        img_path.write_bytes(img_bytes)

        # AI Vision tahlili
        answer = AGENT.analyze_image(img_bytes, mime_type="image/jpeg", prompt=caption)

        try:
            await status_msg.delete()
        except Exception:
            pass

        await send_chunked_message(message, answer)

    except Exception as e:
        logger.error(f"Rasmni tahlil qilishda xatolik: {e}")
        await status_msg.edit_text(f"❌ Rasmni tahlil qilishda xatolik yuz berdi: {e}")


@dp.message(F.voice | F.audio)
async def handle_voice(message: Message):
    """Foydalanuvchi yuborgan ovozli xabarni tahlil qilish va javob berish."""
    if not is_authorized(message.from_user.id):
        return

    caption = (message.caption or "").strip()
    status_msg = await message.answer("🎤 *Ovozli xabar tinglanmoqda va tahlil qilinmoqda...*", parse_mode=ParseMode.MARKDOWN)

    try:
        voice = message.voice or message.audio
        file_info = await message.bot.get_file(voice.file_id)

        import io
        stream = io.BytesIO()
        await message.bot.download_file(file_info.file_path, destination=stream)
        audio_bytes = stream.getvalue()

        mime_type = "audio/ogg" if message.voice else "audio/mp3"
        answer = AGENT.analyze_audio(audio_bytes, mime_type=mime_type, prompt=caption)

        try:
            await status_msg.delete()
        except Exception:
            pass

        await send_chunked_message(message, answer)

    except Exception as e:
        logger.error(f"Ovozli xabarni tahlil qilishda xatolik: {e}")
        await status_msg.edit_text(f"❌ Ovozli xabarni qayta ishlashda xatolik: {e}")


@dp.message(F.document)
async def handle_document(message: Message):
    """Foydalanuvchi telefonidan fayl (PDF, TXT, kod, CSV) yuborsa, uni qabul qilib to'liq tahlil qiladi."""
    if not is_authorized(message.from_user.id):
        return

    doc = message.document
    file_name = doc.file_name or "file_from_telegram"
    dest_path = WORKSPACE_DIR / file_name
    caption = (message.caption or "").strip()

    wait_msg = await message.answer(f"📥 `{file_name}` yuklab olinmoqda va tahlil qilinmoqda...", parse_mode=ParseMode.MARKDOWN)
    try:
        file_info = await message.bot.get_file(doc.file_id)
        await message.bot.download_file(file_info.file_path, destination=dest_path)
        doc_bytes = dest_path.read_bytes()

        # Agent orqali avtomatik tahlil qilish
        mime_type = doc.mime_type or "application/octet-stream"
        answer = AGENT.analyze_document(
            doc_bytes=doc_bytes,
            mime_type=mime_type,
            filename=file_name,
            prompt=caption
        )

        try:
            await wait_msg.delete()
        except Exception:
            pass

        await send_chunked_message(message, f"📄 *{file_name} tahlili:*\n\n{answer}")

    except Exception as e:
        await wait_msg.edit_text(f"❌ Faylni tahlil qilishda xatolik: {e}")

@dp.message(F.text)
async def handle_user_task(message: Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        if not ALLOWED_TELEGRAM_USERS:
            await handle_start(message)
        return

    user_text = message.text.strip()

    # Foydalanuvchiga jarayon boshlanganini ko'rsatish
    status_msg = await message.answer("⏳ *Topshiriq qabul qilindi, agent ishga tushdi...*", parse_mode=ParseMode.MARKDOWN)

    last_edit_time = 0.0
    current_status = ""

    async def progress_callback(status: str):
        nonlocal last_edit_time, current_status
        current_status = status
        now = time.time()
        # Telegram FloodWait cheklovini aylanib o'tish uchun xabarni kamida 1.5 soniyada 1 marta yangilash
        if now - last_edit_time >= 1.5:
            last_edit_time = now
            try:
                await status_msg.edit_text(status, parse_mode=ParseMode.MARKDOWN)
            except Exception:
                pass

    try:
        # Agent topshiriqni bajaradi (Online yoki Offline)
        result = await AGENT.execute_task_async(user_text, progress_callback=progress_callback)

        # Status xabarini o'chirish yoki yakuniy xabarga almashtirish
        try:
            await status_msg.delete()
        except Exception:
            pass

        # Natija matnini yuborish
        await send_chunked_message(message, result["text"])

        # Agar agent fayllar yaratgan bo'lsa, ularni jo'natish
        files = result.get("files", [])
        for file_path in files:
            p = Path(file_path)
            if p.exists() and p.is_file():
                try:
                    input_file = FSInputFile(str(p), filename=p.name)
                    await message.answer_document(input_file, caption=f"📎 Yaratilgan fayl: `{p.name}`", parse_mode=ParseMode.MARKDOWN)
                except Exception as e:
                    logger.error(f"Fayl jo'natishda xatolik: {e}")
                    await message.answer(f"⚠️ Faylni yuborishda xatolik: {p.name} ({e})")

    except Exception as e:
        logger.error(f"Topshiriqni bajarishda kutilmagan xatolik: {e}")
        try:
            await status_msg.edit_text(f"❌ Xatolik yuz berdi:\n`{str(e)}`", parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await message.answer(f"❌ Xatolik yuz berdi:\n`{str(e)}`")

async def start_bot():
    """Botni uzoq muddatli polling rejimida ishga tushirish."""
    global bot
    logger.info("Agent Telegram boti ishga tushirilmoqda...")
    bot = Bot(token=TELEGRAM_BOT_TOKEN)

    runner = None
    port_str = os.getenv("PORT")
    if port_str:
        try:
            from aiohttp import web
            async def health_check(request):
                return web.Response(text="Bot is running! @agentsatka_bot 24/7 active.", status=200)

            app = web.Application()
            app.router.add_get("/", health_check)
            app.router.add_get("/health", health_check)
            runner = web.AppRunner(app)
            await runner.setup()
            site = web.TCPSite(runner, "0.0.0.0", int(port_str))
            await site.start()
            logger.info(f"Render/Cloud HTTP server {port_str}-portda ishga tushirildi.")
        except Exception as e:
            logger.warning(f"HTTP serverni ishga tushirishda ogohlantirish: {e}")

    try:
        while True:
            try:
                # Eski o'qilmagan xabarlarni o'tkazib yuborish
                await bot.delete_webhook(drop_pending_updates=True)
                logger.info("Telegram polling faol ishlamoqda...")
                await dp.start_polling(bot)
            except (KeyboardInterrupt, SystemExit):
                break
            except Exception as e:
                logger.warning(f"Telegram tarmog'ida vaqtinchalik uzilish ({e}). 4 soniyadan so'ng qayta ulanadi...")
                await asyncio.sleep(4)
    finally:
        if runner:
            await runner.cleanup()
        await bot.session.close()
