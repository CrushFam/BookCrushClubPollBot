"""Get the text describing the current state of the poll."""
from pollbot.i18n import i18n
from pollbot.helper import (
    poll_has_limited_votes,
)
from pollbot.models import (
    User,
    PollOption,
    Vote,
)
from .option import (
    get_option_information,
    get_sorted_options,
)
from .vote import (
    get_vote_information_line,
    get_remaining_votes_lines,
)


class Context():
    """Context for poll text creation

    This class contains all necessary information and flags, that
    are needed to decide in which way a poll should be displayed.
    """

    def __init__(self, session, poll):
        self.total_user_count = session.query(User.id) \
            .join(Vote) \
            .join(PollOption) \
            .filter(PollOption.poll == poll) \
            .group_by(User.id) \
            .count()

        # Flags
        self.anonymous = poll.anonymous
        self.show_results = poll.should_show_result()
        self.show_percentage = poll.show_percentage
        self.limited_votes = poll_has_limited_votes(poll)


def get_poll_text(session, poll, show_warning, management=False):
    """Create the text of the poll."""
    context = Context(session, poll)

    # Name and description
    lines = []
    lines.append(f'✉️ *{poll.name}*')
    if poll.description is not None:
        lines.append(f'_{poll.description}_')

    # Anonymity information
    if not context.show_results or context.anonymous:
        lines.append('')
    if context.anonymous:
        lines.append(f"_{i18n.t('poll.anonymous', locale=poll.locale)}_")
    if not context.show_results:
        lines.append(f"_{i18n.t('poll.results_not_visible', locale=poll.locale)}_")

    lines += get_option_information(session, poll, context)
    lines.append('')

    if context.limited_votes:
        lines.append(i18n.t('poll.vote_times',
                            locale=poll.locale,
                            amount=poll.number_of_votes))

    # Total user count information
    information_line = get_vote_information_line(poll, context)
    if information_line is not None:
        lines.append(information_line)

    if context.show_results and context.limited_votes:
        remaining_votes = get_remaining_votes_lines(session, poll)
        lines += remaining_votes

    if poll.due_date is not None:
        lines.append(i18n.t('poll.due',
                            locale=poll.locale,
                            date=poll.get_formatted_due_date()))

    # Own poll note
    if not management:
        lines.append(i18n.t('poll.own_poll', locale=poll.locale))

    # Notify users that poll is closed
    if poll.closed and not management:
        lines.append(i18n.t('poll.closed', locale=poll.locale))

    if show_warning and not management:
        lines.append(i18n.t('poll.too_many_votes', locale=poll.locale))

    return '\n'.join(lines)



