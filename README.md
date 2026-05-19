# 🤖 Shaxsiy AI Telegram Bot

Claude AI bilan ishlaydigan shaxsiy Telegram bot.

## ✨ Imkoniyatlar

- 🤖 **Claude AI** bilan suhbat — istalgan savolga javob
- 📨 **Xabar qoldirish** — boshqalar sizga xabar qoldira oladi
- 🔔 **Ogohlantirish** — yangi tashrif va xabarlar haqida xabardor bo'lasiz
- 💬 **Javob berish** — xabar qoldirgan odamlarga javob yuborish
- 📊 **Statistika** — bot holati va faol suhbatlar

## 🚀 Boshlash

### 1. Telegram Bot Token olish
1. Telegramda **@BotFather** ga yozing
2. `/newbot` yuboring
3. Botga nom va username bering
4. **TOKEN** ni nusxalab saqlang

### 2. Anthropic API kalit olish
1. **https://console.anthropic.com** ga kiring
2. Google akkount bilan ro'yxatdan o'ting
3. **API Keys → Create Key** tugmasini bosing
4. Kalitni nusxalab saqlang

### 3. O'z Chat ID'ingizni bilish
1. Telegramda **@userinfobot** ga `/start` yuboring
2. Ko'rsatilgan raqam sizning **Chat ID** ingiz

### 4. Render.com ga joylashtirish (BEPUL)

#### GitHub ga yuklash:
```bash
git init
git add .
git commit -m "Bot yaratildi"
git remote add origin https://github.com/YOUR_USERNAME/my-telegram-bot.git
git push -u origin main
```

#### Render.com sozlash:
1. **https://render.com** ga kiring (Google bilan kirish mumkin)
2. **New → Web Service** tugmasini bosing
3. GitHub repozitoriyangizni tanlang
4. Quyidagi sozlamalarni kiriting:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `python bot.py`
5. **Environment Variables** bo'limiga quyidagilarni qo'shing:
   ```
   BOT_TOKEN = sizning_bot_tokeningiz
   ANTHROPIC_API_KEY = sizning_api_kalitingiz
   OWNER_CHAT_ID = sizning_chat_id_raqamingiz
   ```
6. **Create Web Service** tugmasini bosing

Bot 2-3 daqiqada ishga tushadi! ✅

## 📋 Buyruqlar

| Buyruq | Tavsif |
|--------|--------|
| `/start` | Botni ishga tushirish |
| `/clear` | Suhbat tarixini tozalash |
| `/pending` | Kutayotgan xabarlar (faqat siz uchun) |
| `/status` | Bot holati (faqat siz uchun) |

## 🔧 Mahalliy ishga tushirish

```bash
# Paketlarni o'rnatish
pip install -r requirements.txt

# .env fayl yaratish
cp .env.example .env
# .env faylini oching va ma'lumotlaringizni kiriting

# Botni ishga tushirish
python bot.py
```

## 📁 Fayl tuzilishi

```
telegram_bot/
├── bot.py           # Asosiy bot kodi
├── requirements.txt # Python paketlar
├── render.yaml      # Render.com sozlamalari
├── .env.example     # Sozlamalar namunasi
└── README.md        # Ushbu fayl
```
