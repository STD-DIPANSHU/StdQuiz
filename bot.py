import logging
import os
from telegram import Update, Poll
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# 🔑 Bot token will be read from Heroku Config Vars
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found! Please set it in Heroku Config Vars.")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

QUIZ_DATA = {}  # user_id -> quiz data

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Welcome to Quiz Bot! 🎉\n\nCommands:\n"
        "/newquiz - Create a new quiz\n"
        "/done - Finish quiz\n"
        "/help - Show help"
    )

async def newquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    QUIZ_DATA[user_id] = {"questions": []}
    await update.message.reply_text(
        "Send me your quiz question in format:\n\n"
        "`Question | Option1 | Option2 | Option3 | CorrectIndex`\n\n"
        "Example:\n`What is 2+2? | 2 | 4 | 5 | 2`",
        parse_mode="Markdown"
    )

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in QUIZ_DATA:
        return
    text = update.message.text
    if "|" not in text:
        return
    try:
        q, o1, o2, o3, ans = [x.strip() for x in text.split("|")]
        ans = int(ans) - 1
        QUIZ_DATA[user_id]["questions"].append((q, [o1, o2, o3], ans))
        await update.message.reply_text("✅ Question added! Send another or type /done to finish.")
    except Exception as e:
        await update.message.reply_text(f"❌ Invalid format. Try again!\nError: {e}")

async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in QUIZ_DATA or not QUIZ_DATA[user_id]["questions"]:
        await update.message.reply_text("⚠️ You haven't added any questions.")
        return

    await update.message.reply_text("🎯 Starting your quiz!")
    for q, options, ans in QUIZ_DATA[user_id]["questions"]:
        await update.message.reply_poll(
            question=q,
            options=options,
            type=Poll.QUIZ,
            correct_option_id=ans,
            is_anonymous=False
        )

    del QUIZ_DATA[user_id]

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Use /newquiz to create quiz.\n\n"
        "Format:\n`Question | Opt1 | Opt2 | Opt3 | CorrectIndex`",
        parse_mode="Markdown"
    )

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("newquiz", newquiz))
    app.add_handler(CommandHandler("done", done))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    app.run_polling()

if __name__ == "__main__":
    main()
