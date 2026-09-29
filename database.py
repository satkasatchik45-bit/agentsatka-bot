import sqlite3
import datetime
from typing import List, Dict, Optional, Any

try:
    from .config import DB_PATH, SECTIONS
except ImportError:
    from config import DB_PATH, SECTIONS

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def init_db():
    """Barcha kerakli jadvallarni yaratish va sozlash."""
    conn = get_connection()
    cursor = conn.cursor()

    # Foydalanuvchilar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            active_section TEXT DEFAULT 'savollar',
            created_at TEXT
        );
    """)

    # Har bir bo'limdagi mustaqil sahifalar jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            section TEXT NOT NULL,
            title TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users (user_id)
        );
    """)

    # Sahifalardagi suhbat xabarlari jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER NOT NULL,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT,
            FOREIGN KEY (page_id) REFERENCES pages (id) ON DELETE CASCADE
        );
    """)

    # O'z-o'zini rivojlantirish va evolyutsiya (XP / Daraja) jadvali
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_evolution (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_type TEXT NOT NULL,
            xp INTEGER DEFAULT 15,
            details TEXT,
            created_at TEXT
        );
    """)

    conn.commit()
    conn.close()

def get_or_create_user(user_id: int, username: str = "", first_name: str = "") -> Dict[str, Any]:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    if not row:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO users (user_id, username, first_name, active_section, created_at) VALUES (?, ?, ?, 'savollar', ?)",
            (user_id, username, first_name, now)
        )
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
    conn.close()
    return dict(row)

def set_active_section(user_id: int, section: str):
    if section not in SECTIONS:
        section = "savollar"
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET active_section = ? WHERE user_id = ?", (section, user_id))
    conn.commit()
    conn.close()

def get_active_section(user_id: int) -> str:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT active_section FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row["active_section"]:
        return row["active_section"]
    return "savollar"

def get_or_create_active_page(user_id: int, section: str) -> Dict[str, Any]:
    """Ushbu bo'limdagi faol sahifani qaytaradi, agar bo'lmasa 1-sahifani yaratadi."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM pages WHERE user_id = ? AND section = ? AND is_active = 1 ORDER BY updated_at DESC LIMIT 1",
        (user_id, section)
    )
    row = cursor.fetchone()

    if not row:
        # Sahifalar sonini hisoblash
        cursor.execute("SELECT COUNT(*) as cnt FROM pages WHERE user_id = ? AND section = ?", (user_id, section))
        cnt = cursor.fetchone()["cnt"] + 1
        sec_title = SECTIONS.get(section, {}).get("title", section.capitalize())
        title = f"{cnt}-Sahifa ({sec_title})"
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cursor.execute(
            "INSERT INTO pages (user_id, section, title, is_active, created_at, updated_at) VALUES (?, ?, ?, 1, ?, ?)",
            (user_id, section, title, now, now)
        )
        conn.commit()
        cursor.execute("SELECT * FROM pages WHERE id = ?", (cursor.lastrowid,))
        row = cursor.fetchone()

    conn.close()
    return dict(row)

def create_new_page(user_id: int, section: str, title: Optional[str] = None) -> Dict[str, Any]:
    """Yangi toza sahifa yaratadi va uni ushbu bo'lim uchun faol qilib belgilaydi."""
    conn = get_connection()
    cursor = conn.cursor()

    # Avvalgi faol sahifalarni is_active = 0 qilish
    cursor.execute("UPDATE pages SET is_active = 0 WHERE user_id = ? AND section = ?", (user_id, section))

    cursor.execute("SELECT COUNT(*) as cnt FROM pages WHERE user_id = ? AND section = ?", (user_id, section))
    cnt = cursor.fetchone()["cnt"] + 1

    sec_title = SECTIONS.get(section, {}).get("title", section.capitalize())
    page_title = title.strip() if title else f"{cnt}-Sahifa"
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute(
        "INSERT INTO pages (user_id, section, title, is_active, created_at, updated_at) VALUES (?, ?, ?, 1, ?, ?)",
        (user_id, section, page_title, now, now)
    )
    conn.commit()
    page_id = cursor.lastrowid
    cursor.execute("SELECT * FROM pages WHERE id = ?", (page_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)

def get_pages_for_section(user_id: int, section: str) -> List[Dict[str, Any]]:
    """Ushbu bo'limdagi barcha sahifalar va ularning xabarlar sonini qaytaradi."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.*, COUNT(m.id) as message_count
        FROM pages p
        LEFT JOIN messages m ON p.id = m.page_id
        WHERE p.user_id = ? AND p.section = ?
        GROUP BY p.id
        ORDER BY p.updated_at DESC
    """, (user_id, section))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]

def set_active_page(user_id: int, page_id: int) -> Optional[Dict[str, Any]]:
    """Mavjud sahifani faol holatga keltiradi."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pages WHERE id = ? AND user_id = ?", (page_id, user_id))
    page = cursor.fetchone()
    if not page:
        conn.close()
        return None

    section = page["section"]
    cursor.execute("UPDATE pages SET is_active = 0 WHERE user_id = ? AND section = ?", (user_id, section))
    cursor.execute("UPDATE pages SET is_active = 1 WHERE id = ?", (page_id,))
    cursor.execute("UPDATE users SET active_section = ? WHERE user_id = ?", (section, user_id))
    conn.commit()

    cursor.execute("SELECT * FROM pages WHERE id = ?", (page_id,))
    updated = cursor.fetchone()
    conn.close()
    return dict(updated)

def get_page_by_id(page_id: int) -> Optional[Dict[str, Any]]:
    """Sahifa ID bo'yicha ma'lumotlarni qaytaradi."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pages WHERE id = ?", (page_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None

def rename_page(page_id: int, user_id: int, new_title: str) -> bool:
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "UPDATE pages SET title = ?, updated_at = ? WHERE id = ? AND user_id = ?",
        (new_title.strip()[:60], now, page_id, user_id)
    )
    affected = cursor.rowcount > 0
    conn.commit()
    conn.close()
    return affected

