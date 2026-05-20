"""
Jarvis Yordamchim - AI Telegram Bot
- Sun'iy intellekt: Claude API (Anthropic)
- Hosting: Railway.app (BEPUL)
- Celery + Redis: background vazifalar
"""

import logging
import os
import sys
from dotenv import load_dotenv

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
    ask_ai_task,
    analyze_text_task,
    translate_text_task,
    summarize_text_task,
    reminder_task,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
if not BOT_TOKEN:
    logger.error("❌ BOT_TOKEN topilmadi!")
    sys.exit(1)


# ===================== BUYRUQLAR =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    keyboard = [
        [
            InlineKeyboardButton("🤖 AI ga savol", callback_data="ai"),
            InlineKeyboardButton("📝 Tahlil", callback_data="analyze"),
        ],
        [
            InlineKeyboardButton("🌍 Tarjima", callback_data="translate"),
            InlineKeyboardButton("📋 Xulosa", callback_data="summarize"),
        ],
        [
            InlineKeyboardButton("⏰ Eslatma", callback_data="reminder"),
            InlineKeyboardButton("❓ Yordam", callback_data="help"),
        ],
    ]
    await update.message.reply_text(
        f"👋 Salom, {user.first_name}!\n\n"
        "🤖 Men *Jarvis* — sun'iy intellektli yordamchingiz!\n\n"
        "💡 Menga istalgan savolingizni bering yoki\n"
        "quyidagi buyruqlardan foydalaning:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🤖 *Jarvis — Buyruqlar:*\n\n"
        "🧠 `/ai savol` — AI ga istalgan savol\n"
        "📝 `/analyze matn` — Matn tahlili\n"
        "🌍 `/translate matn` — Tarjima\n"
        "📋 `/summarize matn` — Xulosa\n"
        "⏰ `/reminder 5 Xabar` — Eslatma\n\n"
        "💬 *Yoki shunchaki xabar yozing* — AI javob beradi!",
        parse_mode="Markdown",
    )


async def ai_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/ai buyrug'i — Claude AI ga savol"""
    if not context.args:
        await update.message.reply_text(
            "❌ Savol kiriting!\nMisol: `/ai Python nima?`",
            parse_mode="Markdown",
        )
        return
    question = " ".join(context.args)
    chat_id = update.effective_chat.id
    msg = await update.message.reply_text("🧠 AI o'ylamoqda...")
    ask_ai_task.delay(chat_id, question, msg.message_id)


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("❌ Misol: `/analyze Bu ajoyib matn!`", parse_mode="Markdown")
        return
    chat_id = update.effective_chat.id
    await update.message.reply_text("⏳ Tahlil qilinmoqda...")
    analyze_text_task.delay(chat_id, " ".join(context.args))


async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("❌ Misol: `/translate Salom dunyo`", parse_mode="Markdown")
        return
    chat_id = update.effective_chat.id
    await update.message.reply_text("⏳ Tarjima qilinmoqda...")
    translate_text_task.delay(chat_id, " ".join(context.args))


async def summarize_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await update.message.reply_text("❌ Misol: `/summarize uzun matn...`", parse_mode="Markdown")
        return
    chat_id = update.effective_chat.id
    await update.message.reply_text("⏳ Xulosa chiqarilmoqda...")
    summarize_text_task.delay(chat_id, " ".join(context.args))


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
        await update.message.reply_text("❌ Daqiqa butun son bo'lishi kerak!")
        return
    chat_id = update.effective_chat.id
    await update.message.reply_text(
        f"✅ *{minutes}* daqiqadan keyin eslataman:\n_{message}_",
        parse_mode="Markdown",
    )
    reminder_task.apply_async(args=[chat_id, message], countdown=minutes * 60)


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    prompts = {
        "ai":        "🧠 *AI savol*\nBuyruq: `/ai savolingiz`\nMisol: `/ai Inson tanasi nechta suyakdan iborat?`",
        "analyze":   "📝 *Tahlil*\nBuyruq: `/analyze matningiz`",
        "translate": "🌍 *Tarjima*\nBuyruq: `/translate matningiz`",
        "summarize": "📋 *Xulosa*\nBuyruq: `/summarize uzun matn`",
        "reminder":  "⏰ *Eslatma*\nBuyruq: `/reminder 10 Choy iching!`",
        "help":      "📋 Buyruqlar: /ai /analyze /translate /summarize /reminder",
    }
    await query.edit_message_text(prompts.get(query.data, "❓"), parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Oddiy xabar — avtomatik AI ga yuborish"""
    text = update.message.text
    chat_id = update.effective_chat.id
    msg = await update.message.reply_text("🧠 Jarvis o'ylamoqda...")
    # Har qanday xabarni AI ga yuborish
    ask_ai_task.delay(chat_id, text, msg.message_id)


# ===================== MAIN =====================

def main() -> None:
    logger.info("🤖 Jarvis ishga tushmoqda...")
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("ai", ai_command))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(CommandHandler("translate", translate_command))
    app.add_handler(CommandHandler("summarize", summarize_command))
    app.add_handler(CommandHandler("reminder", reminder_command))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("✅ Polling boshlandi...")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
