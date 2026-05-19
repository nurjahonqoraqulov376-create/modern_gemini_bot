# 🤖 Shaxsiy Modern AI Telegram Bot

Rasmiy Google GenAI (Gemini 2.5 Flash) modelida va jonli internet qidiruvi (Google Search) bilan ishlaydigan zamonaviy shaxsiy Telegram bot.

## ✨ Imkoniyatlar

* 🌐 **Google Search (Onlayn qidiruv):** Bot jonli internet ma'lumotlariga ulangan. Ob-havo, valyuta kurslari va eng so'nggi yangiliklarni topib bera oladi!
* 🧠 **Google Gemini 2.5 Flash:** Eng tezkor va aqlli AI modeli bilan do'stona muloqot.
* 📩 **Xabar qoldirish & Ega bilan aloqa:** Boshqa foydalanuvchilar yozgan xabarlar sizga keladi va siz to'g'ridan-to'g'ri bot orqali ularga javob bera olasiz.
* 📊 **Statistika:** Bot holati va uning real vaqtdagi ish faoliyati.

## 🚀 Boshlash

### 1. Telegram Bot Token olish
* Telegramda `@BotFather` ga yozing.
* `/newbot` yuboring.
* Botga nom va username bering.
* **TOKEN** ni nusxalab saqlang.

### 2. Google Gemini API kalit olish
* [aistudio.google.com](https://aistudio.google.com/) sahifasiga kiring.
* Google akkauntingiz bilan ro'yxatdan o'ting.
* **Get API Key** -> **Create API Key** tugmasini bosing.
* `AIzaSy...` deb boshlanuvchi kalitni nusxalab saqlang.

### 3. O'z Chat ID'ingizni bilish
* Telegramda `@userinfobot` ga `/start` yuboring.
* Ko'rsatilgan raqam sizning shaxsiy Chat ID raqamingiz hisoblanadi.

### 4. Railway.app platformasiga joylashtirish (Serverga yuklash)

**GitHub ga yuklash:**
PyCharm terminalida quyidagi buyruqlarni bittalab ishlating:
```bash
git init
git add .
git commit -m "Modern Gemini Bot initialized"
git branch -M main
git remote add origin [https://github.com/YOUR_USERNAME/my-telegram-bot.git](https://github.com/YOUR_USERNAME/my-telegram-bot.git)
git push -u origin main