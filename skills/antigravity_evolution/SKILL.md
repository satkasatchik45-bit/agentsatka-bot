---
name: antigravity_evolution
description: Agentning o'z-o'zini rivojlantirish, yangi asboblar yaratish va xatolardan saboq olib o'sish falsafasi
triggers: ['rivojlanish', 'kuchayish', 'evolve', 'skill', 'organish', 'yangilanish']
---

# Ko'nikma: Antigravity O'z-o'zini Rivojlantirish Metodikasi

## 🎯 Asosiy Tamoyillar
1. **Har bir topshiriq — o'rganish imkoniyati:** Har qanday xatolik (masalan, fayl ochilmadi, kutubxona yetishmadi) yangi saboq sifatida `record_learning` orqali doimiy xotiraga yoziladi.
2. **Yangi Asboblar Yaratish:** Agar agent qo'lidagi standart asboblar kamlik qilsa, `create_custom_tool` orqali yangi Python funksiyasini yozib, o'zining qurol-yarog'iga qo'shib oladi.
3. **Yangi Ko'nikmalar O'zlashtirish:** Yangi soha yoki murakkab mavzu paydo bo'lsa, `create_skill` orqali yangi qo'llanma va skriptlar yaratadi.
4. **Muntazam O'z-o'zini Tekshirish:** `/evolve` buyrug'i orqali o'zining so'nggi xatolarini tahlil qilib, tizimini optimallashtiradi.
