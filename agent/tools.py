import os
import sys
import subprocess
import shutil
import zipfile
import urllib.request
import urllib.parse
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from .config import WORKSPACE_DIR, BASE_DIR, COMMAND_TIMEOUT
from .logger import logger
from .system_info import get_system_report_uz, get_top_processes
from .net_checker import is_online

FILES_TO_SEND: List[str] = []

def get_files_to_send() -> List[str]:
    global FILES_TO_SEND
    files = list(FILES_TO_SEND)
    FILES_TO_SEND = []
    return files

def resolve_path(file_path: str, default_base: Optional[Path] = None) -> Path:
    """Fayl yo'lini aniqlaydi. Agar nisbiy bo'lsa, WORKSPACE_DIR yoki default_base ga nisbatan."""
    p = Path(file_path)
    if not p.is_absolute():
        base = default_base or WORKSPACE_DIR
        p = base / p
    return p.resolve()

def execute_command(command: str, cwd: Optional[str] = None, timeout: Optional[int] = None) -> str:
    """PowerShell yoki CMD konsol buyrug'ini bajaradi. Kompyuter bo'ylab barcha drayverlarda ishlaydi.
    
    Args:
        command: Bajarilishi kerak bo'lgan konsol buyrug'i.
        cwd: Buyruq bajariladigan jild (ixtiyoriy, standart: workspace).
        timeout: Kutish vaqti soniyalarda (standart: 90).
    """
    logger.info(f"Asbob: execute_command -> {command}")
    work_dir = Path(cwd).resolve() if cwd else WORKSPACE_DIR
    if not work_dir.exists():
        work_dir = BASE_DIR

    to_use = timeout or COMMAND_TIMEOUT
    try:
        is_windows = sys.platform == "win32"
        if is_windows:
            shell_cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command]
        else:
            shell_cmd = ["bash", "-c", command]

        process = subprocess.run(
            shell_cmd,
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=to_use,
            encoding="utf-8",
            errors="replace"
        )
        output = process.stdout
        if process.stderr:
            output += "\n[STDERR]:\n" + process.stderr

        if not output.strip():
            output = f"[Muvaffaqiyatli bajarildi (kod: {process.returncode}), konsol chiqishi bo'sh]"

        if len(output) > 6000:
            output = output[:3000] + "\n... [Chiqish uzunligi sababli o'rtasi qisqartirildi] ...\n" + output[-3000:]

        return output.strip()
    except subprocess.TimeoutExpired:
        return f"[XATOLIK]: Buyruq berilgan vaqt ({to_use}s) ichida tugamadi."
    except Exception as e:
        return f"[XATOLIK]: {str(e)}"

def execute_python(code: str, cwd: Optional[str] = None) -> str:
    """Python kodini alohida jarayonda bajaradi va natijasini oladi.
    
    Args:
        code: Bajarilishi kerak bo'lgan Python kodi.
        cwd: Bajariladigan jild (ixtiyoriy).
    """
    logger.info("Asbob: execute_python kod bajarilmoqda")
    work_dir = Path(cwd).resolve() if cwd else WORKSPACE_DIR
    try:
        process = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(work_dir),
            capture_output=True,
            text=True,
            timeout=COMMAND_TIMEOUT,
            encoding="utf-8",
            errors="replace"
        )
        out = process.stdout
        if process.stderr:
            out += "\n[XATOLIK/STDERR]:\n" + process.stderr

        if not out.strip():
            out = "[Kod muvaffaqiyatli bajarildi, chiqish bo'sh]"

        if len(out) > 6000:
            out = out[:3000] + "\n... [Chiqish qisqartirildi] ...\n" + out[-3000:]
        return out.strip()
    except subprocess.TimeoutExpired:
        return f"[XATOLIK]: Python kodi belgilangan vaqt ({COMMAND_TIMEOUT}s) ichida tugamadi."
    except Exception as e:
        return f"[XATOLIK]: {str(e)}"

