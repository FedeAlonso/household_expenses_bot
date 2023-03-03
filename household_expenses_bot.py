import logging
import os
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

MAIN_TYPE_BUTTON_TEXT = "ALIMENTACION"
OTHERS_BUTTON_TEXT = "OTROS"
GENERATE_REPORT_BUTTON_TEXT = "GENERAR INFORME"
CANCEL_BUTTON_TEXT = "CANCEL" 
YES_BUTTON_TEXT = "YES"
NO_BUTTON_TEXT = "NO"
RESTART_TEXT = "Si quiere recomenzar el proceso escriba /start"

EXPENSE_TYPE, EXPENSE_DESCRIPTION, EXPENSE_AMOUNT, FINISH_GATHERING_INFO = range(4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Entry point
    """

    buttons = [[MAIN_TYPE_BUTTON_TEXT, 
                OTHERS_BUTTON_TEXT], 
                [GENERATE_REPORT_BUTTON_TEXT],
                [CANCEL_BUTTON_TEXT]]
    message = "¿Qué gasto quieres añadir?"
    
    # using one_time_keyboard to hide the keyboard
    await update.message.reply_text(
        message, reply_markup=ReplyKeyboardMarkup(buttons, one_time_keyboard=True)
    )
    
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
    expense_amount = update.message.text
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
        message= f"""
        Se va a proceder a insertar la siguiente información en la base de datos:
        <b>Usuario:</b>     {context.user_data["user"]}
        <b>Tipo de gasto:</b>     {context.user_data["expense_type"]}
        <b>Descripción del gasto:</b>     {context.user_data["expense_description"]}
        <b>Cantidad del gasto:</b>     {context.user_data["expense_amount"]}\n
        """
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
        "Bye! I hope we can talk again some day.", reply_markup=ReplyKeyboardRemove()
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
            EXPENSE_TYPE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_expense_type)],
            EXPENSE_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_expense_description)],
            EXPENSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_expense_amount)],
            FINISH_GATHERING_INFO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_finish_gathering_info)]
        },
        fallbacks=[CommandHandler("cancel", cancel),
                   MessageHandler("CANCELAR", cancel)],
    )
    application.add_handler(conv_handler)

    # Run the bot until the user presses Ctrl-C
    application.run_polling()



if __name__ == "__main__":
    main()