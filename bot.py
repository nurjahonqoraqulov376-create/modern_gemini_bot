import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)
from google import genai
from google.genai import types

# .env faylidan kalitlarni yuklash
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OWNER_CHAT_ID = int(os.getenv("OWNER_CHAT_ID", "0"))

# Loglarni sozlash
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Yangi Rasmiy Google GenAI Klienti
ai_client = genai.Client(api_key=GEMINI_API_KEY)

# Suhbatlar xotirasi (Chat tarixi)
chats: dict = {}


def is_owner(chat_id: int) -> bool:
    return chat_id == OWNER_CHAT_ID


async def ask_gemini(chat_id: int, user_message: str) -> str:
    """Google Gemini modelidan jonli qidiruv (Google Search) bilan javob olish"""
    try:
        # Har bir foydalanuvchi uchun alohida chat sessiyasi ochiladi (kontekst uchun)
        if chat_id not in chats:
            chats[chat_id] = ai_client.chats.create(
                model="gemini-2.5-flash",
                config=types.GenerateContentConfig(
                    system_instruction=(
                        "Siz foydali, aqlli va do'stona AI yordamchisiz. "
                        "Foydalanuvchi qaysi tilda yozsa, o'sha tilda chiroyli javob bering. "
                        "Sizda Google Search funksiyasi bor, ob-havo yoki yangiliklar so'ralsa, "
                        "jonli internet ma'lumotlaridan foydalaning."
                    ),
                    # MANA SHU JOYI GOOGLE QIDIRUVINI YOQIB BERADI (Ob-havo va h.k. uchun)
                    tools=[{"google_search": {}}]
                )
            )

        # AI'ga xabarni yuborish
        response = chats[chat_id].send_message(user_message)
        return response.text

    except Exception as e:
        logger.error(f"Gemini API xatosi: {e}")
        return "❌ Sun'iy intellekt bilan bog'lanishda xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring."


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id

    if is_owner(chat_id):
        await update.message.reply_text(
            f"👋 Salom, Xo'jayin!\n\n"
            f"🤖 Yangi zamonaviy Gemini botingiz muvaffaqiyatli ishga tushdi!\n"
            f"Internet qidiruvi (Google Search) faol. Ob-havo va yangiliklarni ham biladi.\n\n"
            f"📋 Buyruqlar:\n"
            f"• /start — Qayta ishga tushirish\n"
            f"• /status — Bot holati",
            parse_mode="HTML"
        )
    else:
        # Egaga xabar berish (Yangi odam keldi)
        try:
            await context.bot.send_message(
                chat_id=OWNER_CHAT_ID,
                text=f"🔔 <b>Yangi foydalanuvchi!</b>\n"
                     f"👤 Ism: {user.first_name}\n"
                     f"🆔 Username: @{user.username if user.username else 'yoq'}\n"
                     f"📋 Chat ID: <code>{chat_id}</code>",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Egani ogohlantirishda xato: {e}")

        await update.message.reply_text(
            f"👋 Salom, {user.first_name}!\n\n"
            f"🤖 Men zamonaviy Google Gemini AI yordamchisiman.\n"
            f"Menga istalgan savolingizni berishingiz mumkin.\n"
            f"Jonli ob-havo, valyuta kurslari va yangiliklarni ham topib bera olaman! 🌍"
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    text = update.message.text

    # "Typing..." animatsiyasini chiqarish
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    if is_owner(chat_id):
        # Ega yozganda AI javobi
        response = await ask_gemini(chat_id, text)
        await update.message.reply_text(response)
    else:
        # Boshqalar yozganda ham AI javob beradi + Egaga nusxasi boradi
        try:
            keyboard = [[InlineKeyboardButton("💬 Javob berish", callback_data=f"reply_{chat_id}")]]
            await context.bot.send_message(
                chat_id=OWNER_CHAT_ID,
                text=f"📩 <b>Foydalanuvchidan xabar:</b>\n"
                     f"👤 {user.first_name} (@{user.username if user.username else chat_id})\n\n"
                     f"💬 <i>{text}</i>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Egaga xabar nusxasini yuborishda xato: {e}")

        # Foydalanuvchiga AI'dan javob
        response = await ask_gemini(chat_id, text)
        await update.message.reply_text(response)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_chat.id):
        return
    now = datetime.now().strftime("%H:%M, %d.%m.%Y")
    await update.message.reply_text(
        f"📊 <b>Bot Holati:</b>\n\n"
        f"🟢 Status: Faol va ishlamoqda\n"
        f"🕐 Vaqt: {now}\n"
        f"🤖 AI Model: Google Gemini 2.5 Flash\n"
        f"🌐 Google Search: Yoqilgan (Onlayn)",
        parse_mode="HTML"
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("reply_"):
        target_id = int(query.data.split("_")[1])
        context.user_data["reply_to_user"] = target_id
        await query.message.reply_text(
            f"✏️ Foydalanuvchiga javobingizni yozing (ID: {target_id}):\n"
            f"Bekor qilish uchun /cancel yozing."
        )


async def handle_owner_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    if not is_owner(chat_id) or "reply_to_user" not in context.user_data:
        # Oddiy xabar sifatida qayta ishlashga yuboramiz
        await handle_message(update, context)
        return

    target_id = context.user_data["reply_to_user"]

    if text == "/cancel":
        del context.user_data["reply_to_user"]
        await update.message.reply_text("❌ Javob berish bekor qilindi.")
        return

    try:
        await context.bot.send_message(
            chat_id=target_id,
            text=f"📨 <b>Bot egasidan javob:</b>\n\n{text}",
            parse_mode="HTML"
        )
        await update.message.reply_text("✅ Javobingiz muvaffaqiyatli yuborildi!")
        del context.user_data["reply_to_user"]
    except Exception as e:
        await update.message.reply_text(f"❌ Xabar ketmadi. Xatolik: {e}")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CallbackQueryHandler(callback_handler))

    # Ega kimgadir javob yozayotganini tekshirish filtri
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Chat(OWNER_CHAT_ID),
        handle_owner_reply
    ))

    # Boshqa hamma xabarlar uchun
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🚀 Yangi zamonaviy Gemini bot ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()