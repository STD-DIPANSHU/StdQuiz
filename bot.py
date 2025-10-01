import os
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from db_manager import DBManager

# ================== LOGGING ==================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================== ENV VARS ==================
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")

# Debugging print
print("DEBUG BOT TOKEN:", BOT_TOKEN)
print("DEBUG MONGO URL:", MONGO_URL)

if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN is missing! Did you set it in Heroku?")

if not MONGO_URL:
    raise ValueError("❌ MONGO_URL is missing! Did you set it in Heroku?")

# ================== DB MANAGER ==================
db = DBManager(MONGO_URL)

# ================== COMMAND HANDLERS ==================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome! Use /createquiz <name> to make a quiz.\n"
        "Use /myquizzes to see your quizzes.\n"
        "Use /leaderboard <quiz_id> to see leaderboard."
    )

async def create_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /createquiz <quiz_name>")
        return
    quiz_name = " ".join(context.args)
    quiz_id = db.create_quiz(user_id, quiz_name)
    await update.message.reply_text(f"✅ Quiz created!\nID: {quiz_id}")

async def my_quizzes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    quizzes = db.get_user_quizzes(user_id)
    if not quizzes:
        await update.message.reply_text("❌ You have no quizzes yet.")
        return
    msg = "📚 Your Quizzes:\n"
    for q in quizzes:
        msg += f"- {q['name']} (ID: {q['_id']})\n"
    await update.message.reply_text(msg)

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("⚠️ Usage: /leaderboard <quiz_id>")
        return
    quiz_id = context.args[0]
    scores = db.get_leaderboard(quiz_id)
    if not scores:
        await update.message.reply_text("❌ No scores yet for this quiz.")
        return
    msg = f"🏆 Leaderboard for Quiz {quiz_id}\n"
    for idx, s in enumerate(scores, start=1):
        msg += f"{idx}. {s['username']} — {s['score']}\n"
    await update.message.reply_text(msg)

# ================== MAIN ==================
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("createquiz", create_quiz))
    app.add_handler(CommandHandler("myquizzes", my_quizzes))
    app.add_handler(CommandHandler("leaderboard", leaderboard))

    logger.info("🚀 Bot started successfully!")
    app.run_polling()

if __name__ == "__main__":
    main()
