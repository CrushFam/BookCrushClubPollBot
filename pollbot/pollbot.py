"""A bot which checks if there is a new record in the server section of hetzner."""
import logging
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ChosenInlineResultHandler,
    InlineQueryHandler,
    Filters,
    MessageHandler,
    Updater,
)

from pollbot.config import config
from pollbot.helper.session import session_wrapper
from pollbot.helper.keyboard import get_main_keyboard
from pollbot.helper import (
    start_text,
    help_text,
    donations_text,
)

from pollbot.telegram.message_handler import handle_private_text
from pollbot.telegram.callback_handler import handle_callback_query
from pollbot.telegram.error_handler import error_callback
from pollbot.telegram.inline_query import search
from pollbot.telegram.inline_result_handler import handle_chosen_inline_result
from pollbot.telegram.commands.poll import (
    create_poll,
    cancel_creation,
)


@session_wrapper()
def start(bot, update, session, user):
    """Send a help text."""
    keyboard = get_main_keyboard()
    update.message.chat.send_message(start_text, parse_mode='Markdown', reply_markup=keyboard)


@session_wrapper()
def send_help_text(bot, update, session, user):
    """Send a help text."""
    keyboard = get_main_keyboard()
    update.message.chat.send_message(help_text, parse_mode='Markdown', reply_markup=keyboard)


@session_wrapper()
def send_donation_text(bot, update, session, user):
    """Send the donation text."""
    keyboard = get_main_keyboard()
    update.message.chat.send_message(donations_text, parse_mode='Markdown', reply_markup=keyboard)


logging.basicConfig(level=config.LOG_LEVEL,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Initialize telegram updater and dispatcher
updater = Updater(token=config.TELEGRAM_API_KEY, workers=config.WORKER_COUNT, use_context=True,
                  request_kwargs={'read_timeout': 20, 'connect_timeout': 20})

dispatcher = updater.dispatcher

# Poll commands
dispatcher.add_handler(CommandHandler('create', create_poll))
dispatcher.add_handler(CommandHandler('cancel', cancel_creation))

# Misc commands
dispatcher.add_handler(CommandHandler('start', create_poll))
dispatcher.add_handler(CommandHandler('help', send_help_text))
dispatcher.add_handler(CommandHandler('donations', send_donation_text))


# Callback handler
dispatcher.add_handler(CallbackQueryHandler(handle_callback_query))

# InlineQuery handler
dispatcher.add_handler(InlineQueryHandler(search))

# InlineQuery result handler
dispatcher.add_handler(ChosenInlineResultHandler(handle_chosen_inline_result))

# Message handler

dispatcher.add_handler(
    MessageHandler(
        Filters.text,
        handle_private_text
    ))

# Error handler
dispatcher.add_error_handler(error_callback)