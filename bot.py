import os
import logging
import asyncio
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    filters, ContextTypes, CallbackQueryHandler
)
import anthropic

# ============================================================
#  SOZLAMALAR — bu yerga o'z ma'lumotlaringizni kiriting
# ============================================================
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
# Diqqat: Railway'dagi ANTHROPIC_API_KEY o'zgaruvchisiga OpenRouter'dan olgan sk-or-... kalitingizni qo'ying
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "YOUR_ANTHROPIC_API_KEY_HERE")
OWNER_CHAT_ID = int(os.getenv("OWNER_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID_HERE"))
# ============================================================

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Anthropic klientini OpenRouter bepul xizmatiga ulaymiz
ai_client = anthropic.Anthropic(
    api_key=ANTHROPIC_API_KEY,
    base_url="https://openrouter.ai/api/v1"
)

# Xabarlar xotirasi (conversation history)
conversation_history: dict = {}

# Xabar kutish ro'yxati (owner offline bo'lganda)
pending_messages: list = []


def is_owner(chat_id: int) -> bool:
    """Foydalanuvchi bot egasimi yoki yo'q"""
    return chat_id == OWNER_CHAT_ID


async def get_owner_status(bot) -> bool:
    """Owner onlayn yoki offlayn ekanligini tekshirish"""
    try:
        return True  # Default: onlayn deb hisoblaymiz
    except Exception:
        return False


