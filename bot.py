import logging
import os
import json
from telegram import Update, Poll
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    PollAnswerHandler, ConversationHandler, ContextTypes
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found! Please set it in Heroku Config Vars.")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

QUIZ_FILE = "quizzes.json"
QUIZZES = []
ACTIVE_QUIZ = {}
SCORES = {}

# States for quiz creation
QUESTION, OPTIONS, ANSWER = range(3)


# -------------------- Storage --------------------
def load_quizzes():
    global QUIZZES
    if os.path.exists(QUIZ_FILE):
        with open(QUIZ_FILE, "r") as f:
            QUIZZES = json.load(f)
    else:
        QUIZZES = []


def save_quizzes():
    with open(QUIZ_FILE, "w") as f:
        json.dump(QUIZZES, f, indent=2)


# -------------------- User Quiz Creation --------------------
async def newquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✍️ Send me your question text:")
    return QUESTION


async def get_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["question"] = update.message.text
    await update.message.reply_text("📌 Send options separated by `|` (e.g. A|B|C|D):")
    return OPTIONS


async def get_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    opts = update.message.text.split("|")
    if len(opts) < 2:
        await update.message.reply_text("❌ Please provide at least 2 options.")
        return OPTIONS

    context.user_data["options"] = opts
    await update.message.reply_text("✅ Which option number is correct? (1,2,3,...)")
    return ANSWER


async def get_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        ans_index = int(update.message.text) - 1
    except ValueError:
        await update.message.reply_text("❌ Please enter a valid number.")
        return ANSWER

    q = {
        "question": context.user_data["question"],
        "options": context.user_data["options"],
        "answer": ans_index,
    }
    QUIZZES.append(q)
    save_quizzes()

    await update.message.reply_text("✅ Quiz saved! Use /newquiz to add another.")
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🚫 Quiz creation cancelled.")
    return ConversationHandler.END


# -------------------- Group Quiz --------------------
async def startquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not QUIZZES:
        await update.message.reply_text("⚠️ No quizzes available yet!")
        return

    chat_id = update.effective_chat.id
    SCORES.clear()
    ACTIVE_QUIZ[chat_id] = {"index": 0, "poll_ids": {}}

    await update.message.reply_text("🚀 Starting group quiz now!")
    await send_next_question(update, context)


async def send_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    index = ACTIVE_QUIZ[chat_id]["index"]

    if index >= len(QUIZZES):
        await end_quiz(update, context)
        return

    q = QUIZZES[index]
    poll_msg = await update.effective_chat.send_poll(
        question=q["question"],
        options=q["options"],
        type=Poll.QUIZ,
        correct_option_id=q["answer"],
        is_anonymous=False
    )

    ACTIVE_QUIZ[chat_id]["poll_ids"][poll_msg.poll.id] = index
    ACTIVE_QUIZ[chat_id]["index"] += 1


async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer
    user_id = answer.user.id
    chat_id = None

    for cid, data in ACTIVE_QUIZ.items():
        if answer.poll_id in data["poll_ids"]:
            chat_id = cid
            q_index = data["poll_ids"][answer.poll_id]
            break

    if chat_id is None:
        return

    q = QUIZZES[q_index]
    if answer.option_ids and answer.option_ids[0] == q["answer"]:
        SCORES[user_id] = SCORES.get(user_id, 0) + 1

    if ACTIVE_QUIZ[chat_id]["index"] < len(QUIZZES):
        await send_next_question(await context.bot.get_chat(chat_id), context)
    else:
        await end_quiz(await context.bot.get_chat(chat_id), context)


async def end_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not SCORES:
        await context.bot.send_message(chat_id, "😅 Nobody answered correctly!")
        return

    leaderboard = sorted(SCORES.items(), key=lambda x: x[1], reverse=True)
    text = "🏆 Quiz Finished!\n\n"
    for rank, (uid, score) in enumerate(leaderboard, start=1):
        user = await context.bot.get_chat(uid)
        text += f"{rank}. {user.first_name} → {score} points\n"

    winner = await context.bot.get_chat(leaderboard[0][0])
    text += f"\n🎉 Congrats {winner.first_name}! You are the winner!"

    await context.bot.send_message(chat_id, text)


# -------------------- Main --------------------
def main():
    load_quizzes()
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CommandHandler("newquiz", newquiz)],
        states={
            QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_question)],
            OPTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_options)],
            ANSWER: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_answer)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(conv)
    app.add_handler(CommandHandler("startquiz", startquiz))
    app.add_handler(PollAnswerHandler(handle_poll_answer))

    app.run_polling()


if __name__ == "__main__":
    main()
