import asyncio
import io
import os
import sys
import logging
import time
# Logging sozlamalari
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.types import (
    Message,
    CallbackQuery,
    BufferedInputFile,
    ReplyKeyboardRemove
)
from aiogram.enums import ParseMode, ChatAction
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web, ClientSession

from pathlib import Path
_BASE = Path(__file__).resolve().parent
if str(_BASE) not in sys.path:
    sys.path.insert(0, str(_BASE))

try:
    from .config import (
        TELEGRAM_BOT_TOKEN,
        ALLOWED_TELEGRAM_USERS,
        ALLOWED_USERNAMES,
        SECTIONS,
        PORT,
        RENDER_EXTERNAL_URL,
        WEBHOOK_PATH,
        WEBHOOK_SECRET,
        MODEL_NAME
    )
    from .database import (
        init_db,
        get_or_create_user,
        set_active_section,
        get_active_section,
        get_or_create_active_page,
        create_new_page,
        get_pages_for_section,
        set_active_page,
        get_page_by_id,
        rename_page,
        clear_page_messages,
        delete_page,
        export_page_text,
        get_connection
    )
    from .keyboards import (
        get_main_reply_keyboard,
        get_section_inline_keyboard,
        get_pages_list_keyboard,
        get_page_action_keyboard,
        get_confirm_keyboard
    )
    from .ai_service import ai_service
except ImportError:
    from config import (
        TELEGRAM_BOT_TOKEN,
        ALLOWED_TELEGRAM_USERS,
        ALLOWED_USERNAMES,
        SECTIONS,
        PORT,
        RENDER_EXTERNAL_URL,
        WEBHOOK_PATH,
        WEBHOOK_SECRET,
        MODEL_NAME
    )
    from database import (
        init_db,
        get_or_create_user,
        set_active_section,
        get_active_section,
        get_or_create_active_page,
        create_new_page,
        get_pages_for_section,
        set_active_page,
        get_page_by_id,
        rename_page,
        clear_page_messages,
        delete_page,
        export_page_text,
        get_connection
    )
    from keyboards import (
        get_main_reply_keyboard,
        get_section_inline_keyboard,
        get_pages_list_keyboard,
        get_page_action_keyboard,
        get_confirm_keyboard
    )
    from ai_service import ai_service

# Logging sozlamalari
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("telegram_bot")

bot: Optional[Bot] = None
dp = Dispatcher(storage=MemoryStorage())

# Sahifa nomini o'zgartirish uchun holat (FSM)
class RenameState(StatesGroup):
    waiting_for_title = State()

def is_authorized(user) -> bool:
    """Faqat @satka8491 akkauntiga va uning tasdiqlangan ID raqamiga ruxsat berish."""
    if not user:
        return False
    uname = (user.username or "").strip().lower().lstrip("@")
    uid = user.id
    if uname in ALLOWED_USERNAMES or uid in ALLOWED_TELEGRAM_USERS:
        return True
    return False

UNAUTHORIZED_MESSAGE = (
    "⛔ *Kirish taqiqlangan!*\n\n"
    "Ushbu bot shaxsiy boʻlib, faqat *@satka8491* akkaunti uchun xizmat qiladi. "
    "Boshqa foydalanuvchilar undan foydalana olmaydi."
)

@dp.message.outer_middleware()
async def check_message_auth(handler, event: Message, data: dict):
    if not is_authorized(event.from_user):
        await event.answer(UNAUTHORIZED_MESSAGE, parse_mode=ParseMode.MARKDOWN)
        return
    return await handler(event, data)

@dp.callback_query.outer_middleware()
async def check_callback_auth(handler, event: CallbackQuery, data: dict):
    if not is_authorized(event.from_user):
        await event.answer("⛔ Kirish taqiqlangan! Faqat @satka8491 uchun.", show_alert=True)
        return
    return await handler(event, data)

