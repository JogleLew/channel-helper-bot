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
    if chat_id < 0:
        return

    if helper_database.check_ban(channel_id, chat_id):
        bot.send_message(chat_id=update.message.chat_id, text=helper_global.value("banned_prompt", "You are banned."))
        return

    config = helper_database.get_channel_config(channel_id)
    if config is None:
        return
    recent, username = config[3], config[4]

    if params[0] == "add":
        helper_global.assign(str(chat_id) + "_status", params[1] + "," + params[2])
        if username is not None:
            bot.send_message(chat_id=update.message.chat_id, text=helper_global.value("start_comment_mode", "") + "\n" + helper_global.value("target_message", "") + "https://t.me/%s/%d" % (username, msg_id))
        else:
            bot.send_message(chat_id=update.message.chat_id, text=helper_global.value("start_comment_mode", ""))
    elif params[0] == "show":
        offset = 0
        channel_username = config[4]

        records = helper_database.get_recent_records(channel_id, msg_id, recent, offset)

        # Prepare Keyboard
        msg_buttons = helper_global.records_to_buttons(records, channel_id, msg_id)
        motd_keyboard = msg_buttons + [[
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

        prompt_text = helper_global.value("comment_header", "")
        if channel_username is not None and len(channel_username) > 0:
            prompt_text = "https://t.me/%s/%a\n" % (channel_username, msg_id) + prompt_text
        bot.send_message(
            chat_id=update.message.chat_id, 
            text=prompt_text, 
            parse_mode=telegram.ParseMode.HTML,
            reply_markup=motd_markup
        )


_handler = CommandHandler('start', start, pass_args=True)
