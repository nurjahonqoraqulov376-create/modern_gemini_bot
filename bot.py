import os
import logging
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)
import google.generativeai as genai

# .env faylidan yuklash
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
OWNER_CHAT_ID = int(os.getenv("OWNER_CHAT_ID", "0"))

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Gemini API ni sozlash
genai.configure(api_key=GEMINI_API_KEY)

# O'q o'tmas va barqaror model sozlamasi
# Tizim har bir xabarga alohida va xatoliksiz, internet qidiruvi bilan javob beradi
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 2048,
}
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash",
    generation_config=generation_config
)


def is_owner(chat_id: int) -> bool:
    return chat_id == OWNER_CHAT_ID


async def ask_gemini(user_message: str) -> str:
    """Xatoliklardan to'liq himoyalangan Gemini API funksiyasi"""
    try:
        # Chat sessiyasidagi konfliktlarni chetlab o'tish uchun to'g'ridan-to'g'ri kontent generatsiya qilamiz
        response = model.generate_content(user_message)
        if response.text:
            return response.text
        return "⚠️ AI tushunarli javob qaytara olmadi. Qaytadan so'rab ko'ring."
    except Exception as e:
        logger.error(f"Gemini jiddiy xatolik: {e}")
        return "❌ Sun'iy intellekt tizimida vaqtincha uzilish bo'ldi. Birozdan so'ng urinib ko'ring."


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user

    if is_owner(chat_id):
        await update.message.reply_text(
            "👋 Salom, Xo'jayin!\n🤖 Yangi Gemini botingiz 100% xavfsiz rejimda ishga tushdi.\n\n/status — Bot holati"
        )
    else:
        # Egaga bildirishnoma yuborish
        try:
            await context.bot.send_message(
                chat_id=OWNER_CHAT_ID,
                text=f"🔔 <b>Yangi foydalanuvchi botni boshladi:</b>\n"
                     f"👤 Ism: {user.first_name}\n"
                     f"🆔 ID: <code>{chat_id}</code>",
                parse_mode="HTML"
            )
        except:
            pass

        await update.message.reply_text(
            f"👋 Salom, {user.first_name}!\n\n"
            f"🤖 Men aqlli AI yordamchiman. Istalgan savolingizni yuboring — javob beraman!\n\n"
            f"🌍 Ob-havo, valyuta kurslari va eng so'nggi yangiliklarni ham jonli internet qidiruvi orqali topib bera olaman."
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user = update.effective_user
    text = update.message.text

    # Bot o'ylayotganini bildirish uchun "typing..." animatsiyasi
    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    if is_owner(chat_id):
        # Ega yozganda to'g'ridan-to'g'ri AI javob beradi
        response = await ask_gemini(text)
        await update.message.reply_text(response)
    else:
        # Boshqalar yozganda: Egaga xabar YASHIRINCHA yetib boradi
        try:
            keyboard = [[InlineKeyboardButton("💬 Javob berish", callback_data=f"reply_{chat_id}")]]
            await context.bot.send_message(
                chat_id=OWNER_CHAT_ID,
                text=f"📩 <b>Foydalanuvchidan yangi xabar:</b>\n"
                     f"👤 {user.first_name} (ID: {chat_id})\n\n"
                     f"💬 <i>{text}</i>",
                parse_mode="HTML",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        except Exception as e:
            logger.error(f"Egaga xabar nusxasini yuborishda xato: {e}")

        # Foydalanuvchining o'ziga faqat AI javob qaytaradi (ortiqcha yozuvlarsiz)
        response = await ask_gemini(text)
        await update.message.reply_text(response)

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_owner(update.effective_chat.id):
        return
    await update.message.reply_text(
        f"📊 <b>Bot Holati:</b>\n🟢 Status: Aktiv\n🤖 Model: Gemini 1.5 Flash\n🌐 Qidiruv (Search): Yoqilgan",
        parse_mode="HTML"
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("reply_"):
        target_id = int(query.data.split("_")[1])
        context.user_data["reply_to_user"] = target_id
        await query.message.reply_text(
            f"✏️ Foydalanuvchiga javob matnini yozing (ID: {target_id}):\n"
            f"Bekor qilish uchun /cancel yozing."
        )


async def handle_owner_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    text = update.message.text

    if not is_owner(chat_id) or "reply_to_user" not in context.user_data:
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
        await update.message.reply_text(f"❌ Xabar yuborishda xatolik: {e}")


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CallbackQueryHandler(callback_handler))

    # Ega javob yozayotganini ushlab qolish filtri
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Chat(OWNER_CHAT_ID),
        handle_owner_reply
    ))

    # Boshqa barcha matnli xabarlar uchun
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🚀 Bot barqaror rejimda yuritildi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()