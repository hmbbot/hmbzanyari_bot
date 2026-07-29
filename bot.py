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

# فەرهەنگی زمانەکان (Translation Dictionary)
TRANSLATIONS = {
    "ckb": {
        "welcome": "👋 سڵاو! تکایە زمانەکەت هەڵبژێرە:\n👇 Please select your language:",
        "lang_set": "✅ زمانەکەت بە سەرکەوتوویی کرا بە **کوردی**.\n\n🎬 ئێستا لینکێکی تیکتۆک بنێرە بۆ دابەزاندن:",
        "send_link": "✨ لینکەکە وەرگیرا!\nتکایە یەکێک لەم بژاردانە هەڵبژێرە:",
        "btn_video": "🎬 ڤیدیۆ",
        "btn_mp3": "🎵 MP3 (گۆرانی تەواو)",
        "fetching": "⏳ خەریکە زانیاری لینکەکە دەهێنم...",
        "wait_video": "⏳ خەریکە زانیارییەکان دەهێنم...",
        "sending_video": "📤 ڤیدیۆکە دەنێرمە ناو چات...",
        "searching_audio": "🔍 خەریکە بە دوای گۆرانییە تەواوەکەدا دەگەڕێم...",
        "sending_audio": "📤 گۆرانییە تەواوەکە دەنێرمە ناو چات...",
        "error_link": "⚠️ تکایە لینکێکی ڕاستەقینەی تیکتۆک بنێرە.",
        "error_general": "⚠️ هەڵەیەک ڕووی دا.",
        "audio_not_found": "⚠️ ناتوانم گۆرانییە تەواوەکە بدۆزمەوە.",
        "images_found": "📸 وێنەکان دۆزرانەوە، خەریکە دەیاننێرمە ناو چات..."
    },
    "ar": {
        "welcome": "👋 أهلاً بك! يرجى اختيار لغتك:\n👇 Please select your language:",
        "lang_set": "✅ تم تغيير اللغة بنجاح إلى **العربية**.\n\n🎬 الآن أرسل رابط تيك توك للتحميل:",
        "send_link": "✨ تم استلام الرابط!\nيرجى اختيار أحد الخيارات التالية:",
        "btn_video": "🎬 فيديو",
        "btn_mp3": "🎵 MP3 (الأغنية كاملة)",
        "fetching": "⏳ جاري جلب معلومات الرابط...",
        "wait_video": "⏳ جاري جلب المعلومات...",
        "sending_video": "📤 جاري إرسال الفيديو إلى المحادثة...",
        "searching_audio": "🔍 جاري البحث عن الأغنية الكاملة...",
        "sending_audio": "📤 جاري إرسال الأغنية الكاملة...",
        "error_link": "⚠️ يرجى إرسال رابط تيك توك صحيح.",
        "error_general": "⚠️ حدث خطأ ما.",
        "audio_not_found": "⚠️ عذراً، لم أتمكن من العثور على الأغنية الكاملة.",
        "images_found": "📸 تم العثور على الصور، جاري إرسالها..."
    },
    "en": {
        "welcome": "👋 Hello! Please select your language:\n👇 Lütfen dilinizi seçin:",
        "lang_set": "✅ Language successfully set to **English**.\n\n🎬 Now send a TikTok link to download:",
        "send_link": "✨ Link received!\nPlease choose one of the options below:",
        "btn_video": "🎬 Video",
        "btn_mp3": "🎵 MP3 (Full Song)",
        "fetching": "⏳ Fetching link info...",
        "wait_video": "⏳ Fetching information...",
        "sending_video": "📤 Sending video to chat...",
        "searching_audio": "⏳ Searching for the full song...",
        "sending_audio": "📤 Sending the full song...",
        "error_link": "⚠️ Please send a valid TikTok link.",
        "error_general": "⚠️ An error occurred.",
        "audio_not_found": "⚠️ Could not find the full song.",
        "images_found": "📸 Images found, sending to chat..."
    },
    "tr": {
        "welcome": "👋 Merhaba! Lütfen dilinizi seçin:\n👇 Please select your language:",
        "lang_set": "✅ Dil başarıyla **Türkçe** olarak ayarlandı.\n\n🎬 Şimdi indirmek için bir TikTok bağlantısı gönderin:",
        "send_link": "✨ Bağlantı alındı!\nLütfen aşağıdaki seçeneklerden birini seçin:",
        "btn_video": "🎬 Video",
        "btn_mp3": "🎵 MP3 (Tam Şarkı)",
        "fetching": "⏳ Bağlantı bilgileri alınıyor...",
        "wait_video": "⏳ Bilgiler alınıyor...",
        "sending_video": "📤 Video sohbete gönderiliyor...",
        "searching_audio": "🔍 Tam şarkı aranıyor...",
        "sending_audio": "📤 Tam şarkı sohbete gönderiliyor...",
        "error_link": "⚠️ Lütfen geçerli bir TikTok bağlantısı gönderin.",
        "error_general": "⚠️ Bir hata oluştu.",
        "audio_not_found": "⚠️ Tam şarkı bulunamadı.",
        "images_found": "📸 Fotoğraflar bulundu, sohbete gönderiliyor..."
    }
}

