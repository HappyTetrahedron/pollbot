#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Simple Bot to reply to Telegram messages.
This program is dedicated to the public domain under the CC0 license.
This Bot uses the Updater class to handle the bot.
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
"""
from uuid import uuid4

from telegram import InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler, ConversationHandler, \
    RegexHandler
import logging

import dataset

import json

from telegram.ext.inlinequeryhandler import InlineQueryHandler
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup
from telegram.inline.inlinequeryresultarticle import InlineQueryResultArticle
from telegram.inline.inputtextmessagecontent import InputTextMessageContent

import basic_poll_handler
import set_poll_handler
import instant_runoff_poll_handler
import tie_break_instant_runoff_poll_handler

POLL_TYPE_BASIC, POLL_TYPE_SET, POLL_TYPE_INSTANT_RUNOFF, POLL_TYPE_INSTANT_RUNOFF_TIE_BREAK = range(4)

POLL_TYPES_MAP = {
    POLL_TYPE_BASIC: "Basic poll",
    POLL_TYPE_SET: "Subset poll",
    POLL_TYPE_INSTANT_RUNOFF: "Instant runoff poll",
    POLL_TYPE_INSTANT_RUNOFF_TIE_BREAK: "Instant runoff poll with fallback tie breaking",
}

POLL_TYPES_HANDLERS = {
    POLL_TYPE_BASIC: basic_poll_handler,
    POLL_TYPE_SET: set_poll_handler,
    POLL_TYPE_INSTANT_RUNOFF: instant_runoff_poll_handler,
    POLL_TYPE_INSTANT_RUNOFF_TIE_BREAK: tie_break_instant_runoff_poll_handler,
}


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

db = dataset.connect('sqlite:///votes.db')

# Conversation states:
NOT_ENGAGED, TYPING_TITLE, TYPING_TYPE, TYPING_OPTION = range(4)


# Conversation handlers:
def start(bot, update):
    """Send a message when the command /start is issued."""
    update.message.reply_text('Hi! Please send me the title of your poll.')

    return TYPING_TITLE


def handle_type(bot, update, user_data):
    text = update.message.text
    user_data['type'] = next((i for i, val in POLL_TYPES_MAP.items() if val == text), None)
    user_data['options'] = []
    update.message.reply_text("Awesome. Now, send me the first answer option.")

    return TYPING_OPTION


def handle_title(bot, update, user_data):
    text = update.message.text
    user_data['title'] = text
    update.message.reply_text("Cool! What kind of survey is it going to be?",
                              reply_markup=assemble_reply_keyboard())

    return TYPING_TYPE


def handle_option(bot, update, user_data):
    text = update.message.text
    handler = POLL_TYPES_HANDLERS[user_data['type']]
    user_data['options'].append(text)

    if len(user_data['options']) >= handler.max_options:
        handle_done(bot, update, user_data)

    update.message.reply_text("Doing great! Now, send me another answer option or type /done to publish.",
                              reply_markup=ReplyKeyboardRemove())

    if len(user_data['options']) >= handler.max_options - 1:
        update.message.reply_text("Uh oh, you're running out of options. You can only have one more option.")

    return TYPING_OPTION


def handle_done(bot, update, user_data):
    update.message.reply_text("Thanks man! Now here is your fine poll")
    options = []
    for i,opt in enumerate(user_data['options']):
        options.append({
            'text': opt,
            'index': i
        })

    poll = {
        'poll_id': str(uuid4()),
        'title': user_data['title'],
        'type': user_data['type'],
        'options': options
    }

    table = db['setpolls']

    table.insert(serialize(poll))

    inline_keyboard_items = get_inline_keyboard_items(poll)
    publish_button = InlineKeyboardButton("Publish!",
                                          switch_inline_query=poll['poll_id'])
    inline_keyboard_items.append([publish_button])
    inline_keyboard = InlineKeyboardMarkup(inline_keyboard_items)

    update.message.reply_text(assemble_message_text(poll),
                              reply_markup=inline_keyboard,
                              parse_mode='Markdown'
                              )

    user_data.clear()

    return NOT_ENGAGED


def assemble_reply_keyboard():
    keyboard = []
    for _, val in POLL_TYPES_MAP.items():
        keyboard.append([val])

    return ReplyKeyboardMarkup(
        keyboard,
        one_time_keyboard=True
    )


def assemble_type_regex():
    orclause = '|'.join(list(POLL_TYPES_MAP.values()))
    regex = '^({})$'.format(orclause)
    return regex


def assemble_inline_keyboard(poll):
    return InlineKeyboardMarkup(get_inline_keyboard_items(poll))


def get_inline_keyboard_items(poll):
    handler = POLL_TYPES_HANDLERS[poll['type']]
    button_items = handler.options(poll)
    buttons = []
    for row in button_items:
        current_row = []
        for item in row:
            item['callback_data']['id'] = poll['poll_id']
            current_row.append(InlineKeyboardButton(item['text'],
                                                    callback_data=json.dumps(item['callback_data'], separators=(',', ':')) ))
        buttons.append(current_row)
    return buttons


def assemble_message_text(poll):
    handler = POLL_TYPES_HANDLERS[poll['type']]
    message = '{}\n{}'.format(handler.title(poll),
                              handler.evaluation(poll))
    return message


def serialize(poll):
    ser = dict(poll)
    ser['options'] = json.dumps(poll['options'])
    if 'votes' in ser:
        ser['votes'] = json.dumps(poll['votes'])
    return ser


def deserialize(serialized):
    poll = dict(serialized)
    poll['options'] = json.loads(serialized['options'])
    if 'votes' in poll:
        poll['votes'] = json.loads(serialized['votes'])
    return poll


# Inline query handler
def inline_query(bot, update):
    query = update.inline_query.query

    table = db['setpolls']
    result = table.find_one(poll_id=query)
    if not result:
        update.inline_query.answer(results=[],
                                   switch_pm_text="Create a new poll",
                                   switch_pm_parameter="start")
    else:
        poll = deserialize(result)
        results = [
            InlineQueryResultArticle(
                id=poll['poll_id'],
                title=poll['title'],
                input_message_content=InputTextMessageContent(
                    message_text=assemble_message_text(poll),
                    parse_mode='Markdown'
                ),
                reply_markup=assemble_inline_keyboard(poll)
            )
        ]
        update.inline_query.answer(results)


# Inline button press handler
def button(bot, update):
    query = update.callback_query
    data_dict = json.loads(update.callback_query.data)

    table = db['setpoll_instances']
    templates = db['setpolls']

    kwargs = {}
    if query.message:
        kwargs['message_id'] = query.message.message_id
        kwargs['chat_id'] = query.message.chat.id
        result = table.find_one(message_id=query.message.message_id,
                                chat_id=query.message.chat.id)
        if not result:
            result = templates.find_one(poll_id=data_dict['id'])
            result = dict(result)
            result.pop('id')
            result['message_id'] = query.message.message_id
            result['chat_id'] = query.message.chat.id
            result['votes'] = '{}'
    elif query.inline_message_id:
        kwargs['inline_message_id'] = query.inline_message_id
        result = table.find_one(inline_message_id=query.inline_message_id)
        if not result:
            result = templates.find_one(poll_id=data_dict['id'])
            result = dict(result)
            result.pop('id')
            result['inline_message_id'] = query.inline_message_id
            result['votes'] = '{}'

    poll = deserialize(result)
    uid_str = str(query.from_user.id)
    handler = POLL_TYPES_HANDLERS[poll['type']]

    handler.handle_vote(poll['votes'], uid_str, data_dict)

    query.answer(handler.get_confirmation_message(poll, uid_str))
    table.upsert(serialize(poll), ['inline_message_id', 'message_id', 'chat_id'])
    bot.edit_message_text(text=assemble_message_text(poll),
                          parse_mode='Markdown',
                          reply_markup=assemble_inline_keyboard(poll),
                          **kwargs)


# Help command handler
def help(bot, update):
    """Send a message when the command /help is issued."""
    update.message.reply_text('Oh no, there is no help! You are all alone!')


# Error handler
def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)


def main():
    """Start the bot."""
    # Create the EventHandler and pass it your bot's token.
    updater = Updater("TOKEN")

    # Conversation handler for creating polls

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', start),
                      MessageHandler(Filters.text, handle_title,
                                     pass_user_data=True)],
        states={
            NOT_ENGAGED: [CommandHandler('start', start),
                          MessageHandler(Filters.text, handle_title,
                                         pass_user_data=True)],
            TYPING_TITLE: [MessageHandler(Filters.text,
                                          handle_title,
                                          pass_user_data=True)],
            TYPING_TYPE: [RegexHandler(assemble_type_regex(),
                                       handle_type,
                                       pass_user_data=True)],
            TYPING_OPTION: [MessageHandler(Filters.text,
                                           handle_option,
                                           pass_user_data=True),
                            CommandHandler("done", handle_done,
                                           pass_user_data=True)]
        },
        fallbacks=[RegexHandler('^Done$', handle_done, pass_user_data=True)]
    )

    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    dp.add_handler(conv_handler)

    # on different commands - answer in Telegram
    dp.add_handler(CommandHandler("help", help))

    # Inline queries
    dp.add_handler(InlineQueryHandler(inline_query))

    # Callback queries from button presses
    dp.add_handler(CallbackQueryHandler(button))

    # log all errors
    dp.add_error_handler(error)

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
