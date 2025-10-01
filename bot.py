from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from handlers.quiz_handler import new_quiz, add_question, save_quiz_cmd
from handlers.score_handler import start_quiz, answer_handler

import os

TOKEN = os.getenv("BOT_TOKEN")

app = ApplicationBuilder().token(TOKEN).build()

# Quiz creation
app.add_handler(CommandHandler("newquiz", new_quiz))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, add_question))
app.add_handler(CommandHandler("savequiz", save_quiz_cmd))

# Quiz playing
app.add_handler(CommandHandler("startquiz", start_quiz))
app.add_handler(CallbackQueryHandler(answer_handler))

print("✅ Bot started")
app.run_polling()
