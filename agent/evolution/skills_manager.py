import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from ..logger import logger

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SKILLS_DIR = BASE_DIR / "skills"

class SkillsManager:
    """Antigravity uslubidagi ixtisoslashgan ko'nikmalar (Skills) boshqaruvchisi.
    Agent yangi mahorat o'rganganda, ushbu tizim orqali yangi skill yaratadi yoki mavjudini kuchaytiradi."""

    def __init__(self):
        self.skills_dir = SKILLS_DIR
        self.skills_dir.mkdir(parents=True, exist_ok=True)

    def discover_skills(self) -> Dict[str, Dict[str, Any]]:
        """Barcha mavjud ko'nikmalarni aniqlaydi va o'qiydi."""
        skills = {}
        for skill_folder in self.skills_dir.iterdir():
            if not skill_folder.is_dir():
                continue
            skill_md = skill_folder / "SKILL.md"
            if skill_md.exists():
                try:
                    content = skill_md.read_text(encoding="utf-8")
                    skill_info = self._parse_skill_md(skill_folder.name, content)
                    skills[skill_folder.name] = skill_info
                except Exception as e:
                    logger.warning(f"Skillni o'qishda xatolik ({skill_folder.name}): {e}")
        return skills

    def _parse_skill_md(self, default_name: str, content: str) -> Dict[str, Any]:
        """SKILL.md faylini tahlil qilib ma'lumotlarni ajratib oladi."""
        name = default_name
        description = "Ko'nikma tavsifi mavjud emas"
        triggers = []
        instructions = content

        # YAML Frontmatter qidirish (--- ... ---)
        frontmatter_match = re.search(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
        if frontmatter_match:
            fm_text = frontmatter_match.group(1)
            instructions = frontmatter_match.group(2).strip()

            for line in fm_text.splitlines():
                if line.startswith("name:"):
                    name = line.split(":", 1)[1].strip()
                elif line.startswith("description:"):
                    description = line.split(":", 1)[1].strip()
                elif line.startswith("triggers:"):
                    raw_triggers = line.split(":", 1)[1].strip()
                    triggers = [t.strip().strip("'\"") for t in raw_triggers.strip("[]").split(",") if t.strip()]

        return {
            "name": name,
            "description": description,
            "triggers": triggers,
            "instructions": instructions
        }

    def get_skill(self, name: str) -> Optional[Dict[str, Any]]:
        """Muayyan ko'nikma bo'yicha to'liq qo'llanmani oladi."""
        skills = self.discover_skills()
        for s_name, data in skills.items():
            if s_name.lower() == name.lower() or data["name"].lower() == name.lower():
                return data
        return None

    def create_or_update_skill(
        self,
        name: str,
        description: str,
        triggers: List[str],
        instructions: str,
        script_code: Optional[str] = None
    ) -> str:
        """Agent o'ziga yangi ko'nikma yaratishi yoki mavjudini yangilashi uchun."""
        clean_name = re.sub(r"[^a-zA-Z0-9_\-]", "_", name.strip().lower())
        skill_folder = self.skills_dir / clean_name
        skill_folder.mkdir(parents=True, exist_ok=True)

        triggers_formatted = "[" + ", ".join(f"'{t}'" for t in triggers) + "]"
        content = f"""---
name: {clean_name}
description: {description}
triggers: {triggers_formatted}
---

# Ko'nikma: {name}

## 🎯 Tavsif
{description}

## 📋 Ko'rsatma va Algoritm
{instructions}
"""
        skill_md = skill_folder / "SKILL.md"
        skill_md.write_text(content, encoding="utf-8")

        # Agar yordamchi skript berilgan bo'lsa
        if script_code:
            scripts_dir = skill_folder / "scripts"
            scripts_dir.mkdir(exist_ok=True)
            script_file = scripts_dir / "helper.py"
            script_file.write_text(script_code, encoding="utf-8")

        logger.info(f"✨ Yangi Skill o'zlashtirildi: {clean_name}")
        return f"🎉 Yangi ko'nikma '{clean_name}' muvaffaqiyatli saqlandi va faollashtirildi!"

    def format_skills_summary_for_prompt(self) -> str:
        """Tizim ko'rsatmasiga kiritish uchun barcha ko'nikmalar haqida qisqacha ma'lumot."""
        skills = self.discover_skills()
        if not skills:
            return ""

        lines = ["\n--- MAVJUD MAXSUS KO'NIKMALAR (SKILLS) ---"]
        lines.append("Sizda quyidagi ixtisoslashgan bilimlar to'plami mavjud:")
        for name, data in skills.items():
            trig_str = f" (Kalit so'zlar: {', '.join(data['triggers'][:3])})" if data['triggers'] else ""
            lines.append(f"• **{name}**: {data['description']}{trig_str}")
        lines.append("Ushbu ko'nikmalar bo'yicha to'liq ma'lumot kerak bo'lsa, 'read_skill' asbobini chaqiring.")
        return "\n".join(lines) + "\n"

skills_manager = SkillsManager()
