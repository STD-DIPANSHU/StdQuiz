import os
import json
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters

QUIZ_FILE = "quizzes.json"

# BOT TOKEN from Heroku Config Vars
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not set in Heroku Config Vars")

# Load quizzes
def load_quizzes():
    if not os.path.exists(QUIZ_FILE):
        return []
    with open(QUIZ_FILE, "r") as f:
        return json.load(f)

# Save quizzes
def save_quizzes(quizzes):
    with open(QUIZ_FILE, "w") as f:
        json.dump(quizzes, f, indent=4)

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ Quiz Bot is running!\n\n/addquiz - add a new quiz\n/startquiz - start quiz in group")

# Add quiz
async def addquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.split("|")
        if len(text) != 5:
            await update.message.reply_text("❌ Format: Question | Option1 | Option2 | Option3 | CorrectIndex")
            return
        _, q, o1, o2, o3, correct = text[0], text[1], text[2], text[3], text[4], None
        correct = int(text[4].strip())
        quiz = {
            "question": q.strip(),
            "options": [o1.strip(), o2.strip(), o3.strip()],
            "answer": correct
        }
        quizzes = load_quizzes()
        quizzes.append(quiz)
        save_quizzes(quizzes)
        await update.message.reply_text("✅ Quiz added successfully!")
    except Exception as e:
        await update.message.reply_text(f"⚠ Error: {e}")

# Start quiz in group
user_scores = {}

async def startquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quizzes = load_quizzes()
    if not quizzes:
        await update.message.reply_text("❌ No quizzes found. Use /addquiz first.")
        return

    user_scores.clear()
    for i, quiz in enumerate(quizzes, start=1):
        question = quiz["question"]
        opts = quiz["options"]
        await update.message.reply_text(
            f"📌 Q{i}: {question}\n1️⃣ {opts[0]}\n2️⃣ {opts[1]}\n3️⃣ {opts[2]}\n\nReply with the option number!"
        )
        context.chat_data["current_quiz"] = i - 1

# Handle answers
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    text = update.message.text.strip()
    if not text.isdigit():
        return
    choice = int(text)

    quizzes = load_quizzes()
    current = context.chat_data.get("current_quiz")
    if current is None or current >= len(quizzes):
        return

    correct = quizzes[current]["answer"]
    if user.id not in user_scores:
        user_scores[user.id] = {"name": user.first_name, "score": 0}

    if choice == correct:
        user_scores[user.id]["score"] += 1
        await update.message.reply_text(f"✅ Correct, {user.first_name}!")
    else:
        await update.message.reply_text(f"❌ Wrong, {user.first_name}!")

    # Last quiz? Show results
    if current == len(quizzes) - 1:
        results = "🏆 Final Results:\n"
        for uid, data in user_scores.items():
            results += f"{data['name']}: {data['score']} correct\n"
        await update.message.reply_text(results)
    else:
        context.chat_data["current_quiz"] = current + 1
        next_q = quizzes[current + 1]
        await update.message.reply_text(
            f"📌 Q{current+2}: {next_q['question']}\n1️⃣ {next_q['options'][0]}\n2️⃣ {next_q['options'][1]}\n3️⃣ {next_q['options'][2]}\n\nReply with the option number!"
        )

# Main
def main():
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("addquiz", addquiz))
    app.add_handler(CommandHandler("startquiz", startquiz))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_answer))

    print("🚀 Bot started...")
    app.run_polling()

if __name__ == "__main__":
    main()
