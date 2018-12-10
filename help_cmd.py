#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" help_cmd.py """
""" Copyright 2018, Jogle Lew """
import helper_global
from telegram.ext import CommandHandler

def help(bot, update):
    help_text = helper_global.value("help_cmd_text", "")
    bot.send_message(chat_id=update.message.chat_id, text=help_text)


_handler = CommandHandler('help', help)
