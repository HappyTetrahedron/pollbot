from basic_poll_handler import *

name = "Basic poll with custom description"
desc = "Like basic poll, but lets you add a custom text to the poll message."


def evaluation(poll):
    message = poll['meta']['text']
    message += "\n"
    for i, option in enumerate(poll['options']):
        message += "\n"
        message += "{}: {}".format(option['text'], num_votes(poll, i))
    return message


def ask_for_extra_config(meta):
    return "Please enter the text to be displayed above your poll:"


def register_extra_config(text, meta):
    meta['text'] = text


def num_votes(poll, i):
    return list(poll['votes'].values()).count(i) if 'votes' in poll else 0


def requires_extra_config(meta):
    return 'text' not in meta
