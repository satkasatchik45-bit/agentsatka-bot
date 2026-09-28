---
name: savdo_hisob_kitob
description: #savdo tegi bilan kelgan matnli yoki rasmli ro'yxatlarni tahlil qilib, hisob-kitobini #jadval tegi ostida chiroyli jadval ko'rinishida chiqarish.
triggers: ['#savdo', 'savdo', '#jadval']
---

# Ko'nikma: savdo_hisob_kitob

## 🎯 Tavsif
#savdo tegi bilan kelgan matnli yoki rasmli ro'yxatlarni tahlil qilib, hisob-kitobini #jadval tegi ostida chiroyli jadval ko'rinishida chiqarish.

## 📋 Ko'rsatma va Algoritm
1. Foydalanuvchi #savdo tegi bilan kelgan xabar yoki rasmni qabul qilganda, undagi barcha mahsulotlar nomi, soni/miqdori va narxini aniqlang.
2. Har bir pozitsiya uchun: Jami = Miqdor * Narx formulasi bo'yicha hisoblang.
3. Barcha pozitsiyalar bo'yicha umumiy Jami summani hisoblang.
4. Javobni har doim '#jadval' xesh-tegi bilan boshlang yoki saravhada ko'rsating.
5. Ma'lumotlarni tushunarli Markdown jadvali ko'rinishida (Nomer, Mahsulot, Miqdor, Narxi, Summa) va yakuniy umumiy summa bilan taqdim eting.