async def send_long_message(message: Message, text: str):
    """Uzun matnlarni Telegram chegarasi (4096 belgi) bo'yicha bo'lib yuborish."""
    max_len = 3900
    if len(text) <= max_len:
        try:
            await message.answer(text, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await message.answer(text)
        return

    chunks = [text[i:i + max_len] for i in range(0, len(text), max_len)]
    for chunk in chunks:
        try:
            await message.answer(chunk, parse_mode=ParseMode.MARKDOWN)
        except Exception:
            await message.answer(chunk)
        await asyncio.sleep(0.3)

def format_section_dashboard(section_key: str, page: dict, msg_count: int = 0) -> str:
    sec = SECTIONS.get(section_key, SECTIONS["savollar"])
    return (
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{sec['icon']} *{sec['title'].upper()} BO'LIMI*\n"
        f"📝 _{sec['desc']}_\n\n"
        f"📄 *Joriy faol sahifa:* `{page['title']}`\n"
        f"💬 *Ushbu sahifadagi xabarlar:* {msg_count} ta\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"💡 _Bu yerdagi har bir savol-javobingiz faqat shu bo'lim va ushbu sahifada saqlanadi. "
        f"Boshqa bo'limlardagi mavzular bu yerga aralashmaydi._\n\n"
        f"✍️ Savol yoki vazifangizni yozing:"
    )

# ==========================================
# BUYRUQLAR (COMMANDS)
# ==========================================

@dp.message(CommandStart())
async def handle_start(message: Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    username = message.from_user.username or ""
    first_name = message.from_user.first_name or "Foydalanuvchi"

    if not is_authorized(message.from_user):
        await message.answer(UNAUTHORIZED_MESSAGE, parse_mode=ParseMode.MARKDOWN)
        return

    get_or_create_user(user_id, username, first_name)
    active_sec = get_active_section(user_id)
    active_page = get_or_create_active_page(user_id, active_sec)

    welcome_text = (
        f"👋 *Assalomu alaykum, {first_name}!* \n"
        f"🤖 *@agentsatka_bot* ning yangi ko'p sahifali tizimiga xush kelibsiz!\n\n"
        f"Ushbu bot barcha sohalaringizni tartibli va alohida sahifalarda boshqarish uchun yaratilgan:\n\n"
        f"💼 *Biznes* — Moliya, biznes reja, savdo va strategiya\n"
        f"💻 *Dasturlash* — Kodlar, Python, Web, xatolarni tuzatish\n"
        f"🩺 *Tibbiyot* — Nevrologiya, neyrojarrohlik, tahlillar\n"
        f"❓ *Savollar* — Erkin intellektual savol-javoblar\n"
        f"📋 *Rejalar* — Kunlik reja, vazifalar va checklistlar\n"
        f"💡 *G'oyalar* — YouTube Shorts, Reels va yangi startaplar\n\n"
        f"📊 *Savdo hisob-kitob:* `#savdo`, `#hisobot-savdo`, `#jadval` teglari bilan ro'yxat yoki chek yuborsangiz, avtomatik hisoblab chiroyli jadval qilib beradi.\n\n"
        f"📌 *Asosiy afzalligi:* Har bir bo'limda o'zingiz xohlagancha alohida sahifalar ochishingiz mumkin. "
        f"Mavzular bir-biriga aslo aralashib ketmaydi!\n\n"
        f"Quyidagi tugmalardan kerakli bo'limni tanlang:"
    )

    await message.answer(
        welcome_text,
        reply_markup=get_main_reply_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )

@dp.message(Command("help"))
async def handle_help(message: Message):
    if not is_authorized(message.from_user):
        await message.answer(UNAUTHORIZED_MESSAGE, parse_mode=ParseMode.MARKDOWN)
        return

    text = (
        f"📖 *QO'LLANMA VA IMKONIYATLAR:*\n\n"
        f"1️⃣ *Bo'lim tanlash:* Pastdagi tugmalar orqali kerakli bo'limga o'ting (Biznes, Dasturlash, Tibbiyot...).\n\n"
        f"2️⃣ *Alohida Sahifalar:* Har bir bo'lim ichida '➕ Yangi Sahifa' tugmasini bosib, yangi mavzu boshlashingiz mumkin.\n\n"
        f"3️⃣ *Savdo va Hisob-kitob:* `#savdo` yoki `#hisobot-savdo` tegi bilan tovarlar ro'yxatini yozsangiz yoki chek rasmini yuborsangiz, bot darhol hisoblab `#jadval` ko'rinishida beradi.\n\n"
        f"4️⃣ *Sahifalarni boshqarish:* '📚 Sahifalarim' tugmasi orqali avvalgi barcha sahifalaringizni ko'rishingiz, nomini o'zgartirishingiz yoki .txt formatida yuklab olishingiz mumkin.\n\n"
        f"5️⃣ *24/7 Mustaqil rejim:* Kompyuteringiz o'chiq bo'lsa ham bot bulutda (Render) kecha-yu kunduz mustaqil xizmat qiladi.\n\n"
        f"🔹 `/start` - Botni qayta ishga tushirish\n"
        f"🔹 `/status` - Server va model holatini ko'rish\n"
        f"🔹 `/new` - Yangi sahifa ochish\n"
        f"🔹 `/pages` - Sahifalar ro'yxati"
    )
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("status"))
async def handle_status(message: Message):
    if not is_authorized(message.from_user):
        await message.answer(UNAUTHORIZED_MESSAGE, parse_mode=ParseMode.MARKDOWN)
        return

    user_id = message.from_user.id
    sec_key = get_active_section(user_id)
    page = get_or_create_active_page(user_id, sec_key)
    pages = get_pages_for_section(user_id, sec_key)

    text = (
        f"📊 *AGENT VA BULUT HOLATI:*\n\n"
        f"🤖 *AI Modeli:* `{MODEL_NAME or 'gemini-3.8-flash'}`\n"
        f"🟢 *Bulut Holati:* 24/7 Faol (Render Cloud)\n"
        f"👤 *Foydalanuvchi:* @satka8491 (ID: `{user_id}`)\n"
        f"📁 *Joriy Bo'lim:* `{SECTIONS.get(sec_key, {}).get('title')}`\n"
        f"📄 *Faol Sahifa:* `{page['title']}`\n"
        f"📚 *Ushbu bo'limdagi sahifalar:* {len(pages)} ta\n\n"
        f"⚡ _Kompyuter o'chirilgan holatda ham bot uzluksiz ishlamoqda._"
    )
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("new"))
async def handle_cmd_new(message: Message):
    if not is_authorized(message.from_user):
        await message.answer(UNAUTHORIZED_MESSAGE, parse_mode=ParseMode.MARKDOWN)
        return
    user_id = message.from_user.id
    sec_key = get_active_section(user_id)
    new_page = create_new_page(user_id, sec_key)
    sec_title = SECTIONS.get(sec_key, {}).get("title")

    await message.answer(
        f"✨ *Yangi toza sahifa yaratildi!*\n\n"
        f"📁 Bo'lim: *{sec_title}*\n"
        f"📄 Sahifa: `{new_page['title']}`\n\n"
        f"Endi ushbu mavzu bo'yicha savollaringizni yozishingiz mumkin.",
        reply_markup=get_section_inline_keyboard(sec_key, new_page["id"]),
        parse_mode=ParseMode.MARKDOWN
    )

