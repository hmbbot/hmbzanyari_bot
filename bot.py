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
            InlineKeyboardButton("🎬 ڤیدیۆ (لینک)", callback_data="dl_video"),
            InlineKeyboardButton("🎵 MP3 (لینک)", callback_data="dl_mp3")
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
    status_message = await query.message.reply_text("⏳ خەریکە لینکەکان ئامادە دەکەم...")

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
                text="⚠️ ناتوانم ئەم لینکەی تیکتۆک بخوێنمەوە."
            )
            return

        if action == "dl_video":
            keyboard = [[InlineKeyboardButton("🔗 داگرتنی ڤیدیۆ (بێ لۆگۆ)", url=video_url)]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id,
                text=f"📌 **ناونیشان:** {title}\n\n🎬 ڤیدیۆکەت ئامادەیە بە کوالیتی بەرز:",
                reply_markup=reply_markup,
                parse_mode="Markdown"
            )

        elif action == "dl_mp3":
            if audio_url:
                keyboard = [[InlineKeyboardButton("🔗 داگرتنی دەنگی MP3", url=audio_url)]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=status_message.message_id,
                    text=f"📌 **ناونیشان:** {title}\n\n🎵 دەنگی MP3 ئامادەیە:",
                    reply_markup=reply_markup,
                    parse_mode="Markdown"
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
