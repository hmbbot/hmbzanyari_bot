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
RAPID_API_KEY = os.environ.get("RAPID_API_KEY")

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
        api_key = RAPID_API_KEY.strip() if RAPID_API_KEY else ""

        # بەکارهێنانی ئیندپۆینتێکی تری گونجاو بە شێوازی GET
        api_url = "https://tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com/vid/index"
        querystring = {"url": url}
        headers = {
            "x-rapidapi-key": api_key,
            "x-rapidapi-host": "tiktok-downloader-download-tiktok-videos-without-watermark.p.rapidapi.com"
        }

        response = requests.get(api_url, headers=headers, params=querystring, timeout=20)
        res = response.json()
        
        print(f"API RESPONSE: {res}")

        video_url = None
        audio_url = None

        if isinstance(res, dict):
            # گەڕان بەدوای لینکەکاندا لە وەڵامی ئەیپییەکەدا
            def extract_urls(data):
                nonlocal video_url, audio_url
                if isinstance(data, dict):
                    for k, v in data.items():
                        if isinstance(v, str) and v.startswith("http"):
                            if any(ext in v.lower() for ext in [".mp4", "play", "hd", "watermark"]) and not video_url:
                                video_url = v
                            elif any(ext in v.lower() for ext in [".mp3", "music", "audio"]) and not audio_url:
                                audio_url = v
                        elif isinstance(v, (dict, list)):
                            extract_urls(v)
                elif isinstance(data, list):
                    for item in data:
                        extract_urls(item)

            extract_urls(res)
            
            # ئەگەر بە شێوازی ڕاستەوخۆش لەناو کییە سەرەکییەکاندا هەبن
            if not video_url:
                video_url = res.get("video") or res.get("play") or res.get("hdplay")
            if not audio_url:
                audio_url = res.get("music") or res.get("audio")

        if not video_url:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id,
                text="⚠️ ناتوانم ئەم لینکەی تیکتۆک بخوێنمەوە."
            )
            return

        if action == "dl_video":
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id,
                text="📤 ڤیدیۆکە ئامادە بوو، ئێستا دەنێرم..."
            )
            await query.message.reply_video(video=video_url, supports_streaming=True)

        elif action == "dl_mp3":
            if audio_url:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=status_message.message_id,
                    text="📤 دەنگی MP3 ئامادە بوو، ئێستا دەنێرم..."
                )
                await query.message.reply_audio(audio=audio_url)
            else:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=status_message.message_id,
                    text="⚠️ مۆسیقا بۆ ئەم ڤیدیۆیە بە جیا نەدۆزراوەتەوە."
                )
                return

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
        app.run_polling(drop_pending_updates=True)
