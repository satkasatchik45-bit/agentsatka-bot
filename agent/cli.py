import sys
import os
import time
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown
from rich.prompt import Prompt
from rich.text import Text

from .core import AGENT
from .config import BASE_DIR, WORKSPACE_DIR, MODEL_NAME
from .net_checker import get_connection_details
from .system_info import get_system_report_uz, get_top_processes
from .tools import list_directory

console = Console(highlight=True)

def set_terminal_title(title: str):
    """Windows konsol sarlavhasini o'rnatish."""
    if sys.platform == "win32":
        try:
            os.system(f"title {title}")
        except Exception:
            pass

def print_banner():
    """Konsol boshlang'ich sarlavhasi (Banner)."""
    conn = get_connection_details()
    mode_info = AGENT.get_current_mode()

    banner_text = Text()
    banner_text.append("🤖  ANTIGRAVITY AVTONOM BOSHQARUV AGENTI\n", style="bold cyan")
    banner_text.append("Shaxsiy kompyuterni mustaqil boshqarish va avtomatlashtirish tizimi\n", style="italic white")
    banner_text.append("—"*68 + "\n", style="dim")
    banner_text.append(f"🌐 Tarmoq: {conn['status_uz']}  |  ", style="bold")
    banner_text.append(f"🧠 Miya: {mode_info['label']}\n", style="bold yellow")
    banner_text.append(f"📁 Ishchi papka: {WORKSPACE_DIR}  |  OS: {sys.platform.upper()}", style="dim")

    console.print(Panel(
        banner_text,
        border_style="bright_blue",
        title="[bold green]Terminal CLI v2.0[/bold green]",
        subtitle="[dim]O'zbekiston / Antigravity Engine[/dim]"
    ))

def print_help():
    """Yordam va foydalanish bo'yicha namunalar."""
    help_md = """
### 💡 Agentga berishingiz mumkin bo'lgan buyruqlar namunalari:

1. **Kompyuter holati va diagnostika:**
   - `kompyuterimning tizim holatini tekshir`
   - `disklarimda qancha bo'sh joy bor?`
   - `eng ko'p xotira yeyotgan dasturlarni ko'rsat`

2. **Fayllar va jildlar bilan ishlash:**
   - `D diskdagi barcha rasmlarni topib ber`
   - `workspace papkasida loyiha nomli yangi papka och`
   - `D:/agent/README.md faylini o'qib ber`
   - `D diskda bugungi rejalar nomli fayl yarat`
   - `D:/agent papkasini arxivlab zip qilib ber`

3. **Terminal va dasturlarni boshqarish:**
   - `powershell: Get-Process | Select-Object -First 10`
   - `kalkulyatorni och` yoki `bloknotni och`
   - `notepad jarayonini to'xtat`

4. **Dasturlash va hisob-kitoblar:**
   - `100 gacha bo'lgan tub sonlarni hisoblovchi Python kod yoz va ishga tushir`
   - `(125 * 45) / 12 hisoblab ber`

5. **Internet va axborot (Internet yoqilganda):**
   - `Toshkentdagi ob-havo haqida ma'lumot top`
   - `https://google.com sahifasini tekshir`

### ⚙️ Maxsus konsol buyruqlari:
- `/help`    — Ushbu qo'llanmani chiqarish
- `/status`  — Kompyuterning batafsil texnik parametrlari
- `/top`     — Eng ko'p RAM iste'mol qiluvchi jarayonlar
- `/mode`    — Hozirgi intellekt rejimini ko'rish
- `/clear`   — Konsol oynasini tozalash
- `/exit`    — Dasturdan chiqish
"""
    console.print(Panel(Markdown(help_md), title="[bold yellow]📖 Qo'llanma[/bold yellow]", border_style="yellow"))

def show_status():
    """Kompyuter holatini konsolda chiroyli chiqarish."""
    with console.status("[bold cyan]Tizim parametrlari o'qilmoqda...[/bold cyan]", spinner="dots"):
        rep = get_system_report_uz()
    console.print(Panel(Markdown(rep), title="[bold green]🖥️ Kompyuter Texnik Holati[/bold green]", border_style="green"))

def show_top_procs():
    """Eng ko'p resurs iste'mol qiluvchi jarayonlar jadvali."""
    with console.status("[bold cyan]Jarayonlar skanerlanmoqda...[/bold cyan]", spinner="dots"):
        procs = get_top_processes(limit=12)

    table = Table(title="📊 Eng ko'p RAM sarflayotgan dasturlar", border_style="cyan")
    table.add_column("PID", style="dim", justify="right")
    table.add_column("Dastur nomi", style="bold white")
    table.add_column("RAM (MB)", justify="right", style="bold magenta")
    table.add_column("CPU %", justify="right", style="bold green")

    for p in procs:
        table.add_row(str(p["pid"]), p["name"], f"{p['mem_mb']} MB", f"{p['cpu']}%")

    console.print(table)

