import logging
import os
import json
from telegram import Update, Poll
from telegram.ext import (
    Application, CommandHandler, PollAnswerHandler, ContextTypes
)

BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found! Please set it in Heroku Config Vars.")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

QUIZZES = []
ACTIVE_QUIZ = {}
SCORES = {}

# Load quiz file
def load_quizzes():
    global QUIZZES
    with open("quizzes.json", "r") as f:
        QUIZZES = json.load(f)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎉 Quiz Bot Ready!\nUse /startquiz to begin in a group.")


async def startquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not QUIZZES:
        await update.message.reply_text("⚠️ No quiz found! Please upload quizzes.json")
        return

    chat_id = update.effective_chat.id
    SCORES.clear()
    ACTIVE_QUIZ[chat_id] = {"index": 0, "poll_ids": {}}

    await update.message.reply_text("🚀 Quiz starting now!")
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

    # Track poll → question index
    ACTIVE_QUIZ[chat_id]["poll_ids"][poll_msg.poll.id] = index
    ACTIVE_QUIZ[chat_id]["index"] += 1


async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    answer = update.poll_answer
    user_id = answer.user.id
    chat_id = None

    # Find which quiz this poll belongs to
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

    # अगर सारे participants answer दे चुके तो अगला सवाल भेजो (simplified logic)
    if ACTIVE_QUIZ[chat_id]["index"] < len(QUIZZES):
        await send_next_question(await context.bot.get_chat(chat_id), context)
    else:
        await end_quiz(await context.bot.get_chat(chat_id), context)


async def end_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    if not SCORES:
        await update.message.reply_text("😅 No one answered any question!")
        return

    leaderboard = sorted(SCORES.items(), key=lambda x: x[1], reverse=True)
    text = "🏆 Quiz Finished!\n\n"
    for rank, (uid, score) in enumerate(leaderboard, start=1):
        user = await context.bot.get_chat(uid)
        text += f"{rank}. {user.first_name} → {score} points\n"

    winner = await context.bot.get_chat(leaderboard[0][0])
    text += f"\n🎉 Congrats {winner.first_name}! You are the winner!"

    await context.bot.send_message(chat_id, text)


def main():
    load_quizzes()
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("startquiz", startquiz))
    app.add_handler(PollAnswerHandler(handle_poll_answer))

    app.run_polling()


if __name__ == "__main__":
    main()
