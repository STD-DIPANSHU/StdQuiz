import json
import os
import logging
from telegram import Update, Poll
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
    ConversationHandler,
    PollAnswerHandler
)

logging.basicConfig(level=logging.INFO)

BOT_TOKEN = os.getenv("BOT_TOKEN")

QUIZ_FILE = "quizzes.json"
QUESTION, OPTIONS, ANSWER = range(3)

# {user_id: {quiz_id: score}}
scores = {}
# quizzes loaded from file
quizzes = {}


def save_quizzes():
    with open(QUIZ_FILE, "w") as f:
        json.dump(quizzes, f, indent=4)


def load_quizzes():
    global quizzes
    if os.path.exists(QUIZ_FILE):
        with open(QUIZ_FILE, "r") as f:
            quizzes = json.load(f)
    else:
        quizzes = {}


async def newquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Send me the question for the quiz:")
    return QUESTION


async def get_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["question"] = update.message.text
    await update.message.reply_text("Now send me options separated by `|` (example: A|B|C|D):")
    return OPTIONS


async def get_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    options = update.message.text.split("|")
    context.user_data["options"] = options
    await update.message.reply_text(f"Send me the correct option number (1-{len(options)}):")
    return ANSWER


async def get_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    correct_index = int(update.message.text) - 1
    qid = str(len(quizzes) + 1)
    quizzes[qid] = {
        "question": context.user_data["question"],
        "options": context.user_data["options"],
        "correct": correct_index
    }
    save_quizzes()
    await update.message.reply_text(f"✅ Quiz saved with ID {qid}")
    return ConversationHandler.END


async def startquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    if not quizzes:
        await update.message.reply_text("No quizzes available yet.")
        return

    for qid, quiz in quizzes.items():
        message = await context.bot.send_poll(
            chat_id,
            quiz["question"],
            quiz["options"],
            type=Poll.QUIZ,
            correct_option_id=quiz["correct"],
            is_anonymous=False
        )
        payload = {
            message.poll.id: {
                "chat_id": chat_id,
                "message_id": message.message_id,
                "quiz_id": qid
            }
        }
        context.bot_data.update(payload)


async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer
    user_id = answer.user.id
    poll_id = answer.poll_id

    if poll_id not in context.bot_data:
        return

    quiz_id = context.bot_data[poll_id]["quiz_id"]
    quiz = quizzes[quiz_id]
    correct = quiz["correct"]

    if user_id not in scores:
        scores[user_id] = {}

    if quiz_id not in scores[user_id]:
        scores[user_id][quiz_id] = 0

    if correct in answer.option_ids:
        scores[user_id][quiz_id] = 1


async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not scores:
        await update.message.reply_text("No results yet.")
        return

    text = "🏆 Leaderboard 🏆\n\n"
    for user_id, results in scores.items():
        total = sum(results.values())
        text += f"<a href='tg://user?id={user_id}'>User {user_id}</a>: {total} correct\n"

    await update.message.reply_text(text, parse_mode="HTML")


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Quiz creation cancelled.")
    return ConversationHandler.END


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
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(PollAnswerHandler(handle_poll_answer))

    app.run_polling(close_loop=False)


if __name__ == "__main__":
    main()