def read_file(file_path: str, max_chars: int = 10000) -> str:
    """Fayl ichidagi matnni o'qiydi.
    
    Args:
        file_path: O'qilishi kerak bo'lgan fayl yo'li (masalan 'D:/hujjat.txt' yoki 'app.py').
        max_chars: O'qiladigan maksimal belgilar soni.
    """
    logger.info(f"Asbob: read_file -> {file_path}")
    try:
        p = resolve_path(file_path)
        if not p.exists():
            return f"[XATOLIK]: '{file_path}' fayli topilmadi."
        if not p.is_file():
            return f"[XATOLIK]: '{file_path}' fayl emas, balki papka."

        # Har xil kodlashlarni qo'llab-quvvatlash
        content = None
        for enc in ["utf-8", "cp1251", "latin-1"]:
            try:
                content = p.read_text(encoding=enc)
                break
            except UnicodeDecodeError:
                continue

        if content is None:
            content = p.read_text(encoding="utf-8", errors="replace")

        if len(content) > max_chars:
            content = content[:max_chars//2] + f"\n... [Fayl hajmi katta ({len(content)} belgi), qisqartirildi] ...\n" + content[-max_chars//2:]
        return content
    except Exception as e:
        return f"[XATOLIK]: {str(e)}"

def write_file(file_path: str, content: str, append: bool = False) -> str:
    """Faylga matn yoki kod yozadi (yaratadi yoki yangilaydi).
    
    Args:
        file_path: Fayl yo'li yoki nomi.
        content: Yoziladigan matn yoki kod.
        append: Agar True bo'lsa, fayl oxiriga qo'shadi. False bo'lsa, to'liq yangilaydi.
    """
    logger.info(f"Asbob: write_file -> {file_path} (append={append})")
    try:
        p = resolve_path(file_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        mode = "a" if append else "w"
        with open(p, mode, encoding="utf-8") as f:
            f.write(content)
        status = "oxiriga qo'shildi" if append else "saqlandi"
        return f"[Muvaffaqiyatli]: '{p.name}' fayli {status} ({len(content)} belgi, Manzil: {p})."
    except Exception as e:
        return f"[XATOLIK]: {str(e)}"

def list_directory(path: str = ".") -> str:
    """Papkadagi fayllar va jildlar ro'yxatini batafsil ko'rsatadi.
    
    Args:
        path: Ko'rilishi kerak bo'lgan papka yo'li (masalan 'D:/' yoki 'D:/agent').
    """
    logger.info(f"Asbob: list_directory -> {path}")
    try:
        p = resolve_path(path)
        if not p.exists():
            return f"[XATOLIK]: '{path}' papkasi mavjud emas."
        if not p.is_dir():
            return f"[XATOLIK]: '{path}' papka emas, balki fayl."

        items = []
        dirs_count = 0
        files_count = 0
        for item in sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower())):
            if item.name.startswith("$") or item.name == "System Volume Information":
                continue
            if item.is_dir():
                dirs_count += 1
                items.append(f"📁 [PAPKA]  {item.name}/")
            else:
                files_count += 1
                size = item.stat().st_size
                if size < 1024:
                    s_str = f"{size} B"
                elif size < 1024*1024:
                    s_str = f"{round(size/1024, 1)} KB"
                else:
                    s_str = f"{round(size/(1024*1024), 1)} MB"
                items.append(f"📄 [FAYL]   {item.name} ({s_str})")

        header = f"📂 Manzil: `{p}` (Jami: {dirs_count} papka, {files_count} fayl)\n"
        if not items:
            return header + "Papka bo'sh."
        return header + "\n".join(items[:100])
    except Exception as e:
        return f"[XATOLIK]: {str(e)}"

