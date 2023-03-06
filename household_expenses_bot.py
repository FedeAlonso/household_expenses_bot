import logging
import os
import json
from datetime import date
from utils.household_expenses_db import create_db_if_not_exist, create_table_if_not_exists, insert_in_db, print_table_content
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

CONFIG_FILE = "conf/config.json"
NOT_ALLOWED_USER, EXPENSE_TYPE, EXPENSE_DESCRIPTION, EXPENSE_AMOUNT, FINISH_GATHERING_INFO = range(5)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Entry point
    """

    # Load config:
    config = None
    with open(CONFIG_FILE) as f:
        config = json.loads(f.read())

    context.user_data["config"] = config

    # Create and configure DB:
    create_db_if_not_exist(config.get('db_path')) 
    create_table_if_not_exists(config.get('db_path'))

    if update.message.from_user.id not in config.get("allowed_users", []):
        return NOT_ALLOWED_USER
    main_types = config.get("texts").get("main_type_buttons_text")
    main_types.append(config.get("texts").get("others_button_text"))
    buttons = [main_types, 
              [config.get("texts").get("generate_report_button_text")]]
                # [CANCEL_BUTTON_TEXT, callback_data="/cancel"]]
    
    # using one_time_keyboard to hide the keyboard
    await update.message.reply_text(config.get("texts").get("start_new_expense"), 
                                    reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))
    
    return EXPENSE_TYPE


async def receive_not_allowed_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Filter allowed users
    """

    config = context.user_data.get("config")
    #TODO: This is not working properly. It filters the users but don't write the message
    await update.message.reply_text(config.get("texts").get("user_not_allowed"), 
                                    reply_markup=ReplyKeyboardRemove())
    
    return EXPENSE_TYPE


async def receive_expense_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Get Expense type
    """

    config = context.user_data.get("config")

    user = update.message.from_user
    expense_type = update.message.text.upper()
    logger.info("EXPENSE_TYPE of %s: %s", user.first_name, expense_type)
    context.user_data["user"] = user.first_name.upper()
    context.user_data["expense_type"] = expense_type

    main_types = config.get("texts").get("main_type_buttons_text")
    main_types.append(config.get("texts").get("others_button_text"))
    
    message = ""
    if update.message.text in main_types:
        message += config.get("texts").get("receive_expense_type_message").format(expense_type=expense_type)
    # Generate report
    elif config.get("texts").get("generate_report_button_text") in update.message.text:
        pass
    # Restart
    else:
        await update.message.reply_text(config.get("texts").get("restart_text"), reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END
    
    await update.message.reply_text(message, reply_markup=ReplyKeyboardRemove())

    return EXPENSE_DESCRIPTION
    

async def receive_expense_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Get the Expense Description
    """

    config = context.user_data.get("config")

    user = update.message.from_user
    expense_description = update.message.text.upper()
    logger.info("EXPENSE_DESCRIPTION of %s: %s", user.first_name, expense_description)
    context.user_data["expense_description"] = expense_description
    message = config.get("texts").get("receive_expense_description_message").format(expense_description=expense_description)
    await update.message.reply_text(message)

    return EXPENSE_AMOUNT


async def receive_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Get the Expense Amount
    """

    config = context.user_data.get("config")

    user = update.message.from_user
    try:
        expense_amount = float(update.message.text.replace(",", "."))
    except ValueError:
        expense_amount = 0.0
    context.user_data["expense_amount"] = expense_amount
    logger.info("EXPENSE_AMOUNT of %s: %s", user.first_name, expense_amount)
    buttons = [[config.get("texts").get("yes_button_text"), config.get("texts").get("no_button_text")]]

    message = config.get("texts").get("receive_expense_amount_message").format(expense_type=context.user_data["expense_type"],
                                                                               expense_description=context.user_data["expense_description"],
                                                                               expense_amount=expense_amount)
    await update.message.reply_text(
        message, reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=False)
    )

    return FINISH_GATHERING_INFO


async def receive_finish_gathering_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Finish Gatherinf INFO
    """
    
    config = context.user_data.get("config")

    user = update.message.from_user
    logger.info("FINISH GATHERING INFO of %s: %s", user.first_name, update.message.text)
    message = ""

    if update.message.text == config.get("texts").get("yes_button_text"):
        message = config.get("texts").get("receive_finish_gathering_info_message")
        expense_info = {
            "date": int(date.today().strftime("%Y%m%d")),
            "user": context.user_data["user"],
            "expense_type": context.user_data["expense_type"],
            "expense_description": context.user_data["expense_description"],
            "expense_amount": context.user_data["expense_amount"]
        }
        for k, v in expense_info.items():
            message += f" <b>{k}</b>:  {v}\n"        
        
        insert_in_db(expense_info, config.get('db_path'))
        print_table_content(config.get('db_path'))
    else:
        logger.info("User %s SAID NO WHEN GATHERING INFO", user.first_name)

    message += config.get("texts").get("restart_text")    
    await update.message.reply_text(
        message, reply_markup=ReplyKeyboardRemove(),  parse_mode=ParseMode.HTML
    )
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Cancel and ends the conversation.
    """
    
    config = context.user_data.get("config")

    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        config.get("texts").get("restart_text"), reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


def main() -> None:
    """
    Run bot
    Based on: https://github.com/python-telegram-bot/python-telegram-bot/blob/master/examples/conversationbot.py
    """

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