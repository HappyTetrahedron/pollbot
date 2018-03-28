from instant_runoff_poll_handler import *
from custom_description_poll_handler import ask_for_extra_config
from custom_description_poll_handler import requires_extra_config
from custom_description_poll_handler import register_extra_config
import math

name = "Instant runoff poll with custom description"
desc = "Like instant runoff, but with a custom description"


def evaluation(poll):
    votes = poll.get('votes', {})
    candidates = [opt['index'] for opt in poll['options']]

    explanation = "Click on only those options that work for you, in the order of your preference."

    if votes:
        elected = run_election(candidates, list(votes.values()))

        elected_names = [get_option_name_by_index(poll, el) for el in elected]
        message = "{}: {}".format(
            "Current winner" if len(elected_names) == 1 else "We have a tie",
            ",".join(elected_names)
        )
    else:
        message = "There are currently no votes."

    num_votes = len(poll.get('votes', {}))

    body = poll['meta']['text']
    body += "\n\n{}\n\n*{}*\n{} people voted so far".format(explanation, message, num_votes)
    return body

