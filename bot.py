import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

# ڕێکخستنی لاگین بۆ بینینی زانیاری و هەڵەکان
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# تۆکنی بۆتەکەت لێرە دابنە لە ناو نیشانەی کەوانەکان
TOKEN = "8915633184:AAGc76tcI8yLcZqbQQzRTCBij3HsVYU-sT0"

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    words = text.split()
    
    # پشکنین ئەگەر ناوەکە بە سێ قۆڵی (سیانی) نوسرابێت
    if len(words) >= 3:
        first_name = words[0]
        father_name = words[1]
        family_name = " ".join(words[2:]) # گرتنی بەشی کۆتایی وەک ناوی خێزان یان پاشناو
        
        # دروستکردنی فۆرمەکە بە شێوازێکی ڕێک
        response = (
            "📋 **فۆرمی زانیاری کەسی (تۆمارکراو)**\n"
            "------------------------------------\n"
            f"👤 **ناوی تەواو:** {text}\n"
            f"🔸 **ناوی یەکەم:** {first_name}\n"
            f"👨 **ناوی باوک:** {father_name}\n"
            f"🏛 **ناوی خێزان (پاشناو):** {family_name}\n"
            f"⚧ **جنس (ڕەگەز):** (دیارینەکراو / نێر - مێ)\n"
            f"📅 **مۆلید (ساڵی لەدایکبوون):** (نموونە: 1995)\n"
            f"📍 **شوێنی لەدایکبوون:** (عێراق)\n"
            "------------------------------------\n"
            "✅ *سوپاس، زانیارییەکانت بە سەرکەوتوویی وەربگیران.*"
        )
    else:
        response = (
            "⚠️ **تکایە ناوی خۆت بە سێ قۆڵی (سیانی) بنووسە!**\n"
            "بۆ نموونە: `ئارام محەمەد ئەحمەد`"
        )
    
    await update.message.reply_text(response, parse_mode="Markdown")

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    
    print("🤖 بۆتەکە دەستی بە کارکردن کرد...")
    app.run_polling()