@dp.message(Command("pages"))
async def handle_cmd_pages(message: Message):
    if not is_authorized(message.from_user):
        await message.answer(UNAUTHORIZED_MESSAGE, parse_mode=ParseMode.MARKDOWN)
        return
    user_id = message.from_user.id
    sec_key = get_active_section(user_id)
    pages = get_pages_for_section(user_id, sec_key)
    sec_title = SECTIONS.get(sec_key, {}).get("title")

    await message.answer(
        f"📚 *{sec_title.upper()} BO'LIMIDAGI BARCHA SAHIFALAR:*\n\n"
        f"Quyidagi ro'yxatdan kerakli sahifani tanlang yoki yangisini oching:",
        reply_markup=get_pages_list_keyboard(pages, sec_key),
        parse_mode=ParseMode.MARKDOWN
    )

# ==========================================
# BO'LIMLARGA O'TISH (REPLY BUTTONS)
# ==========================================

SECTION_REPLY_MAP = {
    "💼 Biznes": "biznes",
    "💻 Dasturlash": "dasturlash",
    "🩺 Tibbiyot": "tibbiyot",
    "❓ Savollar": "savollar",
    "📋 Rejalar": "rejalar",
    "💡 G'oyalar": "goyalar"
}

@dp.message(F.text.in_(SECTION_REPLY_MAP.keys()))
async def handle_section_button(message: Message, state: FSMContext):
    await state.clear()
    if not is_authorized(message.from_user):
        await message.answer(UNAUTHORIZED_MESSAGE, parse_mode=ParseMode.MARKDOWN)
        return
    user_id = message.from_user.id

    sec_key = SECTION_REPLY_MAP[message.text]
    set_active_section(user_id, sec_key)
    page = get_or_create_active_page(user_id, sec_key)
    pages = get_pages_for_section(user_id, sec_key)
    curr_page = next((p for p in pages if p["id"] == page["id"]), page)
    msg_count = curr_page.get("message_count", 0)

    dashboard_text = format_section_dashboard(sec_key, page, msg_count)
    await message.answer(
        dashboard_text,
        reply_markup=get_section_inline_keyboard(sec_key, page["id"]),
        parse_mode=ParseMode.MARKDOWN
    )

