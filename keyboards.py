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

def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Doimiy, ixcham va salobatli boshqaruv paneli"""
    kb = [
        [
            KeyboardButton(text="📱 60% Bo'limlar Paneli"),
            KeyboardButton(text="➕ Yangi Sahifa")
        ],
        [
            KeyboardButton(text="📚 Sahifalarim"),
            KeyboardButton(text="🧬 O'zini Rivojlantirish")
        ]
    ]
    return ReplyKeyboardMarkup(
        keyboard=kb,
        resize_keyboard=True,
        is_persistent=True,
        input_field_placeholder="Matn, ovoz, video yoki fayl yuboring..."
    )

def get_collapsed_reply_keyboard() -> ReplyKeyboardMarkup:
    """Ixcham pastki menyu"""
    return get_main_reply_keyboard()

def get_expanded_reply_keyboard() -> ReplyKeyboardMarkup:
    """1 ustun shaklidagi menyu"""
    return get_main_reply_keyboard()

def get_collapsible_inline_panel(
    is_expanded: bool = True,
    active_section: str = "savollar",
    webapp_url: Optional[str] = None
) -> InlineKeyboardMarkup:
    """
    Chat ichidagi 60% interaktiv boshqaruv paneli:
    Barcha 6 ta mustaqil agent bo'limlari ixcham 2x3 ustunda aks etadi va 60% WebApp bilan bog'langan.
    """
    url = webapp_url or RENDER_EXTERNAL_URL
    kb = []

    # 2 tadan qilib bo'limlarni ixcham joylash
    sec_keys = list(SECTIONS.keys())
    for i in range(0, len(sec_keys), 2):
        row = []
        k1 = sec_keys[i]
        s1 = SECTIONS[k1]
        m1 = "🔘" if k1 == active_section else "▫️"
        row.append(InlineKeyboardButton(text=f"{m1} {s1['icon']} {s1['title']}", callback_data=f"set_sec:{k1}"))
        if i + 1 < len(sec_keys):
            k2 = sec_keys[i+1]
            s2 = SECTIONS[k2]
            m2 = "🔘" if k2 == active_section else "▫️"
            row.append(InlineKeyboardButton(text=f"{m2} {s2['icon']} {s2['title']}", callback_data=f"set_sec:{k2}"))
        kb.append(row)

    control_row = [
        InlineKeyboardButton(text="➕ Yangi Sahifa", callback_data=f"page_new:{active_section}"),
        InlineKeyboardButton(text="📚 Sahifalarim", callback_data=f"pages_list:{active_section}")
    ]
    kb.append(control_row)

    if url:
        kb.append([
            InlineKeyboardButton(text="📱 60% Shaffof Panel (Mini App)", web_app=WebAppInfo(url=f"{url}/webapp"))
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
            InlineKeyboardButton(text="📱 60% Paneli", callback_data="panel:expand")
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
