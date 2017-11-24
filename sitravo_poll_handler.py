max_options = 5


def options(poll):
    buttons = []
    opts = poll['options']
    num_opts = len(poll['options'])

    for option in opts:

        votes = 0
        button_row = [{
            'text': "{}{}{}".format(option['text'],
                                    " - " if votes > 0 else "",
                                    votes if votes > 0 else ""),
            'callback_data': {'i': option['index'], 'r': 0}
        }]
        for rank in range(num_opts):
            button_row.append({
                'text': "{}".format(rank + 1),
                'callback_data': {'i': option['index'], 'r': rank}
            })
        buttons.append(button_row)
    return buttons


def title(poll):
    return "*{}*".format(poll['title'])


def evaluation(poll):
    message = ""
    for option in poll['options']:
        message += "\n"
        message += "{}: {}".format(option['text'], 0)
    return message


def handle_vote(votes, user, callback_data):
    print("Handling vote")
    import pprint
    pprint.pprint(callback_data)
    pprint.pprint(votes)
    old_vote = {}
    if user in votes:
        old_vote = votes[user]

    rank_str = str(callback_data['r'])
    if str(old_vote.get(rank_str)) == str(callback_data['i']):
        print("Removing old vote as it is on same option")
        old_vote.pop(rank_str)
    else:
        old_vote[rank_str] = callback_data['i']

    pprint.pprint(old_vote)

    if not old_vote:
        votes.pop(user)
    else:
        sanitize_vote(old_vote)
        pprint.pprint(old_vote)
        votes[user] = old_vote
        pprint.pprint(votes)


def get_confirmation_message(poll, user):
    votes = poll['votes']
    if user in votes:
        vote = votes[user]
        info = ""
        for rank, index in vote.items():
            info += "\nChoice {}: {}".format(
                int(rank) + 1,
                get_option_name_by_index(poll, index)
            )
        return "Your vote: {}".format(info)
    return "Your vote was removed."


def get_option_name_by_index(poll, index):
    opts = poll['options']
    for opt in opts:
        if opt['index'] == index:
            return opt['text']
    return "Invalid option"


def sanitize_vote(vote):
    max_rank = max([int(key) for key in vote.keys()]) + 1
    for rank in range(max_rank):
        if str(rank) not in vote:
            for next_rank in range(rank, max_rank):
                if str(next_rank) in vote:
                    vote[str(rank)] = vote.pop(str(next_rank))
        else:
            curr_ind = vote[str(rank)]
            for next_rank in range(rank + 1, max_rank):
                if str(next_rank) in vote:
                    if vote[str(next_rank)] == curr_ind:
                        vote.pop(str(next_rank))
