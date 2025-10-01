import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters
)
from config import BOT_TOKEN
import db_manager

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# temporary state for quiz creation
user_quiz_data = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Welcome! Use /createquiz to make a quiz or /quiz to play.")

# ---------------- CREATE QUIZ ----------------
async def create_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me your quiz in format:\n\nQuestion | Option1,Option2,Option3,Option4 | CorrectOption")
    return

async def handle_quiz_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        parts = update.message.text.split("|")
        if len(parts) != 3:
            await update.message.reply_text("❌ Wrong format. Use:\nQuestion | Option1,Option2 | CorrectOption")
            return

        question = parts[0].strip()
        options = [opt.strip() for opt in parts[1].split(",")]
        correct_answer = parts[2].strip()

        db_manager.save_quiz(update.effective_user.id, question, options, correct_answer)
        await update.message.reply_text("✅ Quiz saved successfully!")

    except Exception as e:
        logger.error(e)
        await update.message.reply_text("❌ Error saving quiz.")

# ---------------- PLAY QUIZ ----------------
async def play_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quizzes = db_manager.get_all_quizzes()
    if not quizzes:
        await update.message.reply_text("No quizzes available yet. Use /createquiz to add one.")
        return

    context.user_data["quiz_index"] = 0
    context.user_data["quizzes"] = quizzes
    await send_question(update, context)

async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = context.user_data.get("quiz_index", 0)
    quizzes = context.user_data.get("quizzes", [])

    if index >= len(quizzes):
        await update.message.reply_text("🎉 Quiz finished! Use /leaderboard to check scores.")
        return

    quiz = quizzes[index]
    question = quiz["question"]
    options = quiz["options"]

    reply_markup = ReplyKeyboardMarkup(
        [[opt] for opt in options],
        one_time_keyboard=True,
        resize_keyboard=True
    )

    context.user_data["current_quiz"] = quiz
    await update.message.reply_text(f"Q{index+1}: {question}", reply_markup=reply_markup)

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_answer = update.message.text
    quiz = context.user_data.get("current_quiz")

    if not quiz:
        return

    is_correct = user_answer.strip() == quiz["correct_answer"].strip()
    db_manager.save_response(update.effective_user.id, quiz["question"], user_answer, is_correct)

    if is_correct:
        await update.message.reply_text("✅ Correct!")
    else:
        await update.message.reply_text(f"❌ Wrong! Correct answer: {quiz['correct_answer']}")

    context.user_data["quiz_index"] += 1
    await send_question(update, context)

# ---------------- LEADERBOARD ----------------
async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    scores = db_manager.get_leaderboard()
    if not scores:
        await update.message.reply_text("No leaderboard yet.")
        return

    text = "🏆 Leaderboard 🏆\n\n"
    for idx, entry in enumerate(scores, start=1):
        text += f"{idx}. User {entry['_id']} - {entry['score']} points\n"

    await update.message.reply_text(text)

# ---------------- MAIN ----------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("createquiz", create_quiz))
    app.add_handler(CommandHandler("quiz", play_quiz))
    app.add_handler(CommandHandler("leaderboard", leaderboard))

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_quiz_creation))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))

    app.run_polling()

if __name__ == "__main__":
    main()
