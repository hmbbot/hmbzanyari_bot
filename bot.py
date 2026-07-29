import logging
import os
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

TOKEN = os.environ.get("TOKEN")

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 سڵاو! بۆ دابەزاندنی ڤیدیۆ یان وێنەکانی تیکتۆک، تەنها لینکەکەی بنێرە:",
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
                
                # ناردنی هەموو وێنەکان پێکەوە (تا 10 وێنە)
                media_group = [InputMediaPhoto(media=img_url) for img_url in images[:10]]
                await update.message.reply_media_group(media=media_group)
                
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)
                return

    except Exception as e:
        logging.error(f"Image processing error: {str(e)}")

    # ئەگەر وێنە نەبوو (واتە ڤیدیۆ بوو)، دوگمەکانی هەڵبژاردنی بۆ دەنێرین
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
        audio_url = None
        title = "تیکتۆک"

        if isinstance(res, dict) and res.get("code") == 0:
            data = res.get("data", {})
            # یەکەمجار هەوڵ دەدەین سەیری HD بکەین، ئەگەر نەبوو ئاسایی
            video_url = data.get("hdplay") or data.get("play")
            
            # بەدوای گۆرانییەکەدا دەگەڕێین (پێشەنگی دەدەین بە لینکی سەرەکی گۆرانییەکە music_info)
            music_info = data.get("music_info", {})
            audio_url = music_info.get("play") or data.get("music")
            
            title = data.get("title", "فایلی تیکتۆک")

        if not video_url and action == "dl_video":
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id,
                text="⚠️ ناتوانم ئەم لینکەی تیکتۆک بخوێنمەوە."
            )
            return

        if action == "dl_video":
            # پشکنینی قەبارەی ڤیدیۆکە پێش ناردن بۆ ناو چات
            file_size = 0
            try:
                head_res = requests.head(video_url, timeout=10)
                file_size = int(head_res.headers.get('Content-Length', 0))
            except:
                pass

            # سنووری تێلیگرام بۆ ناردنی ڤیدیۆ لە چاتدا نزیکەی 50 مێگابایتە (50 * 1024 * 1024 بايت)
            # ئەگەر قەبارەکە گەورەتر بوو، دەیبەینە دەرەوە بە دوگمە
            if file_size > 45 * 1024 * 1024:
                keyboard = [[InlineKeyboardButton("🔗 داگرتنی ڤیدیۆی قورس (HD)", url=video_url)]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=status_message.message_id,
                    text=f"📌 **ناونیشان:** {title}\n\n⚠️ **ئاگاداری:** ئەم ڤیدیۆیە قەبارەکەی زۆر گەورەیە و تێلیگرام ناتوانێت لە ناو چاتدا بڵاوی بکاتەوە. دەتوانیت لە ڕێگەی ئەم دوگمەیەی خوارەوە بە خێرایی دایبەزێنیت:",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            else:
                # ئەگەر قەبارەکەی ئاسایی بوو، ڕاستەوخۆ لەناو چات دەنێرین
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=status_message.message_id,
                    text="📤 ڤیدیۆکە دەنێرمە ناو چات..."
                )
                try:
                    await query.message.reply_video(video=video_url, supports_streaming=True)
                    await context.bot.delete_message(
                        chat_id=update.effective_chat.id,
                        message_id=status_message.message_id
                    )
                except Exception as send_err:
                    # ئەگەر لە کاتی ناردنیشدا هەڵەیەک ڕووی دا، لینکە دەرەکییەکەی پێشکەش دەکەین
                    keyboard = [[InlineKeyboardButton("🔗 داگرتنی ڤیدیۆ (لینک)", url=video_url)]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=status_message.message_id,
                        text="⚠️ قەبارەی ڤیدیۆکە گەورەیە، تکایە لە ڕێگەی ئەم دوگمەیەوە دایبەزێنە:",
                        reply_markup=reply_markup
                    )

        elif action == "dl_mp3":
            if audio_url:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=status_message.message_id,
                    text="📤 گۆرانییە تەواوەکە دەنێرمە ناو چات..."
                )
                await query.message.reply_audio(audio=audio_url, title=title)
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=status_message.message_id
                )
            else:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=status_message.message_id,
                    text="⚠️ مۆسیقا بۆ ئەم ڤیدیۆیە بە جیا نەدۆزراوەتەوە."
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
