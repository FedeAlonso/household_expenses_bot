import logging
import os
import json
from logging.handlers import RotatingFileHandler
from datetime import datetime
from utils.household_expenses_db import create_db_if_not_exist, create_table_if_not_exists, insert_in_db, get_table_content, delete_from_db
from utils.gdrive import insert_in_sheet, delete_from_sheet
from utils.report import create_report
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


# Load config
CONFIG_FILE = "conf/config.json"
with open(CONFIG_FILE) as f:
    CONFIG = json.loads(f.read())

if not os.path.exists(CONFIG.get("output_folder")):
    os.makedirs(CONFIG.get("output_folder"))
    
REPORTS_FOLDER = os.path.join(os.path.join(CONFIG.get("output_folder"),"reports"))
if not os.path.exists(REPORTS_FOLDER):
    os.makedirs(REPORTS_FOLDER)

DB_PATH = os.path.join(CONFIG.get("output_folder"), CONFIG.get("db_filename"))    

# Enable logging
logging.basicConfig(
    handlers=[RotatingFileHandler(
                os.path.join(CONFIG.get("output_folder"), CONFIG.get("log_filename")), 
                maxBytes=20000000, 
                backupCount=1000)],
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


NOT_ALLOWED_USER, MAIN_ACTION, EXPENSES_TO_DELETE, CONFIRM_EXPENSES_TO_DELETE, EXPENSE_TYPE, EXPENSE_DESCRIPTION, EXPENSE_AMOUNT, FINISH_GATHERING_INFO = range(8)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Entry point
    """
    user = update.effective_user
    context.user_data["user"] = user

    # Check the user
    if user['id'] not in CONFIG.get("allowed_users", []):
        logger.info(f"Not Allowed user: '{user['first_name']}' with username '{user['username']}' and id '{user['id']}'")
        return NOT_ALLOWED_USER
    logger.info(f"Started conversation from user: '{user['first_name']}' with username '{user['username']}' and id '{user['id']}'")
    
    # Create the buttons with the main actions
    main_actions = [CONFIG.get("texts").get("main_actions_add_expense"),
                    CONFIG.get("texts").get("main_actions_delete_expense")]
    buttons = [main_actions, 
              [CONFIG.get("texts").get("main_actions_generate_report")]]
    
    # Send the buttons to the user
    await update.message.reply_text(CONFIG.get("texts").get("select_main_action"), 
                                    reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True))
    return MAIN_ACTION


async def receive_not_allowed_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Not allowed user
    """
    user = update.message.from_user
    logger.info(f"Not Allowed user {user['id']} message: {update.message.text} ")
    await update.message.reply_text(CONFIG.get("texts").get("user_not_allowed"), reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def receive_main_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Get main action
    """
    user = update.message.from_user
    main_action = update.message.text
    logger.info(f"User: {user.id}-{user.first_name} - ACTION: {main_action}")

    # Generate report
    if CONFIG.get("texts").get("main_actions_generate_report") == main_action:
        #TODO: GENERATE REPORT
        # pass
        report_name = datetime.now().strftime(f"%Y%m%d-EXPENSES REPORT-{user.id}-%H%M%S.pdf")
        report_path = os.path.join(REPORTS_FOLDER, report_name)
        create_report(report_path, get_table_content(DB_PATH, limit=0))
        document = open(report_path, 'rb')
        await update.message.reply_document(document)
        await update.message.reply_text(CONFIG.get("texts").get("restart_text"), reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    # Add new expense
    elif CONFIG.get("texts").get("main_actions_add_expense") == main_action:
        buttons = [CONFIG.get("texts").get("main_type_buttons_text")]
        await update.message.reply_text(CONFIG.get("texts").get("start_new_expense"), 
                                        reply_markup=ReplyKeyboardMarkup(buttons, 
                                        one_time_keyboard=True))
        return EXPENSE_TYPE
    
    # Delete expense
    elif CONFIG.get("texts").get("main_actions_delete_expense") == main_action:
        last_expenses = get_table_content(DB_PATH, limit=5)
        response_message = CONFIG.get("texts").get("select_expense_to_delete")
        for expense_id, expense_values in last_expenses.items():
            response_message += f"""
                <b>ID:</b> {expense_id}
                <b>AMOUNT:</b> {expense_values.get("expense_amount","")}
                <b>DESC.:</b> {expense_values.get("expense_description","")}
                <b>DATE:</b> {expense_values.get("date","")}
            """
        await update.message.reply_text(response_message, parse_mode=ParseMode.HTML)
        return EXPENSES_TO_DELETE
    
    else: 
        logger.warning(f"User: {user.id}-{user.first_name} - ACTION: {main_action} - NOT SUPPORTED!")
    return ConversationHandler.END


async def delete_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Delete expenses
    """
    user = update.message.from_user
    message = update.message.text
    logger.info(f"User: {user.id}-{user.first_name} - DELETION MESSAGE: {message}")
    elems_to_delete = [int(x) for x in message.split(",") if x.strip().isnumeric()]
    
    # If the IDs sent by the user are not numeric
    if len(elems_to_delete) == 0:
        logger.info(f"User: {user.id}-{user.first_name} - WRONG DELETION MESSAGE")
        message = f'{CONFIG.get("texts").get("no_expenses_to_delete")} {CONFIG.get("texts").get("restart_text")}'
        await update.message.reply_text(message, reply_markup=ReplyKeyboardRemove())
        return ConversationHandler.END

    elems_to_delete_str = ', '.join(str(x) for x in elems_to_delete)
    context.user_data["elems_to_delete"] = elems_to_delete
    context.user_data["elems_to_delete_str"] = elems_to_delete_str
    return_message = f"""{CONFIG.get("texts").get("confirm_expenses_to_delete")}
    {elems_to_delete_str}
    """
    buttons = [[CONFIG.get("texts").get("yes_button_text"), CONFIG.get("texts").get("no_button_text")]]
    await update.message.reply_text(
        return_message, reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True)
    )
    return CONFIRM_EXPENSES_TO_DELETE


async def confirm_delete_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Confirm expenses deletion
    """
    user = update.message.from_user
    logger.info(f"User: {user.id}-{user.first_name} - CONFIRM DELETE EXPENSES: { update.message.text}")

    message = ""

    if update.message.text == CONFIG.get("texts").get("yes_button_text"):
        deletion_result = delete_from_db(context.user_data.get("elems_to_delete"), DB_PATH)
        
        
        # If there are no errors during the deletion
        if len(deletion_result) == 0:
            message +=  CONFIG.get("texts").get("deletion_result_OK").format(expenses=(context.user_data.get("elems_to_delete_str")))

            # GDRIVE: delete from sheet
            if CONFIG.get("gdrive").get("active"):
                delete_from_sheet(context.user_data.get("elems_to_delete"), CONFIG.get("gdrive"))
        
        # If there are errors
        else:
            expenses_not_deleted = ', '.join(str(x) for x in deletion_result)
            message +=  CONFIG.get("texts").get("deletion_result_KO").format(expenses=expenses_not_deleted)

    message +=  CONFIG.get("texts").get("restart_text")
    await update.message.reply_text(message, reply_markup=ReplyKeyboardRemove())
    return ConversationHandler.END


async def receive_expense_type(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Get Expense type
    """
    user = update.message.from_user
    expense_type = update.message.text.upper()
    logger.info(f"User: {user.id}-{user.first_name} - EXPENSE_TYPE: {expense_type}")

    # Save expense type in context
    context.user_data["expense_type"] = expense_type
    
    message = CONFIG.get("texts").get("receive_expense_type_message").format(expense_type=expense_type)
    await update.message.reply_text(message, reply_markup=ReplyKeyboardRemove())
    return EXPENSE_DESCRIPTION
    

async def receive_expense_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Get the Expense Description
    """
    user = update.message.from_user
    expense_description = update.message.text.upper()
    logger.info(f"User: {user.id}-{user.first_name} - EXPENSE_DESCRIPTION: {expense_description}")
    
    # Save expense description in context
    context.user_data["expense_description"] = expense_description
    
    message = CONFIG.get("texts").get("receive_expense_description_message").format(expense_description=expense_description)
    await update.message.reply_text(message)

    return EXPENSE_AMOUNT


async def receive_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Get the Expense Amount
    """
    user = update.message.from_user
    try:
        expense_amount = float(update.message.text.replace(",", "."))
    except ValueError:
        expense_amount = 0.0
    
    logger.info(f"User: {user.id}-{user.first_name} - EXPENSE_AMOUNT: {expense_amount}")

    # Save expense amountin context
    context.user_data["expense_amount"] = expense_amount
    
    buttons = [[CONFIG.get("texts").get("yes_button_text"), CONFIG.get("texts").get("no_button_text")]]
    message = CONFIG.get("texts").get("receive_expense_amount_message").format(expense_type=context.user_data["expense_type"],
                                                                               expense_description=context.user_data["expense_description"],
                                                                               expense_amount=expense_amount)
    await update.message.reply_text(
        message, reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True)
    )
    return FINISH_GATHERING_INFO


