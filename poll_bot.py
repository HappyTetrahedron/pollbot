#!/usr/bin/env python
# -*- coding: utf-8 -*-
import random
from uuid import uuid4

import yaml
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
import open_poll_handler
import custom_description_poll_handler
import stv_poll_handler
import custom_description_open_poll_handler
import custom_description_instant_runoff_poll_handler
import multiple_options_poll_handler
import open_multiple_options_poll_handler
import doodle_poll_handler


POLL_TYPE_BASIC, \
    POLL_TYPE_SET, \
    POLL_TYPE_INSTANT_RUNOFF, \
    POLL_TYPE_INSTANT_RUNOFF_TIE_BREAK, \
    POLL_TYPE_OPEN, \
    POLL_TYPE_CUSTOM_DESCRIPTION,\
    POLL_TYPE_STV,\
    POLL_TYPE_OPEN_CUSTOM_DESCRIPTION,\
    POLL_TYPE_INSTANT_RUNOFF_CUSTOM_DESCRIPTION,\
    POLL_TYPE_MULTIPLE_OPTIONS,\
    POLL_TYPE_OPEN_MULTIPLE_OPTIONS, \
    POLL_TYPE_DOODLE = range(12)

POLL_HANDLERS = {
    POLL_TYPE_BASIC: basic_poll_handler,
    POLL_TYPE_SET: set_poll_handler,
    POLL_TYPE_INSTANT_RUNOFF: instant_runoff_poll_handler,
    POLL_TYPE_INSTANT_RUNOFF_TIE_BREAK: tie_break_instant_runoff_poll_handler,
    POLL_TYPE_OPEN: open_poll_handler,
    POLL_TYPE_CUSTOM_DESCRIPTION: custom_description_poll_handler,
    POLL_TYPE_STV: stv_poll_handler,
    POLL_TYPE_OPEN_CUSTOM_DESCRIPTION: custom_description_open_poll_handler,
    POLL_TYPE_INSTANT_RUNOFF_CUSTOM_DESCRIPTION: custom_description_instant_runoff_poll_handler,
    POLL_TYPE_MULTIPLE_OPTIONS: multiple_options_poll_handler,
    POLL_TYPE_OPEN_MULTIPLE_OPTIONS: open_multiple_options_poll_handler,
    POLL_TYPE_DOODLE: doodle_poll_handler,
}


logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


# Conversation states:
NOT_ENGAGED, TYPING_TITLE, TYPING_TYPE, TYPING_OPTION, TYPING_META = range(5)

AFFIRMATIONS = [
    "Cool",
    "Nice",
    "Doing great",
    "Awesome",
    "Okey dokey",
    "Neat",
    "Whoo",
    "Wonderful",
    "Splendid",
]


