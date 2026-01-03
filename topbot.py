from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
import os

from handlers.create_quiz import (
    create_quiz_callback,
    quiz_text_handler,
    skip_description,
    add_question_callback,
    poll_handler,
    done_command,
    time_callback,
    shuffle_callback,
    start_quiz_dm,
)

BOT_TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from telegram import InlineKeyboardMarkup, InlineKeyboardButton

    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("➕ Create New Quiz", callback_data="create_quiz")]]
    )

    await update.message.reply_text(
        "This bot will help you create a quiz with a series of multiple choice questions.",
        reply_markup=kb,
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("skip", skip_description))
    app.add_handler(CommandHandler("done", done_command))

    app.add_handler(CallbackQueryHandler(create_quiz_callback, "^create_quiz$"))
    app.add_handler(CallbackQueryHandler(add_question_callback, "^add_question$"))
    app.add_handler(CallbackQueryHandler(time_callback, "^time_"))
    app.add_handler(CallbackQueryHandler(shuffle_callback, "^shuffle_"))
    app.add_handler(CallbackQueryHandler(start_quiz_dm, "^start_quiz_dm$"))

    app.add_handler(MessageHandler(filters.POLL, poll_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, quiz_text_handler))

    print("🤖 IndianQuizBot running...")
    app.run_polling()


if __name__ == "__main__":
    main()
