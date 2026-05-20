"""
Jarvis Yordamchim — Celery Vazifalar (Tasks)
Background'da ishlaydigan barcha vazifalar shu yerda
"""

import os
import time
import requests
import logging
from celery import Celery
from telegram import Bot
from telegram.error import TelegramError

logger = logging.getLogger(__name__)

# ===================== CELERY SOZLASH =====================

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")
BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")  # OpenWeatherMap API key

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
    # Qayta urinish sozlamalari
    task_max_retries=3,
    task_default_retry_delay=60,
)


# ===================== YORDAMCHI FUNKSIYA =====================

def send_telegram_message(chat_id: int, text: str) -> bool:
    """Telegram orqali xabar yuborish"""
    try:
        bot = Bot(token=BOT_TOKEN)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(
            bot.send_message(
                chat_id=chat_id,
                text=text,
                parse_mode="Markdown",
            )
        )
        loop.close()
        return True
    except TelegramError as e:
        logger.error(f"Xabar yuborishda xato: {e}")
        return False


def simple_sentiment(text: str) -> str:
    """Oddiy his-tuyg'u tahlili"""
    positive_words = [
        "yaxshi", "ajoyib", "zo'r", "barakali", "chiroyli", "sevaman",
        "xursand", "good", "great", "excellent", "nice", "love", "happy",
        "хорошо", "отлично", "замечательно", "люблю",
    ]
    negative_words = [
        "yomon", "dahshatli", "xafa", "achinish", "qo'rqinch",
        "bad", "terrible", "hate", "sad", "awful",
        "плохо", "ужасно", "ненавижу", "грустно",
    ]

    text_lower = text.lower()
    pos = sum(1 for w in positive_words if w in text_lower)
    neg = sum(1 for w in negative_words if w in text_lower)

    if pos > neg:
        return "😊 Ijobiy"
    elif neg > pos:
        return "😞 Salbiy"
    else:
        return "😐 Neytral"


def detect_language(text: str) -> str:
    """Tilni aniqlash (oddiy)"""
    cyrillic = sum(1 for c in text if "\u0400" <= c <= "\u04FF")
    latin = sum(1 for c in text if "a" <= c.lower() <= "z")

    if cyrillic > latin:
        # O'zbek yoki Rus
        uzbek_words = ["va", "bu", "ham", "emas", "uchun", "bilan", "salom", "yaxshi"]
        if any(w in text.lower() for w in uzbek_words):
            return "🇺🇿 O'zbek tili"
        return "🇷🇺 Rus tili"
    return "🇬🇧 Ingliz tili"


# ===================== CELERY VAZIFALAR =====================

