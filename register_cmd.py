#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" register_cmd.py """
""" Copyright 2018, Jogle Lew """
import helper_const
import helper_global
import helper_database
from telegram.ext import CommandHandler

def register(bot, update):
    from_id = update.message.from_user.id
    chat_id = update.message.chat_id
    helper_global.assign(str(from_id) + "_status", "0,1")
    bot.send_message(chat_id=chat_id, text=helper_global.value("register_cmd_text", ""))


_handler = CommandHandler('register', register)
