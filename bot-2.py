import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters, ConversationHandler
)
from groq import Groq

# ===== SOZLAMALAR =====
TELEGRAM_TOKEN = os.environ.get("8944587981:AAGun24How9fVEH4fNHtl1B5F86_fJOc4Fg", "")
GROQ_API_KEY = os.environ.get("", "")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)
client = Groq(api_key=GROQ_API_KEY)

# ===== STATES =====
CHOOSING_TYPE, WAITING_LANGUAGE, WAITING_TOPIC, WAITING_PAGES = range(4)

WORK_TYPES = {
    "kurs_ishi": "📄 Kurs Ishi",
    "mustaqil_ish": "📝 Mustaqil Ish",
    "referat": "📋 Referat",
    "esse": "✍️ Esse",
    "hisobot": "📊 Hisobot",
    "dissertatsiya": "🎓 Dissertatsiya bo'limi",
}

LANGUAGES = {
    "uzbek": "🇺🇿 O'zbek tili",
    "russian": "🇷🇺 Rus tili",
    "english": "🇬🇧 Ingliz tili",
}


def generate_text(work_type: str, topic: str, pages: int, language: str = "uzbek") -> str:
    lang_map = {"uzbek": "O'zbek tilida", "russian": "на русском языке", "english": "in English"}
    lang_str = lang_map.get(language, "O'zbek tilida")
    words = pages * 250

    system = f"""Sen professional akademik yozuvchi assistantsan. {lang_str} yozasan.
Qoidalar:
- To'liq akademik tuzilmada yoz
- Ilmiy, professional til ishlat
- Har bir bo'limni mazmunan boy va to'liq yoz
- Kamida 10 ta haqiqiy manba keltir
- O'zbekiston OTM standartlariga mos yoz"""

    prompt = f"""Quyidagi ishni professional tarzda yoz:

ISH TURI: {work_type}
MAVZU: {topic}  
HAJM: {pages} sahifa ({words} so'z)
TIL: {lang_str}

TUZILMA (qat'iy amal qil):

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
O'ZBEKISTON RESPUBLIKASI
OLIY VA O'RTA MAXSUS TA'LIM VAZIRLIGI

[UNIVERSITET NOMI]
[FAKULTET] fakulteti
[KAFEDRA] kafedrasi

{work_type.upper()}

Mavzu: «{topic}»

          Bajardi: ___________
          Tekshirdi: ___________

[SHAHAR] — [YIL]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

MUNDARIJA

KIRISH .................................................. 3
1-BOB. [BOB NOMI] ........................................ 5
  1.1. [kichik bo'lim] ................................... 5
  1.2. [kichik bo'lim] ................................... 8
  1.3. [kichik bo'lim] ................................... 11
2-BOB. [BOB NOMI] ........................................ 14
  2.1. [kichik bo'lim] ................................... 14
  2.2. [kichik bo'lim] ................................... 17
  2.3. [kichik bo'lim] ................................... 20
XULOSA ................................................... 23
FOYDALANILGAN ADABIYOTLAR ................................ 25

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
KIRISH

Mavzuning dolzarbligi: [3-4 gap]
Tadqiqotning maqsadi: [1-2 gap]
Tadqiqotning vazifalari: [5 ta vazifa]
Tadqiqot ob'ekti: [1 gap]
Tadqiqot predmeti: [1 gap]
Ishning tuzilishi: [1-2 gap]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1-BOB. [MAVZUGA OID NAZARIY BOB NOMI]

1.1. [Birinchi kichik bo'lim sarlavhasi]
[To'liq matn - kamida 3 paragraf]

1.2. [Ikkinchi kichik bo'lim sarlavhasi]
[To'liq matn - kamida 3 paragraf]

1.3. [Uchinchi kichik bo'lim sarlavhasi]
[To'liq matn - kamida 3 paragraf]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
2-BOB. [MAVZUGA OID AMALIY BOB NOMI]

2.1. [Birinchi kichik bo'lim sarlavhasi]
[To'liq matn - kamida 3 paragraf]

2.2. [Ikkinchi kichik bo'lim sarlavhasi]
[To'liq matn - kamida 3 paragraf]

2.3. [Uchinchi kichik bo'lim sarlavhasi]
[To'liq matn - kamida 3 paragraf]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
XULOSA

[Asosiy natijalar - 5-7 ta xulosa]
[Tavsiyalar]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FOYDALANILGAN ADABIYOTLAR RO'YXATI

1. [Muallif. Kitob nomi. Shahar: Nashriyot, Yil. - sahifalar soni b.]
2. [Muallif. Kitob nomi. Shahar: Nashriyot, Yil.]
... (kamida 10 ta manba)

Endi shu tuzilmada TO'LIQ yoz. Har bir bo'lim kamida 2-3 paragraf bo'lsin."""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt}
            ],
            max_tokens=8000,
            temperature=0.55,
            top_p=0.9
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Groq xatosi: {e}")
        return None


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    keyboard = [[InlineKeyboardButton(name, callback_data=key)] for key, name in WORK_TYPES.items()]
    await update.message.reply_text(
        f"👋 Salom, *{user.first_name}*!\n\n"
        "🎓 *Akademik Ish Yozuvchi Bot*\n\n"
        "Men sizga professional darajada:\n"
        "✅ Kurs ishi\n✅ Mustaqil ish\n✅ Referat\n✅ Esse va boshqalar\n\n"
        "yozib beraman. 24/7 ishlaydi!\n\n"
        "━━━━━━━━━━━━━━━\n"
        "📌 *Qanday ish kerak?*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSING_TYPE


async def work_type_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["work_type"] = WORK_TYPES[query.data]
    keyboard = [[InlineKeyboardButton(name, callback_data=f"lang_{k}")] for k, name in LANGUAGES.items()]
    await query.edit_message_text(
        f"✅ *{WORK_TYPES[query.data]}* tanlandi!\n\n🌐 *Qaysi tilda yozilsin?*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return WAITING_LANGUAGE


async def language_chosen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    lang = query.data.replace("lang_", "")
    context.user_data["language"] = lang
    await query.edit_message_text(
        f"✅ Til: *{LANGUAGES[lang]}*\n\n"
        "📝 *Mavzuni yozing:*\n\n"
        "_Misol: O'zbekistonda raqamli iqtisodiyotni rivojlantirish_",
        parse_mode="Markdown"
    )
    return WAITING_TOPIC


async def topic_received(update: Update, context: ContextTypes.DEFAULT_TYPE):
    topic = update.message.text.strip()
    if len(topic) < 5:
        await update.message.reply_text("⚠️ Mavzu juda qisqa. To'liqroq yozing!")
        return WAITING_TOPIC
    context.user_data["topic"] = topic
    keyboard = [
        [InlineKeyboardButton("5 📄", callback_data="p_5"), InlineKeyboardButton("10 📄", callback_data="p_10"), InlineKeyboardButton("15 📄", callback_data="p_15")],
        [InlineKeyboardButton("20 📄", callback_data="p_20"), InlineKeyboardButton("25 📄", callback_data="p_25"), InlineKeyboardButton("30 📄", callback_data="p_30")],
        [InlineKeyboardButton("✏️ Boshqa son kiriting", callback_data="p_custom")]
    ]
    await update.message.reply_text(
        f"✅ Mavzu qabul qilindi!\n\n📄 *Necha sahifa bo'lsin?*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return WAITING_PAGES


async def pages_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "p_custom":
        context.user_data["custom_pages"] = True
        await query.edit_message_text("✏️ Sahifalar sonini yozing (1-50):")
        return WAITING_PAGES
    pages = int(query.data.replace("p_", ""))
    await query.edit_message_text(f"⏳ *{pages} sahifali ish yozilmoqda...*", parse_mode="Markdown")
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
        await update.message.reply_text("⚠️ Faqat raqam kiriting! Masalan: 15")
        return WAITING_PAGES
    context.user_data["custom_pages"] = False
    await do_generate(update, context, pages)
    return ConversationHandler.END


async def do_generate(update, context, pages):
    chat_id = update.effective_chat.id
    work_type = context.user_data.get("work_type", "Kurs ishi")
    topic = context.user_data.get("topic", "")
    language = context.user_data.get("language", "uzbek")
    lang_name = LANGUAGES.get(language, "🇺🇿 O'zbek tili")

    msg = await context.bot.send_message(
        chat_id=chat_id,
        text=(
            "⏳ *Ish yozilmoqda...*\n\n"
            f"📋 {work_type}\n"
            f"📌 {topic}\n"
            f"📄 {pages} sahifa\n"
            f"🌐 {lang_name}\n\n"
            "⏱ _30-90 soniya kutib turing..._"
        ),
        parse_mode="Markdown"
    )

    result = generate_text(work_type, topic, pages, language)
    await msg.delete()

    if not result:
        await context.bot.send_message(chat_id=chat_id, text="❌ Xatolik. /start bilan qayta urinib ko'ring.")
        return

    parts = [result[i:i+4000] for i in range(0, len(result), 4000)]
    for i, part in enumerate(parts, 1):
        prefix = f"✅ *{work_type} tayyor!* ({i}/{len(parts)})\n\n" if i == 1 else f"📄 *{i}/{len(parts)}-qism:*\n\n"
        try:
            await context.bot.send_message(chat_id=chat_id, text=prefix + part, parse_mode="Markdown")
        except Exception:
            await context.bot.send_message(chat_id=chat_id, text=prefix + part)

    await context.bot.send_message(
        chat_id=chat_id,
        text="💡 Yana ish kerakmi?",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔄 Yangi ish", callback_data="restart")]])
    )


async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data.clear()
    keyboard = [[InlineKeyboardButton(name, callback_data=key)] for key, name in WORK_TYPES.items()]
    await query.edit_message_text(
        "📌 *Qanday ish kerak?*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    return CHOOSING_TYPE


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 *Bot imkoniyatlari:*\n\n"
        "• Kurs ishi, Mustaqil ish, Referat, Esse, Hisobot\n"
        "• O'zbek 🇺🇿 | Rus 🇷🇺 | Ingliz 🇬🇧 tillari\n"
        "• 5-50 sahifagacha\n"
        "• To'g'ri akademik tuzilma\n"
        "• Manbalar ro'yxati bilan\n"
        "• 24/7 ishlaydi\n\n"
        "*/start* — boshlash\n"
        "*/cancel* — bekor qilish",
        parse_mode="Markdown"
    )


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text("❌ Bekor qilindi. /start bilan qayta boshlang.")
    return ConversationHandler.END


def main():
    app = Application.builder().token(TELEGRAM_TOKEN).build()
    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
            CallbackQueryHandler(restart, pattern="^restart$"),
        ],
        states={
            CHOOSING_TYPE: [CallbackQueryHandler(work_type_chosen, pattern="^(kurs_ishi|mustaqil_ish|referat|esse|hisobot|dissertatsiya)$")],
            WAITING_LANGUAGE: [CallbackQueryHandler(language_chosen, pattern="^lang_")],
            WAITING_TOPIC: [MessageHandler(filters.TEXT & ~filters.COMMAND, topic_received)],
            WAITING_PAGES: [
                CallbackQueryHandler(pages_button, pattern="^p_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, pages_text),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )
    app.add_handler(conv)
    app.add_handler(CommandHandler("help", help_cmd))
    logger.info("✅ Bot 24/7 rejimda ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
