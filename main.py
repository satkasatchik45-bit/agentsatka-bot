import sys
import os
import asyncio
from pathlib import Path

# Loyiha papkasini PYTHONPATH ga qo'shish
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

# Windows konsolida UTF-8 va emojilar xatosiz ishlashi uchun
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

def main():
    args = sys.argv[1:]

    # 1. Telegram bot rejimida ishga tushirish: python main.py --bot
    if "--bot" in args:
        from agent.config import TELEGRAM_BOT_TOKEN
        from agent.bot import start_bot
        from agent.logger import logger
        if not TELEGRAM_BOT_TOKEN:
            print("❌ XATOLIK: .env faylida TELEGRAM_BOT_TOKEN kiritilmagan.")
            return
        logger.info("Telegram bot ishga tushmoqda...")
        asyncio.run(start_bot())
        return

    # 2. Fon rejimida monitoring: python main.py --daemon
    if "--daemon" in args:
        from agent.daemon import run_daemon_loop
        run_daemon_loop()
        return

    # 3. Tizim holatini ko'rish: python main.py --status
    if "--status" in args:
        from agent.system_info import get_system_report_uz
        print(get_system_report_uz())
        return

    # 4. Fon agentiga topshiriq yuborish: python main.py do "vazifa matni"
    if len(args) > 0 and args[0].lower() == "do":
        import datetime
        from agent.config import TASKS_INBOX
        task_text = " ".join(args[1:]).strip()
        if not task_text:
            print("❌ Iltimos, topshiriq matnini kiriting. Masalan: agent do \"D diskni tekshir\"")
            return
        now_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        task_file = TASKS_INBOX / f"vazifa_{now_str}.txt"
        task_file.write_text(task_text, encoding="utf-8")
        print(f"📥 [Muvaffaqiyatli]: Topshiriq fon agentiga yuborildi: {task_file.name}")
        print("💡 Fon agenti ushbu topshiriqni orqa fonda bajaradi va natijani D:\\agent\\tasks\\results ga yozadi.")
        return

    # 5. Standart holat: Qora oynadagi interaktiv Terminal CLI (Qadam-baqadam ko'rsatuvchi dastur)
    from agent.cli import main as cli_main
    cli_main()

if __name__ == "__main__":
    main()