def clear_page_messages(page_id: int, user_id: int) -> bool:
    """Faqat shu sahifadagi suhbat tarixini tozalaydi."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM pages WHERE id = ?", (page_id,))
    row = cursor.fetchone()
    if not row or row["user_id"] != user_id:
        conn.close()
        return False

    cursor.execute("DELETE FROM messages WHERE page_id = ?", (page_id,))
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("UPDATE pages SET updated_at = ? WHERE id = ?", (now, page_id))
    conn.commit()
    conn.close()
    return True

def delete_page(page_id: int, user_id: int) -> bool:
    """Sahifani va uning barcha xabarlarini butunlay o'chiradi."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pages WHERE id = ? AND user_id = ?", (page_id, user_id))
    page = cursor.fetchone()
    if not page:
        conn.close()
        return False

    section = page["section"]
    was_active = bool(page["is_active"])

    cursor.execute("DELETE FROM messages WHERE page_id = ?", (page_id,))
    cursor.execute("DELETE FROM pages WHERE id = ?", (page_id,))
    conn.commit()

    # Agar o'chirilgan sahifa faol bo'lgan bo'lsa, qolgan sahifalardan birini faol qilish
    if was_active:
        cursor.execute(
            "SELECT id FROM pages WHERE user_id = ? AND section = ? ORDER BY updated_at DESC LIMIT 1",
            (user_id, section)
        )
        remaining = cursor.fetchone()
        if remaining:
            cursor.execute("UPDATE pages SET is_active = 1 WHERE id = ?", (remaining["id"],))
            conn.commit()

    conn.close()
    return True

def add_message(page_id: int, role: str, content: str):
    """Sahifaga yangi xabar qo'shadi va sahifa yangilanish vaqtini o'zgartiradi."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        "INSERT INTO messages (page_id, role, content, created_at) VALUES (?, ?, ?, ?)",
        (page_id, role, content, now)
    )
    cursor.execute("UPDATE pages SET updated_at = ? WHERE id = ?", (now, page_id))
    conn.commit()
    conn.close()

def get_page_messages(page_id: int, limit: int = 16) -> List[Dict[str, Any]]:
    """AI uchun suhbat tarixini oladi."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT role, content, created_at 
        FROM messages 
        WHERE page_id = ? 
        ORDER BY id DESC 
        LIMIT ?
    """, (page_id, limit))
    rows = cursor.fetchall()
    conn.close()
    # Tarix ketma-ketligi to'g'ri bo'lishi uchun teskari tartibda
    return [dict(r) for r in reversed(rows)]

def export_page_text(page_id: int, user_id: int) -> Optional[str]:
    """Sahifadagi barcha xabarlarni chiroyli matn shaklida eksport qiladi."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pages WHERE id = ? AND user_id = ?", (page_id, user_id))
    page = cursor.fetchone()
    if not page:
        conn.close()
        return None

    section_key = page["section"]
    sec_info = SECTIONS.get(section_key, {})
    sec_title = sec_info.get("title", section_key.capitalize())
    icon = sec_info.get("icon", "📄")

    cursor.execute("SELECT role, content, created_at FROM messages WHERE page_id = ? ORDER BY id ASC", (page_id,))
    messages = cursor.fetchall()
    conn.close()

    lines = [
        f"═══════════════════════════════════════════════════════════",
        f"{icon} BO'LIM: {sec_title.upper()}",
        f"📄 SAHIFA: {page['title']}",
        f"🕒 Yaratilgan: {page['created_at']} | Yangilangan: {page['updated_at']}",
        f"💬 Jami xabarlar: {len(messages)} ta",
        f"═══════════════════════════════════════════════════════════\n",
    ]

    for m in messages:
        sender = "👤 Siz" if m["role"] == "user" else f"🤖 Sun'iy Intellekt ({sec_title})"
        lines.append(f"[{m['created_at']}] {sender}:")
        lines.append(f"{m['content']}\n")
        lines.append("-" * 40 + "\n")

    return "\n".join(lines)


def record_evolution(task_type: str, xp: int = 15, details: str = ""):
    """Agent har bir topshiriqni bajarganda tajriba to'playdi va o'zini mukammallashtiradi"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute(
            "INSERT INTO agent_evolution (task_type, xp, details, created_at) VALUES (?, ?, ?, ?)",
            (task_type, xp, details, now)
        )
        conn.commit()
        conn.close()
    except Exception:
        pass


def get_evolution_stats() -> dict:
    """Agentning jami tajribasi (XP), darajasi va bajargan vazifalari"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COALESCE(SUM(xp), 0), COUNT(*) FROM agent_evolution")
        row = cursor.fetchone()
        total_xp = row[0] if row else 0
        total_tasks = row[1] if row else 0
        conn.close()

        level = 1 + (total_xp // 100)
        level_titles = {
            1: "Boshlang'ich Kiber Agent",
            2: "Algoritmik Mutaxassis",
            3: "Avtonom Kiber Sentineli",
            4: "Katta AI Tahlilchisi",
            5: "Grand Kiber Master"
        }
        title = level_titles.get(min(level, 5), "Grand Kiber Master v3")

        return {
            "level": level,
            "title": title,
            "total_xp": total_xp,
            "total_tasks": total_tasks
        }
    except Exception:
        return {"level": 1, "title": "Boshlang'ich Kiber Agent", "total_xp": 0, "total_tasks": 0}

