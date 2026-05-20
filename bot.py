"""
Jarvis Yordamchim - Telegram Bot
Celery orqali background vazifalarni bajaradi
"""

import logging
import os
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

# Logging sozlash
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")


# ===================== BUYRUQLAR =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Botni boshlash"""
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
        "🤖 Men **Jarvis Yordamchim** — sizning aqlli yordamchingiz.\n\n"
        "⚡ Barcha vazifalar *background*da ishlaydi — kutib o'tirmang!\n\n"
        "Quyidagi buyruqlardan birini tanlang:",
        reply_markup=reply_markup,
        parse_mode="Markdown",
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Yordam"""
    help_text = (
        "🤖 *Jarvis Yordamchim — Buyruqlar:*\n\n"
        "📝 `/analyze <matn>` — Matnni tahlil qilish\n"
        "🌍 `/translate <matn>` — Matnni inglizchaga tarjima qilish\n"
        "📋 `/summarize <matn>` — Matnni qisqacha xulosa qilish\n"
        "🌤 `/weather <shahar>` — Ob-havo ma'lumoti\n"
        "⏰ `/reminder <daqiqa> <xabar>` — Eslatma o'rnatish\n"
        "📊 `/status` — Faol vazifalar holati\n\n"
        "💡 *Maslahat:* Barcha vazifalar Celery orqali bajariladi.\n"
        "Siz kutmasangiz ham, natija tayyor bo'lganda yuboriladi!"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


async def analyze_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/analyze buyrug'i"""
    if not context.args:
        await update.message.reply_text(
            "❌ Matn kiriting!\n📝 Misol: `/analyze Bu juda ajoyib kitob!`",
            parse_mode="Markdown",
        )
        return

    text = " ".join(context.args)
    chat_id = update.effective_chat.id

    await update.message.reply_text(
        "⏳ Matn tahlil qilinmoqda... Natija tayor bo'lgach xabar beraman!"
    )

    # Celery vazifasini background'da ishga tushirish
    task = analyze_text_task.delay(chat_id, text)

    # Task ID ni saqlash
    if context.user_data.get("tasks") is None:
        context.user_data["tasks"] = []
    context.user_data["tasks"].append({"id": task.id, "type": "analyze", "text": text[:30]})

    logger.info(f"Tahlil vazifasi boshlandi: {task.id} | Foydalanuvchi: {chat_id}")


async def translate_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/translate buyrug'i"""
    if not context.args:
        await update.message.reply_text(
            "❌ Matn kiriting!\n🌍 Misol: `/translate Salom dunyo`",
            parse_mode="Markdown",
        )
        return

    text = " ".join(context.args)
    chat_id = update.effective_chat.id

    await update.message.reply_text(
        "⏳ Tarjima qilinmoqda... Tez orada natija yuboraman!"
    )

    task = translate_text_task.delay(chat_id, text)
    logger.info(f"Tarjima vazifasi: {task.id}")


async def summarize_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/summarize buyrug'i"""
    if not context.args:
        await update.message.reply_text(
            "❌ Matn kiriting!\n📋 Misol: `/summarize <uzun matn>`",
            parse_mode="Markdown",
        )
        return

    text = " ".join(context.args)
    chat_id = update.effective_chat.id

    await update.message.reply_text(
        "⏳ Matn qisqartirilmoqda..."
    )

    task = summarize_text_task.delay(chat_id, text)
    logger.info(f"Xulosa vazifasi: {task.id}")


async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/weather buyrug'i"""
    city = " ".join(context.args) if context.args else "Toshkent"
    chat_id = update.effective_chat.id

    await update.message.reply_text(
        f"⏳ {city} uchun ob-havo tekshirilmoqda..."
    )

    task = weather_task.delay(chat_id, city)
    logger.info(f"Ob-havo vazifasi: {task.id}")