def search_files(pattern: str, path: str = ".", recursive: bool = True, max_results: int = 50) -> str:
    """Fayllarni nomi yoki kengaytmasi bo'yicha tezkor qidiradi (masalan '*.txt', '*video*', '*.py').
    
    Args:
        pattern: Qidiruv shabloni (masalan '*.pdf', 'hujjat*').
        path: Qidiruv boshlanadigan manzil.
        recursive: Ichki papkalardan ham qidirish (True/False).
        max_results: Maksimal natijalar soni.
    """
    logger.info(f"Asbob: search_files -> {pattern} in {path}")
    try:
        p = resolve_path(path)
        if not p.exists():
            return f"[XATOLIK]: '{path}' topilmadi."

        results = []
        glob_fn = p.rglob if recursive else p.glob
        for found in glob_fn(pattern):
            if found.name.startswith("$") or "System Volume Information" in str(found):
                continue
            is_dir = "📁" if found.is_dir() else "📄"
            results.append(f"{is_dir} {found}")
            if len(results) >= max_results:
                break

        if not results:
            return f"'{pattern}' shabloni bo'yicha hech qanday fayl topilmadi."
        return f"🔍 '{pattern}' bo'yicha topilgan fayllar ({len(results)} ta):\n" + "\n".join(results)
    except Exception as e:
        return f"[XATOLIK]: {str(e)}"

def get_system_stats() -> str:
    """Kompyuterning to'liq texnik holati (CPU, RAM, Disklar, Jarayonlar, Tarmoq) hisobotini qaytaradi."""
    logger.info("Asbob: get_system_stats chaqirildi")
    try:
        return get_system_report_uz()
    except Exception as e:
        return f"[XATOLIK]: {str(e)}"

def manage_process(action: str = "list", target: Optional[str] = None) -> str:
    """Kompyuterdagi jarayonlarni nazorat qilish (ko'rish yoki to'xtatish).
    
    Args:
        action: 'list' (ko'rish) yoki 'kill' (to'xtatish).
        target: Jarayon nomi yoki PID raqami (agar kill bo'lsa).
    """
    logger.info(f"Asbob: manage_process -> {action} target={target}")
    try:
        if action == "list":
            procs = get_top_processes(limit=12, sort_by="memory")
            lines = ["📊 **Eng ko'p xotira (RAM) sarflayotgan jarayonlar:**"]
            for p in procs:
                lines.append(f"• PID: `{p['pid']}` | Nomi: `{p['name']}` | RAM: {p['mem_mb']} MB | CPU: {p['cpu']}%")
            return "\n".join(lines)
        elif action == "kill" and target:
            if target.isdigit():
                cmd = f"Stop-Process -Id {target} -Force"
            else:
                cmd = f"Stop-Process -Name '{target.replace('.exe', '')}' -Force"
            return execute_command(cmd)
        else:
            return "[XATOLIK]: Noto'g'ri amal yoki maqsad ko'rsatilmadi."
    except Exception as e:
        return f"[XATOLIK]: {str(e)}"

def open_application(app_or_path: str) -> str:
    """Kompyuterda dastur, papka yoki faylni ochadi (masalan: 'calc', 'notepad', 'explorer D:\\').
    
    Args:
        app_or_path: Ochilishi kerak bo'lgan dastur nomi yoki fayl/papka manzili.
    """
    logger.info(f"Asbob: open_application -> {app_or_path}")
    try:
        if sys.platform == "win32":
            os.startfile(app_or_path)
            return f"[Muvaffaqiyatli]: '{app_or_path}' ishga tushirildi."
        else:
            subprocess.Popen(["xdg-open", app_or_path])
            return f"[Muvaffaqiyatli]: '{app_or_path}' ochildi."
    except Exception as e:
        # Fallback to powershell Start-Process
        try:
            res = execute_command(f"Start-Process '{app_or_path}'")
            return f"Ishga tushirish natijasi: {res}"
        except Exception as e2:
            return f"[XATOLIK]: {str(e)} / {str(e2)}"

