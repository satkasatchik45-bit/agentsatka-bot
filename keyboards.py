from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    WebAppInfo
)
from typing import List, Dict, Any, Optional

try:
    from .config import SECTIONS, RENDER_EXTERNAL_URL
except ImportError:
    from config import SECTIONS, RENDER_EXTERNAL_URL

def get_collapsed_reply_keyboard() -> ReplyKeyboardMarkup:
    """Yashirin / ixcham holatdagi pastki menyu (ekranni egallamaydi, faqat 1 ta kichik belgicha)."""
    kb = [
        [
            KeyboardButton(text="▫️ ⫶ Bo'limlar"),
            KeyboardButton(text="📄 Sahifalar")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Xabar yozing yoki bo'lim tanlang..."
    )

def get_expanded_reply_keyboard() -> ReplyKeyboardMarkup:
    """O'ng yonga / 1 ustun shaklida joylashgan ixcham bo'limlar menyusi."""
    kb = [
        [KeyboardButton(text="💼 Biznes")],
        [KeyboardButton(text="💻 Dasturlash")],
        [KeyboardButton(text="🩺 Tibbiyot")],
        [KeyboardButton(text="❓ Savollar")],
        [KeyboardButton(text="📋 Rejalar")],
        [KeyboardButton(text="💡 G'oyalar")],
        [
            KeyboardButton(text="📄 Sahifalar"),
            KeyboardButton(text="👁️ Yashirish")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Bo'lim tanlang..."
    )

def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Standart ixcham menyu."""
    return get_collapsed_reply_keyboard()

def get_collapsible_inline_panel(
    is_expanded: bool = False,
    active_section: str = "savollar",
    webapp_url: Optional[str] = None
) -> InlineKeyboardMarkup:
    """
    Chat ichidagi 1 ustun shaklidagi interaktiv panel:
    Ochiq va yashirin holatlari mavjud, 60% shaffof WebApp bilan bog'langan.
    """
    url = webapp_url or RENDER_EXTERNAL_URL
    kb = []

    if not is_expanded:
        # Yashirin holati (faqat ochish va WebApp tugmasi)
        row = [
            InlineKeyboardButton(text="▫️ ⫶ Bo'limlar (ochish)", callback_data="panel:expand")
        ]
        if url:
            row.append(InlineKeyboardButton(text="📱 60% Shaffof Panel", web_app=WebAppInfo(url=f"{url}/webapp")))
        kb.append(row)
    else:
        # Ochiq holati - 1 ustun shaklida kichik belgichalar bilan
        for key, s in SECTIONS.items():
            mark = "🔘" if key == active_section else "▫️"
            kb.append([
                InlineKeyboardButton(
                    text=f"{mark} {s['icon']} {s['title']}",
                    callback_data=f"set_sec:{key}"
                )
            ])

        control_row = [
            InlineKeyboardButton(text="📚 Sahifalar", callback_data=f"pages_list:{active_section}"),
            InlineKeyboardButton(text="👁️ Yashirish", callback_data="panel:collapse")
        ]
        kb.append(control_row)

        if url:
            kb.append([
                InlineKeyboardButton(text="📱 60% Shaffof Web Panel", web_app=WebAppInfo(url=f"{url}/webapp"))
            ])

    return InlineKeyboardMarkup(inline_keyboard=kb)

def get_section_inline_keyboard(
    section_key: str,
    page_id: int,
    webapp_url: Optional[str] = None
) -> InlineKeyboardMarkup:
    """Bo'lim ichidagi boshqaruv inline tugmalari."""
    url = webapp_url or RENDER_EXTERNAL_URL
    kb = [
        [
            InlineKeyboardButton(text="➕ Yangi Sahifa", callback_data=f"page_new:{section_key}"),
            InlineKeyboardButton(text="📚 Sahifalarim", callback_data=f"pages_list:{section_key}")
        ],
        [
            InlineKeyboardButton(text="🧹 Tozalash", callback_data=f"page_clear_confirm:{page_id}"),
            InlineKeyboardButton(text="📥 Yuklab Olish (.txt)", callback_data=f"page_download:{page_id}")
        ],
        [
            InlineKeyboardButton(text="✏️ Nomlash", callback_data=f"page_rename:{page_id}"),
            InlineKeyboardButton(text="▫️ ⫶ Bo'limlar", callback_data="panel:expand")
        ]
    ]
    if url:
        kb.append([
            InlineKeyboardButton(text="📱 60% Shaffof Panel (Mini App)", web_app=WebAppInfo(url=f"{url}/webapp"))
        ])
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
