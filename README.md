# 🤖 Jarvis Yordamchim — Telegram Bot

**Celery + Redis** orqali background vazifalarni bajaradigan aqlli Telegram bot.

---

## 📦 Arxitektura

```
Foydalanuvchi
     │
     ▼
Telegram Bot (bot.py)
     │  Vazifa yuboradi
     ▼
Redis (Broker)
     │  Vazifalarni saqlaydi
     ▼
Celery Worker (tasks.py)
     │  Background'da bajaradi
     ▼
Natija → Foydalanuvchiga xabar
```

---

## 🚀 Ishga tushirish (Local)

### 1. Redis o'rnatish

**Ubuntu/Debian:**
```bash
sudo apt install redis-server
sudo systemctl start redis
```

**macOS:**
```bash
brew install redis
brew services start redis
```

**Windows:**
```bash
# WSL yoki Docker ishlatish tavsiya etiladi
docker run -d -p 6379:6379 redis:alpine
```

### 2. Python kutubxonalari

```bash
pip install -r requirements.txt
```

### 3. .env fayl yaratish

```bash
cp .env.example .env
# .env faylni oching va ma'lumotlaringizni kiriting
```

**BOT_TOKEN olish:**
1. Telegramda [@BotFather](https://t.me/BotFather) ga yozing
2. `/newbot` buyrug'ini yuboring
3. Bot nomini kiriting: `jarvis_yordamchim`
4. Token nusxalab, `.env` faylga qo'ying

### 4. Ishga tushirish (3 terminal)

**Terminal 1 — Celery Worker:**
```bash
celery --app tasks worker --loglevel info --concurrency 4
```

**Terminal 2 — Flower Monitor (ixtiyoriy):**
```bash
celery flower --app tasks --loglevel info
# http://localhost:5555 da ko'rasiz
```

**Terminal 3 — Bot:**
```bash
python bot.py
```

---

## ☁️ Render.com'ga Deploy qilish

### Avtomatik (render.yaml bilan):
1. GitHub'ga push qiling
2. [render.com](https://render.com) ga kiring
3. **New → Blueprint** tanlang
4. Repository'ni ulang
5. `BOT_TOKEN` va `WEATHER_API_KEY` ni kiriting
6. **Deploy** bosing!

### Qo'lda:
1. Render'da **Redis** yaratin (noeviction, Starter)
2. Internal URL ni nusxalab oling
3. **Background Worker** yaratin (celery worker)
4. **Web Service** yaratin (bot)
5. Har ikkalasiga `CELERY_BROKER_URL` va `BOT_TOKEN` qo'shing

---

## 🎯 Bot Buyruqlari

| Buyruq | Vazifa |
|--------|--------|
| `/start` | Botni boshlash, menyu |
| `/analyze <matn>` | Matnni tahlil qilish |
| `/translate <matn>` | Inglizchaga tarjima |
| `/summarize <matn>` | Qisqacha xulosa |
| `/weather <shahar>` | Ob-havo ma'lumoti |
| `/reminder 10 Dori!` | 10 daqiqadan keyin eslatma |
| `/status` | Faol vazifalar |
| `/help` | Yordam |

---

## 🔧 Yangi Vazifa Qo'shish

`tasks.py` faylga qo'shish:

```python
@celery_app.task(bind=True, name="tasks.mening_vazifam")
def mening_vazifam(self, chat_id: int, parametr: str) -> dict:
    try:
        # Vazifani bajarish
        natija = # ... kodni yozing
        
        send_telegram_message(chat_id, f"✅ Natija: {natija}")
        return {"status": "success"}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)
```

`bot.py` faylga import qiling va buyruq qo'shing.

---

## 📊 Monitoring

Flower orqali:
- **http://localhost:5555** (local)
- Render'da Flower service URL'i

Ko'rasiz:
- Nechta worker ishlamoqda
- Bajarilgan vazifalar soni
- Muvaffaqiyatsiz vazifalar
- Real vaqt statistika

---

## 📄 Fayl Tuzilishi

```
jarvis_yordamchim/
├── bot.py          # Telegram bot (asosiy fayl)
├── tasks.py        # Celery vazifalar
├── requirements.txt
├── render.yaml     # Render.com deploy
├── .env.example    # Sozlamalar namunasi
└── README.md
```
