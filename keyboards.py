from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton
)
from typing import List, Dict, Any
try:
    from .config import SECTIONS
except ImportError:
    from config import SECTIONS

def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Doimiy pastki menyu (ixcham va qulay)."""
    kb = [
        [
            KeyboardButton(text="💼 Biznes"),
            KeyboardButton(text="💻 Dasturlash")
        ],
        [
            KeyboardButton(text="🩺 Tibbiyot"),
            KeyboardButton(text="❓ Savollar")
        ],
        [
            KeyboardButton(text="📋 Rejalar"),
            KeyboardButton(text="💡 G'oyalar")
        ],
        [
            KeyboardButton(text="📄 Joriy Sahifa"),
            KeyboardButton(text="📚 Sahifalarim")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Xabar yozing yoki bo'lim tanlang..."
    )

def get_section_inline_keyboard(section_key: str, page_id: int) -> InlineKeyboardMarkup:
    """Bo'lim ichidagi boshqaruv inline tugmalari."""
    kb = [
        [
            InlineKeyboardButton(text="➕ Yangi Sahifa Ochish", callback_data=f"page_new:{section_key}"),
            InlineKeyboardButton(text="📚 Barcha Sahifalar", callback_data=f"pages_list:{section_key}")
        ],
        [
            InlineKeyboardButton(text="🧹 Sahifani Tozalash", callback_data=f"page_clear_confirm:{page_id}"),
            InlineKeyboardButton(text="📥 Yuklab Olish (.txt)", callback_data=f"page_download:{page_id}")
        ],
        [
            InlineKeyboardButton(text="✏️ Sahifa Nomini O'zgartirish", callback_data=f"page_rename:{page_id}"),
            InlineKeyboardButton(text="🏠 Bosh Sahifa", callback_data="go_home")
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_pages_list_keyboard(pages: List[Dict[str, Any]], section_key: str) -> InlineKeyboardMarkup:
    """Bo'limdagi barcha sahifalar ro'yxati."""
    buttons = []
    for p in pages:
        status_icon = "🟢" if p.get("is_active") else "📄"
        cnt = p.get("message_count", 0)
        title = p.get("title", "Sahifa")
        btn_text = f"{status_icon} {title} ({cnt} xabar)"
        buttons.append([
            InlineKeyboardButton(text=btn_text, callback_data=f"page_view:{p['id']}")
        ])

    control_row = [
        InlineKeyboardButton(text="➕ Yangi Sahifa", callback_data=f"page_new:{section_key}"),
        InlineKeyboardButton(text="🔙 Bo'limga qaytish", callback_data=f"section_view:{section_key}")
    ]
    buttons.append(control_row)
    return InlineKeyboardMarkup(inline_keyboard=buttons)

def get_page_action_keyboard(page: Dict[str, Any]) -> InlineKeyboardMarkup:
    """Tanlangan sahifa bo'yicha amallar menyusi."""
    page_id = page["id"]
    is_active = bool(page.get("is_active", 0))
    section = page["section"]

    kb = []
    if not is_active:
        kb.append([
            InlineKeyboardButton(text="✅ Faol sahifa qilish", callback_data=f"page_activate:{page_id}")
        ])

    kb.append([
        InlineKeyboardButton(text="📥 Yuklab Olish (.txt)", callback_data=f"page_download:{page_id}"),
        InlineKeyboardButton(text="✏️ Nomlash", callback_data=f"page_rename:{page_id}")
    ])
    kb.append([
        InlineKeyboardButton(text="🧹 Tozalash", callback_data=f"page_clear_confirm:{page_id}"),
        InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"page_delete_confirm:{page_id}")
    ])
    kb.append([
        InlineKeyboardButton(text="🔙 Sahifalar ro'yxatiga", callback_data=f"pages_list:{section}")
    ])
    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_confirm_keyboard(action: str, target_id: int, cancel_callback: str) -> InlineKeyboardMarkup:
    """Tasdiqlash tugmalari."""
    kb = [
        [
            InlineKeyboardButton(text="Ha, tasdiqlayman ⚠️", callback_data=f"confirm_{action}:{target_id}"),
            InlineKeyboardButton(text="Bekor qilish ❌", callback_data=cancel_callback)
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)
