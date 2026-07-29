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

    status_message = await update.message.reply_text("⏳ خەریکە ڤیدیۆکە دادەبەزێنم...")

    try:
        # بەکارهێنانی APIـی فەرمی و بەهێزی TikWM بۆ هێنانی ڤیدیۆی تیکتۆک
        api_url = f"https://tikwm.com/api/?url={url}"
        response = requests.get(api_url, timeout=15).json()
        
        video_url = None
        if "data" in response and "play" in response["data"]:
            video_url = response["data"]["play"]

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
            text="⚠️ هەڵەیەک ڕووی دا."
        )

if __name__ == '__main__':
    if not TOKEN:
        print("❌ هەڵە: تۆکنی بۆت نەدۆزراوەتەوە!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_video))
        
        print("🤖 بۆتی دابەزێنەر دەستی بە کارکردن کرد...")
        app.run_polling()
