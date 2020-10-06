#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" help_cmd.py """
""" Copyright 2018, Jogle Lew """
import helper_const
import helper_global
from telegram.ext import CommandHandler
from ninesix import Logger

def help(bot, update):
    logger = Logger.logger
    chat_id = update.message.chat_id
    logger.msg({
        "user_id": chat_id
    }, tag="help", log_level=80)
    helper_global.send_intro_template(bot, chat_id, helper_const.DEFAULT_LANG, "help", "help_cmd_text")


_handler = CommandHandler('help', help)
