import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import yt_dlp

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

    output_template = 'video_%(id)s.%(ext)s'
    
    # ڕێکخستنی زیرەک: ئەگەر ڤیدیۆکە گەورە بوو، کوالیتییەک هەڵبژێرە کە قەبارەکەی گونجاو بێت بۆ تێلیگرام
    ydl_opts = {
        'format': 'best[filesize<50M]/bestvideo[filesize<50M]+bestaudio/best',
        'outtmpl': output_template,
        'merge_output_format': 'mp4',
    }

    filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            if not filename.endswith('.mp4'):
                filename = os.path.splitext(filename)[0] + '.mp4'

        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_message.message_id,
            text="📤 ڤیدیۆکە ئامادە بوو، ئێستا دەنێرم..."
        )

        with open(filename, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                supports_streaming=True
            )

        if os.path.exists(filename):
            os.remove(filename)

        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=status_message.message_id
        )

    except Exception as e:
        error_msg = str(e)
        logging.error(f"Download Error: {error_msg}")
        
        if filename and os.path.exists(filename):
            os.remove(filename)
            
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_message.message_id,
            text="⚠️ ببورە، ئەم لینکە کێشەی هەیە یان ڤیدیۆکەی زۆر درێژە و ناتوانرێت داببەزێنرێت."
        )

if __name__ == '__main__':
    if not TOKEN:
        print("❌ هەڵە: تۆکنی بۆت نەدۆزراوەتەوە!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_video))
        
        print("🤖 بۆتی دابەزێنەری ڤیدیۆ دەستی بە کارکردن کرد...")
        app.run_polling()
