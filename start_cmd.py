#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" start_cmd.py """
""" Copyright 2018, Jogle Lew """
import helper_global
import helper_database
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler

def start(bot, update, args):
    if args is None or len(args) == 0:
        text = helper_global.value("start_cmd_text", "")
        bot.send_message(chat_id=update.message.chat_id, text=text)
        return
    params = args[0].split("_")
    channel_id = int(params[1])
    msg_id = int(params[2])
    chat_id = update.message.chat_id
    if params[0] == "add":
        helper_global.assign(str(chat_id) + "_status", params[1] + "," + params[2])
        bot.send_message(chat_id=update.message.chat_id, text=helper_global.value("start_comment_mode", ""))
    elif params[0] == "show":
        offset = 0
        config = helper_database.get_channel_config(channel_id)
        if config is None:
            return
        recent = config[3]

        # Prepare Keyboard
        motd_keyboard = [[
            InlineKeyboardButton(
                helper_global.value("prev_page", "Prev Page"),
                callback_data="msg,%d,%d,%d,%d,%d" % (channel_id, msg_id, recent, offset + 1, chat_id)
            ),
            InlineKeyboardButton(
                helper_global.value("next_page", "Next Page"),
                callback_data="msg,%d,%d,%d,%d,%d" % (channel_id, msg_id, recent, offset - 1, chat_id)
            )
        ]]
        motd_markup = InlineKeyboardMarkup(motd_keyboard)

        records = helper_database.get_recent_records(channel_id, msg_id, recent, offset)

        bot.send_message(
            chat_id=update.message.chat_id, 
            text=helper_global.records_to_str(records), 
            parse_mode=telegram.ParseMode.HTML,
            reply_markup=motd_markup
        )


_handler = CommandHandler('start', start, pass_args = True)