async def ask_claude(user_id: int, user_message: str) -> str:
    """OpenRouter orqali bepul modeldan javob olish"""
    if user_id not in conversation_history:
        conversation_history[user_id] = []

    conversation_history[user_id].append({
        "role": "user",
        "content": user_message
    })

    # Oxirgi 20 ta xabarni saqlaymiz (kontekst uchun)
    history = conversation_history[user_id][-20:]

    try:
        # Modelni bepul OpenRouter modeliga almashtirdik
        response = ai_client.messages.create(
            model="google/gemini-2.5-flash:free",
            max_tokens=2048,
            system="""Siz foydali, aqlli va do'stona AI yordamchisiz. 
            Uzbek tilida ham, rus tilida ham, ingliz tilida ham javob bera olasiz.
            Foydalanuvchi qaysi tilda yozsa, o'sha tilda javob bering.
            Aniq, qisqa va tushunarli javoblar bering.""",
            messages=history
        )

        assistant_message = response.content[0].text
        conversation_history[user_id].append({
            "role": "assistant",
            "content": assistant_message
        })

        return assistant_message

    except anthropic.APIError as e:
        logger.error(f"OpenRouter API xatosi: {e}")
        return "❌ AI bilan bog'lanishda xato yuz berdi. Iltimos, keyinroq urinib ko'ring."


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot ishga tushganda"""
    user = update.effective_user
    chat_id = update.effective_chat.id

    if is_owner(chat_id):
        await update.message.reply_text(
            f"👋 Salom, Xo'jayin!\n\n"
            f"🤖 Botingiz ishga tushdi va tayyor!\n\n"
            f"📋 <b>Buyruqlar:</b>\n"
            f"• /start — Botni qayta ishga tushirish\n"
            f"• /clear — Suhbat tarixini tozalash\n"
            f"• /pending — Kutayotgan xabarlar\n"
            f"• /status — Bot holati\n\n"
            f"💬 Istalgan savolni yuboring — AI javob beradi!",
            parse_mode="HTML"
        )
    else:
        await notify_owner_about_visitor(context.bot, user, chat_id)

        keyboard = [[InlineKeyboardButton("📨 Xabar qoldirish", callback_data=f"leave_message_{chat_id}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"👋 Salom, {user.first_name}!\n\n"
            f"🤖 Men aqlli AI yordamchiman.\n"
            f"Istalgan savolingizni yuboring — javob beraman!\n\n"
            f"📨 Yoki bot egasiga xabar qoldirishingiz mumkin.",
            reply_markup=reply_markup
        )


async def notify_owner_about_visitor(bot, visitor, visitor_chat_id: int):
    """Egaga yangi tashrif haqida xabar berish"""
    name = visitor.first_name or ""
    last_name = visitor.last_name or ""
    username = f"@{visitor.username}" if visitor.username else "username yo'q"
    now = datetime.now().strftime("%H:%M, %d.%m.%Y")

    try:
        keyboard = [[
            InlineKeyboardButton("💬 Javob berish", callback_data=f"reply_to_{visitor_chat_id}")
        ]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await bot.send_message(
            chat_id=OWNER_CHAT_ID,
            text=f"🔔 <b>Yangi tashrif!</b>\n\n"
                 f"👤 Ism: {name} {last_name}\n"
                 f"🆔 Username: {username}\n"
                 f"📋 Chat ID: <code>{visitor_chat_id}</code>\n"
                 f"🕐 Vaqt: {now}",
            parse_mode="HTML",
            reply_markup=reply_markup
        )
    except Exception as e:
        logger.error(f"Egaga xabar yuborishda xato: {e}")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Barcha xabarlarni qayta ishlash"""
    chat_id = update.effective_chat.id
    user = update.effective_user
    text = update.message.text

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    if is_owner(chat_id):
        response = await ask_claude(chat_id, text)
        await update.message.reply_text(response)

    else:
        name = user.first_name or "Noma'lum"
        username = f"@{user.username}" if user.username else f"ID: {chat_id}"
        now = datetime.now().strftime("%H:%M")

        try:
            keyboard = [[
                InlineKeyboardButton("💬 Javob berish", callback_data=f"reply_to_{chat_id}")
            ]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await context.bot.send_message(
                chat_id=OWNER_CHAT_ID,
                text=f"📩 <b>Yangi xabar!</b>\n"
                     f"👤 {name} ({username})\n"
                     f"🕐 {now}\n\n"
                     f"💬 <i>{text}</i>",
                parse_mode="HTML",
                reply_markup=reply_markup
            )
        except Exception as e:
            logger.error(f"Egaga xabar yuborishda xato: {e}")

        response = await ask_claude(chat_id, text)
        await update.message.reply_text(
            f"🤖 {response}\n\n"
            f"─────────────────\n"
            f"📨 Bot egasiga ham xabar yetkazildi."
        )

        pending_messages.append({
            "from": name,
            "username": username,
            "chat_id": chat_id,
            "text": text,
            "time": datetime.now().strftime("%H:%M, %d.%m.%Y")
        })


async def clear_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Suhbat tarixini tozalash"""
    chat_id = update.effective_chat.id
    if is_owner(chat_id):
        conversation_history.pop(chat_id, None)
        await update.message.reply_text("🗑️ Suhbat tarixi tozalandi!")
    else:
        conversation_history.pop(chat_id, None)
        await update.message.reply_text("🗑️ Suhbatingiz tarixi tozalandi!")


async def pending_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Kutayotgan xabarlarni ko'rish (faqat ega uchun)"""
    chat_id = update.effective_chat.id
    if not is_owner(chat_id):
        return

    if not pending_messages:
        await update.message.reply_text("📭 Hozircha kutayotgan xabar yo'q.")
        return

    text = f"📬 <b>Kutayotgan xabarlar ({len(pending_messages)} ta):</b>\n\n"
    for i, msg in enumerate(pending_messages[-10:], 1):
        text += (
            f"{i}. 👤 {msg['from']} ({msg['username']})\n"
            f"   🕐 {msg['time']}\n"
            f"   💬 {msg['text'][:100]}{'...' if len(msg['text']) > 100 else ''}\n\n"
        )

    await update.message.reply_text(text, parse_mode="HTML")


async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Bot holati (faqat ega uchun)"""
    chat_id = update.effective_chat.id
    if not is_owner(chat_id):
        return

    active_chats = len(conversation_history)
    pending_count = len(pending_messages)
    now = datetime.now().strftime("%H:%M, %d.%m.%Y")

    await update.message.reply_text(
        f"📊 <b>Bot holati</b>\n\n"
        f"🟢 Status: Ishlamoqda\n"
        f"🕐 Vaqt: {now}\n"
        f"💬 Faol suhbatlar: {active_chats} ta\n"
        f"📨 Kutayotgan xabarlar: {pending_count} ta\n"
        f"🤖 AI Model: Gemini 2.5 Flash (OpenRouter)",
        parse_mode="HTML"
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Inline tugmalar uchun handler"""
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("reply_to_"):
        target_chat_id = int(data.split("_")[-1])
        context.user_data["replying_to"] = target_chat_id
        await query.message.reply_text(
            f"✏️ Javob yozing (Chat ID: <code>{target_chat_id}</code>)\n"
            f"Keyingi xabaringiz shu foydalanuvchiga yuboriladi.\n\n"
            f"/cancel — bekor qilish",
            parse_mode="HTML"
        )

    elif data.startswith("leave_message_"):
        await query.message.reply_text(
            "📝 Egaga qoldirmoqchi bo'lgan xabaringizni yuboring:"
        )
        context.user_data["leaving_message"] = True


async def handle_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Eganing kimgadir javob berishi"""
    chat_id = update.effective_chat.id
    text = update.message.text

    if not is_owner(chat_id):
        return

    if "replying_to" in context.user_data:
        target_id = context.user_data["replying_to"]

        if text == "/cancel":
            del context.user_data["replying_to"]
            await update.message.reply_text("❌ Bekor qilindi.")
            return

        try:
            await context.bot.send_message(
                chat_id=target_id,
                text=f"📨 <b>Bot egasidan xabar:</b>\n\n{text}",
                parse_mode="HTML"
            )
            del context.user_data["replying_to"]
            await update.message.reply_text("✅ Xabar yuborildi!")
        except Exception as e:
            await update.message.reply_text(f"❌ Xabar yuborishda xato: {e}")


def main():
    """Botni ishga tushirish"""
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("clear", clear_command))
    app.add_handler(CommandHandler("pending", pending_command))
    app.add_handler(CommandHandler("status", status_command))
    app.add_handler(CallbackQueryHandler(callback_handler))

    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Chat(OWNER_CHAT_ID),
        handle_reply
    ))

    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    ))

    logger.info("🤖 Bot ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()