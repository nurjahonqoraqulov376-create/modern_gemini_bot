"""
Jarvis Yordamchim - Telegram Bot
python-telegram-bot v20+ (to'liq async)
"""

import logging
import os
import sys
import asyncio
from dotenv import load_dotenv

# .env faylni yuklash (local ishlatganda)
load_dotenv()

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)
from tasks import (
    analyze_text_task,
    translate_text_task,
    summarize_text_task,
    weather_task,
    reminder_task,
)

# Logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

# Token tekshirish
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN topilmadi! .env faylga yoki Render Environment'ga qo'shing.")
    sys.exit(1)

logger.info(f"✅ BOT_TOKEN topildi: ...{BOT_TOKEN[-6:]}")


# ===================== BUYRUQLAR =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    keyboard = [
        [
            InlineKeyboardButton("📝 Matn tahlili", callback_data="analyze"),
            InlineKeyboardButton("🌍 Tarjima", callback_data="translate"),
        ],
        [
            InlineKeyboardButton("📋 Xulosa", callback_data="summarize"),
            InlineKeyboardButton("🌤 Ob-havo", callback_data="weather"),
        ],
        [
            InlineKeyboardButton("⏰ Eslatma", callback_data="reminder"),
            InlineKeyboardButton("❓ Yordam", callback_data="help"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"👋 Salom, {user.first_name}!\n\n"
        "🤖 Men *Jarvis Yordamchim* — sizning aqlli yordamchingiz.\n\n"
        "⚡ Barcha vazifalar _background_da ishlaydi!\n\n"
        "Quyidagi buyruqlardan birini tanlang:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = (
        "🤖 *Jarvis Yordamchim — Buyruqlar:*\n\n"
        "📝 `/analyze matn` — Matnni tahlil qilish\n"
        "🌍 `/translate matn` — Inglizchaga tarjima\n"
        "📋 `/summarize matn` — Qisqacha xulosa\n"
        "🌤 `/weather shahar` — Ob-havo\n"
        "⏰ `/reminder 5 Xabar` — Eslatma (5 daqiqada)\n"
        "📊 `/status` — Faol vazifalar\n\n"
        "💡 Barcha vazifalar Celery orqali bajariladi!"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "❌ Matn kiriting!\nMisol: `/analyze Bu juda ajoyib!`",
            parse_mode="Markdown",
        )
        return
    text = " ".join(context.args)
    chat_id = update.effective_chat.id
    await update.message.reply_text("⏳ Tahlil qilinmoqda...")
    analyze_text_task.delay(chat_id, text)


async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "❌ Matn kiriting!\nMisol: `/translate Salom dunyo`",
            parse_mode="Markdown",
        )
        return
    text = " ".join(context.args)
    chat_id = update.effective_chat.id
    await update.message.reply_text("⏳ Tarjima qilinmoqda...")
    translate_text_task.delay(chat_id, text)


async def summarize_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text(
            "❌ Matn kiriting!\nMisol: `/summarize uzun matn...`",
            parse_mode="Markdown",
        )
        return
    text = " ".join(context.args)
    chat_id = update.effective_chat.id
    await update.message.reply_text("⏳ Xulosa chiqarilmoqda...")
    summarize_text_task.delay(chat_id, text)


async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    city = " ".join(context.args) if context.args else "Toshkent"
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"⏳ {city} ob-havosi tekshirilmoqda...")
    weather_task.delay(chat_id, city)


async def reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Format: `/reminder 5 Dori iching`\n_(5 daqiqadan keyin eslatadi)_",
            parse_mode="Markdown",
        )
        return
    try:
        minutes = int(context.args[0])
        message = " ".join(context.args[1:])
    except ValueError:
        await update.message.reply_text("❌ Daqiqa soni butun son bo'lishi kerak!")
        return

    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"✅ Eslatma o'rnatildi!\n⏰ {minutes} daqiqadan keyin: *{message}*",
        parse_mode="Markdown",
    )
    reminder_task.apply_async(args=[chat_id, message], countdown=minutes * 60)


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    tasks = context.user_data.get("tasks", [])
    if not tasks:
        await update.message.reply_text("📭 Hozircha faol vazifalar yo'q.")
        return
    text = "📊 *Sizning vazifalaringiz:*\n\n"
    for i, t in enumerate(tasks[-5:], 1):
        text += f"{i}. `{t['type']}` — _{t['text'][:20]}..._\n"
    await update.message.reply_text(text, parse_mode="Markdown")


# ===================== CALLBACK =====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    prompts = {
        "analyze": (
            "📝 *Matn tahlili*\n\n"
            "Buyruq: `/analyze matningiz`\n"
            "Misol: `/analyze Bu film juda yaxshi edi!`"
        ),
        "translate": (
            "🌍 *Tarjima*\n\n"
            "Buyruq: `/translate matningiz`\n"
            "Misol: `/translate Salom, qanday yashaysiz?`"
        ),
        "summarize": (
            "📋 *Qisqacha xulosa*\n\n"
            "Buyruq: `/summarize uzun matn`\n"
            "Uzun matnni 2-3 jumlaga qisqartiradi."
        ),
        "weather": (
            "🌤 *Ob-havo*\n\n"
            "Buyruq: `/weather shahar nomi`\n"
            "Misol: `/weather Samarqand`"
        ),
        "reminder": (
            "⏰ *Eslatma*\n\n"
            "Buyruq: `/reminder daqiqa xabar`\n"
            "Misol: `/reminder 10 Choy iching!`"
        ),
    }

    if query.data == "help":
        text = (
            "🤖 *Buyruqlar ro'yxati:*\n\n"
            "/analyze, /translate, /summarize\n"
            "/weather, /reminder, /status"
        )
    else:
        text = prompts.get(query.data, "❓ Noma'lum buyruq")

    await query.edit_message_text(text=text, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = update.message.text
    if len(text) > 20:
        await update.message.reply_text(
            "💬 Matn qabul qilindi! Nima qilishni xohlaysiz?\n\n"
            "• `/analyze` — tahlil\n"
            "• `/translate` — tarjima\n"
            "• `/summarize` — xulosa",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "👋 /help buyrug'ini kiriting yoki menyudan foydalaning."
        )


# ===================== MAIN =====================

def main() -> None:
    logger.info("🤖 Jarvis Yordamchim ishga tushmoqda...")

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(CommandHandler("translate", translate_command))
    app.add_handler(CommandHandler("summarize", summarize_command))
    app.add_handler(CommandHandler("weather", weather_command))
    app.add_handler(CommandHandler("reminder", reminder_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("✅ Polling boshlandi...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
