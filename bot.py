import os
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# .env faylidan o'zgaruvchilarni yuklash
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
Sizning_Tel = os.getenv("MY_PHONE")
Sizning_User = os.getenv("MY_USERNAME")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Ro'yxatdan o'tish bosqichlari (FSM)
class Registration(StatesGroup):
    waiting_for_name = State()
    waiting_for_surname = State()

# Maxsus insonlar ro'yxati
SPECIAL_USERS = [
    {"name": "Sabrina", "surname": "Nuraliyeva"},
    {"name": "Hosila", "surname": "Bo'riyeva"},
    {"name": "Hosila", "surname": "Boriyeva"} 
]

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer(
        "Xush kelibsiz! Botdan foydalanish uchun roʻyxatdan oʻtishingiz kerak.\n\n"
        "Iltimos, ismingizni kiriting:"
    )
    await state.set_state(Registration.waiting_for_name)

@dp.message(Registration.waiting_for_name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip())
    await message.answer("Rahmat. Endi familiyangizni kiriting:")
    await state.set_state(Registration.waiting_for_surname)

@dp.message(Registration.waiting_for_surname)
async def process_surname(message: types.Message, state: FSMContext):
    await state.update_data(surname=message.text.strip())
    
    user_data = await state.get_data()
    await state.clear() 

    input_name = user_data['name'].lower()
    input_surname = user_data['surname'].lower()

    is_special = False
    for user in SPECIAL_USERS:
        if input_name == user['name'].lower() and input_surname == user['surname'].lower():
            is_special = True
            break

    if is_special:
        love_message = (
            "Men seni doimo sevganman bu bizning botimiz bu botni sen uchun ochganman "
            "Menga sendan boshqasi kerakmas iltimos menga qayt 🥺\n\n"
            "👉 Bot egasidan"
        )
        
        builder = InlineKeyboardBuilder()
        builder.row(
            types.InlineKeyboardButton(text="📞 Telefon orqali bogʻlanish", url=f"tel:{Sizning_Tel}")
        )
        builder.row(
            types.InlineKeyboardButton(text="✈️ Telegram orqali bogʻlanish", url=f"https://t.me/{Sizning_User}")
        )
        
        await message.answer(love_message, reply_markup=builder.as_markup())
    else:
        await message.answer("Roʻyxatdan muvaffaqiyatli oʻtdingiz. Bot tez orada ishga tushadi.")

async def main():
    print("Bot muvaffaqiyatli ishga tushdi...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())