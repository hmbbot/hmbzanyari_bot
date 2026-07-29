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

    status_message = await update.message.reply_text("⏳ خەریکە کوالیتی HD دەدۆزمەوە و ڤیدیۆکە دادەبەزێنم...")

    # ڕێکخستنی ناو و فۆرمات بۆ HD (باشترین کوالیتی کە لەگەڵ mp4 کار بکات)
    output_template = 'video_%(id)s.%(ext)s'
    ydl_opts = {
        # هەڵبژاردنی باشترین کوالیتی HD (تا 1080p) لەگەڵ باشترین دەنگ و تێکەڵکردنیان بۆ mp4
        'format': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best',
        'outtmpl': output_template,
        'merge_output_format': 'mp4',
        'max_filesize': 50 * 1024 * 1024, # ڕێگریکردن لە تێپەڕاندنی ٥٠ مێگابایت بۆ ئەوەی تێلیگرام قبووڵی بکات
    }

    filename = None
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            # دڵنیابوونەوە لەوەی فۆرماتەکە mp4ـە دوای تێکەڵکردن
            if not filename.endswith('.mp4'):
                filename = os.path.splitext(filename)[0] + '.mp4'

        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_message.message_id,
            text="📤 ڤیدیۆکە بە کوالیتی HD دابەزی، ئێستا دەنێرم..."
        )

        # ناردنی ڤیدیۆ بە شێوەی وێنەی جووڵاو یان فایل بۆ پاراستنی کوالیتی
        with open(filename, 'rb') as video_file:
            await update.message.reply_video(
                video=video_file,
                supports_streaming=True # بۆ ئەوەی خێرا لە تێلیگرام کار بکات
            )

        # سڕینەوەی ڤیدیۆکە لە سێرڤەر دوای ناردنی
        if os.path.exists(filename):
            os.remove(filename)

        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=status_message.message_id
        )

    except Exception as e:
        error_msg = str(e)
        logging.error(f"Download Error: {error_msg}")
        
        # پاککردنەوەی فایل ئەگەر هەڵەیەک ڕووی دا
        if filename and os.path.exists(filename):
            os.remove(filename)
            
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_message.message_id,
            text="⚠️ ببورە، قەبارەی ئەم ڤیدیۆیە بە کوالیتی HD لە ٥٠ مێگابایت گەورەترە و ناتوانرێت ڕاستەوخۆ لە تێلیگرامدا بنێررێت."
        )

if __name__ == '__main__':
    if not TOKEN:
        print("❌ هەڵە: تۆکنی بۆت نەدۆزراوەتەوە!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_video))
        
        print("🤖 بۆتی دابەزێنەری ڤیدیۆ (HD) دەستی بە کارکردن کرد...")
        app.run_polling()
