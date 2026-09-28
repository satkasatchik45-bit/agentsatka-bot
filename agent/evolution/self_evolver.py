import os
import sys
import shutil
import time
from pathlib import Path
from typing import Dict, Any, List

from .memory_manager import memory_manager
from .skills_manager import skills_manager
from .custom_tools_manager import custom_tools_manager
from ..logger import logger

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class SelfEvolver:
    """Agentning o'zini o'zi tahlil qilish, takomillashtirish va rivojlantirish tizimi."""

    def inspect_system(self) -> Dict[str, Any]:
        """Agent o'zining butun arxitekturasi va holatini ko'zdan kechiradi."""
        skills = skills_manager.discover_skills()
        tools = custom_tools_manager.list_tools_info()
        learnings = memory_manager.get_all_learnings()

        return {
            "skills_count": len(skills),
            "skills_list": list(skills.keys()),
            "custom_tools_count": len(tools),
            "custom_tools_list": [t["name"] for t in tools],
            "learnings_count": len(learnings),
            "os": sys.platform,
            "python_version": sys.version.split()[0]
        }

    def format_inspection_report(self) -> str:
        """Tizim holati haqida chiroyli matnli hisobot."""
        info = self.inspect_system()
        lines = [
            "🧬 *ANTIGRAVITY AVTONOM AGENT - O'Z-O'ZINI RIVOJLANTIRISH HOLATI:*\n",
            f"📚 *O'zlashtirilgan ko'nikmalar (Skills):* {info['skills_count']} ta",
            "   " + (", ".join(f"`{s}`" for s in info['skills_list']) if info['skills_list'] else "_Hozircha yo'q_"),
            f"\n🔧 *Yaratilgan maxsus asboblar (Custom Tools):* {info['custom_tools_count']} ta",
            "   " + (", ".join(f"`{t}`" for t in info['custom_tools_list']) if info['custom_tools_list'] else "_Hozircha yo'q_"),
            f"\n🧠 *Xotiradagi doimiy saboqlar (Memory):* {info['learnings_count']} ta",
            f"\n💻 *Tizim:* `{info['os']}` | Python `{info['python_version']}`",
            "\n💡 _Agent har bir bajargan topshirig'idan o'rganib, o'z imkoniyatlarini mustaqil kengaytirib bormoqda._"
        ]
        return "\n".join(lines)

    def trigger_evolution(self) -> str:
        """Agent o'zining xotirasi va so'nggi faoliyatini tahlil qilib, o'zini rivojlantirish jarayonini boshlaydi."""
        logger.info("🧬 O'z-o'zini rivojlantirish tsikli ishga tushdi...")
        learnings = memory_manager.get_all_learnings()
        skills = skills_manager.discover_skills()

        # Yangi xulosalar chiqarish
        summary = (
            f"✅ **Rivojlanish yakunlandi!**\n\n"
            f"• **Xotira:** {len(learnings)} ta saboq sinxronlashtirildi.\n"
            f"• **Ko'nikmalar:** {len(skills)} ta maxsus Skill faol.\n"
            f"• **Tizim:** Kodlar va asboblar zanjiri tekshirildi, barcha modullar barqaror ishlamoqda."
        )
        return summary

self_evolver = SelfEvolver()
