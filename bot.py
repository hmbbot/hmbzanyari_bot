import logging
import os
import requests
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.environ.get("TOKEN")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith("http"):
        await update.message.reply_text("⚠️ تکایە لینکێکی ڕاستەقینەی ڤیدیۆ بنێرە.")
        return

    status_message = await update.message.reply_text("⏳ خەریکە لینکەکە دەخوێنمەوە و ڤیدیۆکە دابەزێنم...")

    video_url = None

    try:
        # ئەگەر لینکەکە هی تیکتۆک بوو
        if "tiktok.com" in url:
            api_url = f"https://tikwm.com/api/?url={url}"
            res = requests.get(api_url, timeout=15).json()
            if "data" in res and "play" in res["data"]:
                video_url = res["data"]["play"]

        # ئەگەر لینکەکە هی یوتیوب، اينستاگرام یا هەر شوێنێکی تر بوو
        else:
            api_url = f"https://apis.davidcyriltech.my.id/download/tout?url={url}"
            res = requests.get(api_url, timeout=15).json()
            if "result" in res and "video" in res["result"]:
                video_url = res["result"]["video"]
            elif "data" in res and "url" in res["data"]:
                video_url = res["data"]["url"]

        if video_url:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id,
                text="📤 ڤیدیۆکە ئامادە بوو، ئێستا دەنێرم..."
            )
            
            await update.message.reply_video(
                video=video_url,
                supports_streaming=True
            )
            
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id
            )
        else:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id,
                text="⚠️ ببورە، ناتوانم ئەم لینکە بخوێنمەوە یان قەبارەکەی زۆر گەورەیە."
            )

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_message.message_id,
            text="⚠️ هەڵەیەک ڕووی دا."
        )

if __name__ == '__main__':
    if not TOKEN:
        print("❌ هەڵە: تۆکنی بۆت نەدۆزراوەتەوە!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_video))
        
        print("🤖 بۆتی هەمەڕەنگ دەستی بە کارکردن کرد...")
        app.run_polling()
