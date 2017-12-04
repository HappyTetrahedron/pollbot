max_options = 10

name = "Open poll"


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


def title(poll):
    return "*{}*".format(poll['title'])
    

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


def get_confirmation_message(poll, user):
    votes = poll['votes']
    if user in votes:
        vote = votes[user]
        for option in poll['options']:
            if option['index'] == vote['data']:
                return "You voted for \"{}\".".format(option['text'])
    return "Your vote was removed."


def num_votes(poll, i):
    return [val['data'] for val in poll['votes'].values()].count(i) if 'votes' in poll else 0


def get_users_voting_for(poll, option):
    return [val['name'] for val in poll['votes'].values() if val['data'] == option['index']] if 'votes' in poll else []
