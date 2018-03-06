max_options = 10
name = "Unconfigured Poll Type"
desc = "Poll type description goes here."


def options(poll):
    buttons = [[]]
    return buttons


def title(poll):
    return "*{}*".format(poll['title'])


def evaluation(poll):
    return "Somebody messed up! This poll type is not configured."


def handle_vote(votes, user, name, callback_data):
    pass


def get_confirmation_message(poll, user):
    return "Nothing happened."


def requires_extra_config(meta):
    return False


def ask_for_extra_config(meta):
    return "Somebody messed up! This poll type is not configured properly."


def register_extra_config(text, meta):
    pass

