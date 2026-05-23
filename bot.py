import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters, ConversationHandler
)
from groq import Groq

TELEGRAM_TOKEN = os.environ.get("8962662681:AAF-kSF5tA3zCrZzhgFaF33fARgaXo3q2rk", "")
GROQ_API_KEY = os.environ.get("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", "")

logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
client = Groq(api_key=GROQ_API_KEY)

CHOOSING_TYPE, WAITING_LANGUAGE, WAITING_TOPIC, WAITING_PAGES = range(4)

WORK_TYPES = {
    "kurs_ishi": "📄 Kurs Ishi",
    "mustaqil_ish": "📝 Mustaqil Ish",
    "referat": "📋 Referat",
    "esse": "✍️ Esse",
    "hisobot": "📊 Hisobot",
}

LANGUAGES = {
    "uzbek": "🇺🇿 O'zbek tili",
    "russian": "🇷🇺 Rus tili",
    "english": "🇬🇧 Ingliz tili",
}

def generate_text(work_type, topic, pages, language="uzbek"):
    lang_map = {"uzbek": "O'zbek tilida", "russian": "на русском языке", "english": "in English"}
    lang_str = lang_map.get(language, "O'zbek tilida")
    words = pages * 250
    system = f"Sen professional akademik yozuvchi assistantsan. {lang_str} yozasan. Ilmiy, professional til ishlat. Kamida 10 ta manba keltir."
    prompt = f"""Quyidagi ishni yoz:
ISH TURI: {work_type}
MAVZU: {topic}
HAJM: {pages} sahifa ({words} so'z)
TIL: {lang_str}

TUZILMA:
1. SARLAVHA SAHIFASI
2. MUNDARIJA
3. KIRISH (dolzarbligi, maqsad, vazifalar)
4. 1-BOB (3 ta kichik bo'lim, har biri 3+ paragraf)
5. 2-BOB (3 ta kichik bo'lim, har biri 3+ paragraf)
6. XULOSA
7. FOYDALANILGAN ADABIYOTLAR (10+ manba)

To'liq va professional yoz!"""
    try:
        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": prompt}],
            max_tokens=8000,
            temperature=0.55,
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Xato: {e}")
        return None

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton(name, callback_data=key)] for key, name in WORK_TYPES.items()]
    await update.message.reply_text(
        "👋 Salom! Men akademik ishlar yozuvchi botman!\n\n📌 Qanday ish kerak?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSING_TYPE

async def work_type_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["work_type"] = WORK_TYPES[query.data]
    keyboard = [[InlineKeyboardButton(name, callback_data=f"lang_{k}")] for k, name in LANGUAGES.items()]
    await query.edit_message_text("🌐 Qaysi tilda yozilsin?", reply_markup=InlineKeyboardMarkup(keyboard))
    return WAITING_LANGUAGE

async def language_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.replace("lang_", "")
    context.user_data["language"] = lang
    await query.edit_message_text("📝 Mavzuni yozing:\n\nMasalan: O'zbekistonda raqamli iqtisodiyot")
    return WAITING_TOPIC

async def topic_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = update.message.text.strip()
    if len(topic) < 5:
        await update.message.reply_text("⚠️ Mavzu juda qisqa!")
        return WAITING_TOPIC
    context.user_data["topic"] = topic
    keyboard = [
        [InlineKeyboardButton("5 📄", callback_data="p_5"), InlineKeyboardButton("10 📄", callback_data="p_10"), InlineKeyboardButton("15 📄", callback_data="p_15")],
        [InlineKeyboardButton("20 📄", callback_data="p_20"), InlineKeyboardButton("25 📄", callback_data="p_25"), InlineKeyboardButton("30 📄", callback_data="p_30")],
        [InlineKeyboardButton("✏️ Boshqa son", callback_data="p_custom")]
    ]
    await update.message.reply_text("📄 Necha sahifa?", reply_markup=InlineKeyboardMarkup(keyboard))
    return WAITING_PAGES

async def pages_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "p_custom":
        context.user_data["custom_pages"] = True
        await query.edit_message_text("✏️ Sahifalar sonini yozing (1-50):")
        return WAITING_PAGES
    pages = int(query.data.replace("p_", ""))
    await query.edit_message_text(f"⏳ {pages} sahifali ish yozilmoqda...")
    await do_generate(update, context, pages)
    return ConversationHandler.END

async def pages_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.user_data.get("custom_pages"):
        return WAITING_PAGES
    try:
        pages = int(update.message.text.strip())
        if not 1 <= pages <= 50:
            await update.message.reply_text("⚠️ 1 dan 50 gacha raqam kiriting!")
            return WAITING_PAGES
    except ValueError:
        await update.message.reply_text("⚠️ Faqat raqam kiriting!")
        return WAITING_PAGES
    context.user_data["custom_pages"] = False
    await do_generate(update, context, pages)
    return ConversationHandler.END

async def do_generate(update, context, pages):
    chat_id = update.effective_chat.id
    work_type = context.user_data.get("work_type", "Kurs ishi")
    topic = context.user_data.get("topic", "")
    language = context.user_data.get("language", "uzbek")
    msg = await context.bot.send_message(chat_id=chat_id, text=f"⏳ Yozilmoqda...\n\n📋 {work_type}\n📌 {topic}\n📄 {pages} sahifa\n\n30-90 soniya kuting...")
    result = generate_text(work_type, topic, pages, language)
    await msg.delete()
    if not result:
        await context.bot.send_message(chat_id=chat_id, text="❌ Xatolik. /start bilan qayta urinib ko'ring.")
        return
    parts = [result[i:i+4000] for i in range(0, len(result), 4000)]
    for i, part in enumerate(parts, 1):
        prefix = f"✅ {work_type} tayyor! ({i}/{len(parts)})\n\n" if i == 1 else f"📄 {i}/{len(parts)}-qism:\n\n"
        await context.bot.send_message(chat_id=chat_id, text=prefix + part)
    await context.bot.send_message(chat_id=chat_id, text="💡 Yana ish kerakmi?", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Yangi ish", callback_data="restart")]]))

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    keyboard = [[InlineKeyboardButton(name, callback_data=key)] for key, name in WORK_TYPES.items()]
    await query.edit_message_text("📌 Qanday ish kerak?", reply_markup=InlineKeyboardMarkup(keyboard))
    return CHOOSING_TYPE

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Bekor qilindi. /start bilan qayta boshlang.")
    return ConversationHandler.END

def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start), CallbackQueryHandler(restart, pattern="^restart$")],
        states={
            CHOOSING_TYPE: [CallbackQueryHandler(work_type_chosen, pattern="^(kurs_ishi|mustaqil_ish|referat|esse|hisobot)$")],
            WAITING_LANGUAGE: [CallbackQueryHandler(language_chosen, pattern="^lang_")],
            WAITING_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, topic_received)],
            WAITING_PAGES: [CallbackQueryHandler(pages_button, pattern="^p_"), MessageHandler(filters.TEXT & ~filters.COMMAND, pages_text)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    app.add_handler(conv)
    logger.info("Bot ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
