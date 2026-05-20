# 🤖 Jarvis Yordamchim — AI Telegram Bot

**100% BEPUL** — Railway.app + Anthropic (bepul kredit)

---

## Kerakli narsalar (barchasi bepul)

| Xizmat | Link | Narx |
|--------|------|------|
| Bot token | @BotFather (Telegram) | Bepul |
| AI (Claude) | console.anthropic.com | Bepul kredit ($5) |
| Hosting | railway.app | Bepul tier |
| Redis | Railway'da qo'shiladi | Bepul |

---

## Railway.app ga deploy (BEPUL)

### 1. Anthropic API key oling
1. [console.anthropic.com](https://console.anthropic.com) ga kiring
2. Ro'yxatdan o'ting (bepul $5 kredit beriladi)
3. **API Keys** → **Create Key** → nusxalab oling

### 2. Railway'ga deploy qiling
1. [railway.app](https://railway.app) ga kiring (GitHub bilan)
2. **New Project** → **Deploy from GitHub repo**
3. Repo'ni ulang

### 3. Redis qo'shing
1. Railway loyiha ichida **+ New** → **Database** → **Redis**
2. Redis qo'shilgach, `REDIS_URL` avtomatik paydo bo'ladi

### 4. Environment Variables
Railway → Loyiha → **Variables** bo'limiga qo'shing:

```
BOT_TOKEN = sizning_bot_tokeningiz
ANTHROPIC_API_KEY = sizning_api_keyingiz
CELERY_BROKER_URL = ${{Redis.REDIS_URL}}
CELERY_RESULT_BACKEND = ${{Redis.REDIS_URL}}
```

### 5. Ikki servis yarating

**Servis 1 — Bot:**
- Start Command: `python bot.py`

**Servis 2 — Celery Worker:**
- Start Command: `celery --app tasks worker --loglevel info`

---

## Bot imkoniyatlari

- 🧠 **AI savol** — istalgan savolga Claude javob beradi
- 📝 **Tahlil** — matn his-tuyg'u va mavzu tahlili
- 🌍 **Tarjima** — har qanday tilga tarjima
- 📋 **Xulosa** — uzun matnni qisqartirish
- ⏰ **Eslatma** — vaqtli eslatmalar
- 💬 **Har xabarga AI javob** — buyruqsiz ham ishlaydi

---

## Fayl tuzilishi

```
jarvis_yordamchim/
├── bot.py           # Telegram bot
├── tasks.py         # Celery + AI vazifalar
├── requirements.txt
├── .env.example     # Sozlamalar namunasi
└── README.md
```