@dp.message(F.text == "📄 Joriy Sahifa")
async def handle_current_page_button(message: Message, state: FSMContext):
    await state.clear()
    if not is_authorized(message.from_user):
        await message.answer(UNAUTHORIZED_MESSAGE, parse_mode=ParseMode.MARKDOWN)
        return
    user_id = message.from_user.id

    sec_key = get_active_section(user_id)
    page = get_or_create_active_page(user_id, sec_key)
    pages = get_pages_for_section(user_id, sec_key)
    curr_page = next((p for p in pages if p["id"] == page["id"]), page)
    msg_count = curr_page.get("message_count", 0)

    dashboard_text = format_section_dashboard(sec_key, page, msg_count)
    await message.answer(
        dashboard_text,
        reply_markup=get_section_inline_keyboard(sec_key, page["id"]),
        parse_mode=ParseMode.MARKDOWN
    )

@dp.message(F.text == "📚 Sahifalarim")
async def handle_my_pages_button(message: Message, state: FSMContext):
    await state.clear()
    if not is_authorized(message.from_user):
        await message.answer(UNAUTHORIZED_MESSAGE, parse_mode=ParseMode.MARKDOWN)
        return
    user_id = message.from_user.id

    sec_key = get_active_section(user_id)
    pages = get_pages_for_section(user_id, sec_key)
    sec_title = SECTIONS.get(sec_key, {}).get("title")

    await message.answer(
        f"📚 *{sec_title.upper()} BO'LIMIDAGI BARCHA SAHIFALAR:*\n\n"
        f"Quyidagi ro'yxatdan kerakli sahifani tanlang:",
        reply_markup=get_pages_list_keyboard(pages, sec_key),
        parse_mode=ParseMode.MARKDOWN
    )

# ==========================================
# INLINE CALLBACK HANDLERS
# ==========================================

