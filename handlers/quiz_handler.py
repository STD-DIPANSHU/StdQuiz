from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import db_manager

# User ka active quiz store karne ke liye
active_quizzes = {}

async def new_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /newquiz <title>")
        return
    title = " ".join(context.args)
    quiz_id = db_manager.create_quiz(update.effective_user.id, title)
    active_quizzes[update.effective_user.id] = quiz_id
    await update.message.reply_text(f"✅ Quiz created with ID: {quiz_id}\nNow add questions using /addq")

async def add_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in active_quizzes:
        await update.message.reply_text("⚠️ First create a quiz with /newquiz")
        return
    
    try:
        data = " ".join(context.args).split("|")
        question = data[0].strip()
        options = [opt.strip() for opt in data[1:4]]
        correct_index = int(data[4]) - 1
        db_manager.add_question(active_quizzes[user_id], question, options, correct_index)
        await update.message.reply_text("✅ Question added successfully!")
    except Exception as e:
        await update.message.reply_text("❌ Format: Question | Option1 | Option2 | Option3 | CorrectIndex")

async def start_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 1:
        await update.message.reply_text("Usage: /startquiz <quiz_id>")
        return
    
    quiz_id = context.args[0]
    quiz = db_manager.get_quiz(quiz_id)
    if not quiz:
        await update.message.reply_text("❌ Quiz not found!")
        return
    
    for q in quiz["questions"]:
        buttons = [[InlineKeyboardButton(opt, callback_data=f"{quiz_id}|{q['question']}|{i}")]
                   for i, opt in enumerate(q["options"])]
        reply_markup = InlineKeyboardMarkup(buttons)
        await update.message.reply_text(f"❓ {q['question']}", reply_markup=reply_markup)
