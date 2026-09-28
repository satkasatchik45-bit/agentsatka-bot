import json
import urllib.request
import urllib.error
from typing import Dict, Any, List, Optional, Generator, Callable
from .config import OLLAMA_BASE_URL, OLLAMA_MODEL
from .logger import logger

def check_ollama_status(base_url: str = OLLAMA_BASE_URL) -> Dict[str, Any]:
    """Mahalliy Ollama xizmati ishlayotganini va mavjud modellarni tekshiradi."""
    url = f"{base_url.rstrip('/')}/api/tags"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AntigravityAgent"})
        with urllib.request.urlopen(req, timeout=2.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name") for m in data.get("models", [])]
                # Eng yaxshi modelni avtomatik aniqlash
                active = None
                if OLLAMA_MODEL in models:
                    active = OLLAMA_MODEL
                elif any("llama3.2:3b" in m for m in models):
                    active = next(m for m in models if "llama3.2:3b" in m)
                elif any("llama3" in m for m in models):
                    active = next(m for m in models if "llama3" in m)
                elif any("qwen" in m for m in models):
                    active = next(m for m in models if "qwen" in m)
                elif models:
                    active = models[0]

                return {
                    "running": True,
                    "models": models,
                    "active_model": active
                }
    except Exception:
        pass

    return {
        "running": False,
        "models": [],
        "active_model": None
    }

def call_ollama_chat(
    prompt: str,
    system_instruction: str,
    model_name: Optional[str] = None,
    base_url: str = OLLAMA_BASE_URL,
    timeout: int = 60
) -> Optional[str]:
    """Ollama API orqali lokal LLM ga so'rov yuboradi."""
    status = check_ollama_status(base_url)
    if not status["running"]:
        return None

    target_model = model_name or status["active_model"] or OLLAMA_MODEL
    url = f"{base_url.rstrip('/')}/api/chat"

    sys_content = (
        "Siz o'zbek tilida mukammal va to'g'ri grammatika bilan javob beruvchi aqlli shaxsiy agentsiz. "
        "Foydalanuvchi savollariga aniq, ravon va toza o'zbek adabiy tilida javob bering."
    )

    payload = {
        "model": target_model,
        "messages": [
            {"role": "system", "content": sys_content},
            {"role": "user", "content": prompt}
        ],
        "stream": False,
        "options": {
            "temperature": 0.3,
            "num_predict": 500
        }
    }

    try:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            res = json.loads(resp.read().decode("utf-8"))
            return res.get("message", {}).get("content", "").strip()
    except Exception as e:
        logger.error(f"Ollama so'rovida xatolik: {e}")
        return None

def run_ollama_stream(
    prompt: str,
    system_instruction: str,
    tool_map: Dict[str, Callable],
    model_name: Optional[str] = None,
    base_url: str = OLLAMA_BASE_URL,
    max_steps: int = 5
) -> Generator[Dict[str, Any], None, None]:
    """Ollama bilan asboblar yordamida ReAct qadam-baqadam boshqaruv generatori."""
    status = check_ollama_status(base_url)
    if not status["running"]:
        return

    target_model = model_name or status["active_model"] or OLLAMA_MODEL
    url = f"{base_url.rstrip('/')}/api/chat"

    # Ollama uchun sodda asboblar deklaratsiyasi
    ollama_tools = [
        {
            "type": "function",
            "function": {
                "name": "list_directory",
                "description": "Papkadagi barcha fayl va jildlar ro'yxatini ko'rish",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "Papka manzili, masalan 'D:/'"}
                    }
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "get_system_stats",
                "description": "Kompyuter texnik holati (RAM, CPU, Disklar bo'sh joyi)",
                "parameters": {"type": "object", "properties": {}}
            }
        },
        {
            "type": "function",
            "function": {
                "name": "read_file",
                "description": "Fayl ichidagi matnni o'qish",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "O'qiladigan fayl yo'li"}
                    },
                    "required": ["file_path"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "write_file",
                "description": "Fayl yaratish yoki unga matn yozish",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "file_path": {"type": "string", "description": "Fayl yo'li"},
                        "content": {"type": "string", "description": "Yoziladigan matn"}
                    },
                    "required": ["file_path", "content"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "execute_command",
                "description": "PowerShell yoki CMD konsol buyrug'ini bajarish",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "Bajariladigan konsol buyrug'i"}
                    },
                    "required": ["command"]
                }
            }
        }
    ]

    messages = [
        {
            "role": "system",
            "content": (
                "Siz kompyuterni mustaqil boshqaruvchi aqlli agentsiz. "
                "O'zbek adabiy tilida toza va aniq javob bering. "
                "Fayllar yoki kompyuter amallarini bajarish uchun taqdim etilgan asboblardan foydalaning."
            )
        },
        {"role": "user", "content": prompt}
    ]

    for step in range(1, max_steps + 1):
        yield {"type": "step_start", "step": step, "max_steps": max_steps}

        payload = {
            "model": target_model,
            "messages": messages,
            "tools": ollama_tools,
            "stream": False,
            "options": {"temperature": 0.2, "num_predict": 400}
        }

        try:
            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=60) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            logger.warning(f"Ollama aloqa xatosi: {e}")
            break

        msg = resp_data.get("message", {})
        tool_calls = msg.get("tool_calls", [])

        # Agar model asbob chaqirgan bo'lsa
        if tool_calls:
            messages.append(msg)
            for tc in tool_calls:
                fn = tc.get("function", {})
                fn_name = fn.get("name")
                fn_args = fn.get("arguments", {})

                yield {"type": "tool_call", "name": fn_name, "args": fn_args, "step": step}

                tool_fn = tool_map.get(fn_name)
                if tool_fn:
                    try:
                        res_str = str(tool_fn(**fn_args))
                    except Exception as terr:
                        res_str = f"[Xatolik]: {terr}"
                else:
                    res_str = f"[Xatolik]: '{fn_name}' asbobi topilmadi."

                yield {"type": "tool_result", "name": fn_name, "result": res_str, "step": step}

                messages.append({
                    "role": "tool",
                    "content": res_str
                })
        else:
            # Yakuniy javob
            final_text = msg.get("content", "").strip()
            if final_text:
                yield {"type": "final", "text": final_text}
                return
            break
