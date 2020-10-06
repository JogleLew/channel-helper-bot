#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" start_cmd.py """
""" Copyright 2018, Jogle Lew """
import helper_const
import helper_global
import helper_database
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler
from ninesix import Logger

def start(bot, update, args):
    logger = Logger.logger
    if args is None or len(args) == 0:
        chat_id = update.message.chat_id
        logger.msg({"user_id": chat_id}, tag="start", log_level=80)
        helper_global.send_intro_template(bot, chat_id, helper_const.DEFAULT_LANG, "start", "start_cmd_text")
        return

    params = args[0].split("_")
    channel_id = int(params[1])
    msg_id = int(params[2])
    chat_id = update.message.chat_id
    logger.msg({"user_id": chat_id, "args": args}, tag="start", log_level=90)
    if chat_id < 0:
        return

    config = helper_database.get_channel_config(channel_id)
    if config is None:
        return
    channel_lang = config[1]
    recent, username = config[3], config[4]

    if helper_database.check_ban(channel_id, chat_id):
        bot.send_message(chat_id=update.message.chat_id, text=helper_global.value("banned_prompt", "You are banned.", lang=channel_lang))
        return

    if params[0] == "add":
        helper_global.assign(str(chat_id) + "_status", params[1] + "," + params[2])
        motd_keyboard = [[
            InlineKeyboardButton(
                helper_global.value("reply_to", "Reply", lang=channel_lang) + "...",
                switch_inline_query_current_chat=" "
            )
        ]]
        motd_markup = InlineKeyboardMarkup(motd_keyboard)
        if username is not None:
            bot.send_message(
                chat_id=update.message.chat_id, 
                text=helper_global.value("start_comment_mode", "", lang=channel_lang) + "\n" + helper_global.value("target_message", "", lang=channel_lang) + "https://t.me/%s/%d" % (username, msg_id),
                reply_markup=motd_markup
            )
        else:
            link_id = abs(channel_id) % 10000000000
            bot.send_message(
                chat_id=update.message.chat_id, 
                text=helper_global.value("start_comment_mode", "", lang=channel_lang) + "\n" + helper_global.value("target_message", "", lang=channel_lang) + "https://t.me/c/%d/%d" % (link_id, msg_id),
                reply_markup=motd_markup
            )
    elif params[0] == "show":
        offset = 0
        channel_username = config[4]

        records = helper_database.get_recent_records(channel_id, msg_id, recent, offset)

        # Prepare Keyboard
        msg_buttons = helper_global.records_to_buttons(records, channel_id, msg_id)
        motd_keyboard = msg_buttons + [[
            InlineKeyboardButton(
                helper_global.value("prev_page", "Prev Page", lang=channel_lang),
                callback_data="msg,%d,%d,%d,%d,%d" % (channel_id, msg_id, recent, offset + 1, chat_id)
            ),
            InlineKeyboardButton(
                helper_global.value("next_page", "Next Page", lang=channel_lang),
                callback_data="msg,%d,%d,%d,%d,%d" % (channel_id, msg_id, recent, offset - 1, chat_id)
            )
        ]]
        motd_markup = InlineKeyboardMarkup(motd_keyboard)

        prompt_text = helper_global.value("comment_header", "", lang=channel_lang)
        if channel_username is not None and len(channel_username) > 0:
            prompt_text = "https://t.me/%s/%a\n" % (channel_username, msg_id) + prompt_text
        bot.send_message(
            chat_id=update.message.chat_id, 
            text=prompt_text, 
            parse_mode=telegram.ParseMode.HTML,
            reply_markup=motd_markup
        )


_handler = CommandHandler('start', start, pass_args=True)
