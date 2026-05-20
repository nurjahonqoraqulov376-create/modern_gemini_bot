"""
Jarvis Yordamchim — Celery Vazifalar
Sun'iy intellekt: Claude API (Anthropic) — BEPUL TIER bor
"""

import os
import time
import asyncio
import requests
import logging
from celery import Celery
from telegram import Bot
from telegram.error import TelegramError
import anthropic

logger = logging.getLogger(__name__)

# ===================== SOZLAMALAR =====================

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

celery_app = Celery(
    "jarvis_tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
)
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Tashkent",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_max_retries=3,
    task_default_retry_delay=30,
)


# ===================== TELEGRAM XABAR =====================

def send_message(chat_id: int, text: str) -> bool:
    """Telegram xabar yuborish — asyncio.run() bilan"""
    async def _send():
        bot = Bot(token=BOT_TOKEN)
        async with bot:
            await bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="Markdown",
            )
    try:
        asyncio.run(_send())
        return True
    except Exception as e:
        logger.error(f"Xabar yuborishda xato: {e}")
        return False


def edit_message(chat_id: int, message_id: int, text: str) -> bool:
    """Mavjud xabarni tahrirlash"""
    async def _edit():
        bot = Bot(token=BOT_TOKEN)
        async with bot:
            await bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=text,
                parse_mode="Markdown",
            )
    try:
        asyncio.run(_edit())
        return True
    except Exception as e:
        # Tahrirlab bo'lmasa, yangi xabar yuborish
        logger.warning(f"Tahrirlash xatosi, yangi xabar yuboriladi: {e}")
        send_message(chat_id, text)
        return False


# ===================== CLAUDE AI VAZIFA =====================

@celery_app.task(bind=True, name="tasks.ask_ai")
def ask_ai_task(self, chat_id: int, question: str, message_id: int = None) -> dict:
    """
    Claude AI ga savol yuborish va javob olish.
    Anthropic API ishlatiladi.
    """
    try:
        if not ANTHROPIC_API_KEY:
            text = (
                "⚠️ *ANTHROPIC\\_API\\_KEY sozlanmagan!*\n\n"
                "1. [console.anthropic.com](https://console.anthropic.com) ga kiring\n"
                "2. API key oling (bepul kredit beriladi)\n"
                "3. Railway'da `ANTHROPIC_API_KEY` ni qo'shing"
            )
            if message_id:
                edit_message(chat_id, message_id, text)
            else:
                send_message(chat_id, text)
            return {"status": "no_api_key"}

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

        # Claude API ga so'rov
        response = client.messages.create(
            model="claude-haiku-4-5",  # Eng tez va arzon model
            max_tokens=1024,
            system=(
                "Siz Jarvis — o'zbek tilida javob beradigan aqlli yordamchisiz. "
                "Qisqa, aniq va foydali javoblar bering. "
                "Markdown formatlashdan foydalaning (bold, italic, code). "
                "Javob 500 so'zdan oshmasin."
            ),
            messages=[
                {"role": "user", "content": question}
            ],
        )

        answer = response.content[0].text

        result_text = (
            f"🤖 *Jarvis AI javobi:*\n"
            f"{'─' * 28}\n\n"
            f"{answer}\n\n"
            f"_Model: Claude Haiku_"
        )

        if message_id:
            edit_message(chat_id, message_id, result_text)
        else:
            send_message(chat_id, result_text)

        return {"status": "success"}

    except anthropic.AuthenticationError:
        text = "❌ API kalit noto'g'ri! `ANTHROPIC_API_KEY` ni tekshiring."
        if message_id:
            edit_message(chat_id, message_id, text)
        else:
            send_message(chat_id, text)
        return {"status": "auth_error"}

    except anthropic.RateLimitError:
        text = "⏳ AI so'rovlar limiti to'ldi. Bir daqiqadan keyin qayta urinib ko'ring."
        if message_id:
            edit_message(chat_id, message_id, text)
        else:
            send_message(chat_id, text)
        return {"status": "rate_limit"}

    except Exception as exc:
        logger.error(f"AI xatosi: {exc}")
        text = f"❌ Xato yuz berdi: {str(exc)[:100]}"
        if message_id:
            edit_message(chat_id, message_id, text)
        else:
            send_message(chat_id, text)
        raise self.retry(exc=exc, countdown=30)


# ===================== MATN TAHLIL =====================

