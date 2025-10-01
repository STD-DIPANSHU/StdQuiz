from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler
from db_manager import get_quiz, save_score, get_leaderboard
from bson import ObjectId

active_quizzes = {}

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❌ Usage: /startquiz QUIZ_ID")
        return

    quiz_id = context.args[0]
    quiz = get_quiz(ObjectId(quiz_id))
    if not quiz:
        await update.message.reply_text("❌ Quiz not found")
        return

    group_id = update.effective_chat.id
    active_quizzes[group_id] = {"quiz": quiz, "index": 0}

    await send_question(update, context, group_id)

async def send_question(update, context, group_id):
    quiz_data = active_quizzes[group_id]
    index = quiz_data["index"]
    questions = quiz_data["quiz"]["questions"]

    if index >= len(questions):
        await show_leaderboard(update, context, group_id)
        return

    q = questions[index]
    keyboard = [[InlineKeyboardButton(opt, callback_data=f"{index}:{i}")] for i, opt in enumerate(q["options"], start=1)]
    await context.bot.send_message(
        chat_id=group_id,
        text=f"Q{index+1}: {q['q']}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def answer_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    group_id = query.message.chat_id
    quiz_data = active_quizzes.get(group_id)
    if not quiz_data:
        return

    index, user_answer = map(int, query.data.split(":"))
    correct_answer = quiz_data["quiz"]["questions"][index]["correct"]

    if user_answer == correct_answer:
        save_score(query.from_user.id, group_id, quiz_data["quiz"]["_id"], 1)
        await query.edit_message_text(f"✅ Correct! {query.from_user.first_name}")
    else:
        await query.edit_message_text(f"❌ Wrong! {query.from_user.first_name}")

    active_quizzes[group_id]["index"] += 1
    await send_question(update, context, group_id)

async def show_leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE, group_id=None):
    if not group_id:
        group_id = update.effective_chat.id

    quiz_data = active_quizzes.get(group_id)
    if not quiz_data:
        return

    scores = get_leaderboard(group_id, quiz_data["quiz"]["_id"])
    if not scores:
        await context.bot.send_message(chat_id=group_id, text="No answers given!")
        return

    leaderboard = "🏆 Leaderboard 🏆\n"
    for s in scores:
        leaderboard += f"{s['user_id']} → {s['correct']} points\n"

    await context.bot.send_message(chat_id=group_id, text=leaderboard)
    del active_quizzes[group_id]
