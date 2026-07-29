import logging
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.environ.get("TOKEN")
RAPID_API_KEY = "fe029a8932msh71f52a8ab3b2e02p1a5a17jsn70cdfac0e61"

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 سڵاو! بۆ دابەزاندنی تیکتۆک، تەنها لینکەکەی ڤیدیۆکە بنێرە:",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if "tiktok.com" not in url and "vt.tiktok.com" not in url:
        await update.message.reply_text("⚠️ تکایە لینکێکی ڕاستەقینەی تیکتۆک بنێرە.")
        return

    context.user_data['tiktok_url'] = url

    keyboard = [
        [
            InlineKeyboardButton("🎬 ڤیدیۆ", callback_data="dl_video"),
            InlineKeyboardButton("📥 MP4", callback_data="dl_mp4"),
            InlineKeyboardButton("🎵 MP3", callback_data="dl_mp3")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "✨ لینکەکە وەرگیرا!\nتکایە بە ڕەزامەندی خۆت یەکێک لەم بژاردانە هەڵبژێرە:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = context.user_data.get('tiktok_url')
    if not url:
        await query.message.reply_text("⚠️ کێشەیەک ڕووی دا. سکاڵایە دووبارە لینکەکە بنێرەوە.")
        return

    action = query.data
    status_message = await query.message.reply_text("⏳ خەریکە فایلەکە ئامادە دەکەم...")

    try:
        api_url = "https://tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com/rich_response/index"
        querystring = {"url": url}
        headers = {
            "x-rapidapi-key": RAPID_API_KEY,
            "x-rapidapi-host": "tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com",
            "Content-Type": "application/json"
        }

        response = requests.get(api_url, headers=headers, params=querystring, timeout=20)
        res = response.json()
        
        # چاپکردنی وەڵامەکە بۆ پشکنین لە لۆگ
        print("API Response:", res)

        if not res or ("body" not in res and "data" not in res and "video" not in res and "play" not in res):
            # با دڵنیابین لەوەی وەڵامێکی دروست هاتووە
            pass

        # وەرگرتنی بەستەری ڤیدیۆ و دەنگ بەپێی فۆرماتی API
        # زۆربەی کات لەم APIـیەدا لینکەکان لەناو body یان بە شێوەی ڕاستەوخۆ دەگەڕێنەوە
        video_url = None
        audio_url = None

        if "body" in res:
            body = res["body"]
            video_url = body.get("video_url") or body.get("play") or body.get("hdplay")
            audio_url = body.get("music") or body.get("audio_url")
        elif "data" in res:
            data = res["data"]
            video_url = data.get("play") or data.get("hdplay")
            audio_url = data.get("music")
        else:
            video_url = res.get("play") or res.get("video")
            audio_url = res.get("music")

        if not video_url and not audio_url:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id,
                text="⚠️ ناتوانم ئەم لینکەی تیکتۆک بخوێنمەوە."
            )
            return

        if action in ["dl_video", "dl_mp4"]:
            file_url = video_url or audio_url
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id,
                text="📤 ڤیدیۆکە ئامادە بوو، ئێستا دەنێرم..."
            )
            await query.message.reply_video(video=file_url, supports_streaming=True)

        elif action == "dl_mp3":
            file_url = audio_url or video_url
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id,
                text="📤 دەنگی MP3 ئامادە بوو، ئێستا دەنێرم..."
            )
            await query.message.reply_audio(audio=file_url)

        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=status_message.message_id
        )

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_message.message_id,
            text="⚠️ هەڵەیەک ڕووی دا لە هێنانی فایلەکە."
        )

async def post_init(application):
    commands = [
        ("start", "دەستپێکردنی بۆت")
    ]
    await application.bot.set_my_commands(commands)

if __name__ == '__main__':
    if not TOKEN:
        print("❌ هەڵە: تۆکنی بۆت نەدۆزراوەتەوە!")
    else:
        app = ApplicationBuilder().token(TOKEN).post_init(post_init).build()
        
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        app.add_handler(CallbackQueryHandler(button_click))
        
        print("🤖 بۆت دەستی بە کارکردن کرد...")
        app.run_polling()
