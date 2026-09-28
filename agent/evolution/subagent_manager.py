import asyncio
from typing import Dict, Any, Optional
from ..logger import logger

class SubagentManager:
    """Antigravity kabi ixtisoslashgan yordamchi subagentlarni chaqirish va boshqarish tizimi."""

    def __init__(self, main_agent=None):
        self.main_agent = main_agent

    def set_main_agent(self, agent):
        self.main_agent = agent

    def invoke_subagent(self, role: str, task: str) -> str:
        """Ixtisoslashgan yordamchi subagentni ishga tushiradi va natijasini qaytaradi.
        
        Args:
            role: Subagent roli (masalan: 'Dasturchi', 'Kod Tekshiruvchi', 'Tadqiqotchi', 'Tizim Mutaxassisi')
            task: Subagentga yuklatiladigan aniq topshiriq.
        """
        logger.info(f"👥 Subagent chaqirilmoqda: [{role}] -> {task[:80]}...")
        
        subagent_prompt = f"""[SUBAGENT VAZIFASI: {role.upper()}]
Siz asosiy agentga yordam beruvchi maxsus tor mutaxassissiz.
Sizning rolingiz: {role}
Sizga berilgan aniq topshiriq:
{task}

Iltimos, ushbu topshiriqni maksimal darajada aniq, professional va lo'nda bajarib, natijani xulosa qilib bering."""

        if not self.main_agent:
            return f"[Subagent xabari]: Subagent '{role}' vazifani tahlil qildi, lekin asosiy agent ulanmagan."

        try:
            # Asosiy agent orqali subagent kontekstida yechim olish
            res = self.main_agent._run_subagent_task(subagent_prompt)
            return f"👥 [{role} natijasi]:\n{res}"
        except Exception as e:
            return f"❌ Subagent ({role}) ishida xatolik: {e}"

subagent_manager = SubagentManager()
