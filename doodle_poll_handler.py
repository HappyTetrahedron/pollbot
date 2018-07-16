from base_poll_handler import *

name = "Doodle"
desc = "Lets you pick the preferred out of multiple options, with yes-no-ifneedbe answers"


def options(poll):
    buttons = [[{
        'text': "Clear my votes",
        'callback_data': {'i': "C"}
    }]]

    for opt in poll['options']:
        total = num_votes_on_option(poll, opt['index'])
        yes = num_yes_on_option(poll, opt['index'])
        inb = num_inb_on_option(poll, opt['index'])
        buttons.append([{
            'text': "{}{}{}{}{}".format(opt['text'],
                                    " - " if total > 0 else "",
                                    yes if total > 0 else "",
                                    "/" if inb > 0 else "",
                                    inb if inb > 0 else ""),
            'callback_data': {'i': opt['index']}
        }])

    nopes = num_cant_make_it(poll)
    buttons.append([{
        'text': "Can't make it{}{}".format(
            " - " if nopes > 0 else "",
            nopes if nopes > 0 else ""
        ),
        'callback_data': {'i': "N"}
    }])
    return buttons


def evaluation(poll):
    message = ""
    best_opts = find_best(poll)
    num_votes = len(poll.get('votes', {}))
    for option in poll['options']:
        message += "\n"
        if option['index'] in best_opts:
            message += "> "
        message += "{}: {} yes".format(option['text'], num_yes_on_option(poll, option['index']))
        inb = num_inb_on_option(poll, option['index'])
        if inb > 0:
            message += ", {} if need be".format(inb)

    message += "\n\n{} people voted so far".format(num_votes)
    return message


def find_best(poll):
    opts = poll['options']
    votes = poll.get('votes')

    if not votes:
        return []

    best = []
    max_votes = 0

    for opt in opts:
        num = num_votes_on_option(poll, opt['index'])
        if num > max_votes:
            best = [opt]
            max_votes = num
        elif num == max_votes:
            best.append(opt)

    min_inb = 9999999
    best_after_inb = []
    for opt in best:
        num = num_inb_on_option(poll, opt['index'])
        if num < min_inb:
            best_after_inb = [opt['index']]
            min_inb = num
        elif num == min_inb:
            best_after_inb.append(opt['index'])

    return best_after_inb


def handle_vote(votes, user, name, callback_data):
    old_vote = None
    if user in votes:
        old_vote = votes.pop(user)
    pressed = str(callback_data['i'])
    if pressed == 'C':
        # remove vote
        pass
    elif pressed == 'N':
        if old_vote != "nope":
            votes[user] = "nope"
    elif old_vote is not None and old_vote != "nope" and pressed in old_vote.keys():
        if old_vote[pressed] == "y":
            old_vote[pressed] = "i"
            votes[user] = old_vote
        elif old_vote[pressed] == "i":
            old_vote.pop(pressed)
            if old_vote:
                votes[user] = old_vote
    elif old_vote is not None and old_vote != "nope":
        old_vote[pressed] = "y"
        votes[user] = old_vote
    else:
        votes[user] = {pressed: "y"}


def get_confirmation_message(poll, user):
    votes = poll.get('votes')
    if user in votes:
        return "Your vote was registered."
    return "Your vote was removed."


def num_votes_on_option(poll, index):
    if 'votes' not in poll:
        return 0
    votes = poll['votes']

    string_index = str(index)

    num = 0
    for cast_vote in votes.values():
        if cast_vote == "nope":
            continue
        if string_index in cast_vote.keys():
            num += 1
    return num


def num_yes_on_option(poll, index):
    if 'votes' not in poll:
        return 0
    votes = poll['votes']

    string_index = str(index)

    num = 0
    for cast_vote in votes.values():
        if cast_vote == "nope":
            continue
        if string_index in cast_vote.keys():
            if cast_vote[string_index] == 'y':
                num += 1
    return num


def num_inb_on_option(poll, index):
    if 'votes' not in poll:
        return 0
    votes = poll['votes']

    string_index = str(index)

    num = 0
    for cast_vote in votes.values():
        if cast_vote == "nope":
            continue
        if string_index in cast_vote.keys():
            if cast_vote[string_index] == 'i':
                num += 1
    return num


def num_cant_make_it(poll):
    if 'votes' not in poll:
        return 0
    votes = poll['votes']

    num = 0
    for cast_vote in votes.values():
        if cast_vote == "nope":
            num += 1
    return num
