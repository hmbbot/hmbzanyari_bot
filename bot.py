import logging
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters
import yt_dlp

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.environ.get("TOKEN")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 سڵاو! بۆ دابەزاندنی ڤیدیۆ، وێنەکان (Slideshow) و گۆرانییە تەواوەکانی تیکتۆک، تەنها لینکەکەی بنێرە:",
        parse_mode="Markdown"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if "tiktok.com" not in url and "vt.tiktok.com" not in url:
        await update.message.reply_text("⚠️ تکایە لینکێکی ڕاستەقینەی تیکتۆک بنێرە.")
        return

    context.user_data['tiktok_url'] = url
    status_msg = await update.message.reply_text("⏳ خەریکە زانیاری لینکەکە دەهێنم...")

    try:
        api_url = "https://www.tikwm.com/api/"
        querystring = {"url": url, "hd": "1"}
        response = requests.get(api_url, params=querystring, timeout=20)
        res = response.json()
        
        if isinstance(res, dict) and res.get("code") == 0:
            data = res.get("data", {})
            images = data.get("images")
            
            # ئەگەر پۆستەکە کۆمەڵێک وێنە بوو (Slideshow)
            if images and isinstance(images, list) and len(images) > 0:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=status_msg.message_id,
                    text="📸 وێنەکان دۆزرانەوە، خەریکە دەیاننێرمە ناو چات..."
                )
                media_group = [InputMediaPhoto(media=img_url) for img_url in images[:10]]
                await update.message.reply_media_group(media=media_group)
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)
                return

            # چاککردن و پاککردنەوەی ناوی مۆسیقاکە بۆ ئەوەی لە یوتیوب بە جوانی بگەڕێت
            music_info = data.get("music_info", {})
            music_title = music_info.get("title") or ""
            video_title = data.get("title") or "TikTok Audio"
            
            if len(music_title) > 30 or "http" in music_title or not music_title:
                music_query = video_title
            else:
                music_query = f"{music_title} - {music_info.get('author', '')}"
                
            context.user_data['music_query'] = music_query

    except Exception as e:
        logging.error(f"Error fetching info: {str(e)}")
        context.user_data['music_query'] = "TikTok Audio"

    # دوگمەکانی هەڵبژاردن بۆ ڤیدیۆ یان گۆرانییە تەواوەکە
    keyboard = [
        [
            InlineKeyboardButton("🎬 ڤیدیۆ", callback_data="dl_video"),
            InlineKeyboardButton("🎵 MP3 (گۆرانی تەواو)", callback_data="dl_mp3")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=status_msg.message_id,
        text="✨ لینکەکە وەرگیرا!\nتکایە بە ڕەزامەندی خۆت یەکێک لەم بژاردانە هەڵبژێرە:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    url = context.user_data.get('tiktok_url')
    music_query = context.user_data.get('music_query', 'TikTok Audio')
    
    if not url:
        await query.message.reply_text("⚠️ کێشەیەک ڕووی دا. سکاڵایە دووبارە لینکەکە بنێرەوە.")
        return

    action = query.data
    status_message = await query.message.reply_text("⏳ خەریکە زانیارییەکان دەهێنم...")

    try:
        api_url = "https://www.tikwm.com/api/"
        querystring = {"url": url, "hd": "1"}

        response = requests.get(api_url, params=querystring, timeout=20)
        res = response.json()

        video_url = None
        title = "فایلی تیکتۆک"

        if isinstance(res, dict) and res.get("code") == 0:
            data = res.get("data", {})
            video_url = data.get("hdplay") or data.get("play")
            title = data.get("title", "فایلی تیکتۆک")

        if action == "dl_video":
            if not video_url:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=status_message.message_id,
                    text="⚠️ ناتوانم ئەم لینکەی تیکتۆک بخوێنمەوە."
                )
                return

            file_size = 0
            try:
                head_res = requests.head(video_url, timeout=10)
                file_size = int(head_res.headers.get('Content-Length', 0))
            except:
                pass

            if file_size > 45 * 1024 * 1024:
                keyboard = [[InlineKeyboardButton("🔗 داگرتنی ڤیدیۆی قورس (HD)", url=video_url)]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=status_message.message_id,
                    text=f"📌 **ناونیشان:** {title}\n\n⚠️ **ئاگاداری:** ئەم ڤیدیۆیە قەبارەکەی زۆر گەورەیە و تێلیگرام ناتوانێت لە ناو چاتدا بڵاوی بکاتەوە. دەتوانیت لە ڕێگەی ئەم دوگمەیەی خوارەوە دایبەزێنیت:",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            else:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=status_message.message_id,
                    text="📤 ڤیدیۆکە دەنێرمە ناو چات..."
                )
                try:
                    await query.message.reply_video(video=video_url, supports_streaming=True)
                    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_message.message_id)
                except:
                    keyboard = [[InlineKeyboardButton("🔗 داگرتنی ڤیدیۆ (لینک)", url=video_url)]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=status_message.message_id,
                        text="⚠️ قەبارەی ڤیدیۆکە گەورەیە، تکایە لە ڕێگەی ئەم دوگمەیەوە دایبەزێنە:",
                        reply_markup=reply_markup
                    )

        elif action == "dl_mp3":
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id,
                text="🔍 خەریکە بە دوای گۆرانییە تەواوەکەدا دەگەڕێم..."
            )
            
            audio_filename = f"audio_{update.effective_chat.id}.mp3"
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': audio_filename.replace('.mp3', ''),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'default_search': 'ytsearch1',
                'quiet': True,
            }

            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([f"ytsearch1:{music_query}"])
                
                actual_file = None
                for ext in ['.mp3', '.m4a', '.webm']:
                    potential_file = audio_filename.replace('.mp3', ext)
                    if os.path.exists(potential_file):
                        if ext != '.mp3':
                            os.rename(potential_file, audio_filename)
                        actual_file = audio_filename
                        break
                
                if actual_file and os.path.exists(actual_file):
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=status_message.message_id,
                        text="📤 گۆرانییە تەواوەکە دەنێرمە ناو چات..."
                    )
                    with open(actual_file, 'rb') as audio_file:
                        await query.message.reply_audio(audio=audio_file, title=music_query)
                    
                    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_message.message_id)
                    os.remove(actual_file)
                else:
                    raise Exception("File not found")

            except Exception as audio_err:
                logging.error(f"Audio download error: {str(audio_err)}")
                music_url = res.get("data", {}).get("music")
                if music_url:
                    await query.message.reply_audio(audio=music_url, title=title)
                    await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_message.message_id)
                else:
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=status_message.message_id,
                        text="⚠️ ناتوانم گۆرانییە تەواوەکە بدۆزمەوە."
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