@dp.callback_query(F.data.startswith("page_new:"))
async def cb_new_page(call: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = call.from_user.id
    sec_key = call.data.split(":", 1)[1]

    new_page = create_new_page(user_id, sec_key)
    sec_title = SECTIONS.get(sec_key, {}).get("title")

    await call.message.edit_text(
        f"✨ *Yangi sahifa ochildi!*\n\n"
        f"📁 Bo'lim: *{sec_title}*\n"
        f"📄 Sahifa: `{new_page['title']}`\n\n"
        f"Bu sahifadagi suhbat toza holda boshlanadi. Xabaringizni yozishingiz mumkin:",
        reply_markup=get_section_inline_keyboard(sec_key, new_page["id"]),
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer()

@dp.callback_query(F.data.startswith("pages_list:"))
async def cb_pages_list(call: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = call.from_user.id
    sec_key = call.data.split(":", 1)[1]
    pages = get_pages_for_section(user_id, sec_key)
    sec_title = SECTIONS.get(sec_key, {}).get("title")

    await call.message.edit_text(
        f"📚 *{sec_title.upper()} BO'LIMIDAGI SAHIFALAR ({len(pages)} ta):*\n\n"
        f"Ulanish uchun kerakli sahifani bosing:",
        reply_markup=get_pages_list_keyboard(pages, sec_key),
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer()

@dp.callback_query(F.data.startswith("page_view:"))
async def cb_page_view(call: CallbackQuery, state: FSMContext):
    await state.clear()
    user_id = call.from_user.id
    page_id = int(call.data.split(":", 1)[1])
    page = get_page_by_id(page_id)
    if not page:
        await call.answer("Sahifa topilmadi", show_alert=True)
        return

    status = "🟢 Faol sahifa" if page["is_active"] else "⚪ Nofaol sahifa"
    text = (
        f"📄 *SAHIFA MA'LUMOTLARI:*\n\n"
        f"📌 *Nomi:* `{page['title']}`\n"
        f"📁 *Bo'lim:* {page['section'].capitalize()}\n"
        f"🕒 *Yaratilgan:* {page['created_at']}\n"
        f"🔄 *Yangilangan:* {page['updated_at']}\n"
        f"📍 *Holati:* {status}\n\n"
        f"Amalni tanlang:"
    )
    await call.message.edit_text(
        text,
        reply_markup=get_page_action_keyboard(page),
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer()

@dp.callback_query(F.data.startswith("page_activate:"))
async def cb_page_activate(call: CallbackQuery):
    user_id = call.from_user.id
    page_id = int(call.data.split(":", 1)[1])
    updated = set_active_page(user_id, page_id)
    if not updated:
        await call.answer("Sahifa topilmadi", show_alert=True)
        return

    sec_key = updated["section"]
    await call.message.edit_text(
        f"✅ *{updated['title']}* faol sahifa qilib belgilandi!\n\n"
        f"Endi yozadigan barcha xabarlaringiz shu sahifaga tushadi.",
        reply_markup=get_section_inline_keyboard(sec_key, page_id),
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer("Faollashtirildi!")

@dp.callback_query(F.data.startswith("page_download:"))
async def cb_page_download(call: CallbackQuery):
    user_id = call.from_user.id
    page_id = int(call.data.split(":", 1)[1])
    exported_text = export_page_text(page_id, user_id)

    if not exported_text:
        await call.answer("Sahifada hali xabarlar yo'q", show_alert=True)
        return

    page = get_page_by_id(page_id)
    safe_title = "".join(c for c in (page["title"] if page else "sahifa") if c.isalnum() or c in (" ", "_", "-")).strip()
    filename = f"{safe_title}_{page_id}.txt"

    file_bytes = exported_text.encode("utf-8")
    doc_file = BufferedInputFile(file_bytes, filename=filename)

    await call.message.answer_document(
        doc_file,
        caption=f"📥 *{page['title'] if page else 'Sahifa'}* ning to'liq suhbat fayli.",
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer("Fayl yuborildi!")

@dp.callback_query(F.data.startswith("page_rename:"))
async def cb_page_rename(call: CallbackQuery, state: FSMContext):
    user_id = call.from_user.id
    page_id = int(call.data.split(":", 1)[1])
    page = get_page_by_id(page_id)
    if not page:
        await call.answer("Sahifa topilmadi", show_alert=True)
        return

    await state.set_state(RenameState.waiting_for_title)
    await state.update_data(page_id=page_id, section_key=page["section"])

    await call.message.answer(
        f"✏️ *'{page['title']}'* sahifasi uchun yangi nom kiriting:\n\n"
        f"_(Masalan: 'Klinika biznes rejasi' yoki 'Python bot xatosi')_",
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer()

@dp.message(RenameState.waiting_for_title)
async def process_rename_title(message: Message, state: FSMContext):
    data = await state.get_data()
    page_id = data.get("page_id")
    section_key = data.get("section_key")
    new_title = message.text.strip()

    if not new_title:
        await message.answer("Iltimos, yaroqli nom kiriting.")
        return

    rename_page(page_id, message.from_user.id, new_title)
    await state.clear()

    await message.answer(
        f"✅ Sahifa nomi muvaffaqiyatli o'zgartirildi: *{new_title}*",
        reply_markup=get_section_inline_keyboard(section_key, page_id),
        parse_mode=ParseMode.MARKDOWN
    )

@dp.callback_query(F.data.startswith("page_clear_confirm:"))
async def cb_clear_confirm(call: CallbackQuery):
    page_id = int(call.data.split(":", 1)[1])
    page = get_page_by_id(page_id)
    title = page["title"] if page else "Sahifa"

    await call.message.edit_text(
        f"⚠️ *Diqqat!* Siz rostdan ham *'{title}'* sahifasidagi barcha suhbat tarixini tozalashni xohlaysizmi?\n\n"
        f"Bu amalni ortga qaytarib bo'lmaydi.",
        reply_markup=get_confirm_keyboard("clear", page_id, f"page_view:{page_id}"),
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer()

@dp.callback_query(F.data.startswith("confirm_clear:"))
async def cb_execute_clear(call: CallbackQuery):
    user_id = call.from_user.id
    page_id = int(call.data.split(":", 1)[1])
    clear_page_messages(page_id, user_id)
    page = get_page_by_id(page_id)

    await call.message.edit_text(
        f"🧹 *{page['title'] if page else 'Sahifa'}* tozalandi! Yangi suhbatni boshlashingiz mumkin.",
        reply_markup=get_section_inline_keyboard(page["section"] if page else "savollar", page_id),
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer("Tozalandi!")

@dp.callback_query(F.data.startswith("page_delete_confirm:"))
async def cb_delete_confirm(call: CallbackQuery):
    page_id = int(call.data.split(":", 1)[1])
    page = get_page_by_id(page_id)
    title = page["title"] if page else "Sahifa"

    await call.message.edit_text(
        f"🗑 *'{title}'* sahifasini butunlay o'chirib tashlamoqchimisiz?\n\n"
        f"Ushbu sahifadagi barcha xabarlar o'chib ketadi.",
        reply_markup=get_confirm_keyboard("delete", page_id, f"page_view:{page_id}"),
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer()

@dp.callback_query(F.data.startswith("confirm_delete:"))
async def cb_execute_delete(call: CallbackQuery):
    user_id = call.from_user.id
    page_id = int(call.data.split(":", 1)[1])
    page = get_page_by_id(page_id)
    sec_key = page["section"] if page else "savollar"

    delete_page(page_id, user_id)
    active_page = get_or_create_active_page(user_id, sec_key)

    await call.message.edit_text(
        f"🗑 Sahifa muvaffaqiyatli o'chirildi.\n\n"
        f"Hozirgi faol sahifa: *{active_page['title']}*",
        reply_markup=get_section_inline_keyboard(sec_key, active_page["id"]),
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer("O'chirildi!")

@dp.callback_query(F.data.startswith("section_view:"))
async def cb_section_view(call: CallbackQuery):
    user_id = call.from_user.id
    sec_key = call.data.split(":", 1)[1]
    page = get_or_create_active_page(user_id, sec_key)
    pages = get_pages_for_section(user_id, sec_key)
    curr_page = next((p for p in pages if p["id"] == page["id"]), page)
    msg_count = curr_page.get("message_count", 0)

    await call.message.edit_text(
        format_section_dashboard(sec_key, page, msg_count),
        reply_markup=get_section_inline_keyboard(sec_key, page["id"]),
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer()

@dp.callback_query(F.data == "go_home")
async def cb_go_home(call: CallbackQuery):
    await call.message.answer(
        "🏠 *Asosiy Menyu*\nQuyidagi tugmalardan kerakli bo'limni tanlang:",
        reply_markup=get_main_reply_keyboard(),
        parse_mode=ParseMode.MARKDOWN
    )
    await call.answer()

# ==========================================
# ASOSIY SUHBAT XABARLARI (AI BILAN MULOQOT)
# ==========================================

@dp.message(F.text)
async def handle_user_text_message(message: Message, state: FSMContext):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return

    # Agar FSM holatida bo'lsa (masalan qayta nomlash), o'tkazib yuborish
    current_state = await state.get_state()
    if current_state is not None:
        return

    user_text = message.text.strip()
    if not user_text:
        return

    # Foydalanuvchining joriy bo'limi va faol sahifasini olish
    sec_key = get_active_section(user_id)
    active_page = get_or_create_active_page(user_id, sec_key)
    sec_title = SECTIONS.get(sec_key, {}).get("title")

    # Typing indikatori
    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    # Gemini AI orqali faqat shu sahifa kontekstida javob olish
    loop = asyncio.get_running_loop()
    response_text = await loop.run_in_executor(
        None,
        ai_service.generate_response,
        user_text,
        sec_key,
        active_page["id"],
        None,
        None
    )

    # Javobni yuborish
    await send_long_message(message, response_text)

@dp.message(F.photo)
async def handle_user_photo(message: Message):
    user_id = message.from_user.id
    if not is_authorized(user_id):
        return

    sec_key = get_active_section(user_id)
    active_page = get_or_create_active_page(user_id, sec_key)
    caption = (message.caption or "").strip() or "Ushbu rasmni batafsil tahlil qilib bering."

    await message.bot.send_chat_action(chat_id=message.chat.id, action=ChatAction.TYPING)

    try:
        photo = message.photo[-1]
        file_info = await message.bot.get_file(photo.file_id)
        stream = io.BytesIO()
        await message.bot.download_file(file_info.file_path, destination=stream)
        img_bytes = stream.getvalue()

        loop = asyncio.get_running_loop()
        response_text = await loop.run_in_executor(
            None,
            ai_service.generate_response,
            caption,
            sec_key,
            active_page["id"],
            img_bytes,
            "image/jpeg"
        )
        await send_long_message(message, response_text)
    except Exception as e:
        logger.error(f"Rasmni tahlil qilishda xatolik: {e}")
        await message.answer(f"❌ Rasmni tahlil qilishda xatolik yuz berdi: {e}")

# ==========================================
# RENDER 24/7 KEEP-ALIVE VA ISHGA TUSHIRISH
# ==========================================

async def self_ping_loop(base_url: str):
    """Render bepul serverini uxlab qolmasligi uchun har 9 daqiqada uyg'otib turish."""
    url = f"{base_url}/health"
    logger.info(f"Self-ping xizmati ishga tushdi: {url}")
    await asyncio.sleep(60) # Ilk kutish
    while True:
        try:
            async with ClientSession() as session:
                async with session.get(url, timeout=15) as resp:
                    logger.info(f"Self-ping yuborildi: {resp.status}")
        except Exception as e:
            logger.warning(f"Self-pingda vaqtinchalik ogohlantirish: {e}")
        await asyncio.sleep(540) # 9 daqiqa

async def health_check_handler(request):
    return web.Response(text="Bot is running! @agentsatka_bot 24/7 active.", status=200)

async def main():
    global bot
    init_db()

    if not TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN o'rnatilmagan!")
        return

    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    logger.info("Bot tayyorlandi...")

    # 1. Render va Cloud uchun HTTP server (Port binding & Health check)
    runner = None
    try:
        app = web.Application()
        app.router.add_get("/", health_check_handler)
        app.router.add_get("/health", health_check_handler)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, "0.0.0.0", PORT)
        await site.start()
        logger.info(f"Render HTTP server 0.0.0.0:{PORT} da muvaffaqiyatli ochildi.")
    except Exception as e:
        logger.warning(f"HTTP serverni ishga tushirishda ogohlantirish: {e}")

    # 2. Render Free instance uxlab qolmasligi uchun fon pinger
    if RENDER_EXTERNAL_URL:
        asyncio.create_task(self_ping_loop(RENDER_EXTERNAL_URL))

    # 3. Telegram Polling (Doimiy xabarlarni tinglash)
    try:
        while True:
            try:
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
        if bot:
            await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
