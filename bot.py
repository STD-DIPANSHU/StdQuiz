import json
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# ----------------- LOGGING CLEAN -----------------
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("telegram").setLevel(logging.WARNING)
logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s",
    level=logging.WARNING
)

# ----------------- CONFIG -----------------
BOT_TOKEN = "YOUR_BOT_TOKEN"   # <-- yaha apna real token daalna
QUIZ_FILE = "quizzes.json"

# ----------------- DATA -----------------
current_quiz = {}  # group_id -> quiz state
user_scores = {}   # group_id -> {user_id: score}


# ----------------- SAVE & LOAD QUIZZES -----------------
def load_quizzes():
    try:
        with open(QUIZ_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return []


def save_quizzes(quizzes):
    with open(QUIZ_FILE, "w") as f:
        json.dump(quizzes, f, indent=4)


# ----------------- COMMANDS -----------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome!\n\n"
        "Commands:\n"
        "/addquiz - Add a quiz\n"
        "/listquiz - Show all quizzes\n"
        "/startquiz - Start quiz in group"
    )


async def add_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.replace("/addquiz", "").strip()
    # Format: Question | Option1 | Option2 | Option3 | CorrectIndex
    try:
        q, o1, o2, o3, idx = [x.strip() for x in text.split("|")]
        idx = int(idx)
    except Exception:
        await update.message.reply_text("❌ Format: Question | Option1 | Option2 | Option3 | CorrectIndex")
        return

    quizzes = load_quizzes()
    quizzes.append({
        "question": q,
        "options": [o1, o2, o3],
        "answer": idx
    })
    save_quizzes(quizzes)

    await update.message.reply_text("✅ Quiz added successfully!")


async def list_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quizzes = load_quizzes()
    if not quizzes:
        await update.message.reply_text("❌ No quizzes available.")
        return

    msg = "📚 Saved Quizzes:\n"
    for i, q in enumerate(quizzes, 1):
        msg += f"{i}. {q['question']}\n"
    await update.message.reply_text(msg)


async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    quizzes = load_quizzes()

    if not quizzes:
        await update.message.reply_text("❌ No quizzes available. Add with /addquiz")
        return

    current_quiz[chat_id] = {
        "quizzes": quizzes,
        "index": 0
    }
    user_scores[chat_id] = {}

    await send_question(update, context)


# ----------------- QUIZ LOGIC -----------------
async def send_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    quiz_state = current_quiz.get(chat_id)

    if not quiz_state:
        return

    idx = quiz_state["index"]
    quizzes = quiz_state["quizzes"]

    if idx >= len(quizzes):
        await show_results(update, context)
        return

    q = quizzes[idx]
    buttons = [
        [InlineKeyboardButton(opt, callback_data=str(i+1))] for i, opt in enumerate(q["options"])
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"❓ {q['question']}",
        reply_markup=reply_markup
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    chat_id = query.message.chat_id
    user_id = query.from_user.id
    user_name = query.from_user.first_name

    quiz_state = current_quiz.get(chat_id)
    if not quiz_state:
        return

    idx = quiz_state["index"]
    q = quiz_state["quizzes"][idx]
    answer = int(query.data)

    if user_id not in user_scores[chat_id]:
        user_scores[chat_id][user_id] = {"name": user_name, "score": 0}

    if answer == q["answer"]:
        user_scores[chat_id][user_id]["score"] += 1
        await query.edit_message_text(f"✅ Correct, {user_name}!")
    else:
        await query.edit_message_text(f"❌ Wrong, {user_name}!")

    # Next Question
    current_quiz[chat_id]["index"] += 1
    await send_question(update, context)


async def show_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    scores = user_scores.get(chat_id, {})

    if not scores:
        await context.bot.send_message(chat_id, "📊 No one participated.")
        return

    msg = "🏆 Quiz Finished!\n\n"
    for user_id, data in scores.items():
        msg += f"{data['name']}: {data['score']} correct answers\n"

    await context.bot.send_message(chat_id, msg)


# ----------------- MAIN -----------------
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addquiz", add_quiz))
    app.add_handler(CommandHandler("listquiz", list_quiz))
    app.add_handler(CommandHandler("startquiz", start_quiz))
    app.add_handler(CallbackQueryHandler(button_handler))

    app.run_polling()


if __name__ == "__main__":
    main()