async def receive_finish_gathering_info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Finish Gatherinf INFO
    """

    user = update.message.from_user
    logger.info(f"User: {user.id}-{user.first_name} - FINISH GATHERING INFO: { update.message.text}")

    message = ""

    if update.message.text == CONFIG.get("texts").get("yes_button_text"):
        message = CONFIG.get("texts").get("receive_finish_gathering_info_message")
        expense_info = {
            "date": datetime.today().strftime("%Y%m%d"),
            "user": context.user_data.get("user").first_name,
            "expense_type": context.user_data["expense_type"],
            "expense_description": context.user_data["expense_description"],
            "expense_amount": context.user_data["expense_amount"]
        }
        for k, v in expense_info.items():
            message += f" <b>{k}</b>:  {v}\n"        
        
        insert_result = insert_in_db(expense_info, DB_PATH)
        
        #Insert goes wrong
        if insert_result == -1:
            message += f'<b>{CONFIG.get("texts").get("insert_result_KO")}</b>\n'
        # GDRIVE: Add to sheet    
        elif CONFIG.get("gdrive").get("active"):
            expense_info["id"] = insert_result
            insert_in_sheet(expense_info, CONFIG.get("gdrive"))
            #TODO: Gestionar esto

    else:
        logger.info("User %s SAID NO WHEN GATHERING INFO", user.first_name)

    message += CONFIG.get("texts").get("restart_text")    
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
        CONFIG.get("texts").get("restart_text"), reply_markup=ReplyKeyboardRemove()
    )
    return ConversationHandler.END


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
            MAIN_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_main_action)],
            EXPENSES_TO_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, delete_expenses)],
            CONFIRM_EXPENSES_TO_DELETE: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_delete_expenses)],
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