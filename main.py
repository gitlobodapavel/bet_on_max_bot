import logging
import sqlite3
from telegram import (
    Poll,
    ParseMode,
    KeyboardButton,
    KeyboardButtonPollType,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    Updater,
    CommandHandler,
    PollAnswerHandler,
    PollHandler,
    MessageHandler,
    Filters,
    CallbackContext,
)

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)


def start(update: Update, context: CallbackContext) -> None:
    """Inform user about what this bot can do"""
    update.message.reply_text(
        'Принимаються ставки на судьбу Макса в этом семестре: \n /bet - что бы сделать ставку'
    )


def get_stat(update: Update, context: CallbackContext) -> None:
    conn = sqlite3.connect("db_sqlite3.db")  # или :memory: чтобы сохранить в RAM
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM votes ")
    rows = cursor.fetchall()
    stat_1 = 0
    stat_2 = 0
    stat_3 = 0
    for row in rows:
        if row[0] == 'Макса пойдет на допку и будет безжалосно отчислен':
            stat_2 = stat_2 + 1
        elif row[0] == 'Макс пойдет на допку, но тем не менее пройдет на второй курс':
            stat_1 = stat_1 + 1
        elif row[0] == 'Макс без проблем попадет на основную сессию ( Звучит как шутка ! )':
            stat_3 = stat_3 + 1
    print(stat_1)
    print(stat_2)
    print(stat_3)

    full = stat_1 + stat_2 + stat_3

    c1 = 0
    c2 = 0
    c3 = 0

    try:
        c1 = round(full / stat_1, 1)
        print(c1)
    except ZeroDivisionError:
        print('no votes')
    try:
        c2 = round(full / stat_2, 1)
        print(c2)
    except ZeroDivisionError:
        print('no votes')
    try:
        c3 = round(full / stat_3, 1)
        print(c3)
    except ZeroDivisionError:
        print('no votes')

    context.bot.send_message(
        update.effective_message.chat_id,
        f"За вариант №1 проголосовало " + str(stat_1) + " человек из " + str(full) + " значит коефициент - " + str(c1) + "\n"
        f"За вариант №1 проголосовало " + str(stat_2) + " человек из " + str(full) + " значит коефициент - " + str(c2) + "\n"
        f"За вариант №1 проголосовало " + str(stat_3) + " человек из " + str(full) + " значит коефициент - " + str(c3) + "\n",
        parse_mode=ParseMode.HTML,
    )



def poll(update: Update, context: CallbackContext) -> None:
    """Sends a predefined poll"""
    questions = ["Макс пойдет на допку, но тем не менее пройдет на второй курс",
                 "Макса пойдет на допку и будет безжалосно отчислен",
                 "Макс без проблем попадет на основную сессию ( Звучит как шутка ! )"]
    message = context.bot.send_poll(
        update.effective_chat.id,
        "Какова судьба макса в этом году?",
        questions,
        is_anonymous=False,
        allows_multiple_answers=False,
    )
    # Save some info about the poll the bot_data for later use in receive_poll_answer
    payload = {
        message.poll.id: {
            "questions": questions,
            "message_id": message.message_id,
            "chat_id": update.effective_chat.id,
            "answers": 0,
        }
    }
    context.bot_data.update(payload)


def receive_poll_answer(update: Update, context: CallbackContext) -> None:
    """Summarize a users poll vote"""
    answer = update.poll_answer
    poll_id = answer.poll_id
    try:
        questions = context.bot_data[poll_id]["questions"]
    # this means this poll answer update is from an old poll, we can't do our answering then
    except KeyError:
        return
    selected_options = answer.option_ids
    answer_string = ""
    for question_id in selected_options:
        if question_id != selected_options[-1]:
            answer_string += questions[question_id] + " and "
        else:
            answer_string += questions[question_id]
    conn = sqlite3.connect("db_sqlite3.db")  # или :memory: чтобы сохранить в RAM
    cursor = conn.cursor()

    user = username = update.effective_user.username

    cursor.execute("SELECT * FROM votes WHERE username = ?", (username,))
    rows = cursor.fetchall()
    if rows:
        context.bot.send_message(
            context.bot_data[poll_id]["chat_id"],
            f"Ты уже голосовал, хитрец !!!",
            parse_mode=ParseMode.HTML,
        )
        return 0

    cursor.execute("INSERT INTO votes VALUES (?, ?)", (answer_string, str(user)))
    conn.commit()

    context.bot.send_message(
        context.bot_data[poll_id]["chat_id"],
        f"{update.effective_user.mention_html()}Чтож, вы выбрали вариант: \n\n '{answer_string}' \n\n Я это запомнил, посмотрим, насколько точен ваш прогноз ! (/get_stat)",
        parse_mode=ParseMode.HTML,
    )
    cursor.execute("SELECT * FROM votes ")
    rows = cursor.fetchall()

    print(rows)

    # print(rows)

    context.bot_data[poll_id]["answers"] += 1
    # Close poll after three participants voted
    if context.bot_data[poll_id]["answers"] == 3:
        context.bot.stop_poll(
            context.bot_data[poll_id]["chat_id"], context.bot_data[poll_id]["message_id"]
        )


def main() -> None:

    # Create the Updater and pass it your bot's token.
    updater = Updater("1533382326:AAF1z4pEVZTzfxBppjX7QUAyVOwUFaNgU88")
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CommandHandler('bet', poll))
    dispatcher.add_handler(CommandHandler('get_stat', get_stat))
    dispatcher.add_handler(PollAnswerHandler(receive_poll_answer))

    # Start the Bot
    updater.start_polling()

    # Run the bot until the user presses Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT
    updater.idle()


if __name__ == '__main__':
    conn = sqlite3.connect("db_sqlite3.db")  # или :memory: чтобы сохранить в RAM
    cursor = conn.cursor()

    try:
        # Создание таблицы
        cursor.execute("""CREATE TABLE votes
                                                     (vote text, username text) """)

    except sqlite3.OperationalError:
        # table already exists
        pass
    main()