@celery_app.task(bind=True, name="tasks.analyze_text")
def analyze_text_task(self, chat_id: int, text: str) -> dict:
    """Matnni AI orqali tahlil qilish"""
    try:
        if not ANTHROPIC_API_KEY:
            send_message(chat_id, "⚠️ `ANTHROPIC_API_KEY` sozlanmagan!")
            return {"status": "no_api_key"}

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=800,
            system="Siz matn tahlilchisisiz. O'zbek tilida javob bering. Markdown ishlating.",
            messages=[{
                "role": "user",
                "content": (
                    f"Quyidagi matnni tahlil qiling:\n\n'{text}'\n\n"
                    "Quyidagilarni ko'rsating:\n"
                    "1. His-tuyg'u (ijobiy/salbiy/neytral)\n"
                    "2. Asosiy mavzu\n"
                    "3. Kalit so'zlar\n"
                    "4. Qisqacha baho"
                )
            }],
        )

        result = (
            f"📊 *Matn Tahlili*\n"
            f"{'─' * 28}\n\n"
            f"{response.content[0].text}"
        )
        send_message(chat_id, result)
        return {"status": "success"}

    except Exception as exc:
        logger.error(f"Tahlil xatosi: {exc}")
        send_message(chat_id, f"❌ Tahlil xatosi: {str(exc)[:100]}")
        raise self.retry(exc=exc, countdown=30)


# ===================== TARJIMA =====================

@celery_app.task(bind=True, name="tasks.translate_text")
def translate_text_task(self, chat_id: int, text: str) -> dict:
    """Matnni AI orqali tarjima qilish"""
    try:
        if not ANTHROPIC_API_KEY:
            send_message(chat_id, "⚠️ `ANTHROPIC_API_KEY` sozlanmagan!")
            return {"status": "no_api_key"}

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=1000,
            system="Siz professional tarjimonisiz.",
            messages=[{
                "role": "user",
                "content": (
                    f"Quyidagi matnni ingliz tiliga tarjima qiling.\n\n"
                    f"Matn: {text}\n\n"
                    f"Faqat tarjimani yozing, izoh yozmang."
                )
            }],
        )

        translated = response.content[0].text
        result = (
            f"🌍 *Tarjima Natijasi*\n"
            f"{'─' * 28}\n\n"
            f"📥 *Asl:*\n_{text}_\n\n"
            f"📤 *Inglizcha:*\n*{translated}*"
        )
        send_message(chat_id, result)
        return {"status": "success"}

    except Exception as exc:
        logger.error(f"Tarjima xatosi: {exc}")
        send_message(chat_id, f"❌ Tarjima xatosi: {str(exc)[:100]}")
        raise self.retry(exc=exc, countdown=30)


# ===================== XULOSA =====================

@celery_app.task(bind=True, name="tasks.summarize_text")
def summarize_text_task(self, chat_id: int, text: str) -> dict:
    """Matnni AI orqali qisqartirish"""
    try:
        if not ANTHROPIC_API_KEY:
            send_message(chat_id, "⚠️ `ANTHROPIC_API_KEY` sozlanmagan!")
            return {"status": "no_api_key"}

        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        response = client.messages.create(
            model="claude-haiku-4-5",
            max_tokens=500,
            system="Siz matnni qisqartiruvchi ekspertsiz. O'zbek tilida javob bering.",
            messages=[{
                "role": "user",
                "content": (
                    f"Quyidagi matnni 3-4 jumlaga qisqartiring:\n\n{text}"
                )
            }],
        )

        summary = response.content[0].text
        result = (
            f"📋 *Qisqacha Xulosa*\n"
            f"{'─' * 28}\n\n"
            f"{summary}\n\n"
            f"_Asl matn: {len(text.split())} so'z → {len(summary.split())} so'z_"
        )
        send_message(chat_id, result)
        return {"status": "success"}

    except Exception as exc:
        logger.error(f"Xulosa xatosi: {exc}")
        send_message(chat_id, f"❌ Xulosa xatosi: {str(exc)[:100]}")
        raise self.retry(exc=exc, countdown=30)


# ===================== ESLATMA =====================

@celery_app.task(bind=True, name="tasks.reminder")
def reminder_task(self, chat_id: int, message: str) -> dict:
    """Eslatma xabarini yuborish"""
    try:
        send_message(
            chat_id,
            f"⏰ *ESLATMA!*\n{'─' * 28}\n\n🔔 {message}\n\n_Jarvis Yordamchim_"
        )
        return {"status": "success"}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=60)
