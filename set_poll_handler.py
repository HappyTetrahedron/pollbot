from functools import reduce


max_options = 4


def options(poll):
    buttons = []
    set_opts = get_subsets_of(poll['options'])

    for set_opt in set_opts:
        index_set = [opt['index'] for opt in set_opt]
        title_set = [opt['text'] for opt in set_opt]
        votes = num_votes_on_set(poll, index_set)
        buttons.append([{
            'text': "{}{}{}".format(get_set_opt_text(title_set), 
                                    " - " if votes > 0 else "",
                                    votes if votes > 0 else ""),
            'callback_data': {'i': index_set}
        }])
    return buttons



def title(poll):
    return "*{}*".format(poll['title'])


def evaluation(poll):
    message = ""
    for option in poll['options']:
        message += "\n"
        message += "{}: {}".format(option['text'], num_votes_on_option(poll, option['index']))
    return message



def handle_vote(votes, user, callback_data):
    old_vote = None
    if user in votes:
        old_vote = votes.pop(user)
    if old_vote is not None and old_vote == callback_data['i']:
        # remove old vote
        pass
    else:
        votes[user] = callback_data['i']


def get_set_opt_text(title_set):
    return ','.join(title_set) if title_set else "None"
    

def num_votes_on_option(poll, index):
    if 'votes' not in poll:
        return 0
    votes = poll['votes']

    num = 0
    for cast_vote in votes.values():
        if index in cast_vote:
            num += 1
    return num


def num_votes_on_set(poll, index_set):
    if 'votes' not in poll:
        return 0
    votes = poll['votes']

    num = 0
    for cast_vote in votes.values():
        if cast_vote == index_set:
            num += 1
    return num


def get_subsets_of(some_set):
    return reduce(lambda z, x: z + [y + [x] for y in z], some_set, [[]])
