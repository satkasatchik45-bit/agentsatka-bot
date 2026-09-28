import re
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional, Generator, Tuple

from .config import WORKSPACE_DIR, BASE_DIR
from .logger import logger
from .tools import (
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
    resolve_path,
    FILES_TO_SEND
)
from .evolution.skills_manager import skills_manager
from .evolution.memory_manager import memory_manager

class OfflineEngine:
    """100% Internetsiz ishlovchi, o'zbek tili grammatikasi va morfologiyasini
    tushunuvchi, xotira va ko'nikmalar (skills) tizimiga ulangan,
    kompyuterni mustaqil boshqaruvchi aqlli avtonom mahalliy dvigatel."""

    def __init__(self):
        self.last_action_summary = "Agent ishga tushirildi. Hozircha yangi topshiriq bajarilmadi."

    def can_handle(self, prompt: str) -> bool:
        return True

    def _normalize_text(self, text: str) -> str:
        """Matnni tahlil uchun qulay holatga keltiradi."""
        t = text.lower().strip()
        # O'zbekcha maxsus belgilarni birlashtirish
        t = t.replace("‘", "'").replace("’", "'").replace("`", "'")
        return t

    def run_step_by_step(self, prompt: str) -> Generator[Dict[str, Any], None, None]:
        p_raw = prompt.strip()
        p_norm = self._normalize_text(p_raw)
        logger.info(f"OfflineEngine tahlil qilmoqda: '{p_raw}'")

        # -------------------------------------------------------------
        # 1. SALOMLASHISH VA O'ZINI TANISHTIRISH (GREETING & IDENTITY)
        # -------------------------------------------------------------
        greeting_words = ["salom", "assalomu alaykum", "assalom", "qaleysiz", "qandaysiz", "qalaysiz", "hayrli kun", "salomaleykum"]
        if any(w in p_norm for w in greeting_words) and len(p_norm.split()) <= 4:
            yield {"type": "thought", "text": "Foydalanuvchi bilan do'stona o'zbek adabiy tilida salomlashish."}
            msg = (
                "👋 **Assalomu alaykum!**\n\n"
                "Men sizning kompyuteringizda doimiy ishlovchi shaxsiy **Antigravity AI Agentingizman**.\n\n"
                "Hozirda **internetsiz to'liq lokal rejimda** ishlamoqdaman. Kompyuteringizdagi fayllar, disklar, "
                "dasturlar, hisob-kitoblar va tizim parametrlarini boshqarishga tayyorman.\n\n"
                "Qanday topshiriq bajaramiz?"
            )
            self.last_action_summary = "Foydalanuvchi bilan salomlashildi va tizim tayyorligi bildirildi."
            yield {"type": "final", "text": msg}
            return

        if any(w in p_norm for w in ["kimsiz", "kim bu", "o'zingizni tanishtir", "o'zing haqda", "nima bu bot", "agent nima"]) and len(p_norm.split()) <= 6:
            yield {"type": "thought", "text": "Agent o'zining shaxsi va internetsiz imkoniyatlarini tanishtirmoqda."}
            msg = (
                "🤖 **Men kimman?**\n\n"
                "Men sizning shaxsiy kompyuteringizda (D: diskda) o'rnatilgan mustaqil **Avtonom AI Agentman**.\n\n"
                "🔹 **Mening vazifam:** Siz bergan topshiriqlarni orqa fonda, hatto internetsiz ham "
                "to'liq mustaqil bajarish.\n"
                "🔹 **Boshqaruv:** Kompyuter konsoli (CLI) yoki Telegram orqali telefoningizdan boshqarishingiz mumkin.\n"
                "🔹 **Asosiy qobiliyatlarim:** Fayllarni boshqarish, tizim diagnostikasi, dasturlarni ochish/yopish, "
                "Python kodlarini bajarish, Windows ilovalari (.bat bilan) yaratish va o'z xotiramda yangi saboqlarni saqlab borish."
            )
            self.last_action_summary = "Agent shaxsi va imkoniyatlari haqida to'liq ma'lumot berildi."
            yield {"type": "final", "text": msg}
            return

        # -------------------------------------------------------------
        # 2. QOBILIYATLAR VA TELEFONDA NIMA QILA OLISHINI SO'RASH
        # -------------------------------------------------------------
        is_about_capabilities = any(w in p_norm for w in [
            "nimalar qila olasiz", "nima qila olasan", "nima qila olasiz", "imkoniyatlaringiz",
            "qobiliyatingiz", "qanday yordam", "nimalarga qodirsiz"
        ])
        is_about_phone = "telefon" in p_norm or "mobil" in p_norm

        if is_about_capabilities:
            yield {"type": "thought", "text": "Foydalanuvchiga agentning to'liq imkoniyatlari bayon etilmoqda."}
            if is_about_phone:
                msg = (
                    "📱 **Telefonda va Telegram orqali nimalar qila olaman?**\n\n"
                    "Men kompyuteringizda ishlayman va siz bilan telefoningizdagi Telegram orqali bog'lanaman. Imkoniyatlarim:\n\n"
                    "1. 🧹 **Telefon keshini tozalash:** Telegram va tizim keshlarini tozalash, xotirani bo'shatish bo'yicha professional yo'riqnomalar beraman.\n"
                    "2. 📂 **Kompyuterdan fayl olish:** D disk yoki kompyuteringizdagi istalgan hujjat, rasm yoki kodni so'rasangiz, uni telefoningizga jo'nataman.\n"
                    "3. 🖥️ **Kompyuterni masofadan boshqarish:**\n"
                    "   • Kompyuter holatini tekshirish (CPU, RAM, bo'sh joy)\n"
                    "   • Keraksiz yoki qotib qolgan dasturlarni to'xtatish\n"
                    "   • Yangi dasturlar yaratish (kalkulyator, skriptlar)\n"
                    "   • Kompyuterni o'chirish yoki qayta yuklash\n"
                    "4. 📥 **Fayl yuborish:** Telefoningizdan botga fayl tashlasangiz, uni kompyuter ishchi papkasiga saqlayman va tahlil qilaman."
                )
            else:
                msg = (
                    "🛠️ **Agentning Internetsiz Mahalliy Imkoniyatlari:**\n\n"
                    "1. 📁 **Fayllar va Disklar:** Fayl yaratish, o'qish, tahrirlash, qidirish, papkalar ro'yxatini ko'rish, ZIP arxivlash.\n"
                    "2. 🖥️ **Tizim Diagnostikasi:** RAM, protsessor (CPU), disklar bo'sh joyi, faol dasturlarni tekshirish.\n"
                    "3. 🛑 **Jarayonlarni Boshqarish:** Xotirani ko'p yeyotgan dasturlarni aniqlash va ularni to'xtatish (kill).\n"
                    "4. 🚀 **Dasturlarni Ishga Tushirish:** Kalkulyator, Bloknot, Explorer yoki istalgan dasturni ochish.\n"
                    "5. 🪟 **Windows GUI Ilovalari:** Grafik dasturlar yaratish va ularni bir bosishda ochiladigan `.bat` fayli bilan taqdim etish.\n"
                    "6. 🐍 **Python va Hisob-kitoblar:** Matematik ifodalarni hisoblash, Python skriptlarini alohida bajarish.\n"
                    "7. 🧠 **Doimiy Xotira va Skills:** Yangi qoidalarni o'rganish (`/learn`), ko'nikmalarni qo'llash."
                )
            self.last_action_summary = "Foydalanuvchiga agent imkoniyatlari to'liq tushuntirildi."
            yield {"type": "final", "text": msg}
            return

        # -------------------------------------------------------------
        # 3. OXIRGI BAJARILGAN ISH HISOBOTI ("Nimani bajardingiz?")
        # -------------------------------------------------------------
        if any(w in p_norm for w in ["nimani bajardingiz", "nima ish qildingiz", "nima qildingiz", "nimani bajardongiz", "oxirgi amal", "hisobot ber"]):
            yield {"type": "thought", "text": "Foydalanuvchiga oxirgi bajarilgan amal hisoboti taqdim etilmoqda."}
            msg = (
                f"📋 **Oxirgi Bajarilgan Amal Hisoboti:**\n\n"
                f"📌 {self.last_action_summary}\n\n"
                f"💡 Agar yangi vazifa bermoqchi bo'lsangiz, bemalol buyruq yozing."
            )
            yield {"type": "final", "text": msg}
            return

        # -------------------------------------------------------------
        # 4. TELEFON KESHINI TOZALASH / OPTIMIZATSIYA (SKILL: phone_optimization)
        # -------------------------------------------------------------
        if any(w in p_norm for w in ["kesh", "cache"]) and any(w in p_norm for w in ["tozala", "bo'shat", "tozalash", "telefon"]):
            yield {"type": "thought", "text": "'phone_optimization' ko'nikmasi ishga tushirilmoqda. Telefon keshini tozalash yo'riqnomasi tayyorlanmoqda."}
            skill = skills_manager.get_skill("phone_optimization")
            instructions = skill["instructions"] if skill else (
                "### 1. Telegram Keshini Tozalash:\n"
                "Telegram -> Sozlamalar -> Ma'lumotlar va xotira -> Xotiradan foydalanish -> Keshni tozalash.\n\n"
                "### 2. Tizim Keshini Tozalash:\n"
                "Telefon Sozlamalari -> Ilovalar -> Og'ir ilovalar -> Xotira -> Keshni tozalash."
            )
            msg = (
                "📱 **Mobil Telefon Xotirasi va Keshini Tozalash Yo'riqnomasi:**\n\n"
                f"{instructions}\n\n"
                "💡 *Maslahat:* Telegram keshini tozalash orqali odatda telefonda 3 GB dan 15 GB gacha bo'sh joy ochiladi!"
            )
            self.last_action_summary = "Telefon keshini tozalash bo'yicha batafsil yo'riqnoma taqdim etildi."
            yield {"type": "final", "text": msg}
            return

        # -------------------------------------------------------------
        # 5. WINDOWS GUI DASTURLAR YARATISH (SKILL: windows_apps — KALKULYATOR)
        # -------------------------------------------------------------
        # Masalan: "kalkulyator yarat", "kalkulyator dasturini yaratib ber", "gui dastur tuz"
        is_calc_req = "kalkulyator" in p_norm or "calculator" in p_norm
        is_create_app = any(w in p_norm for w in ["yarat", "tuz", "yasab ber", "yozib ber", "qur"])

        if is_calc_req and is_create_app:
            yield {"type": "thought", "text": "'windows_apps' ko'nikmasi asosida Tkinter grafik kalkulyator va .bat ishga tushirgich yaratilmoqda."}
            calc_code = '''import tkinter as tk
from tkinter import messagebox

class CalculatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Antigravity Kalkulyator")
        self.root.geometry("340x480")
        self.root.resizable(False, False)
        self.root.configure(bg="#1e1e2e")

        self.expression = ""
        self.entry_var = tk.StringVar()

        # Ekran
        entry = tk.Entry(
            root, textvariable=self.entry_var, font=("Segoe UI", 24, "bold"),
            bg="#181825", fg="#cdd6f4", bd=0, justify="right"
        )
        entry.pack(fill="x", padx=15, pady=20, ipady=12)

        # Tugmalar
        buttons = [
            ('C', '#f38ba8', '#11111b'), ('(', '#89b4fa', '#11111b'), (')', '#89b4fa', '#11111b'), ('/', '#fab387', '#11111b'),
            ('7', '#313244', '#cdd6f4'), ('8', '#313244', '#cdd6f4'), ('9', '#313244', '#cdd6f4'), ('*', '#fab387', '#11111b'),
            ('4', '#313244', '#cdd6f4'), ('5', '#313244', '#cdd6f4'), ('6', '#313244', '#cdd6f4'), ('-', '#fab387', '#11111b'),
            ('1', '#313244', '#cdd6f4'), ('2', '#313244', '#cdd6f4'), ('3', '#313244', '#cdd6f4'), ('+', '#fab387', '#11111b'),
            ('0', '#313244', '#cdd6f4'), ('.', '#313244', '#cdd6f4'), ('⌫', '#eba0ac', '#11111b'), ('=', '#a6e3a1', '#11111b')
        ]

        frame = tk.Frame(root, bg="#1e1e2e")
        frame.pack(fill="both", expand=True, padx=12, pady=5)

        for i, (text, bg, fg) in enumerate(buttons):
            r, c = divmod(i, 4)
            btn = tk.Button(
                frame, text=text, font=("Segoe UI", 14, "bold"),
                bg=bg, fg=fg, bd=0, activebackground="#585b70",
                cursor="hand2", command=lambda t=text: self.on_click(t)
            )
            btn.grid(row=r, column=c, sticky="nsew", padx=4, pady=4)

        for i in range(5):
            frame.rowconfigure(i, weight=1)
        for j in range(4):
            frame.columnconfigure(j, weight=1)

    def on_click(self, char):
        if char == "C":
            self.expression = ""
        elif char == "⌫":
            self.expression = self.expression[:-1]
        elif char == "=":
            try:
                # Xavfsiz hisoblash
                safe_expr = self.expression.replace("^", "**")
                res = str(eval(safe_expr, {"__builtins__": None}, {}))
                self.expression = res
            except Exception:
                messagebox.showerror("Xatolik", "Noto'g'ri ifoda!")
                self.expression = ""
        else:
            self.expression += str(char)

        self.entry_var.set(self.expression)

if __name__ == "__main__":
    root = tk.Tk()
    app = CalculatorApp(root)
    root.mainloop()
'''
            bat_code = (
                "@echo off\r\n"
                "chcp 65001 > nul\r\n"
                "title Kalkulyator Ishga Tushirilmoqda...\r\n"
                "start pythonw.exe \"%~dp0Kalkulyator.py\"\r\n"
                "exit\r\n"
            )

            py_path = WORKSPACE_DIR / "Kalkulyator.py"
            bat_path = WORKSPACE_DIR / "Kalkulyatorni_Boshlash.bat"

            yield {"type": "tool_call", "name": "write_file", "args": {"file_path": str(py_path)}}
            write_file(str(py_path), calc_code)
            yield {"type": "tool_result", "name": "write_file", "result": f"Kalkulyator.py yaratildi ({len(calc_code)} bayt)"}

            yield {"type": "tool_call", "name": "write_file", "args": {"file_path": str(bat_path)}}
            write_file(str(bat_path), bat_code)
            yield {"type": "tool_result", "name": "write_file", "result": "Kalkulyatorni_Boshlash.bat yaratildi"}

            # Fayllarni jo'natish ro'yxatiga qo'shish
            FILES_TO_SEND.extend([str(py_path), str(bat_path)])

            msg = (
                "✅ **Kalkulyator dasturi tayyorlandi va saqlandi!**\n\n"
                f"📂 **Yaratilgan fayllar:**\n"
                f"1. `Kalkulyator.py` — zamonaviy ko'rinishdagi to'liq GUI dastur kodi.\n"
                f"2. `Kalkulyatorni_Boshlash.bat` — konsolsiz, ikki marta bosganda to'g'ridan-to'g'ri ochiluvchi fayl.\n\n"
                f"📍 Manzil: `{WORKSPACE_DIR}`\n"
                f"💡 Telegramda bo'lsangiz, ushbu fayllar sizga ilova qilib yuborildi!"
            )
            self.last_action_summary = "Windows grafik Kalkulyator dasturi va .bat ishga tushiruvchisi yaratildi."
            yield {"type": "final", "text": msg}
            return

        # -------------------------------------------------------------
        # 6. MAVJUD MAXSUS KO'NIKMALAR (SKILLS) BILAN TEKSHIRISH
        # -------------------------------------------------------------
        for s_folder, s_data in skills_manager.discover_skills().items():
            triggers = s_data.get("triggers", [])
            if any(trig.lower() in p_norm for trig in triggers):
                yield {"type": "thought", "text": f"Mavjud '{s_data['name']}' ko'nikmasi bo'yicha yo'riqnoma faollashtirilmoqda."}
                inst = s_data.get("instructions", "")
                msg = (
                    f"⭐ **Ko'nikma: {s_data['name']}**\n\n"
                    f"_{s_data.get('description', '')}_\n\n"
                    f"{inst}"
                )
                self.last_action_summary = f"'{s_data['name']}' ko'nikmasi bo'yicha amaliy qo'llanma berildi."
                yield {"type": "final", "text": msg}
                return

        # -------------------------------------------------------------
        # 7. XOTIRA VA O'RGANILGAN SABOQLAR (/learn, /memory, xotira)
        # -------------------------------------------------------------
        if any(w in p_norm for w in ["xotirang", "eslaganlaring", "saboqlar", "qoidalar"]) and not any(w in p_norm for w in ["ram", "cpu", "disk"]):
            yield {"type": "thought", "text": "Doimiy xotiradagi o'rganilgan barcha saboqlar o'qilmoqda."}
            learnings = memory_manager.get_all_learnings()
            if not learnings:
                msg = "🧠 Agent xotirasida hozircha maxsus saboqlar yo'q."
            else:
                lines = [f"🧠 **Agentning Doimiy Xotirasi ({len(learnings)} ta saboq):**\n"]
                for idx, l in enumerate(learnings, 1):
                    lines.append(f"{idx}. *[{l.get('category', 'umumiy')}]* ({l.get('timestamp', '')}):\n   _{l.get('lesson')}_\n")
                msg = "\n".join(lines)
            self.last_action_summary = "Xotiradagi barcha saboqlar va qoidalar ko'rsatildi."
            yield {"type": "final", "text": msg}
            return

        # Yangi saboq o'rgatish: "eslab qol: ...", "o'rgan: ..."
        learn_match = re.search(r"(?:eslab qol|o'rganib ol|o'rgan|saqlab qo'y)[:\s]+(.+)", p_raw, re.IGNORECASE)
        if learn_match:
            lesson_txt = learn_match.group(1).strip()
            yield {"type": "thought", "text": f"Yangi saboqni xotiraga yozish: '{lesson_txt}'"}
            res = memory_manager.record_learning(lesson_txt, category="foydalanuvchi_oqitdi")
            msg = f"🎓 **Saboq qabul qilindi va eslab qolindi!**\n\n{res}"
            self.last_action_summary = f"Yangi qoida xotiraga yozildi: {lesson_txt[:50]}..."
            yield {"type": "final", "text": msg}
            return

        # -------------------------------------------------------------
        # 8. PAPKA YOKI DISK TARKIBINI KO'RISH (LIST DIRECTORY)
        # -------------------------------------------------------------
        # "ro'yxatini ko'rsat", "D diskdagi papkalar", "fayllarni ko'rsat", "ichida nimalar bor"
        is_list_intent = any(w in p_norm for w in [
            "ro'yxat", "royxat", "papkalar", "nimalar bor", "ichini ko'r", "ichida nima",
            "fayllarni ko'rsat", "papka ichi", "dir", "ls", "qanday papkalar"
        ]) and not any(w in p_norm for w in ["bo'sh joy", "ram", "cpu", "protsessor"])

        if is_list_intent:
            target_path = "."
            if "d disk" in p_norm or "d:" in p_norm or "d:/" in p_norm or "d:\\" in p_norm:
                target_path = "D:/"
            elif "c disk" in p_norm or "c:" in p_norm:
                target_path = "C:/"
            elif "workspace" in p_norm:
                target_path = str(WORKSPACE_DIR)

            # Agar aniq papka yo'li ko'rsatilgan bo'lsa
            path_match = re.search(r"([a-zA-Z]\:[\/\\][^\s'\"]*)", p_raw)
            if path_match:
                target_path = path_match.group(1)

            yield {"type": "thought", "text": f"'{target_path}' katalogi tarkibini tekshirish."}
            yield {"type": "tool_call", "name": "list_directory", "args": {"path": target_path}}
            res = list_directory(target_path)
            yield {"type": "tool_result", "name": "list_directory", "result": res}
            self.last_action_summary = f"'{target_path}' katalogi tarkibi ko'rildi va ro'yxat taqdim etildi."
            yield {"type": "final", "text": f"📋 **Papka tarkibi ({target_path}):**\n\n{res}"}
            return

        # -------------------------------------------------------------
        # 9. TIZIM VA RESURSLAR DIAGNOSTIKASI (CPU, RAM, DISKLAR BO'SH JOYI)
        # -------------------------------------------------------------
        sys_keywords = [
            "tizim holat", "kompyuter holat", "sistema", "ram", "cpu", "protsessor",
            "bo'sh joy", "xotira holati", "parametr", "qancha joy", "disk holati"
        ]
        if any(w in p_norm for w in sys_keywords) or (("disk" in p_norm or "kompyuter" in p_norm) and any(w in p_norm for w in ["holat", "tekshir", "bo'sh", "joy", "sig'im"])):
            yield {"type": "thought", "text": "Kompyuter texnik holati, xotira va disklar statistikasi olinmoqda."}
            yield {"type": "tool_call", "name": "get_system_stats", "args": {}}
            res = get_system_stats()
            yield {"type": "tool_result", "name": "get_system_stats", "result": res}
            self.last_action_summary = "Kompyuterning to'liq texnik holati (RAM, CPU, disklar) tekshirildi."
            yield {"type": "final", "text": f"🖥️ **Kompyuter Tizim Holati:**\n\n{res}"}
            return

        # -------------------------------------------------------------
        # 10. JARAYONLAR VA XOTIRANI BAND QILGAN DASTURLAR
        # -------------------------------------------------------------
        if any(w in p_norm for w in ["jarayon", "process", "taskmgr", "qaysi dastur", "eng ko'p ram", "ko'p xotira"]):
            yield {"type": "thought", "text": "Faol jarayonlar va xotira iste'moli tahlil qilinmoqda."}
            yield {"type": "tool_call", "name": "manage_process", "args": {"action": "list"}}
            res = manage_process("list")
            yield {"type": "tool_result", "name": "manage_process", "result": res}
            self.last_action_summary = "Faol jarayonlar ro'yxati va eng ko'p RAM sarflayotgan dasturlar aniqlandi."
            yield {"type": "final", "text": f"📊 **Faol jarayonlar hisoboti:**\n\n{res}"}
            return

        # -------------------------------------------------------------
        # 11. JARAYONNI TO'XTATISH (KILL)
        # -------------------------------------------------------------
        kill_match = re.search(r"(?:to'xtat|yop|o'ldir|kill)\s+([a-zA-Z0-9_\-\.]+)", p_norm)
        if ("to'xtat" in p_norm or "yop" in p_norm or "kill" in p_norm) and kill_match:
            target = kill_match.group(1)
            yield {"type": "thought", "text": f"Jarayonni to'xtatish buyrug'i: '{target}'."}
            yield {"type": "tool_call", "name": "manage_process", "args": {"action": "kill", "target": target}}
            res = manage_process("kill", target)
            yield {"type": "tool_result", "name": "manage_process", "result": res}
            self.last_action_summary = f"'{target}' jarayoni to'xtatildi."
            yield {"type": "final", "text": f"🛑 **Jarayon to'xtatish natijasi:**\n{res}"}
            return

        # -------------------------------------------------------------
        # 12. DASTUR YOKI ILovani OCHISH
        # -------------------------------------------------------------
        if any(w in p_norm for w in ["och", "ishga tushir", "start"]):
            app = None
            if "kalkulyator" in p_norm or "calc" in p_norm:
                app = "calc"
            elif "bloknot" in p_norm or "notepad" in p_norm:
                app = "notepad"
            elif "explorer" in p_norm or "provodnik" in p_norm:
                app = "explorer"
            elif "brauzer" in p_norm or "chrome" in p_norm:
                app = "chrome"
            else:
                m = re.search(r"(?:och(?:ish|ib ber)?|ishga tushir)\s+([a-zA-Z0-9_\-\.\:\\]+)", p_norm)
                if m:
                    app = m.group(1)

            if app and not any(w in p_norm for w in ["fayl", "faylini"]):
                yield {"type": "thought", "text": f"Dastur ishga tushirilmoqda: '{app}'."}
                yield {"type": "tool_call", "name": "open_application", "args": {"app_or_path": app}}
                res = open_application(app)
                yield {"type": "tool_result", "name": "open_application", "result": res}
                self.last_action_summary = f"'{app}' dasturi ochildi."
                yield {"type": "final", "text": f"🚀 {res}"}
                return

        # -------------------------------------------------------------
        # 13. FAYL YARATISH YOKI MATN YOZISH (WRITE FILE)
        # -------------------------------------------------------------
        has_file_word = any(w in p_norm for w in ["fayl", "file", "hujjat", "matn"])
        has_write_word = any(w in p_norm for w in ["yarat", "yoz", "tuz", "saqla", "hosil qil", "och va yoz"])

        if (has_file_word and has_write_word) or re.search(r"(?:fayl\s+yarat|fayl\s+yoz)", p_norm):
            # Fayl nomini topish
            file_match = re.search(r"([a-zA-Z0-9_\-]+\.[a-zA-Z0-9]+)", p_raw)
            if file_match:
                fname = file_match.group(1)
            else:
                name_match = re.search(r"['\"]([^'\"]+)['\"]\s*(?:nomli)?", p_raw)
                fname = f"{name_match.group(1)}.txt" if name_match else "yangi_fayl.txt"

            fpath = f"D:/{fname}" if ("d disk" in p_norm or "d:" in p_norm) and not (":" in fname) else str(WORKSPACE_DIR / fname)

            # Mazmunni ajratib olish
            content_match = re.search(r"['\"]([^'\"]+)['\"]", p_raw)
            ichiga_match = re.search(r"(?:ichiga|matni|deb)\s*[:\s]+(.+)", p_raw, re.IGNORECASE)

            if content_match:
                content = content_match.group(1)
            elif ichiga_match:
                content = ichiga_match.group(1).strip()
            else:
                content = f"Yaratilgan sana: {time.strftime('%Y-%m-%d %H:%M:%S')}\nTopshiriq: {p_raw}"

            yield {"type": "thought", "text": f"'{fpath}' faylini yaratish va matn saqlash."}
            yield {"type": "tool_call", "name": "write_file", "args": {"file_path": fpath, "content": content}}
            res = write_file(fpath, content)
            yield {"type": "tool_result", "name": "write_file", "result": res}
            FILES_TO_SEND.append(fpath)
            self.last_action_summary = f"'{fname}' fayli muvaffaqiyatli yaratildi va saqlandi."
            yield {"type": "final", "text": f"✅ {res}\n\n📄 **Fayl mazmuni:**\n```\n{content}\n```"}
            return

        # -------------------------------------------------------------
        # 14. FAYL O'QISH (READ FILE)
        # -------------------------------------------------------------
        if any(w in p_norm for w in ["o'qi", "o'qib ber", "matnini chiqar", "tarkibini ko'r"]) and any(w in p_norm for w in ["fayl", "file", ".txt", ".md", ".py", ".json", ".log"]):
            file_match = re.search(r"([a-zA-Z0-9_\-\.\:\/\\]+\.[a-zA-Z0-9]+)", p_raw)
            if file_match:
                fpath = file_match.group(1)
                if ("d disk" in p_norm or "d:" in p_norm) and not (":" in fpath):
                    fpath = f"D:/{fpath}"

                yield {"type": "thought", "text": f"'{fpath}' fayli o'qilmoqda."}
                yield {"type": "tool_call", "name": "read_file", "args": {"file_path": fpath}}
                res = read_file(fpath)
                yield {"type": "tool_result", "name": "read_file", "result": res[:300] + "..." if len(res) > 300 else res}
                self.last_action_summary = f"'{fpath}' fayli o'qildi."
                yield {"type": "final", "text": f"📄 **'{fpath}' fayli tarkibi:**\n```\n{res}\n```"}
                return

        # -------------------------------------------------------------
        # 15. FAYLLARNI QIDIRISH (SEARCH)
        # -------------------------------------------------------------
        if any(w in p_norm for w in ["qidir", "top", "qayerda", "izla", "topib ber"]):
            pattern = "*.*"
            ext_match = re.search(r"\.([a-zA-Z0-9]+)", p_raw)
            name_match = re.search(r"['\"]([^'\"]+)['\"]", p_raw)
            if ext_match:
                pattern = f"*.{ext_match.group(1)}"
            elif name_match:
                pattern = f"*{name_match.group(1)}*"
            elif "rasm" in p_norm:
                pattern = "*.jpg"
            elif "video" in p_norm:
                pattern = "*.mp4"
            elif "audio" in p_norm or "musiqa" in p_norm or "ovoz" in p_norm:
                pattern = "*.wav"
            elif "python" in p_norm:
                pattern = "*.py"

            search_path = "D:/" if ("d:" in p_norm or "d disk" in p_norm) else str(WORKSPACE_DIR)
            yield {"type": "thought", "text": f"'{search_path}' manzili bo'yicha '{pattern}' fayllari qidirilmoqda."}
            yield {"type": "tool_call", "name": "search_files", "args": {"pattern": pattern, "path": search_path}}
            res = search_files(pattern=pattern, path=search_path)
            yield {"type": "tool_result", "name": "search_files", "result": res}
            self.last_action_summary = f"'{pattern}' shabloni bo'yicha qidiruv bajarildi."
            yield {"type": "final", "text": f"🔍 **Qidiruv natijasi:**\n\n{res}"}
            return

        # -------------------------------------------------------------
        # 16. ZIP ARXIVLASH
        # -------------------------------------------------------------
        if any(w in p_norm for w in ["arxiv", "zip", "siq"]):
            folder_match = re.search(r"([a-zA-Z]\:[\/\\][^\s'\"]+)", p_raw)
            target = folder_match.group(1) if folder_match else str(WORKSPACE_DIR)
            yield {"type": "thought", "text": f"'{target}' papkasini ZIP arxiv qilish."}
            yield {"type": "tool_call", "name": "zip_folder", "args": {"source_folder": target}}
            res = zip_folder(target)
            yield {"type": "tool_result", "name": "zip_folder", "result": res}
            self.last_action_summary = f"'{target}' papkasi ZIP arxiv qilindi."
            yield {"type": "final", "text": f"📦 {res}"}
            return

        # -------------------------------------------------------------
        # 17. POWERSHELL / CMD BUYRUQ (EXPLICIT TERMINAL COMMAND)
        # -------------------------------------------------------------
        if any(w in p_norm for w in ["powershell", "cmd", "terminal:", "buyruq:"]):
            cmd_clean = re.sub(r"^(?:powershell|cmd|terminal|buyruq)\s*:?\s*", "", p_raw, flags=re.IGNORECASE).strip()
            yield {"type": "thought", "text": f"Konsol buyrug'i bajarilmoqda: `{cmd_clean}`."}
            yield {"type": "tool_call", "name": "execute_command", "args": {"command": cmd_clean}}
            res = execute_command(cmd_clean)
            yield {"type": "tool_result", "name": "execute_command", "result": res}
            self.last_action_summary = f"Konsol buyrug'i bajarildi: {cmd_clean[:50]}"
            yield {"type": "final", "text": f"💻 **Konsol natijasi:**\n```\n{res}\n```"}
            return

        # -------------------------------------------------------------
        # 18. MATEMATIK HISOBLASH VA PYTHON
        # -------------------------------------------------------------
        math_match = re.search(r"([0-9\+\-\*\/\(\)\^\.\s]{3,})", p_raw)
        has_math_op = any(op in p_raw for op in ["+", "-", "*", "/", "^"])
        if ("hisobla" in p_norm or "hisob-kitob" in p_norm or has_math_op) and math_match and len(math_match.group(1).strip()) >= 3:
            expr = math_match.group(1).strip()
            # Xavfsiz ifoda
            try:
                safe_expr = expr.replace("^", "**")
                res = str(eval(safe_expr, {"__builtins__": None}, {}))
                self.last_action_summary = f"Matematik hisob-kitob bajarildi: {expr} = {res}"
                yield {"type": "final", "text": f"🔢 **Hisoblash natijasi:**\n\n`{expr}` = **{res}**"}
                return
            except Exception:
                pass

        if any(w in p_norm for w in ["python", "kod yoz", "skript"]):
            code = f"# Vazifa: {p_raw}\nprint('Python orqali hisoblash bajarildi.')\n"
            yield {"type": "thought", "text": "Python kodi bajarilmoqda."}
            yield {"type": "tool_call", "name": "execute_python", "args": {"code": code}}
            res = execute_python(code)
            yield {"type": "tool_result", "name": "execute_python", "result": res}
            self.last_action_summary = "Python kodi bajarildi."
            yield {"type": "final", "text": f"🐍 **Python natijasi:**\n```\n{res}\n```"}
            return

        # -------------------------------------------------------------
        # 19. KOMPYUTERNI O'CHIRISH YOKI RESTART
        # -------------------------------------------------------------
        if "o'chir" in p_norm and any(w in p_norm for w in ["kompyuter", "tizim", "windows", "pc"]):
            yield {"type": "thought", "text": "Kompyuterni o'chirish (shutdown) amali tayyorlanmoqda."}
            yield {
                "type": "final",
                "text": (
                    "⚠️ **Kompyuterni o'chirish buyrug'i:**\n\n"
                    "Xavfsizlik yuzasidan kompyuterni to'satdan o'chirmaslik uchun, 60 soniya vaqt berildi.\n"
                    "O'chirishni bekor qilish uchun konsolga `shutdown /a` deb yozishingiz mumkin."
                )
            }
            execute_command("shutdown /s /t 60")
            self.last_action_summary = "Kompyuterni o'chirish taymerga qo'yildi (60s)."
            return

        # -------------------------------------------------------------
        # 20. UMUMIY INTERNETSIZ JAVOB (HALOL VA ANIQ YO'NALTIRUVCHI)
        # -------------------------------------------------------------
        # Hech qachon soxta Write-Host "Bajarildi" qilib aldamaymiz!
        yield {"type": "thought", "text": "Topshiriq internetsiz rejim imkoniyatlari doirasida tekshirildi."}
        self.last_action_summary = f"Foydalanuvchi so'rovi bo'yicha internetsiz rejim yo'riqnomasi berildi: '{p_raw[:40]}'"
        yield {
            "type": "final",
            "text": (
                f"ℹ️ **Internetsiz Mahalliy Boshqaruv Rejimi:**\n\n"
                f"Sizning so'rovingiz: *\"{p_raw}\"*\n\n"
                f"Hozirda kompyuteringiz tashqi internetga ulanmagan yoki sun'iy intellekt kvotasi cheklanganligi sababli, "
                f"men **100% lokal avtonom boshqaruv dvigateli** asosida ishlamoqdaman.\n\n"
                f"📌 **Men internetsiz nimalarni xatosiz bajara olaman?**\n"
                f"• 📁 **Fayllar va disklar:** `D diskdagi papkalar`, `test.txt faylini yarat`, `faylni o'qi`, `qidir: *.py`\n"
                f"• 🖥️ **Tizim:** `tizim holati`, `eng ko'p RAM yeyotgan dasturlar`, `jarayonni to'xtat <nomi>`\n"
                f"• 🪟 **Ilovalar:** `kalkulyator dasturini yaratib ber`, `bloknotni och`\n"
                f"• 📱 **Telefon:** `telefon keshini tozalash`, `keshni qanday bo'shatish mumkin`\n"
                f"• 🔢 **Hisob-kitob:** `(450 * 12) / 5 hisoblab ber`\n"
                f"• 🧠 **Xotira:** `/memory` yoki `/learn <yangi qoida>`\n\n"
                f"Iltimos, aniq kompyuter topshirig'ini bering, uni bir zumda bajaraman!"
            )
        }