class PollBot:
    def __init__(self):
        self.db = None

    # Conversation handlers:
    def start(self, bot, update):
        """Send a message when the command /start is issued."""
        update.message.reply_text('Hi! Please send me the title of your poll. (/cancel to exit)')

        return TYPING_TITLE

    def handle_type(self, bot, update, user_data):
        text = update.message.text
        polltype = next((i for i, handler in POLL_HANDLERS.items() if handler.name == text), None)
        user_data['type'] = polltype
        user_data['options'] = []
        user_data['meta'] = dict()

        if POLL_HANDLERS[polltype].requires_extra_config(user_data['meta']):
            update.message.reply_text(POLL_HANDLERS[polltype].ask_for_extra_config(user_data.get('meta')))
            return TYPING_META
        else:
            update.message.reply_text("{}. Now, send me the first answer option. (or /cancel)".format(self.get_affirmation()))
            return TYPING_OPTION

    def handle_title(self, bot, update, user_data):
        text = update.message.text
        user_data['title'] = text
        update.message.reply_text("{}! What kind of poll is it going to be? (/cancel to shut me up)"
                                  .format(self.get_affirmation()),
                                  reply_markup=self.assemble_reply_keyboard())

        return TYPING_TYPE

    def handle_option(self, bot, update, user_data):
        text = update.message.text
        handler = POLL_HANDLERS[user_data['type']]
        user_data['options'].append(text)

        if len(user_data['options']) >= handler.max_options:
            return self.handle_done(bot, update, user_data)

        update.message.reply_text("{}! Now, send me another answer option or type /done to publish."
                                  .format(self.get_affirmation()),
                                  reply_markup=ReplyKeyboardRemove())

        if len(user_data['options']) >= handler.max_options - 1:
            update.message.reply_text("Uh oh, you're running out of options. You can only have one more option.")

        return TYPING_OPTION

    def handle_meta(self, bot, update, user_data):
        text = update.message.text
        polltype = user_data['type']
        POLL_HANDLERS[polltype].register_extra_config(text, user_data.get('meta'))
        if POLL_HANDLERS[polltype].requires_extra_config(user_data.get('meta')):
            update.message.reply_text(POLL_HANDLERS[polltype].ask_for_extra_config(user_data.get('meta')))
            return TYPING_META
        else:
            update.message.reply_text("{}, that's it! Next, please send me the first answer option."
                                      .format(self.get_affirmation()))
            return TYPING_OPTION

    def handle_done(self, bot, update, user_data):
        update.message.reply_text("Thanks man! Now here is your fine poll:")
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
            'options': options,
            'meta': user_data.get('meta'),
        }

        table = self.db['setpolls']

        table.insert(self.serialize(poll))

        update.message.reply_text(self.assemble_message_text(poll),
                                  reply_markup=self.assemble_inline_keyboard(poll, True),
                                  parse_mode='Markdown'
                                  )

        user_data.clear()

        return NOT_ENGAGED

    def get_affirmation(self):
        return random.choice(AFFIRMATIONS)

    def assemble_reply_keyboard(self):
        keyboard = []
        for _, val in POLL_HANDLERS.items():
            keyboard.append([val.name])

        return ReplyKeyboardMarkup(
            keyboard,
            one_time_keyboard=True
        )

    def assemble_type_regex(self):
        orclause = '|'.join([handler.name for handler in POLL_HANDLERS.values()])
        regex = '^({})$'.format(orclause)
        return regex

    def assemble_inline_keyboard(self, poll, include_publish_button=False):
        inline_keyboard_items = self.get_inline_keyboard_items(poll)
        if include_publish_button:
            publish_button = InlineKeyboardButton("Publish!",
                                                  switch_inline_query=poll['poll_id'])
            inline_keyboard_items.append([publish_button])

        return InlineKeyboardMarkup(inline_keyboard_items)

    def get_inline_keyboard_items(self, poll):
        handler = POLL_HANDLERS[poll['type']]
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

    def assemble_message_text(self, poll):
        handler = POLL_HANDLERS[poll['type']]
        message = '{}\n{}'.format(handler.title(poll),
                                  handler.evaluation(poll))
        return message

    def serialize(self, poll):
        ser = dict(poll)
        ser['options'] = json.dumps(poll['options'])
        if 'votes' in ser:
            ser['votes'] = json.dumps(poll['votes'])
        if 'meta' in ser:
            ser['meta'] = json.dumps(poll['meta'])
        return ser

    def deserialize(self, serialized):
        poll = dict(serialized)
        poll['options'] = json.loads(serialized['options'])
        if 'votes' in poll:
            poll['votes'] = json.loads(serialized['votes'])
        if 'meta' in poll:
            meta = serialized['meta']
            poll['meta'] = "" if meta is None else json.loads(meta)
        return poll

    # Inline query handler
    def inline_query(self, bot, update):
        query = update.inline_query.query

        table = self.db['setpolls']
        result = list(table.find(poll_id=query))
        if not result:
            table = self.db['setpolls'].table
            statement = table.select(table.c.title.like('%{}%'.format(query)))
            result = list(self.db.query(statement))

            if not result:
                update.inline_query.answer(results=[],
                                           switch_pm_text="Create a new poll",
                                           switch_pm_parameter="start")
                return

        inline_results = []
        for res in result:
            poll = self.deserialize(res)
            inline_results.append(
                InlineQueryResultArticle(
                    id=poll['poll_id'],
                    title=poll['title'],
                    input_message_content=InputTextMessageContent(
                        message_text=self.assemble_message_text(poll),
                        parse_mode='Markdown'
                    ),
                    reply_markup=self.assemble_inline_keyboard(poll)
                )
            )
        update.inline_query.answer(inline_results)

    # Inline button press handler
    def button(self, bot, update):
        query = update.callback_query
        data_dict = json.loads(update.callback_query.data)

        table = self.db['setpoll_instances']
        templates = self.db['setpolls']

        kwargs = {}
        include_publish_button = False
        if query.message:
            if query.message.from_user.bot == bot:
                include_publish_button = True

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

        poll = self.deserialize(result)
        uid_str = str(query.from_user.id)
        name = str(query.from_user.first_name)
        handler = POLL_HANDLERS[poll['type']]

        handler.handle_vote(poll['votes'], uid_str, name, data_dict)

        query.answer(handler.get_confirmation_message(poll, uid_str))
        table.upsert(self.serialize(poll), ['inline_message_id', 'message_id', 'chat_id'])
        bot.edit_message_text(text=self.assemble_message_text(poll),
                              parse_mode='Markdown',
                              reply_markup=self.assemble_inline_keyboard(poll, include_publish_button),
                              **kwargs)

    # Help command handler
    def send_help(self, bot, update):
        """Send a message when the command /help is issued."""
        helptext = "I'm a poll bot! I can do polls!\n\n" \
                   "Start by typing /start or by directly " \
                   "sending me the title of your poll. I " \
                   "will then help you to construct a wonderful " \
                   "poll suited for your purpose. \n\n" \
                   "There are a multitude of poll types available. " \
                   "Here I have a description of each: \n\n"

        for poll in POLL_HANDLERS.values():
            helptext += "*{}*: _{}_\n".format(
                poll.name,
                poll.desc
            )

        update.message.reply_text(helptext, parse_mode="Markdown")

    def cancel(self, bot, update):
        update.message.reply_text("Oh, too bad. Maybe next time!",
                                  reply_markup=ReplyKeyboardRemove())
        return NOT_ENGAGED

    # Error handler
    def error(self, bot, update, error):
        """Log Errors caused by Updates."""
        logger.warning('Update "%s" caused error "%s"', update, error)

    def run(self, opts):
        with open(opts.config, 'r') as configfile:
            config = yaml.load(configfile)

        self.db = dataset.connect('sqlite:///{}'.format(config['db']))

        """Start the bot."""
        # Create the EventHandler and pass it your bot's token.
        updater = Updater(config['token'], use_context=False)

        # Conversation handler for creating polls

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start),
                          MessageHandler(Filters.text, self.handle_title,
                                         pass_user_data=True)],
            states={
                NOT_ENGAGED: [CommandHandler('start', self.start),
                              MessageHandler(Filters.text, self.handle_title,
                                             pass_user_data=True),
                              CommandHandler('cancel', self.cancel)],
                TYPING_TITLE: [MessageHandler(Filters.text,
                                              self.handle_title,
                                              pass_user_data=True),
                               CommandHandler('cancel', self.cancel)],
                TYPING_TYPE: [RegexHandler(self.assemble_type_regex(),
                                           self.handle_type,
                                           pass_user_data=True),
                              CommandHandler('cancel', self.cancel)],
                TYPING_META: [MessageHandler(Filters.text,
                                             self.handle_meta,
                                             pass_user_data=True),
                              CommandHandler('cancel', self.cancel)],
                TYPING_OPTION: [MessageHandler(Filters.text,
                                               self.handle_option,
                                               pass_user_data=True),
                                CommandHandler("done", self.handle_done,
                                               pass_user_data=True),
                                CommandHandler('cancel', self.cancel)]
            },
            fallbacks=[RegexHandler('^Done$', self.handle_done, pass_user_data=True)]
        )

        # Get the dispatcher to register handlers
        dp = updater.dispatcher
        dp.add_handler(conv_handler)

        # on different commands - answer in Telegram
        dp.add_handler(CommandHandler("help", self.send_help))

        # Inline queries
        dp.add_handler(InlineQueryHandler(self.inline_query))

        # Callback queries from button presses
        dp.add_handler(CallbackQueryHandler(self.button))

        # log all errors
        dp.add_error_handler(self.error)

        # Start the Bot
        updater.start_polling()

        # Run the bot until you press Ctrl-C or the process receives SIGINT,
        # SIGTERM or SIGABRT. This should be used most of the time, since
        # start_polling() is non-blocking and will stop the bot gracefully.
        updater.idle()


def main(opts):
    PollBot().run(opts)


if __name__ == '__main__':
    from optparse import OptionParser
    parser = OptionParser()
    parser.add_option('-c', '--config', dest='config', default='config.yml', type='string', help="Path of configuration file")
    (opts, args) = parser.parse_args()
    main(opts)
