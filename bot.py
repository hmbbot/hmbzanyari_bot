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
        await update.message.reply_text("⚠️ تکایە لینکێکی ڕاستەقینەی ڤیدیۆ بنێرە (یوتیوب، تیکتۆک، اینستاگرام، و هتد).")
        return

    status_message = await update.message.reply_text("⏳ خەریکە کوالیتی ڕاستەقینەی ڤیدیۆکە دادەبەزێنم...")

    # ڕێکخستنی yt-dlp بۆ بەدەستهێنانی باشترین و بەرزترین کوالیتی ڕەسەن (Original Quality)
    output_template = 'video_%(id)s.%(ext)s'
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best', # هەڵبژاردنی باشترین ڤیدیۆ و دەنگی ڕەسەن
        'outtmpl': output_template,
        'merge_output_format': 'mp4',
        'max_filesize': 50 * 1024 * 1024, # سنووری ٥٠ مێگابایت بۆ ناردن لە ڕێگەی بۆتی تێلیگرامەوە
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
            text="📤 ڤیدیۆکە بە کوالیتی ڕاستەقینە دابەزی، ئێستا دەنێرم..."
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
            text="⚠️ ببورە، قەبارەی ئەم ڤیدیۆیە بە کوالیتی ڕاستەقینە لە ٥٠ مێگابایت گەورەترە و ناتوانرێت ڕاستەوخۆ لە تێلیگرامدا بنێررێت."
        )

if __name__ == '__main__':
    if not TOKEN:
        print("❌ هەڵە: تۆکنی بۆت نەدۆزراوەتەوە!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_video))
        
        print("🤖 بۆتی دابەزێنەری ڤیدیۆ (بە کوالیتی ڕاستەقینە) دەستی بە کارکردن کرد...")
        app.run_polling()
