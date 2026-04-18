from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from database import add_birthday, add_admin, is_admin, get_admin_data, get_all_admins, remove_admin, delete_birthday, get_all_birthdays, get_user_added_birthdays
from config import OWNER_ID
import re

router = Router()

def parse_birthday_line(line):
    # Format: Name Surname - DD.MM.YYYY or DD.MM
    match = re.match(r"^(.*?)\s*-\s*(\d{2})\.(\d{2})\.?(\d{4})?$", line.strip())
    if match:
        name = match.group(1).strip()
        day = int(match.group(2))
        month = int(match.group(3))
        year = int(match.group(4)) if match.group(4) else None
        return name, day, month, year
    return None

@router.message(Command("add"))
async def add_bday_handler(message: Message):
    text = message.text.replace("/add", "").strip()
    if not text:
        await message.answer("⚠️ Iltimos, ma'lumotlarni quyidagi formatda kiriting:\n\n"
                             "`/add Komiljonov Ibrohim - 24.08.2005`\n"
                             "yoki bir nechta:\n"
                             "`/add \nKomiljonov Ibrohim - 24.08.2005\nAli - 12.12.2000`", parse_mode="Markdown")
        return

    lines = text.split("\n")
    added_count = 0
    errors = []

    for line in lines:
        parsed = parse_birthday_line(line)
        if parsed:
            name, day, month, year = parsed
            await add_birthday(name, day, month, year, message.chat.id, message.from_user.id)
            added_count += 1
        else:
            errors.append(line)

    resp = f"✅ {added_count} ta tug'ilgan kun muvaffaqiyatli saqlandi! 🎉"
    if errors:
        resp += f"\n\n❌ Quyidagi qatorlarni tushuna olmadim:\n" + "\n".join(errors)
    
    await message.answer(resp)
    # Trigger a check for the current chat immediately
    from main import check_birthdays_for_chat
    await check_birthdays_for_chat(message.chat.id)

@router.message(Command("del"))
async def del_bday_handler(message: Message):
    text = message.text.replace("/del", "").strip()
    if not text:
        await message.answer("⚠️ Iltimos, o'chirish uchun ma'lumotni quyidagi formatda kiriting:\n\n"
                             "`/del Ism Familiya - DD.MM.YYYY`", parse_mode="Markdown")
        return

    parsed = parse_birthday_line(text)
    if parsed:
        name, day, month, year = parsed
        await delete_birthday(name, day, month, message.from_user.id)
        await message.answer(f"🗑 *{name}* sizning ro'yxatingizdan o'chirildi.", parse_mode="Markdown")
    else:
        await message.answer("❌ Noto'g'ri format. Iltimos, `/add` dagi kabi formatdan foydalaning.")

@router.message(Command("list"))
async def list_bdays_handler(message: Message):
    bdays = await get_user_added_birthdays(message.from_user.id)
    if not bdays:
        await message.answer("📭 Siz hali hech qanday tug'ilgan kun qo'shmagansiz.")
        return

    text = "📅 *Siz qo'shgan tug'ilgan kunlar:* \n\n"
    for name, day, month, year, chat_id in bdays:
        year_str = f".{year}" if year else ""
        text += f"• ` {name} - {day:02d}.{month:02d}{year_str} `\n"
    
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("admin"))
async def admin_panel(message: Message):
    if message.from_user.id != OWNER_ID and not await is_admin(message.from_user.id):
        return

    markup = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👥 Adminlar ro'yxati", callback_data="list_admins")],
        [InlineKeyboardButton(text="➕ Admin qo'shish", callback_data="add_admin_prompt")]
    ])
    
    await message.answer("🛠 *Admin Panel*\n\nBoshqarish uchun tugmalardan foydalaning:", 
                         reply_markup=markup, parse_mode="Markdown")

@router.callback_query(F.data == "list_admins")
async def list_admins_handler(call: CallbackQuery):
    admins = await get_all_admins()
    text = "📋 *Adminlar ro'yxati:*\n\n"
    for uid, can_manage in admins:
        status = "👑 (Asosiy)" if uid == OWNER_ID else ("🛠 (Huquqli)" if can_manage else "👤 (Oddiy)")
        text += f"• `{uid}` {status}\n"
    
    await call.message.edit_text(text, parse_mode="Markdown")

@router.callback_query(F.data == "add_admin_prompt")
async def add_admin_prompt(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        await call.answer("❌ Sizda bu huquq yo'q!", show_alert=True)
        return
    
    await call.message.edit_text("👤 Yangi adminning Telegram ID sini kiritish uchun `/setadmin ID` buyrug'idan foydalaning.\n\n"
                                 "Masalan: `/setadmin 12345678`", parse_mode="Markdown")

@router.message(Command("setadmin"))
async def set_admin_handler(message: Message):
    if message.from_user.id != OWNER_ID:
        return

    args = message.text.split()
    if len(args) < 2:
        await message.answer("⚠️ ID ko'rsatilmadi. Masalan: `/setadmin 12345678`")
        return

    try:
        new_admin_id = int(args[1])
        await add_admin(new_admin_id, can_manage_admins=False)
        
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Huquq berish (Admin boshqarish)", callback_data=f"perm_manage_{new_admin_id}")],
            [InlineKeyboardButton(text="❌ Huquqni olib tashlash", callback_data=f"perm_none_{new_admin_id}")],
            [InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"remove_admin_{new_admin_id}")]
        ])
        
        await message.answer(f"✅ Foydalanuvchi `{new_admin_id}` admin sifatida qo'shildi!\n"
                             "Uning huquqlarini sozlang:", reply_markup=markup, parse_mode="Markdown")
    except ValueError:
        await message.answer("❌ Noto'g'ri ID!")

@router.callback_query(F.data.startswith("perm_manage_"))
async def perm_manage_handler(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    admin_id = int(call.data.split("_")[2])
    await add_admin(admin_id, can_manage_admins=True)
    await call.answer("✅ Huquq berildi!", show_alert=True)
    await call.message.edit_text(f"✅ Admin `{admin_id}` endi boshqa adminlarni boshqara oladi.")

@router.callback_query(F.data.startswith("remove_admin_"))
async def remove_admin_handler(call: CallbackQuery):
    if call.from_user.id != OWNER_ID:
        return
    admin_id = int(call.data.split("_")[2])
    await remove_admin(admin_id)
    await call.answer("🗑 Admin o'chirildi!", show_alert=True)
    await call.message.edit_text(f"🗑 Admin `{admin_id}` ro'yxatdan o'chirildi.")
