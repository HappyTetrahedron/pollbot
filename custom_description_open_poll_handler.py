from open_poll_handler import *
from custom_description_poll_handler import ask_for_extra_config
from custom_description_poll_handler import requires_extra_config
from custom_description_poll_handler import register_extra_config

name = "Open poll with custom description"
desc = "Like open poll, but lets you add a custom text to the poll message."


def evaluation(poll):
    message = poll['meta']['text']
    message += "\n"
    for i, option in enumerate(poll['options']):
        message += "\n"
        message += "*{}: {}*".format(option['text'], num_votes(poll, i))
        users = get_users_voting_for(poll, option)
        for user in users:
            message += "\n "
            message += user
    return message
