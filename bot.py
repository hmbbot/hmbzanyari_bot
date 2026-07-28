import json
import logging
import os
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# خوێندنی تۆکن لە Environment Variables ی سێرڤەرەکە (ڕایلی)
TOKEN = os.environ.get("TOKEN")
DATA_FILE = "database.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except:
                return {}
    return {}

def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

user_data_db = load_data()
user_states = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_states[user_id] = {"step": "waiting_for_name"}
    await update.message.reply_text(
        "👋 بە خیر بێیت بۆ بۆتی زانیاری خێزانی.\n"
        "تکایە **ناوی تەواوی (سیانی)** خۆت بنووسە:"
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    
    if user_id not in user_states:
        if text in user_data_db:
            p = user_data_db[text]
            children_str = "\n".join([f"   - {c['name']} (مۆلید: {c['year']})" for c in p['children']]) if p['children'] else "هیچ منداڵێک تۆمار نەکراوە"
            
            response = (
                f"📋 **فۆرمی زانیاری کەسی و خێزانی**\n"
                f"------------------------------------\n"
                f"👤 **ناوی تەواو:** {p['full_name']}\n"
                f"⚧ **ڕەگەز (جنس):** {p['gender']}\n"
                f"💍 **ناوی هاوسەر:** {p['spouse']}\n"
                f"👶 **ژمارەی منداڵەکان:** {len(p['children'])}\n"
                f"👨‍👧 **ناوی منداڵەکان و مۆلیدیان:**\n{children_str}\n"
                f"------------------------------------\n"
                f"💡 بۆ تۆمارکردن یان نوێکردنەوەی ناوێکی نوێ، `/start` بنووسە."
            )
            await update.message.reply_text(response, parse_mode="Markdown")
            return
        else:
            user_states[user_id] = {"step": "waiting_for_name"}

    state = user_states[user_id].get("step")

    if state == "waiting_for_name":
        user_states[user_id]["full_name"] = text
        user_states[user_id]["step"] = "waiting_for_gender"
        await update.message.reply_text("⚧ ڕەگەزی خۆت بنووسە (بۆ نموونە: نێر / مێ):")

    elif state == "waiting_for_gender":
        user_states[user_id]["gender"] = text
        user_states[user_id]["step"] = "waiting_for_spouse"
        await update.message.reply_text("💍 ناوی هاوسەری خۆت بنووسە:")

    elif state == "waiting_for_spouse":
        user_states[user_id]["spouse"] = text
        user_states[user_id]["step"] = "waiting_for_children_count"
        await update.message.reply_text("👶 چەند منداڵت هەەیە؟ (ژمارەیەک بنووسە، بۆ نموونە: 2):")

    elif state == "waiting_for_children_count":
        try:
            count = int(text)
            user_states[user_id]["children_count"] = count
            user_states[user_id]["children"] = []
            if count > 0:
                user_states[user_id]["step"] = "collecting_children"
                await update.message.reply_text(
                    f"تکایە ناوی منداڵی یەکەم و ساڵی لەدایکبوونی (مۆلید) بنووسە\n"
                    f"(بۆ نموونە: ئارام - 2015):"
                )
            else:
                full_name = user_states[user_id]["full_name"]
                user_data_db[full_name] = {
                    "full_name": full_name,
                    "gender": user_states[user_id]["gender"],
                    "spouse": user_states[user_id]["spouse"],
                    "children": []
                }
                save_data(user_data_db)
                del user_states[user_id]
                await update.message.reply_text("✅ زانیارییەکانت بە سەرکەوتوویی پاشەکەوت کران! ئێستا دەتوانیت ناوی خۆت بنووسیت بۆ بینینی زانیارییەکان.")
        except ValueError:
            await update.message.reply_text("⚠️ تکایە تەنها ژمارەیەک بنووسە بۆ ژمارەی منداڵەکان:")

    elif state == "collecting_children":
        parts = text.rsplit("-", 1)
        c_name = parts[0].strip()
        c_year = parts[1].strip() if len(parts) > 1 else "دیارینەکراو"
        
        user_states[user_id]["children"].append({"name": c_name, "year": c_year})
        current_len = len(user_states[user_id]["children"])
        total_count = user_states[user_id]["children_count"]

        if current_len < total_count:
            await update.message.reply_text(f"منداڵی ژمارە {current_len + 1} بە هەمان شێوە بنووسە (ناو - مۆلید):")
        else:
            full_name = user_states[user_id]["full_name"]
            user_data_db[full_name] = {
                "full_name": full_name,
                "gender": user_states[user_id]["gender"],
                "spouse": user_states[user_id]["spouse"],
                "children": user_states[user_id]["children"]
            }
            save_data(user_data_db)
            del user_states[user_id]
            await update.message.reply_text("✅ هەموو زانیارییەکان بە سەرکەوتوویی پاشەکەوت کران! ئێستا ئەگەر ناوی خۆت بنووسیت، فۆرمەکە بە تەواوی دەردەکەوێت.")

if __name__ == '__main__':
    if not TOKEN:
        print("❌ هەڵە: تۆکن لە سێرڤەرەکەدا نەدۆزراوەتەوە!")
    else:
        app = ApplicationBuilder().token(TOKEN).build()
        app.add_handler(CommandHandler("start", start))
        app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
        
        print("🤖 بۆتەکە دەستی بە کارکردن کرد...")
        app.run_polling()
