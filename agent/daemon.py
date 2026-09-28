import time
import os
import sys
import datetime
from pathlib import Path

# Loyiha papkasini PYTHONPATH ga qo'shish
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parent
if str(PROJECT_DIR) not in sys.path:
    sys.path.insert(0, str(PROJECT_DIR))

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from .config import (
    BASE_DIR,
    TASKS_INBOX,
    TASKS_COMPLETED,
    TASKS_RESULTS,
    LOGS_DIR
)
from .logger import logger
from .core import AGENT

PID_FILE = LOGS_DIR / "daemon.pid"

def notify_user(title: str, message: str):
    """Windows tizimida foydalanuvchiga bildirishnoma ko'rsatish (ixtiyoriy PowerShell orqali)."""
    if sys.platform == "win32":
        try:
            ps_script = f"""
            [reflection.assembly]::loadwithpartialname('System.Windows.Forms') | Out-Null
            $notify = New-Object System.Windows.Forms.NotifyIcon
            $notify.Icon = [System.Drawing.SystemIcons]::Information
            $notify.Visible = $true
            $notify.ShowBalloonTip(4000, '{title}', '{message}', [System.Windows.Forms.ToolTipIcon]::Info)
            """
            # Fon jarayonida ishga tushirish
            import subprocess
            subprocess.Popen(["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception:
            pass

def process_task_file(task_path: Path):
    """Inbox papkasidagi vazifa faylini olib, mustaqil bajaradi."""
    try:
        prompt_text = task_path.read_text(encoding="utf-8", errors="replace").strip()
        if not prompt_text:
            task_path.unlink(missing_ok=True)
            return

        task_id = task_path.stem
        start_time = datetime.datetime.now()
        logger.info(f"⚡ [FON AGENTI]: Yangi topshiriq qabul qilindi ({task_id}): '{prompt_text[:80]}'")

        log_lines = [
            f"# Vazifa Hisoboti: {task_id}",
            f"**Qabul qilingan vaqt:** {start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Topshiriq matni:** {prompt_text}",
            "---",
            "## Ijro qadamlari:"
        ]

        final_answer = ""
        step_idx = 0

        # Vazifani qadam-baqadam bajarish
        for event in AGENT.execute_task_stream(prompt_text):
            etype = event.get("type")
            if etype == "step_start":
                step_idx = event.get("step", 1)
            elif etype == "thought":
                th = event.get("text", "")
                log_lines.append(f"\n### 🧠 {step_idx}-Qadam: Tahlil\n> {th}")
                logger.info(f"[{task_id}] Qadam {step_idx}: {th[:100]}")
            elif etype == "tool_call":
                tname = event.get("name")
                args = event.get("args")
                log_lines.append(f"\n⚙️ **Asbob:** `{tname}`\n```json\n{args}\n```")
                logger.info(f"[{task_id}] Asbob chaqirildi: {tname}")
            elif etype == "tool_result":
                res = str(event.get("result", ""))
                disp = res[:1000] + "\n...[qisqartirildi]..." if len(res) > 1000 else res
                log_lines.append(f"\n👁️ **Natija:**\n```\n{disp}\n```")
            elif etype == "final":
                final_answer = event.get("text", "")
                log_lines.append(f"\n---\n## ✨ Yakuniy Xulosa va Natija:\n{final_answer}")

        # Natijani results papkasiga yozish
        result_file = TASKS_RESULTS / f"{task_id}_natija.md"
        result_file.write_text("\n".join(log_lines), encoding="utf-8")

        # Asl topshiriq faylini completed ga ko'chirish
        dest_completed = TASKS_COMPLETED / f"{task_id}_{int(time.time())}.txt"
        task_path.rename(dest_completed)

        end_time = datetime.datetime.now()
        duration = (end_time - start_time).total_seconds()
        logger.info(f"✅ [FON AGENTI]: '{task_id}' vazifasi {round(duration, 1)} soniyada muvaffaqiyatli yakunlandi.")

        notify_user("Antigravity Fon Agenti", f"Topshiriq bajarildi: {task_id}")

    except Exception as e:
        logger.error(f"Topshiriqni bajarishda xatolik ({task_path.name}): {e}")

def run_daemon_loop():
    """Doimiy 24/7 fon xizmati sikli."""
    # PID yozish
    PID_FILE.write_text(str(os.getpid()), encoding="utf-8")
    logger.info(f"🚀 Antigravity Fon Agenti ishga tushdi (PID: {os.getpid()})")
    logger.info(f"Kuzatilayotgan papka: {TASKS_INBOX}")

    try:
        while True:
            # Inbox papkasini tekshirish
            task_files = list(TASKS_INBOX.glob("*.txt")) + list(TASKS_INBOX.glob("*.task"))
            for tf in task_files:
                process_task_file(tf)

            time.sleep(2.0)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Fon agenti to'xtatilmoqda...")
    finally:
        PID_FILE.unlink(missing_ok=True)
        logger.info("Fon agenti to'xtatildi.")

if __name__ == "__main__":
    run_daemon_loop()
