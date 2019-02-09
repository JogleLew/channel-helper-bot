#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" channel_msg.py """
""" Copyright 2018, Jogle Lew """
import helper_const
import helper_global
import helper_database
import telegram
from telegram.ext import MessageHandler, Filters, BaseFilter
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def add_comment(bot, chat_id, message_id):
    # Prepare Keyboard
    motd_keyboard = [[
        InlineKeyboardButton(
            helper_global.value("add_comment", "Add Comment"),
            url="http://telegram.me/%s?start=add_%d_%d" % (helper_global.value('bot_username', ''), chat_id, message_id)
        ),
        InlineKeyboardButton(
            helper_global.value("show_all_comments", "Show All"),
            url="http://telegram.me/%s?start=show_%s_%d" % (helper_global.value('bot_username', ''), chat_id, message_id)
        )
    ]]
    motd_markup = InlineKeyboardMarkup(motd_keyboard)

    config = helper_database.get_channel_config(chat_id)
    if config is None:
        return
    recent = config[3]
    records = helper_database.get_recent_records(chat_id, message_id, recent)

    comment_message = bot.send_message(
        chat_id=chat_id, 
        text=helper_global.records_to_str(records), 
        reply_to_message_id=message_id,
        reply_markup=motd_markup, 
        parse_mode=telegram.ParseMode.HTML
    ).result()
    helper_database.add_reflect(chat_id, message_id, comment_message.message_id)


def add_compact_comment(bot, chat_id, message_id):
    # Prepare Keyboard
    motd_keyboard = [[
        InlineKeyboardButton(
            helper_global.value("add_comment", "Add Comment"),
            url="http://telegram.me/%s?start=add_%d_%d" % (helper_global.value('bot_username', ''), chat_id, message_id)
        ), 
        InlineKeyboardButton(
            helper_global.value("show_all_comments", "Show All"),
            url="http://telegram.me/%s?start=show_%s_%d" % (helper_global.value('bot_username', ''), chat_id, message_id)
        )
    ]]
    motd_markup = InlineKeyboardMarkup(motd_keyboard)

    try:
        bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=motd_markup
        ).result()
    except:
        add_comment(bot, chat_id, message_id)


def channel_post_msg(bot, update):
    message = update.channel_post
    # print("Channel ID: %d, Channel Username: %s" % (message.chat_id, message.chat.username))
    chat_id = message.chat_id
    message_id = message.message_id
    config = helper_database.get_channel_config(chat_id)
    if config is None:
        return
    lang, mode, recent = config[1], config[2], config[3]

    # Auto Comment Mode
    if mode == 1: 
        add_comment(bot, chat_id, message_id)
    elif mode == 2:
        add_compact_comment(bot, chat_id, message_id)

    # Manual Mode
    elif mode == 0 and message.reply_to_message is not None and message.text == "/comment":
        message_id = message.reply_to_message.message_id
        bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        add_compact_comment(bot, chat_id, message_id)


class FilterChannelPost(BaseFilter):
    def filter(self, message):
        return message.chat.type == "channel"


channel_post_filter = FilterChannelPost()
_handler = MessageHandler(channel_post_filter, channel_post_msg)
