import math

max_options = 5


def options(poll):
    buttons = []
    opts = poll['options']

    for option in opts:

        votes_per_rank = get_votes_per_rank(poll, option['index'])
        vote_str = ",".join([str(v) for v in votes_per_rank])
        has_votes = True
        if max(votes_per_rank) == 0:
            has_votes=False

        buttons.append([{
            'text': "{}{}{}{}".format(option['text'],
                                      " - (" if has_votes else "",
                                      vote_str if has_votes else "",
                                      ")" if has_votes else ""),
            'callback_data': {'i': option['index']}
        }])
    return buttons


def get_votes_per_rank(poll, opt_index):
    num_opts = len(poll['options'])
    counts = [0] * num_opts
    for vote in poll.get('votes', {}).values():
        for i, opt_ind in enumerate(vote):
            if opt_ind == opt_index:
                counts[i] += 1
    return counts


def title(poll):
    return "*{}*".format(poll['title'])


def evaluation(poll):
    votes = poll.get('votes', {})
    candidates = [opt['index'] for opt in poll['options']]

    if votes:
        elected = None
        quota = math.floor(len(votes) / 2) + 1

        while elected is None:
            counts = count_votes(votes, candidates)
            max_votes = max(counts)
            if max_votes >= quota:
                elected = [candidates[i] for i, count in enumerate(counts) if count == max_votes]
            else:
                min_votes = min(counts)
                del candidates[counts.index(min_votes)]

        elected_names = [get_option_name_by_index(poll, el) for el in elected]
        message = "Current winner: {}".format(
            ",".join(elected_names)
        )
    else:
        message = "There is currently no winner."

    body = "This is a instant runoff vote. \n" \
           "You define an order of preference for the available options " \
           "by clicking on them in that order. For evaluation, the lowest " \
           "ranking candidate is eliminated until there is a clear winner.\n\n*{}*".format(message)
    return body


def count_votes(votes, candidates):
    counts = [0] * len(candidates)
    for vote in votes.values():
        vote_counted = False
        for preference in vote:
            if preference in candidates and not vote_counted:
                counts[candidates.index(preference)] += 1
                vote_counted = True
    return counts


def handle_vote(votes, user, callback_data):
    old_vote = []
    if user in votes:
        old_vote = votes[user]

    if callback_data['i'] in old_vote:
        old_vote.remove(callback_data['i'])
    else:
        old_vote.append(callback_data['i'])

    if not old_vote:
        votes.pop(user)
    else:
        votes[user] = old_vote


def get_confirmation_message(poll, user):
    votes = poll['votes']
    if user in votes:
        vote = votes[user]
        vote_names = [get_option_name_by_index(poll, i) for i in vote]
        info = ",".join(vote_names)
        return "Your order of preference: {}".format(info)
    return "Your vote was removed."


def get_option_name_by_index(poll, index):
    opts = poll['options']
    for opt in opts:
        if opt['index'] == index:
            return opt['text']
    return "Invalid option"