def zip_folder(source_folder: str, output_zip: Optional[str] = None) -> str:
    """Papkani zip arxiv shaklida arxivlaydi.
    
    Args:
        source_folder: Arxivlanadigan papka.
        output_zip: Yaratiladigan zip fayl nomi yoki manzili.
    """
    logger.info(f"Asbob: zip_folder -> {source_folder}")
    try:
        src = resolve_path(source_folder)
        if not src.exists() or not src.is_dir():
            return f"[XATOLIK]: '{source_folder}' papkasi topilmadi."

        if not output_zip:
            out_file = src.parent / f"{src.name}.zip"
        else:
            out_file = resolve_path(output_zip)
            if not out_file.name.endswith(".zip"):
                out_file = out_file.with_suffix(".zip")

        shutil.make_archive(str(out_file.with_suffix('')), 'zip', str(src))
        return f"[Muvaffaqiyatli]: Papka arxivlandi: {out_file} ({round(out_file.stat().st_size / 1024, 1)} KB)"
    except Exception as e:
        return f"[XATOLIK]: {str(e)}"

def fetch_webpage(url: str) -> str:
    """Internetdan veb sahifa matnini yuklaydi (faqat internet mavjud bo'lganda ishlaydi).
    
    Args:
        url: Veb sahifa manzili (http:// yoki https://).
    """
    logger.info(f"Asbob: fetch_webpage -> {url}")
    if not is_online():
        return "[XATOLIK]: Hozirda internet tarmog'i mavjud emas. Internetsiz lokal rejimda ishlamoqdasiz."

    try:
        req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=15) as response:
            html = response.read().decode("utf-8", errors="replace")

        clean_text = re.sub(r'<script.*?</script>', '', html, flags=re.DOTALL | re.IGNORECASE)
        clean_text = re.sub(r'<style.*?</style>', '', clean_text, flags=re.DOTALL | re.IGNORECASE)
        clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
        clean_text = re.sub(r'\s+', ' ', clean_text).strip()

        if len(clean_text) > 5000:
            clean_text = clean_text[:2500] + "\n... [Matn qisqartirildi] ...\n" + clean_text[-2500:]
        return clean_text
    except Exception as e:
        return f"[XATOLIK veb sahifani yuklashda]: {str(e)}"

def search_web(query: str) -> str:
    """Internetdan ma'lumot qidiradi (DuckDuckGo orqali, internet kerak).
    
    Args:
        query: Qidiruv so'zi yoki savol.
    """
    logger.info(f"Asbob: search_web -> {query}")
    if not is_online():
        return "[XATOLIK]: Internet mavjud emas. Lokal rejimda qidiruv faqat kompyuter ichidagi fayllarda ishlaydi (`search_files`)."

    try:
        encoded = urllib.parse.quote_plus(query)
        url = f"https://html.duckduckgo.com/html/?q={encoded}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        with urllib.request.urlopen(req, timeout=12) as resp:
            content = resp.read().decode("utf-8", errors="replace")

        # Natija snippetlarini ajratish
        snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', content, flags=re.DOTALL)
        titles = re.findall(r'<a class="result__url[^>]*>(.*?)</a>', content, flags=re.DOTALL)

        results = []
        for i in range(min(5, len(snippets))):
            s_clean = re.sub(r'<[^>]+>', '', snippets[i]).strip()
            results.append(f"{i+1}. {s_clean}")

        if not results:
            return "Qidiruv bo'yicha ma'lumot topilmadi yoki tarmoq bloklandi."
        return "\n\n".join(results)
    except Exception as e:
        return f"[Qidiruv xatoligi]: {str(e)}"

def send_file_to_telegram(file_path: str) -> str:
    """Yaratilgan faylni foydalanuvchining Telegramiga yuborish uchun belgilaydi."""
    logger.info(f"Asbob: send_file_to_telegram -> {file_path}")
    p = resolve_path(file_path)
    if not p.exists() or not p.is_file():
        return f"[XATOLIK]: '{file_path}' fayli topilmadi."
    FILES_TO_SEND.append(str(p))
    return f"[Muvaffaqiyatli]: '{file_path}' Telegramga yuborish uchun belgilandi."

