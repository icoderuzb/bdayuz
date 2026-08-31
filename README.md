# 🎂 Birthday Reminder Bot (Tug'ilgan kunlarni eslatuvchi bot)

Telegram foydalanuvchilari va guruhlar uchun yaqinlar, do'stlar hamda shaxsiy tug'ilgan kunlarni eslab qoluvchi va o'z vaqtida avtomatik tabriknoma va eslatmalar yuboruvchi asinxron Telegram boti.

---

## 📌 Mundarija
1. [Loyiha haqida](#-loyiha-haqida)
2. [Asosiy imkoniyatlar](#-asosiy-imkoniyatlar)
3. [Botning ishlash tartibi va logikasi](#-botning-ishlash-tartibi-va-logikasi)
4. [Mavjud buyruqlar](#-mavjud-buyruqlar)
5. [Loyiha tuzilishi](#-loyiha-tuzilishi)
6. [Ma'lumotlar bazasi strukturasi](#-malumotlar-bazasi-strukturasi)
7. [O'rnatish va ishga tushirish](#-ornatish-va-ishga-tushirish)
8. [Muhit o'zgaruvchilari (.env)](#-muhit-ozgaruvchilari-env)

---

## 🌟 Loyiha haqida

Ushbu bot **Python 3**, **Aiogram 3**, **PostgreSQL** (`asyncpg`) va **APScheduler** yordamida qurilgan. Barcha vaqt hisob-kitoblari va eslatmalar **Toshkent vaqt mintaqasi (`Asia/Tashkent`)** asosida ishlaydi.

Bot quyidagi masalalarni to'liq avtomatlashtiradi:
- Do'stlar, qarindoshlar yoki guruh a'zolarining tug'ilgan kunlarini ro'yxatga olish;
- Guruhlarga aynan tug'ilgan kuni soat 00:05 da tabriknoma va bayramona GIF animatsiyalar yuborish (ortiqcha oldindan eslatmalarsiz);
- Foydalanuvchining o'z tug'ilgan kuni haqida esa shaxsiy sozlamalariga ko'ra ertalab 08:08 da oldindan eslatib turish.

---

## 🚀 Asosiy imkoniyatlar

- **Ko'p qatorli qo'shish:** `/add` buyrug'i orqali bir vaqtning o'zida o'nlab kishilarni yangi qatordan kiritish imkoniyati.
- **Moslashuvchan sana formatlari:** `DD.MM.YYYY` (yil bilan) yoki `DD.MM` (yilsiz).
- **Kabisa yili va sanalar validatsiyasi:** 29-fevral va noto'g'ri kiritilgan sanalarni to'g'ri tekshirish.
- **Soddalashtirilgan guruh eslatmalari:** Guruhlarda faqat tug'ilgan kuni soat 00:05 da tabrik + yosh + GIF jo'natiladi.
- **Shaxsiy eslatma sozlamalari:** Har bir foydalanuvchi o'z tug'ilgan kuni uchun qachon eslatma olishni (0, 1, 2, 7 kun oldin) inline tugmalar orqali sozlashi mumkin (`/remind_settings`).
- **Taqvim va oraliq ko'rinishi:** Keyingi 30 kun ichida kimlarning tug'ilgan kuni borligini qulay formatda ko'rish (`/calendar`).
- **Guruh va shaxsiy chat integratsiyasi:** Guruhda `/bday` yozilganda, foydalanuvchi ma'lumoti bo'lmasa, uni botning shaxsiy chatiga yo'naltiruvchi maxsus havola (Deep Linking).
- **Admin paneli:** Bot egasi (`OWNER_ID`) va qo'shimcha adminlar tizimi.

---

## ⚙️ Botning ishlash tartibi va logikasi

```mermaid
flowchart TD
    A[Foydalanuvchi / Guruh] -->|Tug'ilgan kun kiritadi /add| B[(PostgreSQL: birthdays)]
    A -->|Shaxsiy sozlamalar /remind_settings| C[(PostgreSQL: user_settings)]
    
    subgraph Scheduler [APScheduler - Har kuni avtomatik]
        T1["00:05 (Toshkent vaqti)"] -->|check_birthdays| D[Guruh tug'ilgan kunlarini tekshirish]
        T2["08:08 (Toshkent vaqti)"] -->|daily_user_reminders| E[Shaxsiy eslatmalarni tekshirish]
    end
    
    D -->|diff == 0 (Aynan bugun)| F[🥳 Tabrik xabari + Yoshi + GIF]
    F --> G[Guruh / Chatga yuborish]
    
    E -->|diff in remind_days| H{Qancha vaqt qoldi?}
    H -->|0 kun (Bugun)| I[🥳 Tabrik xabari]
    H -->|7 kun qoldi| J[🔔 1 hafta qoldi eslatmasi]
    H -->|N kun qoldi| K[⏰ N kun qoldi eslatmasi]
    
    I --> L[Foydalanuvchiga shaxsiy yuborish]
    J --> L
    K --> L
```

### 1. Tug'ilgan kun qo'shish tartibi
1. Foydalanuvchi `/add Ism Familiya - DD.MM.YYYY` ko'rinishida yozadi.
2. Bot RegEx orqali matnni tahlil qiladi va sananing haqiqiyligini tekshiradi (`date(year, month, day)`).
3. Ma'lumot `birthdays` jadvaliga yoziladi (`chat_id` va `added_by` saqlanadi).
4. Ma'lumot saqlanishi bilanoq joriy chat uchun darhol tekshiruv chaqiriladi (agar bugun bo'lsa, darhol tabriklanadi).

### 2. Eslatmalar yuborish mexanizmi
- **Guruh / umumiy eslatmalar (`00:05` da):**
  - Har kecha soat 00:05 da `check_birthdays()` ishga tushadi.
  - `birthdays` jadvalidan `days_until_birthday(day, month) == 0` (aynan bugun) bo'lgan yozuvlar aniqlanadi.
  - O'sha chatga tabriknoma, insonning yoshi hisoblanib va bayramona GIF animatsiya jo'natiladi.
- **Shaxsiy eslatmalar (`08:08` da):**
  - Har kuni ertalab 08:08 da `daily_user_reminders()` ishga tushadi.
  - `user_birthdays` dagi har bir foydalanuvchining shaxsiy `remind_days` sozlamalari (0, 1, 2, 7 kun) tekshirilib, mos xabar yuboriladi.

---

## 📋 Mavjud buyruqlar

### 👤 Foydalanuvchi buyruqlari:
| Buyruq | Tavsif | Namuna |
| :--- | :--- | :--- |
| `/start` | Botni ishga tushirish va qo'llanmani ko'rish | `/start` |
| `/add` | Bitta yoki bir nechta tug'ilgan kunni qo'shish | `/add Alisher Navoiy - 09.02.1441` |
| `/del` | O'zingiz qo'shgan tug'ilgan kunni o'chirish | `/del Alisher Navoiy - 09.02.1441` |
| `/list` | Siz qo'shgan barcha tug'ilgan kunlar ro'yxati | `/list` |
| `/calendar` | Keyingi 30 kun ichidagi tug'ilgan kunlar taqvimi | `/calendar` |
| `/bday` | O'z tug'ilgan kuningizni kiritish / qolgan vaqtni bilish | `/bday` |
| `/remind_settings` | Qaysi kunlarda eslatma olishni sozlash | `/remind_settings` |

### 🛠 Admin buyruqlari (Faqat Adminlar uchun):
| Buyruq | Tavsif | Namuna |
| :--- | :--- | :--- |
| `/admin` | Admin panelini ochish (Adminlar ro'yxati va boshqaruv) | `/admin` |
| `/setadmin ID` | Yangi admin tayinlash (Faqat Bot egasi uchun) | `/setadmin 123456789` |

---

## 📂 Loyiha tuzilishi

```text
bday-reminder/
├── main.py              # Botning asosiy kirish nuqtasi, scheduler va bildirishnomalar
├── admin.py             # Admin paneli, /add, /del, /list, /calendar handlerlari
├── user.py              # Foydalanuvchi shaxsiy tug'ilgan kuni (/bday) va /remind_settings
├── database.py          # PostgreSQL asinxron ulanish puli va barcha DB funksiyalari
├── utils.py             # Vaqt hisob-kitoblari (Toshkent vaqti, yosh, countdown)
├── config.py            # .env o'qish va asosiy konfiguratsiya sozlamalari
├── requirements.txt     # Kerakli Python kutubxonalari
├── .env                 # Maxfiy tokenlar va DB ulanish parametrlari
└── README.md            # Loyiha hujjatlari va yo'riqnoma
```

---

## 🗄 Ma'lumotlar bazasi strukturasi

Bot PostgreSQL ma'lumotlar bazasida 4 ta asosiy jadvaldan foydalanadi:

### 1. `birthdays` (Umumiy qo'shilgan tug'ilgan kunlar)
- `id` (SERIAL PRIMARY KEY) — Yozuv ID raqami
- `name` (TEXT) — Shaxsning ismi/familiyasi
- `day` (INTEGER) — Tug'ilgan kuni
- `month` (INTEGER) — Tug'ilgan oyi
- `year` (INTEGER) — Tug'ilgan yili (ixtiyoriy)
- `chat_id` (BIGINT) — Qaysi guruh/chatga yuborilishi
- `added_by` (BIGINT) — Kim tomonidan qo'shilganligi

### 2. `user_birthdays` (Foydalanuvchilarning o'z tug'ilgan kunlari)
- `user_id` (BIGINT PRIMARY KEY) — Foydalanuvchi Telegram ID si
- `name` (TEXT) — Ismi
- `day` (INTEGER), `month` (INTEGER), `year` (INTEGER)

### 3. `user_settings` (Eslatma sozlamalari)
- `user_id` (BIGINT PRIMARY KEY) — Telegram ID
- `remind_days` (TEXT JSON) — Tanlangan kunlar ro'yxati (default: `[0, 1, 2]`)

### 4. `admins` (Adminlar ro'yxati)
- `user_id` (BIGINT PRIMARY KEY) — Admin ID si
- `can_manage_admins` (BOOLEAN) — Boshqa adminlarni boshqara olish huquqi
- `permissions` (TEXT JSON) — Qo'shimcha ruxsatlar

---

## 🛠 O'rnatish va ishga tushirish

### 1. Repozitoriyani yuklab olish
```bash
git clone <repo-url>
cd "bday reminder"
```

### 2. Virtual muhitni yaratish va faollashtirish
```bash
# Windows:
python -m venv venv
venv\Scripts\activate

# Linux / MacOS:
python3 -m venv venv
source venv/bin/activate
```

### 3. Bog'liqliklarni o'rnatish
```bash
pip install -r requirements.txt
```

### 4. `.env` faylini sozlash
Loyihaning asosiy papkasida `.env` faylini yarating va quyidagi ma'lumotlarni to'ldiring:
```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
OWNER_ID=123456789
DATABASE_URL=postgresql://postgres:parol@localhost:5432/bday_db
```

### 5. Botni ishga tushirish
```bash
python main.py
```

---

## 🔐 Muhit o'zgaruvchilari (.env)

| O'zgaruvchi | Tavsif | Majburiy |
| :--- | :--- | :---: |
| `BOT_TOKEN` | @BotFather orqali olingan Telegram Bot Token | Ha |
| `OWNER_ID` | Bot asosiy egasining Telegram ID raqami | Ha |
| `DATABASE_URL` | PostgreSQL ulanish URL manzili (`postgresql://user:pass@host:port/db`) | Ha |

---

Developed with ❤️ using **Python**, **Aiogram 3** & **PostgreSQL**.
