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

TRANSLATIONS = {
    "ckb": {
        "welcome": "👋 سڵاو! تکایە زمانەکەت هەڵبژێرە:\n👇 Please select your language:",
        "lang_set": "✅ زمانەکەت بە سەرکەوتوویی کرا بە **کوردی**.\n\n🎬 ئێستا لینکێکی تیکتۆک بنێرە بۆ دابەزاندن:",
        "send_link": "✨ لینکەکە وەرگیرا!\nتکایە بە ڕەزامەندی خۆت یەکێک لەم بژاردانە هەڵبژێرە:",
        "btn_video": "🎬 ڤیدیۆ",
        "btn_mp3": "🎵 MP3",
        "fetching": "⏳ خەریکە زانیاری لینکەکە دەهێنم...",
        "wait_video": "⏳ خەریکە زانیاری ڤیدیۆکە دەهێنم...",
        "sending_video": "📤 ڤیدیۆکە دەنێرمە ناو چات...",
        "sending_audio": "📤 دەنگی MP3 دەنێرمە ناو چات...",
        "error_link": "⚠️ تکایە لینکێکی ڕاستەقینەی تیکتۆک بنێرە.",
        "error_general": "⚠️ هەڵەیەک ڕووی دا لە هێنانی فایلەکە.",
        "error_not_found": "⚠️ ناتوانم ئەم لینکەی تیکتۆک بخوێنمەوە.",
        "audio_not_found": "⚠️ مۆسیقا بۆ ئەم ڤیدیۆیە بە جیا نەدۆزراوەتەوە.",
        "images_found": "📸 وێنەکان دۆزرانەوە، خەریکە دەیاننێرمە ناو چات..."
    },
    "ar": {
        "welcome": "👋 أهلاً بك! يرجى اختيار لغتك:\n👇 Please select your language:",
        "lang_set": "✅ تم تغيير اللغة بنجاح إلى **العربية**.\n\n🎬 الآن أرسل رابط تيك توك للتحميل:",
        "send_link": "✨ تم استلام الرابط!\nيرجى اختيار أحد الخيارات التالية:",
        "btn_video": "🎬 فيديو",
        "btn_mp3": "🎵 MP3",
        "fetching": "⏳ جاري جلب معلومات الرابط...",
        "wait_video": "⏳ جاري جلب معلومات الفيديو...",
        "sending_video": "📤 جاري إرسال الفيديو إلى المحادثة...",
        "sending_audio": "📤 جاري إرسال صوت MP3 إلى المحادثة...",
        "error_link": "⚠️ يرجى إرسال رابط تيك توك صحيح.",
        "error_general": "⚠️ حدث خطأ ما أثناء جلب الملف.",
        "error_not_found": "⚠️ عذراً، لم أتمكن من قراءة رابط تيك توك هذا.",
        "audio_not_found": "⚠️ لم يتم العثور على موسيقى منفصلة لهذا الفيديو.",
        "images_found": "📸 تم العثور على الصور، جاري إرسالها..."
    },
    "en": {
        "welcome": "👋 Hello! Please select your language:\n👇 Lütfen dilinizi seçin:",
        "lang_set": "✅ Language successfully set to **English**.\n\n🎬 Now send a TikTok link to download:",
        "send_link": "✨ Link received!\nPlease choose one of the options below:",
        "btn_video": "🎬 Video",
        "btn_mp3": "🎵 MP3",
        "fetching": "⏳ Fetching link info...",
        "wait_video": "⏳ Fetching video info...",
        "sending_video": "📤 Sending video to chat...",
        "sending_audio": "📤 Sending MP3 audio to chat...",
        "error_link": "⚠️ Please send a valid TikTok link.",
        "error_general": "⚠️ An error occurred while fetching the file.",
        "error_not_found": "⚠️ Could not read this TikTok link.",
        "audio_not_found": "⚠️ Separate music not found for this video.",
        "images_found": "📸 Images found, sending to chat..."
    },
    "tr": {
        "welcome": "👋 Merhaba! Lütfen dilinizi seçin:\n👇 Please select your language:",
        "lang_set": "✅ Dil başarıyla **Türkçe** olarak ayarlandı.\n\n🎬 Şimdi indirmek için bir TikTok bağlantısı gönderin:",
        "send_link": "✨ Bağlantı alındı!\nLütfen aşağıdaki seçeneklerden birini seçin:",
        "btn_video": "🎬 Video",
        "btn_mp3": "🎵 MP3",
        "fetching": "⏳ Bağlantı bilgileri alınıyor...",
        "wait_video": "⏳ Video bilgileri alınıyor...",
        "sending_video": "📤 Video sohbete gönderiliyor...",
        "sending_audio": "📤 MP3 ses sohbete gönderiliyor...",
        "error_link": "⚠️ Lütfen geçerli bir TikTok bağlantısı gönderin.",
        "error_general": "⚠️ Dosya alınırken bir hata oluştu.",
        "error_not_found": "⚠️ Bu TikTok bağlantısı okunamadı.",
        "audio_not_found": "⚠️ Bu video için ayrı bir müzik bulunamadı.",
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

    except Exception as e:
        logging.error(f"Image processing error: {str(e)}")

    keyboard = [
        [
            InlineKeyboardButton(get_text(context, "btn_video"), callback_data="dl_video"),
            InlineKeyboardButton(get_text(context, "btn_mp3"), callback_data="dl_mp3")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_msg.message_id,
            text=get_text(context, "send_link"),
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )
    except Exception:
        await update.message.reply_text(
            get_text(context, "send_link"),
            reply_markup=reply_markup,
            parse_mode="Markdown"
        )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data_callback = query.data

    if data_callback.startswith("lang_"):
        lang_code = data_callback.split("_")[1]
        context.user_data['language'] = lang_code
        try:
            await query.message.edit_text(get_text(context, "lang_set"), parse_mode="Markdown")
        except Exception:
            await query.message.reply_text(get_text(context, "lang_set"), parse_mode="Markdown")
        return

    url = context.user_data.get('tiktok_url')
    
    # ئەگەر لینکەکە لە یادگەی کاتیدا نەبوو، هەوڵ بدە لە ناونیشانی نامەکەی پێشوو وەریبگرە ئەگەر هه‌بێت
    if not url and query.message.reply_to_message and query.message.reply_to_message.text:
        possible_url = query.message.reply_to_message.text.strip()
        if "tiktok.com" in possible_url or "vt.tiktok.com" in possible_url:
            url = possible_url

    if not url:
        await query.message.reply_text("⚠️ بەڕێزم، تکایە جارێکی تر لینکەکە بنێرەوە چونکە یادگە نوێ بووەوە.")
        return

    action = data_callback
    status_message = await query.message.reply_text(get_text(context, "wait_video"))

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
            video_url = data.get("hdplay") or data.get("play")
            audio_url = data.get("music")
            title = data.get("title", "فایلی تیکتۆک")

        if not video_url:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id,
                text=get_text(context, "error_not_found")
            )
            return

        if action == "dl_video":
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
                    text=f"📌 **ناونیشان:** {title}\n\n⚠️ **ئاگاداری:** ئەم ڤیدیۆیە قەبارەکەی زۆر گەورەیە و تێلیگرام ناتوانێت لە ناو چاتدا بڵاوی بکاتەوە. دەتوانیت لە ڕێگەی ئەم دوگمەیەی خوارەوە بە خێرایی دایبەزێنیت:",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
                )
            else:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=status_message.message_id,
                    text=get_text(context, "sending_video")
                )
                try:
                    await query.message.reply_video(video=video_url, supports_streaming=True)
                    await context.bot.delete_message(
                        chat_id=update.effective_chat.id,
                        message_id=status_message.message_id
                    )
                except Exception as send_err:
                    keyboard = [[InlineKeyboardButton("🔗 داگرتنی ڤیدیۆ (لینک)", url=video_url)]]
                    reply_markup = InlineKeyboardMarkup(keyboard)
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=status_message.message_id,
                        text=get_text(context, "error_general"),
                        reply_markup=reply_markup
                    )

        elif action == "dl_mp3":
            if audio_url:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=status_message.message_id,
                    text=get_text(context, "sending_audio")
                )
                await query.message.reply_audio(audio=audio_url)
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=status_message.message_id
                )
            else:
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=status_message.message_id,
                    text=get_text(context, "audio_not_found")
                )

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id,
                text=get_text(context, "error_general")
            )
        except:
            pass

async def post_init(application):
    commands = [
        ("start", "دەستپێکردنی بۆت / Start")
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