@celery_app.task(bind=True, name="tasks.analyze_text")
def analyze_text_task(self, chat_id: int, text: str) -> dict:
    """
    Matnni tahlil qilish vazifasi
    - His-tuyg'u tahlili
    - Til aniqlash
    - Statistika
    """
    try:
        logger.info(f"Tahlil boshlandi: chat_id={chat_id}")

        # Ishlov berish vaqtini simulyatsiya qilish
        time.sleep(2)

        # Tahlil
        words = text.split()
        sentences = text.split(".")
        sentiment = simple_sentiment(text)
        language = detect_language(text)

        # Kalit so'zlar (eng uzun so'zlar)
        keywords = sorted(set(words), key=len, reverse=True)[:5]
        keywords_str = ", ".join(f"`{k}`" for k in keywords if len(k) > 3)

        result_text = (
            f"📊 *Matn Tahlili Natijasi*\n"
            f"{'─' * 30}\n\n"
            f"🌐 *Til:* {language}\n"
            f"💭 *His-tuyg'u:* {sentiment}\n\n"
            f"📈 *Statistika:*\n"
            f"• So'zlar soni: `{len(words)}`\n"
            f"• Jumlalar soni: `{len([s for s in sentences if s.strip()])}`\n"
            f"• Belgilar soni: `{len(text)}`\n"
            f"• O'rtacha so'z uzunligi: `{sum(len(w) for w in words) // max(len(words), 1)}` harf\n\n"
            f"🔑 *Kalit so'zlar:*\n{keywords_str or '_Topilmadi_'}\n\n"
            f"✅ Tahlil muvaffaqiyatli bajarildi!"
        )

        send_telegram_message(chat_id, result_text)
        logger.info(f"Tahlil yakunlandi: chat_id={chat_id}")
        return {"status": "success", "chat_id": chat_id}

    except Exception as exc:
        logger.error(f"Tahlilda xato: {exc}")
        send_telegram_message(chat_id, f"❌ Tahlil paytida xato yuz berdi: {exc}")
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(bind=True, name="tasks.translate_text")
def translate_text_task(self, chat_id: int, text: str) -> dict:
    """
    Matnni tarjima qilish vazifasi
    MyMemory API (bepul) ishlatiladi
    """
    try:
        logger.info(f"Tarjima boshlandi: chat_id={chat_id}")
        time.sleep(1)

        # MyMemory bepul tarjima API
        url = "https://api.mymemory.translated.net/get"
        params = {
            "q": text,
            "langpair": "uz|en",  # O'zbekdan inglizga
        }

        response = requests.get(url, params=params, timeout=10)
        data = response.json()

        if data.get("responseStatus") == 200:
            translated = data["responseData"]["translatedText"]
            match_quality = data["responseData"].get("match", 0)

            result_text = (
                f"🌍 *Tarjima Natijasi*\n"
                f"{'─' * 30}\n\n"
                f"📥 *Asl matn:*\n_{text}_\n\n"
                f"📤 *Inglizcha:*\n*{translated}*\n\n"
                f"🎯 Aniqlik: `{int(float(match_quality) * 100)}%`\n\n"
                f"✅ Tarjima muvaffaqiyatli!"
            )
        else:
            result_text = (
                f"⚠️ Tarjima xizmati vaqtincha ishlamayapti.\n"
                f"Keyinroq qayta urinib ko'ring."
            )

        send_telegram_message(chat_id, result_text)
        return {"status": "success", "chat_id": chat_id}

    except requests.Timeout:
        send_telegram_message(chat_id, "⏱ Tarjima xizmati javob bermadi. Qayta urinib ko'ring.")
        raise self.retry(exc=Exception("Timeout"), countdown=30)
    except Exception as exc:
        logger.error(f"Tarjimada xato: {exc}")
        send_telegram_message(chat_id, f"❌ Tarjima xatosi: {exc}")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, name="tasks.summarize_text")
def summarize_text_task(self, chat_id: int, text: str) -> dict:
    """
    Matnni qisqacha xulosa qilish
    """
    try:
        logger.info(f"Xulosa boshlandi: chat_id={chat_id}")
        time.sleep(2)

        words = text.split()
        total_words = len(words)

        if total_words < 20:
            send_telegram_message(
                chat_id,
                "ℹ️ Matn xulosa qilish uchun juda qisqa (kamida 20 so'z kerak)."
            )
            return {"status": "skipped"}

        # Oddiy ekstrakt usuli: birinchi va oxirgi jumlalar
        sentences = [s.strip() for s in text.replace("!", ".").replace("?", ".").split(".") if s.strip()]

        if len(sentences) <= 2:
            summary = text
        elif len(sentences) <= 5:
            summary = f"{sentences[0]}. {sentences[-1]}."
        else:
            # Muhim jumlalarni tanlash (uzunligi o'rtachadan yuqori)
            avg_len = sum(len(s) for s in sentences) / len(sentences)
            important = [s for s in sentences if len(s) > avg_len][:3]
            summary = ". ".join(important) + "."

        compression = int((1 - len(summary.split()) / total_words) * 100)

        result_text = (
            f"📋 *Qisqacha Xulosa*\n"
            f"{'─' * 30}\n\n"
            f"📄 *Asl matn:* `{total_words}` so'z\n"
            f"✂️ *Xulosa:* `{len(summary.split())}` so'z\n"
            f"📉 *Qisqarish:* `{compression}%`\n\n"
            f"💡 *Xulosa:*\n_{summary}_\n\n"
            f"✅ Xulosa tayyor!"
        )

        send_telegram_message(chat_id, result_text)
        return {"status": "success"}

    except Exception as exc:
        logger.error(f"Xulosada xato: {exc}")
        send_telegram_message(chat_id, f"❌ Xulosa chiqarishda xato: {exc}")
        raise self.retry(exc=exc, countdown=30)


