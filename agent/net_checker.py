import socket
import time
import urllib.request
from typing import Dict, Any

_last_check_time: float = 0.0
_cached_online_status: bool = False
CACHE_DURATION_SECONDS = 4.0

def is_online(force_refresh: bool = False) -> bool:
    """Internet mavjudligini tezkor (1 soniyada) tekshiradi."""
    global _last_check_time, _cached_online_status
    now = time.time()
    if not force_refresh and (now - _last_check_time < CACHE_DURATION_SECONDS):
        return _cached_online_status

    status = False
    # 1. Tezkor DNS socket orqali (8.8.8.8:53 yoki 1.1.1.1:53)
    for host in ["8.8.8.8", "1.1.1.1"]:
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1.2)
            sock.connect((host, 53))
            sock.close()
            status = True
            break
        except (socket.timeout, OSError):
            continue

    # 2. Agar socket ishlamasa, HTTP tekshiruvi
    if not status:
        try:
            req = urllib.request.Request(
                "http://www.msftconnecttest.com/connecttest.txt",
                headers={"User-Agent": "Mozilla/5.0"}
            )
            with urllib.request.urlopen(req, timeout=1.5) as resp:
                if resp.status == 200:
                    status = True
        except Exception:
            status = False

    _last_check_time = now
    _cached_online_status = status
    return status

def get_connection_details() -> Dict[str, Any]:
    """Tarmoq haqida to'liq o'zbekcha ma'lumot qaytaradi."""
    start_time = time.time()
    online = is_online(force_refresh=True)
    latency_ms = round((time.time() - start_time) * 1000, 1) if online else None

    # Mahalliy IP manzil
    local_ip = "127.0.0.1"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        pass

    return {
        "online": online,
        "latency_ms": latency_ms,
        "local_ip": local_ip,
        "status_uz": "🟢 INTERNET ULANGAN" if online else "🔴 INTERNETSIZ (LOKAL REJIM)"
    }
