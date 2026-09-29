import collections
import logging
import datetime
import urllib.request
import json
from typing import List, Dict, Any, Optional

try:
    from .config import RENDER_API_KEY, RENDER_SERVICE_ID, RENDER_EXTERNAL_URL
except ImportError:
    from config import RENDER_API_KEY, RENDER_SERVICE_ID, RENDER_EXTERNAL_URL

# So'nggi 200 ta log yozuvini xotirada saqlash uchun halqa buferi (Ring Buffer)
LOG_BUFFER = collections.deque(maxlen=200)

class BufferLogHandler(logging.Handler):
    def emit(self, record):
        try:
            msg = self.format(record)
            LOG_BUFFER.append(msg)
        except Exception:
            pass

def setup_cloud_logging():
    handler = BufferLogHandler()
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logging.getLogger().addHandler(handler)

def get_recent_logs(limit: int = 40) -> List[str]:
    return list(LOG_BUFFER)[-limit:]

def trigger_render_restart() -> Dict[str, Any]:
    """Render API orqali xizmatni qayta ishga tushirish (restart / re-deploy)."""
    if not RENDER_API_KEY or not RENDER_SERVICE_ID:
        return {"ok": False, "error": "RENDER_API_KEY yoki RENDER_SERVICE_ID sozlanmagan"}

    url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}/deploys"
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    payload = json.dumps({"clearCache": "do_not_clear"}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())
            return {"ok": True, "data": data}
    except Exception as e:
        return {"ok": False, "error": str(e)}

def get_render_status() -> Dict[str, Any]:
    """Render API orqali xizmat holatini olish."""
    if not RENDER_API_KEY or not RENDER_SERVICE_ID:
        return {"ok": False, "error": "Sozlanmagan"}

    url = f"https://api.render.com/v1/services/{RENDER_SERVICE_ID}"
    headers = {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json"
    }
    req = urllib.request.Request(url, headers=headers)

    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            svc = data.get("service", {})
            return {
                "ok": True,
                "name": svc.get("name"),
                "suspended": svc.get("suspended"),
                "url": svc.get("serviceDetails", {}).get("url")
            }
    except Exception as e:
        return {"ok": False, "error": str(e)}
