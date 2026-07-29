import logging
import os
import requests
from telegram import Update, BotCommand
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.environ.get("TOKEN")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 سڵاو! بۆ دابەزاندنی ڤیدیۆ، سلاش (/) دابگرە و فەرمانی مەبەست هەڵبژێرە:\n\n"
        "🎵 `/tiktok [لینک]`\n"
        "📸 `/instagram [لینک]`",
        parse_mode="Markdown"
    )

async def tiktok_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ تکایە لینکەکە دوای فەرمانەکە بنووسە.\nنموونە:\n`/tiktok https://vt.tiktok.com/...`", parse_mode="Markdown")
        return

    url = context.args[0].strip()
    status_message = await update.message.reply_text("⏳ خەریکە ڤیدیۆی تیکتۆک ئامادە دەکەم...")

    try:
        api_url = f"https://tikwm.com/api/?url={url}"
        res = requests.get(api_url, timeout=20).json()
        
        video_url = None
        if "data" in res and "play" in res["data"]:
            video_url = res["data"]["play"]

        if video_url:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id,
                text="📤 ڤیدیۆکە ئامادە بوو، ئێستا دەنێرم..."
            )
            await update.message.reply_video(video=video_url, supports_streaming=True)
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_message.message_id)
        else:
            await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_message.message_id, text="⚠️ ناتوانم ئەم لینکەی تیکتۆک بخوێنمەوە.")
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_message.message_id, text="⚠️ هەڵەیەک ڕووی دا.")

async def instagram_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ تکایە لینکەکە دوای فەرمانەکە بنووسە.\nنموونە:\n`/instagram https://www.instagram.com/reel/...`", parse_mode="Markdown")
        return

    url = context.args[0].strip()
    status_message = await update.message.reply_text("⏳ خەریکە ڤیدیۆی اینستاگرام ئامادە دەکەم...")

    try:
        api_url = f"https://apis.davidcyriltech.my.id/instagram?url={url}"
        res = requests.get(api_url, timeout=20).json()
        
        video_url = None
        if "download_url" in res:
            video_url = res["download_url"]
        elif "result" in res:
            video_url = res["result"]
        elif "data" in res and "url" in res["data"]:
            video_url = res["data"]["url"]

        if video_url:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id,
                text="📤 ڤیدیۆکە ئامادە بوو، ئێستا دەنێرم..."
            )
            await update.message.reply_video(video=video_url, supports_streaming=True)
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_message.message_id)
        else:
            await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_message.message_id, text="⚠️ ناتوانم ئەم لینکەی اینستاگرام بخوێنمەوە.")
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_message.message_id, text="⚠️ هەڵەیەک ڕووی دا.")

async def post_init(application):
    # ڕێکخستنی فەرمانەکان بە شێوازێکی زۆر پاک و بێ کێشە
    commands = [
        ("start", "دەستپێکردنی بۆت"),
        ("tiktok", "دابەزاندنی ڤیدیۆی تیکتۆک"),
        ("instagram", "دابەزاندنی ڤیدیۆی اینستاگرام")
    ]
    await application.bot.set_my_commands(commands)

if __name__ == '__main__':
    if not TOKEN:
        print("❌ هەڵە: تۆکنی بۆت نەدۆزراوەتەوە!")
    else:
        app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
        
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CommandHandler("tiktok", tiktok_command))
        app.add_handler(CommandHandler("instagram", instagram_command))
        
        print("🤖 بۆت دەستی بە کارکردن کرد...")
        app.run_polling()
