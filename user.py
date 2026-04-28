from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import set_user_birthday, get_user_birthday, get_user_remind_settings, set_user_remind_settings
from utils import days_until_birthday
import re

router = Router()

REMIND_OPTIONS = [
    (0,  "Tug'ilgan kuni 🥳"),
    (1,  "1 kun oldin ⏳"),
    (2,  "2 kun oldin 🗓"),
    (7,  "1 hafta oldin 🔔"),
]

def build_remind_keyboard(active_days: list):
    buttons = []
    for day, label in REMIND_OPTIONS:
        mark = "✅" if day in active_days else "☑️"
        buttons.append([InlineKeyboardButton(
            text=f"{mark} {label}",
            callback_data=f"remind_toggle_{day}"
        )])
    buttons.append([InlineKeyboardButton(text="💾 Saqlash", callback_data="remind_save")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

class UserBdayState(StatesGroup):
    waiting_for_bday = State()

@router.message(Command("bday"))
async def bday_handler(message: Message, state: FSMContext, bot: Bot):
    if message.chat.type != 'private':
        # Group handling
        user_data = await get_user_birthday(message.from_user.id)
        if user_data:
            name, day, month, year = user_data
            days = days_until_birthday(day, month)
            if days == 0:
                await message.reply(f"🎂 Bugun sizning tug'ilgan kuningiz! Tabriklaymiz!")
            else:
                await message.reply(f"🎈 {message.from_user.first_name}, sizning tug'ilgan kuningizga *{days} kun* qoldi! ✨", parse_mode="Markdown")
        else:
            bot_info = await bot.get_me()
            markup = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎁 Tug'ilgan kunni qo'shish", url=f"https://t.me/{bot_info.username}?start=set_bday")]
            ])
            await message.reply("⚠️ Avval tug'ilgan kuningizni bot lichkasida qo'shing!", reply_markup=markup)
        return

    # Private chat handling
    await message.answer("🎂 Tug'ilgan kuningizni `DD.MM.YYYY` yoki `DD.MM` formatida yuboring:\n\n(Masalan: `24.08.2005`)", parse_mode="Markdown")
    await state.set_state(UserBdayState.waiting_for_bday)

@router.message(UserBdayState.waiting_for_bday)
async def process_user_bday(message: Message, state: FSMContext):
    # Regex to check DD.MM.YYYY or DD.MM
    match = re.match(r"^(\d{2})\.(\d{2})\.?(\d{4})?$", message.text.strip())
    if match:
        day = int(match.group(1))
        month = int(match.group(2))
        year = int(match.group(3)) if match.group(3) else None
        
        # Simple validation
        if not (1 <= day <= 31 and 1 <= month <= 12):
            await message.answer("❌ Noto'g'ri sana! Iltimos, haqiqiy sanani kiriting.")
            return

        await set_user_birthday(message.from_user.id, message.from_user.first_name, day, month, year)
        days = days_until_birthday(day, month)
        
        if days == 0:
            resp = f"✅ Saqlandi! \n\n🎂 *Bugun sizning tug'ilgan kuningiz!* Tabriklaymiz! ✨🎉"
        else:
            resp = f"✅ Saqlandi! \n\n🌟 {message.from_user.first_name}, sizning tug'ilgan kuningizga *{days} kun* qoldi! 🎉"
            
        await message.answer(resp, parse_mode="Markdown")
        await state.clear()
    else:
        await message.answer("❌ Noto'g'ri format! Iltimos, `DD.MM.YYYY` formatida kiriting (masalan: `24.08.2005`).")

@router.message(Command("remind_settings"))
async def remind_settings_handler(message: Message):
    current = await get_user_remind_settings(message.from_user.id)
    markup = build_remind_keyboard(current)
    await message.answer(
        "🔔 *Eslatma sozlamalari*\n\n"
        "Qachon eslatma olishni xohlaysiz?\n"
        "_(Bir nechta variant tanlash mumkin)_",
        reply_markup=markup,
        parse_mode="Markdown"
    )

@router.callback_query(F.data.startswith("remind_toggle_"))
async def remind_toggle_handler(call: CallbackQuery):
    day = int(call.data.split("_")[2])
    current = await get_user_remind_settings(call.from_user.id)

    if day in current:
        current.remove(day)
    else:
        current.append(day)

    await set_user_remind_settings(call.from_user.id, current)
    markup = build_remind_keyboard(current)
    await call.message.edit_reply_markup(reply_markup=markup)
    await call.answer("✅ O'zgartirildi!")

@router.callback_query(F.data == "remind_save")
async def remind_save_handler(call: CallbackQuery):
    current = await get_user_remind_settings(call.from_user.id)
    labels = [label for day, label in REMIND_OPTIONS if day in current]
    if labels:
        text = "✅ *Sozlamalar saqlandi!*\n\n🔔 Eslatmalar:\n" + "\n".join(f"• {l}" for l in labels)
    else:
        text = "⚠️ Hech qanday eslatma tanlanmagan!\nKamida bittasini tanlang."
    await call.message.edit_text(text, parse_mode="Markdown")
    await call.answer("💾 Saqlandi!")
