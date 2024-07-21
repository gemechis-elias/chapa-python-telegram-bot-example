import requests
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, CallbackContext, MessageHandler, filters
import logging
import random
from chapa import Chapa

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Define your tokens and other constants
TOKEN = 'YOUR_TELEGRAM_BOT_TOKEN'
CHAPPA_API_KEY = 'YOUR_CHAPPA_API_KEY' 
chapa = Chapa(CHAPPA_API_KEY, 
              response_format='json')


user_data = {}
# Start command
async def start(update: Update, context: CallbackContext) -> None:
    logger.info("==========> Received /start command")
    await update.message.reply_text("Welcome! Please enter your name:")

# Handle user messages
async def handle_message(update: Update, context: CallbackContext) -> None:
    user_id = update.message.from_user.id
    text = update.message.text

    if user_id not in user_data:
        user_data[user_id] = {'name': text}
        await update.message.reply_text(f"Nice to meet you, {text}! How much would you like to pay?")
    elif 'amount' not in user_data[user_id]:
        user_data[user_id]['amount'] = text
        name = user_data[user_id]['name']
        amount = user_data[user_id]['amount']
        keyboard = [
            [InlineKeyboardButton(f"Confirm {amount} ETB", callback_data=f'confirm_{amount}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"Name: {name}\nAmount: {amount} ETB\n\nClick confirm to proceed:", reply_markup=reply_markup)

# Button handler
async def button(update: Update, context: CallbackContext) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id

    logger.info(f"==========> Button pressed by user {user_id} with data: {query.data}")
    print(f"==========> Button pressed by user {user_id} with data: {query.data}")

    if query.data.startswith('confirm_'):
        amount = query.data.split('_')[1]
        logger.info(f"==========> Initiating payment for user {user_id} with amount: {amount}")
        print(f"==========> Initiating payment for user {user_id} with amount: {amount}")
        await initiate_chappa_payment(update, context, amount)

# Initiate Chappa payment
async def initiate_chappa_payment(update: Update, context: CallbackContext, amount: str) -> None:
    try:
        logger.info(f"==========> Inside initiate_chappa_payment function")
        print(f"==========> Inside initiate_chappa_payment function")

        user_id = update.callback_query.from_user.id
        name = user_data[user_id]['name']
        logger.info(f"==========> Retrieved user ID: {user_id} and name: {name}")
        print(f"==========> Retrieved user ID: {user_id} and name: {name}")

        reference = ''.join(random.choices('abcdefghijklmnopqrstuvwxyz0123456789', k=10))
        logger.info(f"==========> Generated reference: {reference}")
        print(f"==========> Generated reference: {reference}")
        
        payload = {
            "amount": float(amount),
            "currency": "ETB",
            "email": "abelabebe@gmail.com",
            "first_name": name,
            "last_name": "Abebe",
            "phone_number": "0912345678",
            "tx_ref": reference,
            "callback_url": "https://webhook.site/077164d6-29cb-40df-ba29-8a00e59a7e60",
            "return_url": f"https://t.me/{context.bot.username}?start=success_{reference}",
            "customization": {
                "title": "Payment",
                "description": "Payment for service"
            }
        }
        
        # Debugging logs and prints
        print(f"==========> Initiating payment for user {user_id} with payload: {payload}")
        
        response = chapa.initialize(**payload)
        print(f"==========> Initiatized")
        
        # Debugging logs and prints
        print(f"==========> Chappa response:" + str(response))
        if response['status'] == 'success':
            payment_url = response['data']['checkout_url']
            # Launch the payment URL directly
            keyboard = [
                [InlineKeyboardButton("Complete Payment", web_app=WebAppInfo(url=payment_url))]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await update.callback_query.message.reply_text(
                text="Click the button below to complete your payment:",
                reply_markup=reply_markup
            )
            logger.info(f"==========> User {user_id} initiated a payment: {amount} ETB")
            print(f"==========> User {user_id} initiated a payment: {amount} ETB")
        else:
            error_message = response.get('message', 'Unknown error')
            await context.bot.send_message(chat_id=update.callback_query.message.chat_id, text=f"There was an error initiating the payment: {error_message}. Please try again.")
            logger.error(f"==========> Chappa API error for user {user_id}: {response}")
            print(f"==========> Chappa API error for user {user_id}: {response}")
    
    except Exception as e:
        logger.error(f"==========> Exception during Chappa payment initiation for user {user_id}: {e}")
        print(f"==========> Exception during Chappa payment initiation for user {user_id}: {e}")
        await context.bot.send_message(chat_id=update.callback_query.message.chat_id, text="There was an error initiating the payment. Please try again.")

# Handle the start command after payment success
async def handle_start(update: Update, context: CallbackContext) -> None:
    query = update.message.text
    if query.startswith('/start success_'):
        reference = query.split('_')[1]
        await update.message.reply_text(f"Payment was successful! Reference: {reference}")
        logger.info(f"==========> Payment success for reference: {reference}")
    else:
        await start(update, context)

# Error handler
async def error(update: Update, context: CallbackContext) -> None:
    """Log Errors caused by Updates."""
    logger.warning('==========> Update "%s" caused error "%s"', update, context.error)

def main() -> None:
    """Start the bot."""
    application = Application.builder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.add_error_handler(error)

    logger.info("==========> Starting the bot")
    print("==========> Starting the bot")
    application.run_polling()

if __name__ == '__main__':
    main()