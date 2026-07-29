import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
from openai import OpenAI

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.environ.get("TOKEN")
# دەتوانین هەمان ناوی GEMINI_API_KEY بەکاربهێنین یان ناوی بگۆڕین
API_KEY = os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENROUTER_API_KEY")

# ڕێکخستنی کڵایەنت بۆ OpenRouter (بە سیستمی OpenAI سازگارە)
client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY,
)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    
    if not API_KEY:
        await update.message.reply_text("⚠️ هەڵە: API Key لە ڕایلی دانەناوە!")
        return

    prompt = (
        f"تکایە وەک پسپۆڕێکی زانیاری کەسی و خێزانی، ئەگەر زانیاری لەسەر ئەم کەسە هەبێت "
        f"({text})، زانیارییەکان بە شێوازێکی زۆر ڕێک و پێق بە زمانی کوردی بهێنە بەم شێوەیە:\n"
        f"1. ناوی تەواو\n"
        f"2. ڕەگەز (جنس)\n"
        f"3. ناوی هاوسەر (خێزان)\n"
        f"4. ژمارەی منداڵەکان\n"
        f"5. ناوی منداڵەکان لەگەڵ ساڵی لەدایکبوونیان (مۆلید)\n"
        f"ئەگەر زانیاریت لەسەر نەبوو، بە جوانی پێمی بڵێ کە زانیاری لەبەردەستدا نییە."
    )

    try:
        # بەکارهێنانی مۆدێلی خۆڕایی و بەهێزی OpenRouter
        response = client.chat.completions.create(
            model="deepseek/deepseek-chat", # یان دەتوانیت بەکاربهێنیت meta-llama/llama-3-8b-instruct
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        ai_reply = response.choices[0].message.content
        
        formatted_response = (
            f"📋 **فۆرمی زانیاری خێزانی (OpenRouter AI):**\n"
            f"------------------------------------\n"
            f"{ai_reply}\n"
            f"------------------------------------\n"
        )
        await update.message.reply_text(formatted_response, parse_mode="Markdown")
        
    except Exception as e:
        error_msg = str(e)
        logging.error(f"OpenRouter Error: {error_msg}")
        await update.message.reply_text(f"⚠️ هەڵە: {error_msg}")

if __name__ == '__main__':
    if not TOKEN:
        print("❌ هەڵە: تۆکنی بۆت نەدۆزراوەتەوە!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        
        print("🤖 بۆتە زیرەکەکە لەسەر OpenRouter دەستی بە کارکردن کرد...")
        app.run_polling()
