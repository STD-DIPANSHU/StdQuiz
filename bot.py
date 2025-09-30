import logging
import os
from telegram import Update, Poll
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters,
    ConversationHandler, ContextTypes
)

# 🔑 Bot token from Heroku Config Vars
BOT_TOKEN = os.getenv("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("❌ BOT_TOKEN not found! Please set it in Heroku Config Vars.")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Conversation states
ASK_QUESTION, ASK_OPTIONS, ASK_ANSWER = range(3)

QUIZ_DATA = {}  # user_id -> list of (question, options, answer_index)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎉 Welcome to Quiz Bot!\n\n"
        "Use /newquiz to create a quiz step by step.\n"
        "Use /done when finished."
    )


async def newquiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    QUIZ_DATA[user_id] = []
    await update.message.reply_text("✍️ Send me your quiz question:")
    return ASK_QUESTION


async def ask_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["question"] = update.message.text
    await update.message.reply_text("📌 Now send options separated by `|`\nExample: 2 | 4 | 5", parse_mode="Markdown")
    return ASK_OPTIONS


async def ask_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    options = [opt.strip() for opt in update.message.text.split("|")]
    if len(options) < 2:
        await update.message.reply_text("⚠️ At least 2 options required. Try again:")
        return ASK_OPTIONS

    context.user_data["options"] = options
    await update.message.reply_text(
        f"✅ Options saved!\nNow send correct option number (1-{len(options)}):"
    )
    return ASK_ANSWER


async def save_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        correct_index = int(update.message.text) - 1
        question = context.user_data["question"]
        options = context.user_data["options"]

        if correct_index < 0 or correct_index >= len(options):
            await update.message.reply_text("❌ Invalid number. Try again:")
            return ASK_ANSWER

        user_id = update.message.from_user.id
        QUIZ_DATA[user_id].append((question, options, correct_index))

        await update.message.reply_text(
            "✅ Question saved!\n"
            "Send another question or type /done to finish."
        )
        return ASK_QUESTION
    except Exception:
        await update.message.reply_text("❌ Please send a valid number:")
        return ASK_ANSWER


async def done(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in QUIZ_DATA or not QUIZ_DATA[user_id]:
        await update.message.reply_text("⚠️ No questions added.")
        return ConversationHandler.END

    await update.message.reply_text("🎯 Starting your quiz!")
    for q, options, ans in QUIZ_DATA[user_id]:
        await update.message.reply_poll(
            question=q,
            options=options,
            type=Poll.QUIZ,
            correct_option_id=ans,
            is_anonymous=False
        )

    del QUIZ_DATA[user_id]
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("❌ Quiz creation cancelled.")
    return ConversationHandler.END


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("newquiz", newquiz)],
        states={
            ASK_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_options)],
            ASK_OPTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_answer)],
            ASK_ANSWER: [MessageHandler(filters.TEXT & ~filters.COMMAND, save_question)],
        },
        fallbacks=[CommandHandler("done", done), CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("done", done))

    app.run_polling()


if __name__ == "__main__":
    main()
