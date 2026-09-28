import os
import sys
import platform
import time
import datetime
from typing import Dict, Any, List

try:
    import psutil
except ImportError:
    psutil = None

from .net_checker import get_connection_details

def get_system_snapshot() -> Dict[str, Any]:
    """Kompyuterning barcha parametrlarini yig'adi."""
    info: Dict[str, Any] = {
        "os": f"{platform.system()} {platform.release()} ({platform.architecture()[0]})",
        "node": platform.node(),
        "processor": platform.processor(),
        "python": sys.version.split()[0],
        "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    if psutil:
        # CPU
        info["cpu_percent"] = psutil.cpu_percent(interval=0.2)
        info["cpu_count_logical"] = psutil.cpu_count(logical=True)
        info["cpu_count_physical"] = psutil.cpu_count(logical=False)

        # RAM
        mem = psutil.virtual_memory()
        info["ram_total_gb"] = round(mem.total / (1024**3), 2)
        info["ram_used_gb"] = round(mem.used / (1024**3), 2)
        info["ram_free_gb"] = round(mem.available / (1024**3), 2)
        info["ram_percent"] = mem.percent

        # Disklar
        disks = []
        for part in psutil.disk_partitions(all=False):
            if os.name == 'nt' and ('cdrom' in part.opts or part.fstype == ''):
                continue
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    "device": part.device,
                    "mount": part.mountpoint,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "used_gb": round(usage.used / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent": usage.percent
                })
            except (PermissionError, OSError):
                continue
        info["disks"] = disks

        # Uptime
        boot_time = datetime.datetime.fromtimestamp(psutil.boot_time())
        uptime = datetime.datetime.now() - boot_time
        info["uptime_str"] = str(uptime).split(".")[0]

        # Jarayonlar soni
        info["process_count"] = len(psutil.pids())

        # Batareya
        battery = psutil.sensors_battery()
        if battery:
            info["battery"] = {
                "percent": battery.percent,
                "power_plugged": battery.power_plugged
            }
        else:
            info["battery"] = None
    else:
        info["ram_percent"] = "psutil o'rnatilmagan"
        info["disks"] = []

    # Tarmoq
    info["network"] = get_connection_details()
    return info

def get_system_report_uz() -> str:
    """Kompyuter holati bo'yicha chiroyli o'zbekcha matnli hisobot yaratadi."""
    snap = get_system_snapshot()
    lines = [
        "🖥️ **KOMPYUTER TIZIM HOLATI HISOBOTI**",
        f"• **Operatsion tizim:** {snap['os']}",
        f"• **Kompyuter nomi:** `{snap['node']}`",
        f"• **Sana va vaqt:** {snap['time']}",
        f"• **Ishlash vaqti (Uptime):** {snap.get('uptime_str', 'Nomaʼlum')}",
        f"• **Tarmoq:** {snap['network']['status_uz']} (IP: `{snap['network']['local_ip']}`)",
        ""
    ]

    if "cpu_percent" in snap:
        lines.append(f"⚙️ **Protsessor (CPU):** {snap['cpu_percent']}% yuklama ({snap['cpu_count_logical']} ta mantiqiy yadro)")
        lines.append(f"🧠 **Tezkor xotira (RAM):** {snap['ram_used_gb']} GB / {snap['ram_total_gb']} GB ({snap['ram_percent']}% ishlatilmoqda, bo'sh: {snap['ram_free_gb']} GB)")
        
        if snap.get("battery"):
            bat = snap["battery"]
            status = "Zaryadlanmoqda ⚡" if bat["power_plugged"] else "Batareyada 🔋"
            lines.append(f"🔋 **Akkumulyator:** {bat['percent']}% ({status})")

        lines.append("\n💾 **Disklar holati:**")
        for d in snap.get("disks", []):
            lines.append(f"  - `{d['device']}` Jami: {d['total_gb']} GB | Bo'sh: **{d['free_gb']} GB** | Band: {d['percent']}%")

        lines.append(f"\n📊 **Faol jarayonlar soni:** {snap['process_count']} ta")
    
    return "\n".join(lines)

def get_top_processes(limit: int = 10, sort_by: str = "memory") -> List[Dict[str, Any]]:
    """Eng ko'p resurs yeyotgan jarayonlarni oladi (sort_by: 'memory' yoki 'cpu')."""
    if not psutil:
        return []

    procs = []
    for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'memory_info']):
        try:
            p_info = p.info
            mem_mb = round(p_info['memory_info'].rss / (1024 * 1024), 1) if p_info.get('memory_info') else 0
            procs.append({
                "pid": p_info['pid'],
                "name": p_info['name'],
                "cpu": p_info.get('cpu_percent') or 0.0,
                "mem_mb": mem_mb
            })
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    key = "mem_mb" if sort_by == "memory" else "cpu"
    procs.sort(key=lambda x: x[key], reverse=True)
    return procs[:limit]