def get_text(context: ContextTypes.DEFAULT_TYPE, key: str) -> str:
    lang = context.user_data.get('language', 'ckb')
    return TRANSLATIONS.get(lang, TRANSLATIONS['ckb']).get(key, TRANSLATIONS['ckb'][key])

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("کوردی 🇮🇶", callback_data="lang_ckb"),
            InlineKeyboardButton("العربية 🇸🇦", callback_data="lang_ar")
        ],
        [
            InlineKeyboardButton("English 🇺🇸", callback_data="lang_en"),
            InlineKeyboardButton("Türkçe 🇹🇷", callback_data="lang_tr")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # ئەگەر لە رێگەی /startـەوە هات، دەتوانین بە کوردی سەرەتایی پێشوازی بکەین
    await update.message.reply_text(
        TRANSLATIONS['ckb']['welcome'],
        reply_markup=reply_markup
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if "tiktok.com" not in url and "vt.tiktok.com" not in url:
        await update.message.reply_text(get_text(context, "error_link"))
        return

    context.user_data['tiktok_url'] = url
    status_msg = await update.message.reply_text(get_text(context, "fetching"))

    try:
        api_url = "https://www.tikwm.com/api/"
        querystring = {"url": url, "hd": "1"}
        response = requests.get(api_url, params=querystring, timeout=20)
        res = response.json()
        
        if isinstance(res, dict) and res.get("code") == 0:
            data = res.get("data", {})
            images = data.get("images")
            
            if images and isinstance(images, list) and len(images) > 0:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=status_msg.message_id,
                    text=get_text(context, "images_found")
                )
                media_group = [InputMediaPhoto(media=img_url) for img_url in images[:10]]
                await update.message.reply_media_group(media=media_group)
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)
                return

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

    keyboard = [
        [
            InlineKeyboardButton(get_text(context, "btn_video"), callback_data="dl_video"),
            InlineKeyboardButton(get_text(context, "btn_mp3"), callback_data="dl_mp3")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.edit_message_text(
        chat_id=update.effective_chat.id,
        message_id=status_msg.message_id,
        text=get_text(context, "send_link"),
        reply_markup=reply_markup
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data_callback = query.data

    # پشکنینی گۆڕینی زمان
    if data_callback.startswith("lang_"):
        lang_code = data_callback.split("_")[1]
        context.user_data['language'] = lang_code
        await query.message.edit_text(get_text(context, "lang_set"), parse_mode="Markdown")
        return

    url = context.user_data.get('tiktok_url')
    music_query = context.user_data.get('music_query', 'TikTok Audio')
    
    if not url:
        await query.message.reply_text(get_text(context, "error_general"))
        return

    status_message = await query.message.reply_text(get_text(context, "wait_video"))

    try:
        api_url = "https://www.tikwm.com/api/"
        querystring = {"url": url, "hd": "1"}

        response = requests.get(api_url, params=querystring, timeout=20)
        res = response.json()

        video_url = None
        title = "TikTok"

        if isinstance(res, dict) and res.get("code") == 0:
            data = res.get("data", {})
            video_url = data.get("hdplay") or data.get("play")
            title = data.get("title", "TikTok")

        if data_callback == "dl_video":
            if not video_url:
                await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_message.message_id, text=get_text(context, "error_general"))
                return

            await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_message.message_id, text=get_text(context, "sending_video"))
            try:
                await query.message.reply_video(video=video_url, supports_streaming=True)
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_message.message_id)
            except:
                keyboard = [[InlineKeyboardButton("🔗 Download Link", url=video_url)]]
                await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_message.message_id, text=get_text(context, "error_general"), reply_markup=InlineKeyboardMarkup(keyboard))

        elif data_callback == "dl_mp3":
            await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_message.message_id, text=get_text(context, "searching_audio"))
            
            audio_filename = f"audio_{update.effective_chat.id}.mp3"
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': audio_filename.replace('.mp3', ''),
                'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}],
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
                    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_message.message_id, text=get_text(context, "sending_audio"))
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
                    await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_message.message_id, text=get_text(context, "audio_not_found"))

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        await context.bot.edit_message_text(chat_id=update.effective_chat.id, message_id=status_message.message_id, text=get_text(context, "error_general"))

async def post_init(application):
    commands = [("start", "دەستپێکردنی بۆت / Start")]
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
