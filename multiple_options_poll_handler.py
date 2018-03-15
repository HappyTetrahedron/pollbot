from functools import reduce
from base_poll_handler import *

name = "Multiple options poll"
desc = "Lets you vote for multiple options"


def options(poll):
    buttons = [[{
        'text': "Clear my votes",
        'callback_data': {'i': "C"}
    }]]

    for opt in poll['options']:
        votes = num_votes_on_option(poll, opt['index'])
        buttons.append([{
            'text': "{}{}{}".format(opt['text'],
                                    " - " if votes > 0 else "",
                                    votes if votes > 0 else ""),
            'callback_data': {'i': opt['index']}
        }])
    return buttons


def evaluation(poll):
    message = ""
    for option in poll['options']:
        message += "\n"
        message += "{}: {}".format(option['text'], num_votes_on_option(poll, option['index']))
    return message


def handle_vote(votes, user, name, callback_data):
    old_vote = None
    if user in votes:
        old_vote = votes.pop(user)
    if callback_data['i'] == 'C':
        # remove vote
        pass
    elif old_vote is not None and callback_data['i'] in old_vote:
        old_vote.remove(callback_data['i'])
        if old_vote:
            votes[user] = old_vote
    elif old_vote is not None:
        old_vote.append(callback_data['i'])
        votes[user] = old_vote
    else:
        votes[user] = [callback_data['i']]


def get_confirmation_message(poll, user):
    votes = poll['votes']
    if user in votes:
        vote = votes[user]
        opts = poll['options']
        vote_set = [opt['text'] for opt in opts if opt['index'] in vote]
        string = ",".join(vote_set) if vote_set else "nothing"
        return "You voted for {}.".format(string)
    return "Your vote was removed."


def num_votes_on_option(poll, index):
    if 'votes' not in poll:
        return 0
    votes = poll['votes']

    num = 0
    for cast_vote in votes.values():
        if index in cast_vote:
            num += 1
    return num

