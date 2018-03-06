from base_poll_handler import *

name = "Basic poll"
desc = "A straightforward first-past-the-post poll."


def options(poll):
    buttons = []
    for i, option in enumerate(poll['options']):
        votes = num_votes(poll, i)
        buttons.append([{
            'text': "{}{}{}".format(option['text'],
                                    " - " if votes > 0 else "",
                                    votes if votes > 0 else ""),
            'callback_data': {'i': i},
        }])
    return buttons


def evaluation(poll):
    message = ""
    for i, option in enumerate(poll['options']):
        message += "\n"
        message += "{}: {}".format(option['text'], num_votes(poll, i))
    return message


def handle_vote(votes, user, name, callback_data):
    old_vote = None
    if user in votes:
        old_vote = votes.pop(user)
    if old_vote is not None and str(old_vote) == str(callback_data['i']):
        # remove old vote
        pass
    else:
        votes[user] = callback_data['i']


def get_confirmation_message(poll, user):
    votes = poll['votes']
    if user in votes:
        vote = votes[user]
        for option in poll['options']:
            if option['index'] == vote:
                return "You voted for \"{}\".".format(option['text'])
    return "Your vote was removed."


def num_votes(poll, i):
    return list(poll['votes'].values()).count(i) if 'votes' in poll else 0
