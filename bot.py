import json
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

QUIZ_FILE = "quizzes.json"
current_quiz = {}
user_scores = {}

# ---------- QUIZ STORAGE ----------
def load_quizzes():
    try:
        with open(QUIZ_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []
    except json.JSONDecodeError:
        return []

def save_quizzes(quizzes):
    with open(QUIZ_FILE, "w") as f:
        json.dump(quizzes, f, indent=4)

# ---------- ADD QUIZ ----------
async def add_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Usage: /addquiz <question> | <answer>")
        return

    text = " ".join(context.args)
    if "|" not in text:
        await update.message.reply_text("Please separate question and answer with |")
        return

    question, answer = text.split("|", 1)
    quizzes = load_quizzes()
    quizzes.append({"question": question.strip(), "answer": answer.strip().lower()})
    save_quizzes(quizzes)

    await update.message.reply_text("✅ Quiz added successfully!")

# ---------- START QUIZ ----------
async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_quiz, user_scores
    quizzes = load_quizzes()

    if not quizzes:
        await update.message.reply_text("❌ No quizzes available. Add some using /addquiz.")
        return

    current_quiz["quizzes"] = quizzes
    current_quiz["index"] = 0
    user_scores = {}

    await update.message.reply_text("🎉 Quiz is starting now!")
    await ask_question(update, context)

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    index = current_quiz.get("index", 0)
    quizzes = current_quiz.get("quizzes", [])

    if index < len(quizzes):
        question = quizzes[index]["question"]
        await update.message.reply_text(f"❓ Q{index+1}: {question}")
    else:
        await end_quiz(update)

# ---------- HANDLE ANSWERS ----------
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global current_quiz, user_scores
    if "quizzes" not in current_quiz:
        return

    index = current_quiz.get("index", 0)
    quizzes = current_quiz.get("quizzes", [])

    if index >= len(quizzes):
        return

    correct_answer = quizzes[index]["answer"]
    user_answer = update.message.text.strip().lower()
    user_id = update.message.from_user.id
    username = update.message.from_user.first_name

    if user_answer == correct_answer:
        user_scores[user_id] = user_scores.get(user_id, {"name": username, "score": 0})
        user_scores[user_id]["score"] += 1
        await update.message.reply_text(f"✅ Correct, {username}!")
        current_quiz["index"] += 1
        await ask_question(update, context)
    else:
        await update.message.reply_text(f"❌ Wrong, {username}! Try again.")

# ---------- END QUIZ ----------
async def end_quiz(update: Update):
    global user_scores
    if not user_scores:
        await update.message.reply_text("😅 No correct answers were given.")
        return

    results = "🏆 Final Scores:\n"
    for uid, data in sorted(user_scores.items(), key=lambda x: x[1]["score"], reverse=True):
        results += f"{data['name']}: {data['score']} points\n"

    await update.message.reply_text(results)

# ---------- MAIN ----------
def main():
    import os
    TOKEN = os.getenv("BOT_TOKEN")  # Add BOT_TOKEN in Heroku Config Vars

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("addquiz", add_quiz))
    app.add_handler(CommandHandler("startquiz", start_quiz))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
