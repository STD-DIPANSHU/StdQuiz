from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
)
from telegram.ext import ContextTypes
import uuid
import random

QUIZ_CREATE_STATE = {}
QUIZ_STORE = {}   # quiz_id -> quiz data
QUIZ_PLAY_STATE = {}  # user_id -> play index


# ======================
# STEP 1: Create Quiz
# ======================
async def create_quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    QUIZ_CREATE_STATE[uid] = {
        "title": None,
        "description": None,
        "questions": [],
        "timer": None,
        "shuffle": None,
    }

    await q.message.reply_text(
        "Let's create a new quiz.\n\n"
        "First, send me the *title* of your quiz.",
        parse_mode="Markdown",
    )


# ======================
# STEP 2: Title & Desc
# ======================
async def quiz_text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    text = update.message.text

    if uid not in QUIZ_CREATE_STATE:
        return

    state = QUIZ_CREATE_STATE[uid]

    if state["title"] is None:
        state["title"] = text
        await update.message.reply_text(
            "Good. Now send me a *description* of your quiz.\n"
            "This is optional, you can /skip this step.",
            parse_mode="Markdown",
        )
        return

    if state["description"] is None:
        state["description"] = text
        await show_create_question(update)


async def skip_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in QUIZ_CREATE_STATE:
        return

    QUIZ_CREATE_STATE[uid]["description"] = ""
    await show_create_question(update)


# ======================
# STEP 3: Create Question
# ======================
async def show_create_question(update: Update):
    kb = InlineKeyboardMarkup(
        [[InlineKeyboardButton("➕ Create a question", callback_data="add_question")]]
    )

    await update.message.reply_text(
        "Good. Now create your question.\n"
        "Make sure *Quiz Mode* is ON.",
        parse_mode="Markdown",
        reply_markup=kb,
    )


async def add_question_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    poll_btn = KeyboardButton(
        text="➕ Create Quiz Question",
        request_poll={"type": "quiz"},
    )

    await q.message.reply_text(
        "📊 Tap below to create a *Quiz Poll*.",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            [[poll_btn]],
            resize_keyboard=True,
            one_time_keyboard=True,
        ),
    )


async def poll_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in QUIZ_CREATE_STATE:
        return

    QUIZ_CREATE_STATE[uid]["questions"].append(update.message.poll)

    await update.message.reply_text(
        f"✅ Question {len(QUIZ_CREATE_STATE[uid]['questions'])} added.\n\n"
        "Send next question or type /done when finished.",
        reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("➕ Create a question", callback_data="add_question")]]
        ),
    )


# ======================
# STEP 4: /done → Timer
# ======================
async def done_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("10 sec", callback_data="time_10"),
                InlineKeyboardButton("15 sec", callback_data="time_15"),
                InlineKeyboardButton("30 sec", callback_data="time_30"),
            ],
            [
                InlineKeyboardButton("1 min", callback_data="time_60"),
                InlineKeyboardButton("2 min", callback_data="time_120"),
            ],
        ]
    )

    await update.message.reply_text("⏱ Set time limit:", reply_markup=kb)


async def time_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    QUIZ_CREATE_STATE[uid]["timer"] = int(q.data.split("_")[1])

    await ask_shuffle(q.message)


# ======================
# STEP 5: Shuffle
# ======================
async def ask_shuffle(message):
    kb = InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔀 Shuffle All", callback_data="shuffle_all"),
                InlineKeyboardButton("❌ No Shuffle", callback_data="shuffle_none"),
            ]
        ]
    )

    await message.reply_text("Shuffle questions and answers?", reply_markup=kb)


async def shuffle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    uid = q.from_user.id
    state = QUIZ_CREATE_STATE[uid]
    state["shuffle"] = q.data

    quiz_id = str(uuid.uuid4())[:8]
    QUIZ_STORE[quiz_id] = state.copy()

    kb = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("▶️ Start this quiz", callback_data=f"start_quiz_{quiz_id}")],
            [InlineKeyboardButton("👥 Start quiz in group", switch_inline_query=quiz_id)],
            [InlineKeyboardButton("🔗 Share quiz", switch_inline_query=quiz_id)],
        ]
    )

    await q.message.reply_text(
        f"👍 *Quiz created!*\n\n"
        f"📝 {state['title']}\n"
        f"❓ {len(state['questions'])} questions\n"
        f"⏱ {state['timer']} sec",
        parse_mode="Markdown",
        reply_markup=kb,
    )


# ======================
# STEP 7: PLAY QUIZ
# ======================
async def start_quiz_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    quiz_id = q.data.replace("start_quiz_", "")
    quiz = QUIZ_STORE.get(quiz_id)
    uid = q.from_user.id

    if not quiz:
        await q.message.reply_text("Quiz not found.")
        return

    questions = quiz["questions"][:]
    if quiz["shuffle"] == "shuffle_all":
        random.shuffle(questions)

    QUIZ_PLAY_STATE[uid] = {
        "quiz_id": quiz_id,
        "index": 0,
        "questions": questions,
    }

    await send_next_question(q.message.chat_id, context, uid)


async def send_next_question(chat_id, context, uid):
    play = QUIZ_PLAY_STATE.get(uid)
    if not play:
        return

    if play["index"] >= len(play["questions"]):
        await context.bot.send_message(chat_id, "🎉 Quiz finished!")
        return

    poll = play["questions"][play["index"]]
    play["index"] += 1

    await context.bot.send_poll(
        chat_id=chat_id,
        question=poll.question,
        options=poll.options,
        type="quiz",
        correct_option_id=poll.correct_option_id,
        is_anonymous=True,
        open_period=QUIZ_STORE[play["quiz_id"]]["timer"],
    )
