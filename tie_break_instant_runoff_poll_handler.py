import math

max_options = 10

name = "Instant runoff poll with fallback tie-breaking"


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
                # Somebody has hit the quota, elect them:
                elected = [candidates[i] for i, count in enumerate(counts) if count == max_votes]
            else:
                min_votes = min(counts)
                old_candidates = list(candidates)
                # eliminate all candidates with lowest count:
                delete_pls = []
                for i, count in enumerate(counts):
                    if count == min_votes:
                        delete_pls.append(candidates[i])
                for candidate in delete_pls:
                    candidates.remove(candidate)
                if not candidates:
                    # The last remaining candidates were eliminated at the same time. We have a tie!
                    candidates = old_candidates
                    # Tiebreak fallback solution
                    tiered_votes = {}
                    for candidate in old_candidates:
                        tiered_vote = get_votes_per_rank(poll, candidate)
                        tiered_votes[candidate] = tiered_vote

                    for i in range(1, len(poll['options']) + 1):
                        # To resolve the tie, continually calculate prefix sums of our the votes per rank
                        max_candidate_vote = 0
                        current_best_candidates = []
                        for candidate, vote in tiered_votes.items():
                            prefix_sum = sum(vote[:i])
                            # Keep all candidates with highest prefix sum
                            if max_candidate_vote == prefix_sum:
                                current_best_candidates.append(candidate)
                            elif max_candidate_vote < prefix_sum:
                                max_candidate_vote = prefix_sum
                                current_best_candidates = [candidate]

                        # Throw out all candidates that don't have highest prefix sum anymore
                        to_remove = []
                        for candidate, vote in tiered_votes.items():
                            if candidate not in current_best_candidates:
                                to_remove.append(candidate)
                        for candidate in to_remove:
                            tiered_votes.pop(candidate)

                        if len(current_best_candidates) == 1:
                            # we have a winner!
                            elected = current_best_candidates
                            break

                    if not elected:
                        # We have a true tie
                        elected = current_best_candidates

        elected_names = [get_option_name_by_index(poll, el) for el in elected]
        message = "{}: {}".format(
            "Current winner" if len(elected_names) == 1 else "We have a tie",
            ",".join(elected_names)
        )
    else:
        message = "There are currently no votes."

    body = "This is an instant runoff poll with tie breaking. \n" \
           "You define an order of preference for the available options " \
           "by clicking on them in that order. For evaluation, the lowest " \
           "ranking candidate is eliminated until there is a clear winner. \n" \
           "This poll uses a fall-back tie-breaking algorithm, meaning that it " \
           "will try extra hard to break ties.\n\n*{}*".format(message)
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
