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
    keyboard = [
        [
            InlineKeyboardButton("🎵 تیکتۆک (TikTok)", callback_data="download_tiktok"),
            InlineKeyboardButton("📸 اینستاگرام (Instagram)", callback_data="download_instagram")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "👋 سڵاو! بە خێر بێیت بۆ بۆتی دابەزاندنی ڤیدیۆ.\n\n"
        "تکایە پلاتفۆرمی مەبەست هەڵبژێرە:",
        reply_markup=reply_markup
    )

async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "download_tiktok":
        context.user_data['platform'] = 'tiktok'
        await query.message.reply_text("🎵 تکایە **لینکەی تیکتۆک** بنێرە:")
    elif query.data == "download_instagram":
        context.user_data['platform'] = 'instagram'
        await query.message.reply_text("📸 تکایە **لینکەی اینستاگرام** بنێرە:")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    
    if not url.startswith("http"):
        await update.message.reply_text("⚠️ تکایە لینکێکی ڕاستەقینە بنێرە.")
        return

    platform = context.user_data.get('platform')
    
    if platform == 'tiktok' and "tiktok.com" not in url:
        await update.message.reply_text("⚠️ ئەمە لینکێکی تیکتۆک نییە. سەرەتا `/start` دابگرە و پلاتفۆرمەکە هەڵبژێرەوە.")
        return
    elif platform == 'instagram' and "instagram.com" not in url:
        await update.message.reply_text("⚠️ ئەمە لینکێکی اینستاگرام نییە. سەرەتا `/start` دابگرە و پلاتفۆرمەکە هەڵبژێرەوە.")
        return

    status_message = await update.message.reply_text("⏳ خەریکە ڤیدیۆکە ئامادە دەکەم...")

    video_url = None

    try:
        api_url = f"https://apis.davidcyriltech.my.id/download/tout?url={url}"
        response = requests.get(api_url, timeout=20).json()
        
        if "result" in response and "video" in response["result"]:
            video_url = response["result"]["video"]
        elif "data" in response and "url" in response["data"]:
            video_url = response["data"]["url"]
        elif "video" in response:
            video_url = response["video"]

        if video_url:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id,
                text="📤 ڤیدیۆکە ئامادە بوو، ئێستا دەنێرم..."
            )
            
            await update.message.reply_video(
                video=video_url,
                supports_streaming=True
            )
            
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id
            )
            
            context.user_data['platform'] = None
        else:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=status_message.message_id,
                text="⚠️ ببورە، ناتوانم ئەم لینکە بخوێنمەوە."
            )

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=status_message.message_id,
            text="⚠️ هەڵەیەک ڕووی دا لە هێنانی ڤیدیۆکە."
        )

if __name__ == '__main__':
    if not TOKEN:
        print("❌ هەڵە: تۆکنی بۆت نەدۆزراوەتەوە!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        
        app.add_handler(CommandHandler("start", start_command))
        app.add_handler(CallbackQueryHandler(button_click))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        
        print("🤖 بۆت دەستی بە کارکردن کرد...")
        app.run_polling()
