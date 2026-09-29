"""
Telegram Mini App (WebApp) - 60% Shaffoflik bilan o'ng yonga ustun shaklida joylashgan panel.
"""

WEBAPP_HTML = """<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>@agentsatka_bot - 60% Shaffof Panel</title>
    <script src="https://telegram.org/js/telegram-web-app.js"></script>
    <style>
        :root {
            --bg-color: #0b0f19;
            --glass-bg: rgba(15, 23, 42, 0.60); /* Aniq 60% shaffoflik */
            --glass-border: rgba(255, 255, 255, 0.15);
            --accent-blue: #3b82f6;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
        }

        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            -webkit-tap-highlight-color: transparent;
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
        }

        body {
            background-color: var(--bg-color);
            background-image: 
                radial-gradient(circle at 10% 20%, rgba(59, 130, 246, 0.15) 0%, transparent 40%),
                radial-gradient(circle at 90% 80%, rgba(139, 92, 246, 0.15) 0%, transparent 40%);
            color: var(--text-main);
            min-height: 100vh;
            padding: 20px 80px 20px 20px; /* O'ng ustun uchun joy qoldirish */
            position: relative;
            overflow-x: hidden;
        }

        /* Asosiy ma'lumot kartochkasi */
        .content-card {
            background: rgba(30, 41, 59, 0.50);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 24px;
            margin-bottom: 20px;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
            animation: fadeIn 0.3s ease;
        }

        .header-title {
            font-size: 22px;
            font-weight: 700;
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
        }

        .header-desc {
            font-size: 14px;
            color: var(--text-muted);
            line-height: 1.5;
            margin-bottom: 18px;
        }

        .badge {
            display: inline-block;
            background: rgba(59, 130, 246, 0.2);
            color: #60a5fa;
            border: 1px solid rgba(59, 130, 246, 0.4);
            padding: 4px 10px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
            margin-bottom: 12px;
        }

        .btn-select {
            width: 100%;
            background: linear-gradient(135deg, #2563eb, #1d4ed8);
            color: #ffffff;
            border: none;
            padding: 14px 20px;
            border-radius: 14px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 4px 15px rgba(37, 99, 235, 0.35);
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 8px;
        }

        .btn-select:active {
            transform: scale(0.98);
        }

        /* O'NG YONGA USTUN SHAKLIDA 60% SHAFFOF PANEL */
        .glass-column {
            position: fixed;
            top: 50%;
            transform: translateY(-50%);
            right: 12px;
            width: 58px;
            background: var(--glass-bg); /* 60% shaffoflik */
            backdrop-filter: blur(16px);
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid var(--glass-border);
            border-radius: 24px;
            padding: 10px 4px;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.45);
            transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
            z-index: 1000;
        }

        /* Yashirin (Collapsed) holati */
        .glass-column.collapsed {
            right: -42px;
            background: rgba(15, 23, 42, 0.40);
        }

        .glass-column.collapsed .toggle-tab {
            transform: rotate(180deg);
        }

        .glass-column.collapsed .icon-badge {
            opacity: 0.3;
        }

        /* Yashirish / Ko'rsatish kichik tugmachasi */
        .toggle-tab {
            width: 26px;
            height: 26px;
            border-radius: 50%;
            background: rgba(255, 255, 255, 0.12);
            color: #cbd5e1;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 11px;
            cursor: pointer;
            border: 1px solid rgba(255, 255, 255, 0.15);
            transition: transform 0.3s ease, background 0.2s ease;
        }

        .toggle-tab:hover {
            background: rgba(255, 255, 255, 0.25);
        }

        /* Kichik belgichalar (miniature badges) */
        .icon-badge {
            width: 44px;
            height: 44px;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.08);
            border: 1px solid rgba(255, 255, 255, 0.1);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 20px;
            cursor: pointer;
            transition: all 0.2s ease;
            position: relative;
        }

        .icon-badge:hover {
            background: rgba(255, 255, 255, 0.18);
            transform: scale(1.05);
        }

        .icon-badge.active {
            background: rgba(59, 130, 246, 0.65);
            border-color: rgba(147, 197, 253, 0.8);
            box-shadow: 0 0 16px rgba(59, 130, 246, 0.6);
            transform: scale(1.08);
        }

        .hint-text {
            font-size: 13px;
            color: #64748b;
            text-align: center;
            margin-top: 15px;
        }

        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(6px); }
            to { opacity: 1; transform: translateY(0); }
        }
    </style>
</head>
<body>

    <div class="content-card">
        <div class="badge" id="cardBadge">⚡ FAOL BO'LIM</div>
        <div class="header-title" id="cardTitle">💼 Biznes</div>
        <div class="header-desc" id="cardDesc">
            Moliya, biznes reja, daromadlar tahlili, bozor va marketing strategiyalari boʻyicha maxsus ko'p sahifali bo'lim.
        </div>
        <button class="btn-select" id="btnSelect" onclick="confirmSelection()">
            <span>✅ Ushbu bo'limga o'tish</span>
        </button>
    </div>

    <div class="content-card" style="padding: 18px;">
        <div style="font-size: 14px; font-weight: 600; margin-bottom: 6px;">💡 Maslahat:</div>
        <div style="font-size: 13px; color: var(--text-muted); line-height: 1.4;">
            O'ng tomondagi 60% shaffof ustunda har bir bo'limning kichik belgichasi joylashgan. 
            Tepasidagi kichik <b>&gt;</b> tugmachasi orqali ustunni yashirib yoki ochib qo'yishingiz mumkin.
        </div>
    </div>

    <div class="hint-text">
        🔒 Faqat @satka8491 shaxsiy akkaunti uchun
    </div>

    <!-- O'NG YONGA USTUN SHAKLIDA 60% SHAFFOF PANEL -->
    <div class="glass-column" id="glassCol">
        <!-- Yashirish / Ko'rsatish kichik tugmasi -->
        <div class="toggle-tab" id="toggleBtn" onclick="toggleColumn()" title="Yashirish / Ko'rsatish">
            ▶
        </div>

        <!-- Kichik belgichalar -->
        <div class="icon-badge active" data-sec="biznes" onclick="selectSec('biznes')" title="Biznes">
            💼
        </div>
        <div class="icon-badge" data-sec="dasturlash" onclick="selectSec('dasturlash')" title="Dasturlash">
            💻
        </div>
        <div class="icon-badge" data-sec="tibbiyot" onclick="selectSec('tibbiyot')" title="Tibbiyot">
            🩺
        </div>
        <div class="icon-badge" data-sec="savollar" onclick="selectSec('savollar')" title="Savollar">
            ❓
        </div>
        <div class="icon-badge" data-sec="rejalar" onclick="selectSec('rejalar')" title="Rejalar">
            📋
        </div>
        <div class="icon-badge" data-sec="goyalar" onclick="selectSec('goyalar')" title="G'oyalar">
            💡
        </div>
    </div>

    <script>
        const tg = window.Telegram && window.Telegram.WebApp ? window.Telegram.WebApp : null;
        if (tg) {
            tg.ready();
            tg.expand();
        }

        const SECTIONS = {
            "biznes": {
                icon: "💼",
                title: "Biznes",
                desc: "Moliya, biznes reja, savdo va daromadlar hisob-kitobi boʻyicha maxsus yordamchi."
            },
            "dasturlash": {
                icon: "💻",
                title: "Dasturlash",
                desc: "Python kodlari, algoritmlar, arxitektura, xatolarni tahlil qilish va yechish."
            },
            "tibbiyot": {
                icon: "🩺",
                title: "Tibbiyot",
                desc: "Nevrologiya va neyrojarrohlik tarixi, darslar, tibbiy ilmiy adabiyotlar tahlili."
            },
            "savollar": {
                icon: "❓",
                title: "Savollar",
                desc: "Turli mavzudagi umumiy va chuqurlashtirilgan savol-javoblar uchun muloqot maydoni."
            },
            "rejalar": {
                icon: "📋",
                title: "Rejalar",
                desc: "Kunlik, haftalik va oylik maqsadlar, checklistlar va vazifalar taqvimi."
            },
            "goyalar": {
                icon: "💡",
                title: "G'oyalar",
                desc: "YouTube Shorts, Instagram Reels, startaplar va ijodiy innovatsion loyihalar."
            }
        };

        let currentSec = "biznes";
        let isCollapsed = false;

        function selectSec(secKey) {
            currentSec = secKey;
            const data = SECTIONS[secKey];
            if (!data) return;

            document.getElementById("cardTitle").innerText = `${data.icon} ${data.title}`;
            document.getElementById("cardDesc").innerText = data.desc;
            document.getElementById("cardBadge").innerText = `⚡ ${data.title.toUpperCase()}`;

            // Aktiv klassini yangilash
            document.querySelectorAll(".icon-badge").forEach(el => {
                if (el.getAttribute("data-sec") === secKey) {
                    el.classList.add("active");
                } else {
                    el.classList.remove("active");
                }
            });

            // Haptic tebranish agar Telegramda bo'lsa
            if (tg && tg.HapticFeedback) {
                tg.HapticFeedback.impactOccurred('light');
            }
        }

        function toggleColumn() {
            const col = document.getElementById("glassCol");
            const btn = document.getElementById("toggleBtn");
            isCollapsed = !isCollapsed;
            if (isCollapsed) {
                col.classList.add("collapsed");
                btn.innerText = "◀";
            } else {
                col.classList.remove("collapsed");
                btn.innerText = "▶";
            }
        }

        function confirmSelection() {
            if (tg) {
                tg.sendData(`sec_${currentSec}`);
                tg.close();
            } else {
                alert(`Tanlandi: ${SECTIONS[currentSec].title}`);
            }
        }
    </script>
</body>
</html>
"""