@celery_app.task(bind=True, name="tasks.weather")
def weather_task(self, chat_id: int, city: str) -> dict:
    """
    Ob-havo ma'lumotini olish
    OpenWeatherMap API ishlatiladi
    """
    try:
        logger.info(f"Ob-havo so'rovi: {city}")
        time.sleep(1)

        api_key = WEATHER_API_KEY

        if not api_key:
            # API key yo'q bo'lsa, demo ma'lumot
            result_text = (
                f"🌤 *{city} — Ob-havo*\n"
                f"{'─' * 30}\n\n"
                f"⚠️ Ob-havo API kaliti sozlanmagan.\n\n"
                f"🔧 `.env` faylga `WEATHER_API_KEY` qo'shing:\n"
                f"1. [openweathermap.org](https://openweathermap.org/api) ga kiring\n"
                f"2. Bepul ro'yxatdan o'ting\n"
                f"3. API kalitni `.env` faylga qo'shing\n\n"
                f"📍 *Demo ma'lumot ({city}):*\n"
                f"🌡 Harorat: `24°C`\n"
                f"💧 Namlik: `45%`\n"
                f"💨 Shamol: `3 m/s`\n"
                f"☀️ Holat: Quyoshli"
            )
        else:
            url = "https://api.openweathermap.org/data/2.5/weather"
            params = {
                "q": city,
                "appid": api_key,
                "units": "metric",
                "lang": "uz",
            }
            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if response.status_code == 200:
                temp = data["main"]["temp"]
                feels_like = data["main"]["feels_like"]
                humidity = data["main"]["humidity"]
                wind = data["wind"]["speed"]
                desc = data["weather"][0]["description"].capitalize()
                icon_map = {
                    "Clear": "☀️", "Clouds": "☁️", "Rain": "🌧",
                    "Snow": "❄️", "Thunderstorm": "⛈", "Drizzle": "🌦",
                    "Mist": "🌫", "Fog": "🌫",
                }
                weather_main = data["weather"][0]["main"]
                icon = icon_map.get(weather_main, "🌤")

                result_text = (
                    f"{icon} *{city} — Ob-havo*\n"
                    f"{'─' * 30}\n\n"
                    f"🌡 *Harorat:* `{temp:.1f}°C`\n"
                    f"🤔 *His qilish:* `{feels_like:.1f}°C`\n"
                    f"💧 *Namlik:* `{humidity}%`\n"
                    f"💨 *Shamol:* `{wind} m/s`\n"
                    f"☁️ *Holat:* {desc}\n\n"
                    f"✅ Ma'lumot yangilangan!"
                )
            else:
                result_text = (
                    f"❌ `{city}` shahri topilmadi.\n"
                    "To'g'ri shahar nomini kiriting."
                )

        send_telegram_message(chat_id, result_text)
        return {"status": "success", "city": city}

    except Exception as exc:
        logger.error(f"Ob-havo xatosi: {exc}")
        send_telegram_message(chat_id, "❌ Ob-havo ma'lumotini olishda xato yuz berdi.")
        raise self.retry(exc=exc, countdown=60)


@celery_app.task(bind=True, name="tasks.reminder")
def reminder_task(self, chat_id: int, message: str) -> dict:
    """
    Eslatma vazifasi — belgilangan vaqtda xabar yuboradi
    Bu vazifa apply_async(countdown=...) bilan chaqiriladi
    """
    try:
        logger.info(f"Eslatma yuborilmoqda: chat_id={chat_id}")

        result_text = (
            f"⏰ *ESLATMA!*\n"
            f"{'─' * 30}\n\n"
            f"🔔 {message}\n\n"
            f"_Jarvis Yordamchim eslatmasi_"
        )

        send_telegram_message(chat_id, result_text)
        return {"status": "success", "message": message}

    except Exception as exc:
        logger.error(f"Eslatma xatosi: {exc}")
        raise self.retry(exc=exc, countdown=60)


# ===================== DAVRIY VAZIFALAR =====================

@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    """Har soatda bir marta ishlaydigan vazifalar"""
    # Misol: har 6 soatda health check
    sender.add_periodic_task(
        6 * 60 * 60,  # 6 soat (soniyada)
        health_check_task.s(),
        name="health-check-every-6-hours",
    )


@celery_app.task(name="tasks.health_check")
def health_check_task() -> dict:
    """Bot sog'ligi tekshiruvi"""
    logger.info("✅ Health check: Bot ishlayapti!")
    return {"status": "healthy", "timestamp": time.time()}
