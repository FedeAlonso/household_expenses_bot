import logging
import os
import sqlite3
from datetime import date
from household_expenses_db import create_db_if_not_exist, create_table_if_not_exists, insert_in_db, print_table_content
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, Update
from telegram.constants import ParseMode
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)


# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

USERS = [183302873]
DB_PATH = "_output/household_expenses.db"

USER_NOT_ALLOWED = "Sorry but your user is not allowed to use this bot"
MAIN_TYPE_BUTTON_TEXT = "ALIMENTACION"
OTHERS_BUTTON_TEXT = "OTROS"
GENERATE_REPORT_BUTTON_TEXT = "GENERAR INFORME"
CANCEL_BUTTON_TEXT = "CANCEL" 
YES_BUTTON_TEXT = "YES"
NO_BUTTON_TEXT = "NO"
RESTART_TEXT = "Si quiere recomenzar el proceso escriba /start"

NOT_ALLOWED_USER, EXPENSE_TYPE, EXPENSE_DESCRIPTION, EXPENSE_AMOUNT, FINISH_GATHERING_INFO = range(5)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Entry point
    """
    if update.message.from_user.id not in USERS:
        return NOT_ALLOWED_USER
    buttons = [[MAIN_TYPE_BUTTON_TEXT, 
                OTHERS_BUTTON_TEXT], 
                [GENERATE_REPORT_BUTTON_TEXT]]
                # [CANCEL_BUTTON_TEXT, callback_data="/cancel"]]
    message = "¿Qué gasto quieres añadir?"
    
    # using one_time_keyboard to hide the keyboard
    await update.message.reply_text(
        message, reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True)
    )
    
    return EXPENSE_TYPE


async def receive_not_allowed_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Filter allowed users
    """
    #TODO: This is not working properly. It filters the users but don't write the message
    await update.message.reply_text(USER_NOT_ALLOWED, reply_markup=ReplyKeyboardRemove())
    
    return EXPENSE_TYPE


async def receive_expense_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Get Expense type
    """
    user = update.message.from_user
    expense_type = update.message.text
    logger.info("EXPENSE_TYPE of %s: %s", user.first_name, expense_type)
    context.user_data["user"] = user.first_name
    context.user_data["expense_type"] = expense_type

    message = ""
    if update.message.text in [MAIN_TYPE_BUTTON_TEXT, OTHERS_BUTTON_TEXT]:
        message += f"Tipo de Gasto: {expense_type}\nAñade una descripción o nombre del comercio"
    elif GENERATE_REPORT_BUTTON_TEXT in update.message.text:
        pass
    else:
        await update.message.reply_text(RESTART_TEXT, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    
    await update.message.reply_text(message, reply_markup=ReplyKeyboardRemove())

    return EXPENSE_DESCRIPTION
    

async def receive_expense_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Get the Expense Description
    """
    user = update.message.from_user
    expense_description = update.message.text
    logger.info("EXPENSE_DESCRIPTION of %s: %s", user.first_name, expense_description)
    context.user_data["expense_description"] = expense_description
    await update.message.reply_text(f"Descripción del gasto: {expense_description}\nAñade la cantidad:")

    return EXPENSE_AMOUNT


async def receive_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Get the Expense Amount
    """
    user = update.message.from_user
    expense_amount = float(update.message.text)
    context.user_data["expense_amount"] = expense_amount
    logger.info("EXPENSE_AMOUNT of %s: %s", user.first_name, expense_amount)
    buttons = [[YES_BUTTON_TEXT, NO_BUTTON_TEXT]]
    message = f"""
    Tipo de gasto: {context.user_data["expense_type"]}
    Descripción del gasto: {context.user_data["expense_description"]}
    Cantidad del gasto: {expense_amount}
    Es correcto?"""
    await update.message.reply_text(
        message, reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=False)
    )

    return FINISH_GATHERING_INFO


async def receive_finish_gathering_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Finish Gatherinf INFO
    """
    user = update.message.from_user
    logger.info("FINISH GATHERING INFO of %s: %s", user.first_name, update.message.text)
    message = ""

    if update.message.text == YES_BUTTON_TEXT:
        message = "Se ha insertado la siguiente información en la base de datos:\n"
        expense_info = {
            "date": int(date.today().strftime("%Y%m%d")),
            "user": context.user_data["user"],
            "expense_type": context.user_data["expense_type"],
            "expense_description": context.user_data["expense_description"],
            "expense_amount": context.user_data["expense_amount"]
        }
        for k, v in expense_info.items():
            message += f" <b>{k}</b>:  {v}\n"        
        
        insert_in_db(expense_info, DB_PATH)
        print_table_content(DB_PATH)
    else:
        logger.info("User %s SAID NO WHEN GATHERING INFO", user.first_name)

    message += RESTART_TEXT    
    await update.message.reply_text(
        message, reply_markup=ReplyKeyboardRemove(),  parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancel and ends the conversation.
    """
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        RESTART_TEXT, reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def insert_in_sqlite3(expense_info):
    """
    Insert the expense info in the database
    """
    conn = sqlite3.connect('DN/household_expenses.db')

def main() -> None:
    """
    Run bot
    Based on: https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/conversationbot.py
    """
    # Create and configure DB:
    create_db_if_not_exist(DB_PATH) 
    create_table_if_not_exists(DB_PATH)

    # Create the Application and pass it your bot's token.
    application = Application.builder().token(os.environ['TG_BOT_HOUSEHOLD_EXPENSES_TOKEN']).build()
    
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            NOT_ALLOWED_USER:[MessageHandler(filters.TEXT & ~filters.COMMAND, receive_not_allowed_user)],
            EXPENSE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_expense_type)],
            EXPENSE_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_expense_description)],
            EXPENSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_expense_amount)],
            FINISH_GATHERING_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_finish_gathering_info)]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()



if __name__ == "__main__":
    main()