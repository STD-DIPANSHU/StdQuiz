import os
from telegram.ext import Application, CommandHandler, CallbackQueryHandler
from handlers.quiz_handler import new_quiz, add_question, start_quiz

TOKEN = os.getenv("BOT_TOKEN")  # Heroku me BOT_TOKEN set karna hoga

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("newquiz", new_quiz))
    app.add_handler(CommandHandler("addq", add_question))
    app.add_handler(CommandHandler("startquiz", start_quiz))

    print("🤖 Bot running...")
    app.run_polling()

if __name__ == "__main__":
    main()
