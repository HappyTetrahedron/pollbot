from basic_poll_handler import *

name = "Open poll"
desc = "Like basic poll, but you can see who voted for what."


def evaluation(poll):
    message = "This is an open poll. People will see what you voted for.\n"
    for i, option in enumerate(poll['options']):
        message += "\n"
        message += "*{}: {}*".format(option['text'], num_votes(poll, i))
        users = get_users_voting_for(poll, option)
        for user in users:
            message += "\n "
            message += user
    return message


def handle_vote(votes, user, name, callback_data):
    old_vote = None
    if user in votes:
        old_vote = votes.pop(user)
    if old_vote is not None and str(old_vote['data']) == str(callback_data['i']):
        # remove old vote
        pass
    else:
        votes[user] = {
            'data': callback_data['i'],
            'name': name
        }


def num_votes(poll, i):
    return [val['data'] for val in poll['votes'].values()].count(i) if 'votes' in poll else 0


def get_users_voting_for(poll, option):
    return [val['name'] for val in poll['votes'].values() if val['data'] == option['index']] if 'votes' in poll else []
