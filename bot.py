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

    status_message = await update.message.reply_text("⏳ خەریکە ڤیدیۆکە لە تیکتۆکەوە وەردەگرم...")

    try:
        # بەکارهێنانی APIـی خێرا و باوەڕپێکراو بۆ داگرتنی ڤیدیۆی تیکتۆک و سوشیاڵ میدیا بێ کێشە
        api_url = f"https://apis.davidcyriltech.my.id/download/tout?url={url}"
        res = requests.get(api_url).json()
        
        video_url = None
        if "result" in res and "video" in res["result"]:
            video_url = res["result"]["video"]
        elif "video_url" in res:
            video_url = res["video_url"]

        if not video_url:
            # ڕێگای دووەم ئەگەر لینکی سەرەکی نەبوو
            api_url_2 = f"https://tikwm.com/api/?url={url}"
            res_2 = requests.get(api_url_2).json()
            if "data" in res_2 and "play" in res_2["data"]:
                video_url = res_2["data"]["play"]

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
                text="⚠️ ببورە، ناتوانم ئەم لینکە بخوێنمەوە."
            )

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_message.message_id,
            text="⚠️ هەڵەیەک ڕووی دا لە دابەزاندنی ڤیدیۆکەدا."
        )

if __name__ == '__main__':
    if not TOKEN:
        print("❌ هەڵە: تۆکنی بۆت نەدۆزراوەتەوە!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_video))
        
        print("🤖 بۆتی تیکتۆک دەستی بە کارکردن کرد...")
        app.run_polling()
