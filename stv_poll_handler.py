from base_poll_handler import *
import math

name = "Single transferable vote poll"
desc = "Similar to instant runoff, but multiple choices will be elected."

HOPEFUL, ELECTED, ELIMINATED = range(3)


def options(poll):
    buttons = [[{
            'text': "Clear my votes",
            'callback_data': {'i': "C"}
        }]]
    opts = poll['options']

    for option in opts:

        votes_per_rank = get_votes_per_rank(poll, option['index'])
        vote_str = ",".join([str(v) for v in votes_per_rank])
        has_votes = True
        if max(votes_per_rank) == 0:
            has_votes = False

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


def evaluation(poll):
    votes = poll.get('votes', {})
    numopts = int(poll.get('meta').get('numopts'))
    candidates = [opt['index'] for opt in poll['options']]

    quota = int(float(len(votes))/float(numopts + 1)) + 1

    if votes:
        candidate_info = {}
        for candidate in candidates:
            candidate_info[candidate] = {
                'votes': {},
                'status': HOPEFUL,
            }
        initialize_votes(candidate_info, votes)

        elected, ties = run_election(quota, numopts, votes, candidate_info)

        elected_names = [get_option_name_by_index(poll, el) for el in elected]
        tied_names = [get_option_name_by_index(poll, el) for el in ties]

        message = "Current Top {}:\n".format(numopts)
        for elected_name in elected_names:
            message += "• *{}*\n".format(elected_name)

        if ties:
            message += "And in the end, we have a tie: \n"
            message += "*{}*\n".format(", ".join(tied_names))

    else:
        message = "There are currently no votes."

    num_votes = len(poll.get('votes', {}))

    body = "This is a single transferable vote poll.\n" \
           "You define an order of preference for the available options " \
           "by clicking on them in that order. For evaluation, the lowest " \
           "ranking candidate is eliminated until there are clear winners. \n" \
           "Make sure to select all options that would work for you, but " \
           "don't select any of those that don't work.\n\n{}\n{} people voted so far".format(message, num_votes)
    return body


def initialize_votes(candidate_info, votes):
    for voter, vote in votes.items():
        candidate_info[vote[0]]['votes'][voter] = 1.0


def run_election(quota, seats, votes, candidate_info):
    if len(candidate_info) <= seats:
        return list(candidate_info.keys()), []

    elected_candidates = count_candidate_votes_and_check_for_elections(candidate_info, quota)
    if not elected_candidates:
        eliminated_candidates = eliminate_lowest_candidates(candidate_info)
    transfer_votes(votes, quota, candidate_info)

    (hopeful, elected, eliminated) = count_candidate_types(candidate_info)
    hopeful_candidates = get_hopeful_candidates(candidate_info)

    if hopeful + elected <= seats:
        ties = []
        if hopeful + elected < seats:
            ties = eliminated_candidates
        return elected_candidates + hopeful_candidates, ties
    else:
        el, ti = run_election(quota, seats, votes, candidate_info)
        return elected_candidates + el, ti


def count_candidate_votes_and_check_for_elections(candidate_info, quota):
    elected_candidates = []
    for candidate, info in candidate_info.items():
        candidate_votes = 0.0
        for vote, value in info['votes'].items():
            candidate_votes += value
        if candidate_votes >= quota and info['status'] == HOPEFUL:
            elected_candidates.append(candidate)
            info['status'] = ELECTED
        info['curr_vote_count'] = candidate_votes

    return elected_candidates


def transfer_votes(votes, quota, candidate_info):
    for candidate, info in candidate_info.items():
        if info['status'] == ELIMINATED:
            retain_ratio = 0
            transfer_ratio = 1
        if info['status'] == ELECTED:
            retain_ratio = quota / info['curr_vote_count']
            transfer_ratio = 1 - retain_ratio
        if info['status'] == HOPEFUL:
            # retain all votes, no transfer
            continue

        del_voters = []
        for voter, vote_value in info['votes'].items():
            if retain_ratio == 0:
                # schedule for deletion
                del_voters.append(voter)
            else:
                info['votes'][voter] = vote_value * retain_ratio
            transfer_value = vote_value * transfer_ratio
            vote = votes[voter]
            idx = vote.index(candidate)
            while idx < len(vote) \
                    and candidate_info[vote[idx]]['status'] != HOPEFUL:
                idx += 1
            if idx < len(vote):
                candidate_info[vote[idx]]['votes'][voter] = transfer_value
            else:
                pass  # vote is lost
        for del_voter in del_voters:
            del info['votes'][del_voter]


def eliminate_lowest_candidates(candidate_info):
    minimum = float('inf')
    lowest = []

    for candidate, info in candidate_info.items():
        if info['status'] == HOPEFUL:
            if info['curr_vote_count'] < minimum:
                lowest = [candidate]
                minimum = info['curr_vote_count']
            elif info['curr_vote_count'] == minimum:
                lowest.append(candidate)

    for candidate in lowest:
        candidate_info[candidate]['status'] = ELIMINATED

    return lowest


def count_candidate_types(candidate_info):
    hopeful, elected, eliminated = [0, 0, 0]

    for candidate, info in candidate_info.items():
        if info['status'] == HOPEFUL:
            hopeful += 1
        elif info['status'] == ELECTED:
            elected += 1
        elif info['status'] == ELIMINATED:
            eliminated += 1

    return hopeful, elected, eliminated


def get_hopeful_candidates(candidate_info):
    hopeful_candidates = []

    for candidate, info in candidate_info.items():
        if info['status'] == HOPEFUL:
            hopeful_candidates.append(candidate)

    return hopeful_candidates


def handle_vote(votes, user, name, callback_data):
    old_vote = []
    if user in votes:
        old_vote = votes[user]

    if callback_data['i'] == 'C':
        old_vote = {}
    elif callback_data['i'] in old_vote:
        old_vote.remove(callback_data['i'])
    else:
        old_vote.append(callback_data['i'])

    if not old_vote:
        if user in votes:
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


def ask_for_extra_config(meta):
    return "Please specify how many options should be elected. Type a number:"


def register_extra_config(text, meta):
    if text.strip().isdigit():
        meta['numopts'] = text


def requires_extra_config(meta):
    return 'numopts' not in meta