async def reminder_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/reminder buyrug'i — /reminder 5 Dori iching"""
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ To'g'ri format kiriting!\n"
            "⏰ Misol: `/reminder 5 Dori iching`\n"
            "_(5 daqiqadan keyin eslatadi)_",
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
        f"✅ Eslatma o'rnatildi!\n"
        f"⏰ {minutes} daqiqadan keyin: *{message}*",
        parse_mode="Markdown",
    )

    # countdown_seconds * 60
    task = reminder_task.apply_async(
        args=[chat_id, message],
        countdown=minutes * 60,
    )
    logger.info(f"Eslatma vazifasi: {task.id} | {minutes} daqiqadan keyin")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """/status — faol vazifalar"""
    tasks = context.user_data.get("tasks", [])
    if not tasks:
        await update.message.reply_text("📭 Sizda hozircha faol vazifalar yo'q.")
        return

    text = "📊 *Sizning vazifalaringiz:*\n\n"
    for i, t in enumerate(tasks[-5:], 1):
        text += f"{i}. `{t['type']}` — _{t['text']}..._\n   ID: `{t['id'][:8]}...`\n\n"

    await update.message.reply_text(text, parse_mode="Markdown")


# ===================== CALLBACK HANDLER =====================

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Inline tugmalar uchun handler"""
    query = update.callback_query
    await query.answer()

    prompts = {
        "analyze": (
            "📝 *Matn tahlili*\n\n"
            "Buyruq: `/analyze <matningiz>`\n"
            "Misol: `/analyze Bu film juda yaxshi edi!`\n\n"
            "_Bot his-tuyg'ularni, kalit so'zlarni va matn uzunligini tahlil qiladi._"
        ),
        "translate": (
            "🌍 *Tarjima*\n\n"
            "Buyruq: `/translate <matningiz>`\n"
            "Misol: `/translate Salom, qanday yashaysiz?`\n\n"
            "_Matn o'zbek/rus tilidan inglizchaga tarjima qilinadi._"
        ),
        "summarize": (
            "📋 *Qisqacha xulosa*\n\n"
            "Buyruq: `/summarize <uzun matn>`\n\n"
            "_Uzun matnni 2-3 jumlaga qisqartiradi._"
        ),
        "weather": (
            "🌤 *Ob-havo*\n\n"
            "Buyruq: `/weather <shahar nomi>`\n"
            "Misol: `/weather Samarqand`\n\n"
            "_Shahar ob-havo ma'lumotini ko'rsatadi._"
        ),
        "reminder": (
            "⏰ *Eslatma*\n\n"
            "Buyruq: `/reminder <daqiqa> <xabar>`\n"
            "Misol: `/reminder 10 Choy iching!`\n\n"
            "_Belgilangan vaqtdan keyin eslatma yuboradi._"
        ),
        "help": None,
    }

    if query.data == "help":
        await help_command(update, context)
        return

    text = prompts.get(query.data, "❓ Noma'lum buyruq")
    await query.edit_message_text(text=text, parse_mode="Markdown")


# ===================== XABAR HANDLER =====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Oddiy xabarlarni qabul qilish"""
    text = update.message.text
    chat_id = update.effective_chat.id

    # Qisqa matnlarni avtomatik tahlil qilish
    if len(text) > 20:
        await update.message.reply_text(
            "💬 Matn qabul qilindi!\n\n"
            "Nima qilishni xohlaysiz?\n"
            "• `/analyze` — tahlil qilish\n"
            "• `/translate` — tarjima qilish\n"
            "• `/summarize` — xulosa chiqarish",
            parse_mode="Markdown",
        )
    else:
        await update.message.reply_text(
            "👋 Salom! `/help` buyrug'ini kiriting yoki menyu tugmalaridan foydalaning."
        )


# ===================== MAIN =====================

def main() -> None:
    """Botni ishga tushirish"""
    logger.info("🤖 Jarvis Yordamchim ishga tushmoqda...")

    app = Application.builder().token(BOT_TOKEN).build()

    # Buyruqlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("analyze", analyze_command))
    app.add_handler(CommandHandler("translate", translate_command))
    app.add_handler(CommandHandler("summarize", summarize_command))
    app.add_handler(CommandHandler("weather", weather_command))
    app.add_handler(CommandHandler("reminder", reminder_command))
    app.add_handler(CommandHandler("status", status_command))

    # Callback va xabarlar
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("✅ Bot tayyor! Polling boshlandi...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