def record_learning(lesson: str, category: str = "tajriba") -> str:
    """Agent o'zining xatolaridan, tajribasidan yoki foydalanuvchi ko'rsatmasidan olingan saboqni doimiy xotirasiga yozib qo'yadi.
    
    Args:
        lesson: O'rganilgan muhim xulosa, qoida yoki saboq.
        category: Saboq yo'nalishi (masalan: 'windows_apps', 'dasturlash', 'xatolik', 'foydalanuvchi_odati').
    """
    from .evolution.memory_manager import memory_manager
    return memory_manager.record_learning(lesson, category)

def create_skill(name: str, description: str, triggers: list, instructions: str, script_code: str = "") -> str:
    """Agent yangi soha yoki murakkab mavzuni to'liq o'zlashtirganda, o'ziga yangi Skill (ko'nikma) yaratadi.
    
    Args:
        name: Ko'nikma nomi (masalan: 'telegram_bot_creator', 'excel_analyzer').
        description: Ko'nikma nima haqida ekanligi.
        triggers: Ushbu ko'nikma ishga tushadigan kalit so'zlar ro'yxati (masalan: ['excel', 'jadval']).
        instructions: Qadam-baqadam to'liq yo'riqnoma va algoritm.
        script_code: Kerak bo'lsa yordamchi Python kodi.
    """
    from .evolution.skills_manager import skills_manager
    return skills_manager.create_or_update_skill(name, description, triggers, instructions, script_code or None)

def read_skill(name: str) -> str:
    """Mavjud maxsus ko'nikma (Skill) bo'yicha to'liq yo'riqnomani o'qiydi.
    
    Args:
        name: O'qilishi kerak bo'lgan ko'nikma nomi.
    """
    from .evolution.skills_manager import skills_manager
    skill = skills_manager.get_skill(name)
    if not skill:
        return f"[XATOLIK]: '{name}' nomli ko'nikma topilmadi."
    return f"📖 Ko'nikma: {skill['name']}\n🎯 Tavsif: {skill['description']}\n\n📋 Yo'riqnoma:\n{skill['instructions']}"

def create_custom_tool(name: str, code: str, description: str) -> str:
    """Agent o'z imkoniyatlarini kengaytirish uchun yangi Python asbobi (funksiya) yaratadi va o'ziga darhol ulab oladi.
    
    Args:
        name: Funksiya nomi (masalan: 'clean_phone_cache_instructions', 'convert_audio_wav').
        code: Funksiyaning to'liq Python kodi.
        description: Funksiya nima qilishi haqida tavsif.
    """
    from .evolution.custom_tools_manager import custom_tools_manager
    return custom_tools_manager.create_custom_tool(name, code, description)

def inspect_self() -> str:
    """Agent o'zining butun ichki tuzilishi, o'rgangan saboqlari, faol ko'nikmalari va asboblarini ko'zdan kechiradi."""
    from .evolution.self_evolver import self_evolver
    return self_evolver.format_inspection_report()

def invoke_subagent(role: str, task: str) -> str:
    """Antigravity kabi alohida ixtisoslashgan yordamchi subagentni (masalan: 'Dasturchi', 'Kod Tekshiruvchi', 'Tadqiqotchi') ishga tushiradi.
    
    Args:
        role: Subagentning ixtisoslashgan roli.
        task: Subagent bajarishi kerak bo'lgan aniq vazifa.
    """
    from .evolution.subagent_manager import subagent_manager
    return subagent_manager.invoke_subagent(role, task)

# Barcha asboblar ro'yxati
AGENT_TOOLS = [
    execute_command,
    execute_python,
    read_file,
    write_file,
    list_directory,
    search_files,
    get_system_stats,
    manage_process,
    open_application,
    zip_folder,
    fetch_webpage,
    search_web,
    send_file_to_telegram,
    # O'z-o'zini rivojlantirish (Evolution) asboblari:
    record_learning,
    create_skill,
    read_skill,
    create_custom_tool,
    inspect_self,
    invoke_subagent
]
