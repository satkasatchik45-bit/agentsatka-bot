import os
import sys
import py_compile
import importlib.util
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
from ..logger import logger

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CUSTOM_TOOLS_DIR = BASE_DIR / "custom_tools"

class CustomToolsManager:
    """Agent o'zi mustaqil yangi Python asboblari (Tools) yaratishi va ularni
    qayta ishga tushirmasdan, issiq holatda (hot-reload) o'ziga ulab olishi uchun boshqaruvchi."""

    def __init__(self):
        self.tools_dir = CUSTOM_TOOLS_DIR
        self.tools_dir.mkdir(parents=True, exist_ok=True)
        self.loaded_tools: Dict[str, Callable] = {}
        self.load_all_tools()

    def load_all_tools(self):
        """Barcha custom_tools papkasidagi asboblarni xotiraga yuklaydi."""
        for file in self.tools_dir.glob("*.py"):
            if file.name.startswith("__"):
                continue
            self._load_tool_from_file(file)

    def _load_tool_from_file(self, file_path: Path) -> Optional[Callable]:
        """Bitta fayldan asbob funksiyasini yuklaydi."""
        try:
            tool_name = file_path.stem
            spec = importlib.util.spec_from_file_location(tool_name, str(file_path))
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                sys.modules[tool_name] = module
                spec.loader.exec_module(module)

                # Modul ichidagi asosiy funksiyani topish
                tool_func = getattr(module, tool_name, None)
                if not tool_func:
                    # Agar bir xil nomli bo'lmasa, birinchi callable funksiyani olish
                    for attr_name in dir(module):
                        attr = getattr(module, attr_name)
                        if callable(attr) and not attr_name.startswith("_") and attr.__module__ == tool_name:
                            tool_func = attr
                            break

                if tool_func:
                    self.loaded_tools[tool_name] = tool_func
                    logger.info(f"🔧 Dinamik asbob yuklandi: {tool_name}")
                    return tool_func
        except Exception as e:
            logger.error(f"Asbobni yuklashda xatolik ({file_path.name}): {e}")
        return None

    def create_custom_tool(self, name: str, code: str, description: str) -> str:
        """Agent o'ziga yangi asbob (Python funksiyasi) yaratadi va darhol faollashtiradi.
        
        Args:
            name: Asbob nomi (masalan: parse_excel, convert_currency, download_youtube)
            code: Funksiyaning to'liq Python kodi. Kod docstring va tipizatsiyaga ega bo'lishi shart!
            description: Asbob nima qilishining qisqa tavsifi.
        """
        clean_name = "".join(c if c.isalnum() or c == "_" else "_" for c in name.strip().lower())
        tool_file = self.tools_dir / f"{clean_name}.py"

        # Kod to'g'ri docstring ga ega ekanligiga ishonch hosil qilish
        if f"def {clean_name}" not in code:
            code = f'def {clean_name}(*args, **kwargs):\n    """{description}"""\n' + "\n".join("    " + l for l in code.splitlines())

        # Faylga yozish
        temp_file = self.tools_dir / f"temp_{clean_name}.py"
        try:
            temp_file.write_text(code, encoding="utf-8")
            # Sintaksisni tekshirish
            py_compile.compile(str(temp_file), doraise=True)
            # Agar xatosiz bo'lsa, haqiqiy joyga ko'chirish
            if temp_file.exists():
                temp_file.replace(tool_file)
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink(missing_ok=True)
            return f"❌ Asbob kodida sintaktik xatolik aniqlandi va saqlanmadi:\n{e}"

        # Darhol hot-reload orqali yuklash
        loaded_func = self._load_tool_from_file(tool_file)
        if loaded_func:
            return f"🎉 Yangi asbob '{clean_name}' muvaffaqiyatli yaratildi va darhol agent qurollariga qo'shildi!"
        return f"⚠️ Asbob saqlandi, lekin yuklashda muammo bo'ldi. Fayl: {tool_file.name}"

    def get_all_tools(self) -> List[Callable]:
        """Barcha dinamik asboblar ro'yxatini qaytaradi."""
        return list(self.loaded_tools.values())

    def list_tools_info(self) -> List[Dict[str, str]]:
        """Mavjud dinamik asboblar haqida ma'lumot."""
        info = []
        for name, fn in self.loaded_tools.items():
            doc = fn.__doc__ or "Tavsif mavjud emas"
            info.append({"name": name, "description": doc.strip().split("\n")[0]})
        return info

custom_tools_manager = CustomToolsManager()
