#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" cancel_cmd.py """
""" Copyright 2018, Jogle Lew """
import helper_global
from telegram.ext import CommandHandler

def cancel(bot, update):
    chat_id = update.message.chat_id
    helper_global.assign(str(chat_id) + "_status", "0,0")
    help_text = helper_global.value("stop_comment_mode", "")
    bot.send_message(chat_id=chat_id, text=help_text)


_handler = CommandHandler('cancel', cancel)
