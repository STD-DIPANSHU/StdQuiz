from telegram import Update
from telegram.ext import ContextTypes
from db_manager import save_quiz

user_quiz_data = {}

async def new_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_quiz_data[user_id] = {"questions": []}
    await update.message.reply_text("Send me your quiz title:")

async def add_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_quiz_data:
        await update.message.reply_text("Start with /newquiz first")
        return
    
    try:
        # Format: Question | Option1 | Option2 | Option3 | CorrectIndex
        parts = update.message.text.split("|")
        q, o1, o2, o3, correct = [p.strip() for p in parts]
        question = {
            "q": q,
            "options": [o1, o2, o3],
            "correct": int(correct)
        }
        user_quiz_data[user_id]["questions"].append(question)
        await update.message.reply_text("✅ Question added! Add more or use /savequiz")
    except:
        await update.message.reply_text("❌ Format galat hai. Use:\nQuestion | Option1 | Option2 | Option3 | CorrectIndex")

async def save_quiz_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in user_quiz_data or not user_quiz_data[user_id]["questions"]:
        await update.message.reply_text("❌ No quiz found, use /newquiz first")
        return

    title = "My Quiz"
    if context.args:
        title = " ".join(context.args)

    quiz_id = save_quiz(user_id, title, user_quiz_data[user_id]["questions"])
    await update.message.reply_text(f"✅ Quiz saved with ID: {quiz_id}")
    del user_quiz_data[user_id]
