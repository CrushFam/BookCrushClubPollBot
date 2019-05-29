"""Session helper functions."""
import traceback
from functools import wraps
from telegram.error import (
    TelegramError,
    Unauthorized,
)

from pollbot.db import get_session
from pollbot.sentry import sentry
from pollbot.models import User
from pollbot.helper import error_text
from pollbot.helper.telegram import call_tg_func


def job_session_wrapper():
    """Create a session, handle permissions and exceptions for jobs."""
    def real_decorator(func):
        """Parametrized decorator closure."""
        @wraps(func)
        def wrapper(context):
            session = get_session()
            try:
                func(context, session)

                session.commit()
            except: # noqa
                # Capture all exceptions from jobs. We need to handle those insidse the jobs
                traceback.print_exc()
                sentry.captureException()
            finally:
                session.close()
        return wrapper

    return real_decorator


def hidden_session_wrapper():
    """Create a session, handle permissions and exceptions."""
    def real_decorator(func):
        """Parametrized decorator closure."""
        @wraps(func)
        def wrapper(update, context):
            session = get_session()
            try:
                user = get_user(session, update)
                if not is_allowed(user, update):
                    return

                func(context.bot, update, session, user)

                session.commit()
            # Raise all telegram errors and let the generic error_callback handle it
            finally:
                session.close()
        return wrapper

    return real_decorator


def session_wrapper(send_message=True, private=False):
    """Create a session, handle permissions, handle exceptions and prepare some entities."""
    def real_decorator(func):
        """Parametrized decorator closure."""
        @wraps(func)
        def wrapper(update, context):
            session = get_session()
            try:
                user = get_user(session, update)
                if not is_allowed(user, update, private=private):
                    return

                if hasattr(update, 'message') and update.message:
                    message = update.message
                elif hasattr(update, 'edited_message') and update.edited_message:
                    message = update.edited_message

                if not is_allowed(user, update, private=private):
                    return

                response = func(context.bot, update, session, user)

                session.commit()
                # Respond to user
                if hasattr(update, 'message') and response is not None:
                    call_tg_func(message.chat, 'send_message', args=[response])

            # A user banned the bot
            except Unauthorized:
                session.delete(user)

            # Raise all telegram errors and let the generic error_callback handle it
            except TelegramError as e:
                raise e

            except:
                if send_message:
                    session.close()
                    call_tg_func(message.chat, 'send_message',
                                 args=[error_text])
                raise
            finally:
                session.close()

        return wrapper

    return real_decorator


def get_user(session, update):
    """Get the user from the update."""
    user = None
    # Check user permissions
    if hasattr(update, 'message') and update.message:
        user = User.get_or_create(session, update.message.from_user)
    if hasattr(update, 'edited_message') and update.edited_message:
        user = User.get_or_create(session, update.edited_message.from_user)
    elif hasattr(update, 'inline_query') and update.inline_query:
        user = User.get_or_create(session, update.inline_query.from_user)
    elif hasattr(update, 'callback_query') and update.callback_query:
        user = User.get_or_create(session, update.callback_query.from_user)

    return user


def is_allowed(user, update, private=False):
    """Check whether the user is allowed to access this endpoint."""
    if private and update.message.chat.type != 'private':
        call_tg_func(update.message.chat, 'send_message',
                     ['Please do this in a direct conversation with me.'])
        return False

    return True