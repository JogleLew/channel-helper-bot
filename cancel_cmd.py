#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" cancel_cmd.py """
""" Copyright 2018, Jogle Lew """
import helper_global
import helper_database
from telegram.ext import CommandHandler

def cancel(bot, update):
    chat_id = update.message.chat_id
    channel_id = helper_global.value(str(chat_id) + "_status", "0,0").split(",")[0]
    config = helper_database.get_channel_config(channel_id)
    if config is None:
        lang = "all"
    else:
        lang = config[1]
    helper_global.assign(str(chat_id) + "_status", "0,0")
    help_text = helper_global.value("stop_comment_mode", "", lang=lang)
    bot.send_message(chat_id=chat_id, text=help_text)


_handler = CommandHandler('cancel', cancel)
