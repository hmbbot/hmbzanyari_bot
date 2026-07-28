import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import google.generativeai as genai

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# وەرگرتنی تۆکنی بۆت و کۆدی ئەپی زیرەکی دەستکرد لە سێرڤەر (ڕایلی)
TOKEN = os.environ.get("TOKEN")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ڕێکخستنی کۆدی جێמיני
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    model = genai.GenerativeModel('gemini-1.5-flash')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if not GEMINI_API_KEY:
        await update.message.reply_text("⚠️ هەڵە: تکایە GEMINI_API_KEY لە بەشی Variablesـی ڕایلی دابنێ.")
        return

    # پەیامێک بۆ زیرەکی دەستکرد تاوەکو بە شێوازێکی ڕێک وەڵام بداتەوە
    prompt = (
        f"تکایە وەک پسپۆڕێکی زانیاری کەسی و خێزانی، ئەگەر زانیاری لەسەر ئەم کەسە هەبێت "
        f"({text})، زانیارییەکان بە شێوازێکی زۆر ڕێک و پێق بە زمانی کوردی بهێنە بەم شێوەیە:\n"
        f"1. ناوی تەواو\n"
        f"2. ڕەگەز (جنس)\n"
        f"3. ناوی هاوسەر (خێزان)\n"
        f"4. ژمارەی منداڵەکان\n"
        f"5. ناوی منداڵەکان لەگەڵ ساڵی لەدایکبوونیان (مۆلید)\n"
        f"ئەگەر زانیاری وردت لەسەر ئەم کەسە نەبوو، بە جوانی پێمی بڵێ کە زانیاریت لەبەردەستدا نییە."
    )

    try:
        response = model.generate_content(prompt)
        ai_reply = response.text
        
        formatted_response = (
            f"📋 **فۆرمی زانیاری خێزانی (زیرەکی دەستکرد):**\n"
            f"------------------------------------\n"
            f"{ai_reply}\n"
            f"------------------------------------\n"
        )
        await update.message.reply_text(formatted_response, parse_mode="Markdown")
        
    except Exception as e:
        await update.message.reply_text("⚠️ هەڵەیەک ڕوودا لە پەیوەندیکردن بە زیرەکی دەستکردەوە.")

if __name__ == '__main__':
    if not TOKEN:
        print("❌ هەڵە: تۆکنی بۆت نەدۆزراوەتەوە!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        
        print("🤖 بۆتە زیرەکەکە دەستی بە کارکردن کرد...")
        app.run_polling()