def execute_cli_task(prompt_text: str):
    """Topshiriqni qadam-baqadam konsolda vizual ko'rsatib bajarish."""
    console.print()
    console.print(f"[bold cyan]🎯 Vazifa:[/bold cyan] [white]{prompt_text}[/white]")
    console.print("—"*68, style="dim")

    step_counter = 0

    for event in AGENT.execute_task_stream(prompt_text):
        etype = event.get("type")

        if etype == "mode_info":
            minfo = event["mode"]
            console.print(f"[dim]Rejim: {minfo['label']}[/dim]")

        elif etype == "step_start":
            step_counter = event.get("step", 1)

        elif etype == "thought":
            thought_text = event.get("text", "")
            console.print(Panel(
                Text(thought_text, style="italic yellow"),
                title=f"[bold yellow]🧠 {step_counter}-Qadam: Tahlil va Reja[/bold yellow]",
                border_style="yellow",
                padding=(0, 1)
            ))

        elif etype == "tool_call":
            fn_name = event.get("name", "")
            fn_args = event.get("args", {})
            args_str = ", ".join(f"{k}='{v}'" if isinstance(v, str) else f"{k}={v}" for k, v in fn_args.items())
            console.print(Panel(
                f"[bold white]Asbob:[/bold white] [bold cyan]{fn_name}[/bold cyan]\n[dim]Parametrlar: ({args_str})[/dim]",
                title="[bold cyan]⚙️ Asbob chaqiruvi[/bold cyan]",
                border_style="cyan",
                padding=(0, 1)
            ))

        elif etype == "tool_result":
            fn_name = event.get("name", "")
            res = str(event.get("result", ""))
            disp = res if len(res) <= 1200 else res[:600] + "\n... [Chiqish qisqartirildi] ...\n" + res[-400:]
            console.print(Panel(
                disp,
                title=f"[dim]👁️ Asbob natijasi ({fn_name})[/dim]",
                border_style="dim",
                padding=(0, 1)
            ))

        elif etype == "final":
            final_text = event.get("text", "")
            console.print()
            console.print(Panel(
                Markdown(final_text),
                title="[bold green]✨ YAKUNIY JAVOB VA NATIJA[/bold green]",
                border_style="green",
                padding=(1, 2)
            ))

            files = event.get("files", [])
            if files:
                console.print("[bold cyan]📎 Yaratilgan fayllar:[/bold cyan]")
                for f in files:
                    console.print(f"  • [green]{f}[/green]")

    console.print()

def main():
    """Asosiy CLI interaktiv konsol sikli."""
    set_terminal_title("Antigravity AI Agent [Terminal CLI - O'zbekiston]")

    # Agar argument berilgan bo'lsa (masalan: python -m agent.cli "vazifa")
    if len(sys.argv) > 1:
        single_task = " ".join(sys.argv[1:]).strip()
        print_banner()
        execute_cli_task(single_task)
        return

    # Interaktiv rejim
    print_banner()
    console.print("[dim]Yordam uchun [/dim][bold yellow]/help[/bold yellow][dim], chiqish uchun [/dim][bold red]/exit[/bold red][dim] yoki 'chiqish' deb yozing.[/dim]\n")

    while True:
        try:
            user_input = Prompt.ask(
                Text("Antigravity (D:\\agent) ❯", style="bold bright_green")
            ).strip()

            if not user_input:
                continue

            # Buyruqlarni tekshirish
            cmd_lower = user_input.lower()
            if cmd_lower in ["/exit", "exit", "quit", "chiqish", "tamom"]:
                console.print("[bold green]Agent faoliyati yakunlandi. Xayr![/bold green] 👋")
                break
            elif cmd_lower in ["/clear", "cls", "clear", "tozala"]:
                os.system("cls" if sys.platform == "win32" else "clear")
                print_banner()
                continue
            elif cmd_lower in ["/help", "help", "yordam", "?"]:
                print_help()
                continue
            elif cmd_lower in ["/status", "status", "holat"]:
                show_status()
                continue
            elif cmd_lower in ["/top", "top", "jarayonlar"]:
                show_top_procs()
                continue
            elif cmd_lower in ["/mode", "mode", "rejim"]:
                curr = AGENT.get_current_mode()
                console.print(f"Hozirgi faol rejim: [bold yellow]{curr['label']}[/bold yellow] (Online: {curr['is_online']})")
                continue

            # Vazifani qadam-baqadam bajarish
            execute_cli_task(user_input)

        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold yellow]Amal bekor qilindi. Chiqish uchun /exit yozing.[/bold yellow]")
        except Exception as e:
            console.print(f"[bold red]Kutilmagan xatolik:[/bold red] {e}")

if __name__ == "__main__":
    main()
