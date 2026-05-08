import asyncio
import logging
import pytz
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from config import BOT_TOKEN, OWNER_ID
from database import init_db, close_db, get_all_birthdays, is_admin, get_all_user_birthdays, get_user_remind_settings
from utils import get_next_birthday, format_countdown, get_age, days_until_birthday, today_tashkent
import admin
import user

TASHKENT_TZ = pytz.timezone('Asia/Tashkent')

# Register logging
logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler(timezone=TASHKENT_TZ)

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext = None):
    # Check for deep link parameters
    args = message.text.split()
    if len(args) > 1 and args[1] == "set_bday":
        await message.answer("🎂 Tug'ilgan kuningizni `DD.MM.YYYY` yoki `DD.MM` formatida yuboring:\n\n(Masalan: `24.08.2005`)", parse_mode="Markdown")
        if state:
            await state.set_state(user.UserBdayState.waiting_for_bday)
        return

    is_user_admin = await is_admin(message.from_user.id) or message.from_user.id == OWNER_ID
    
    text = (f"👋 Salom {message.from_user.full_name}!\n\n"
            "🎂 Men tug'ilgan kunlarni eslatib turuvchi botman.\n\n"
            "📢 *Buyruqlar:*\n"
            "• `/add Ism - DD.MM.YYYY` — Tug'ilgan kun qo'shish\n"
            "• `/del Ism - DD.MM.YYYY` — Ro'yxatingizdan o'chirish\n"
            "• `/list` — Siz qo'shgan tug'ilgan kunlar\n"
            "• `/calendar` — Keyingi 30 kun ichidagi tug'ilgan kunlar\n"
            "• `/bday` — Shaxsiy tug'ilgan kuningizni bilish\n"
            "• `/remind_settings` — Eslatma vaqtini sozlash\n\n")
            
    if is_user_admin:
        text += ("🛠 *Admin buyruqlari:*\n"
                 "• `/admin` — Admin panelini ochish\n"
                 "• `/setadmin ID` — Yangi admin tayinlash\n\n")
    
    text += "💡 Bir vaqtning o'zida bir nechta odamni qo'shish uchun `/add` dan so'ng har birini yangi qatordan yozing.\n\n"
    text += "⏰ Eslatmalar 2 kun oldin, 1 kun oldin va tug'ilgan kuni soat 00:05 da yuboriladi."
    await message.answer(text, parse_mode="Markdown")

async def send_notification(name, day, month, year, chat_id, diff=None):
    next_bday = get_next_birthday(day, month)
    today = today_tashkent()
    if diff is None:
        diff = (next_bday - today).days
    
    target_chat = chat_id if chat_id else OWNER_ID 

    if diff == 0:
        age_text = f" ({get_age(year, today.year)} yosh)" if year else ""
        msg = (f"🥳 *Bugun quvonchli kun!* \n\n"
               f"🎈 Bugun *{name}*{age_text}ning tug'ilgan kuni! \n"
               f"Keling, uni birgalikda tabriklaymiz! 🍰✨")
    elif diff == 1:
        countdown = format_countdown(next_bday)
        msg = (f"⏳ *Eslatma!* \n\n"
               f"🎁 Ertaga *{name}*ning tug'ilgan kuni! \n"
               f"Tug'ilgan kungacha: `{countdown}` qoldi. \n"
               f"Tayyorgarlikni ko'ring! 🎊")
    elif diff == 2:
        countdown = format_countdown(next_bday)
        msg = (f"🗓 *Yaqinlashmoqda!* \n\n"
               f"💠 2 kundan keyin *{name}*ning tug'ilgan kuni! \n"
               f"Tug'ilgan kungacha: `{countdown}` qoldi. \n"
               f"Sovg'a haqida o'ylash vaqti keldi! 🧸")
    elif diff == 7:
        msg = (f"🔔 *1 hafta qoldi!* \n\n"
               f"📅 *{name}*ning tug'ilgan kuniga 1 hafta qoldi! \n"
               f"Erta tayyorgarlik ko'rsangiz yaxshi! 🎁")
    else:
        countdown = format_countdown(next_bday)
        msg = (f"🔔 *Eslatma!* \n\n"
               f"📅 *{diff} kundan* keyin *{name}*ning tug'ilgan kuni! \n"
               f"Tug'ilgan kungacha: `{countdown}` qoldi.")
    await bot.send_message(target_chat, msg, parse_mode="Markdown")

async def check_birthdays_for_chat(target_chat_id):
    birthdays = await get_all_birthdays()
    for name, day, month, year, chat_id, added_by in birthdays:
        if chat_id == target_chat_id:
            remind_days = await get_user_remind_settings(added_by)
            today = today_tashkent()
            diff = (get_next_birthday(day, month) - today).days
            if diff in remind_days:
                await send_notification(name, day, month, year, chat_id, diff)

async def check_birthdays():
    birthdays = await get_all_birthdays()
    for name, day, month, year, chat_id, added_by in birthdays:
        remind_days = await get_user_remind_settings(added_by)
        today = today_tashkent()
        diff = (get_next_birthday(day, month) - today).days
        if diff in remind_days:
            await send_notification(name, day, month, year, chat_id, diff)

async def daily_user_reminders():
    user_birthdays = await get_all_user_birthdays()
    for user_id, name, day, month, year in user_birthdays:
        days = days_until_birthday(day, month)
        remind_days = await get_user_remind_settings(user_id)
        if days not in remind_days:
            continue
        try:
            if days == 0:
                msg = f"🥳 *Bugun quvonchli kun!* \n\n🌟 {name}, tug'ilgan kuningiz muborak bo'lsin! 🍰✨"
            elif days == 7:
                msg = f"🔔 *Eslatma!* \n\n🌟 {name}, tug'ilgan kuningizga *1 hafta* qoldi! 🎁"
            else:
                msg = f"⏰ *Eslatma!* \n\n🌟 {name}, tug'ilgan kuningizga *{days} kun* qoldi! 🎁"
            await bot.send_message(user_id, msg, parse_mode="Markdown")
        except Exception as e:
            logging.error(f"Failed to send daily reminder to {user_id}: {e}")

async def main():
    # Initialize DB
    await init_db()
    
    # Include routers
    dp.include_router(admin.router)
    dp.include_router(user.router)
    
    # Schedule birthday checks at 00:05 every day
    scheduler.add_job(check_birthdays, 'cron', hour=0, minute=5, timezone=TASHKENT_TZ)
    
    # Schedule daily personal reminders at 08:08 every day (Tashkent time)
    scheduler.add_job(daily_user_reminders, 'cron', hour=8, minute=8, timezone=TASHKENT_TZ)
    
    # Also add a job to check 1, 2 days before at a reasonable time or 00:05 as well
    # The prompt says 2 days before and 1 day before. 
    # Let's say we check at 00:05 for everything.
    
    scheduler.start()
    
    logging.info("Bot is starting...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("Bot stopped!")
    finally:
        asyncio.run(close_db())
