#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" register_cmd.py """
""" Copyright 2018, Jogle Lew """
import helper_const
import helper_global
import helper_database
from telegram.ext import CommandHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from ninesix import Logger

def register(bot, update):
    logger = Logger.logger
    from_id = update.message.from_user.id
    chat_id = update.message.chat_id
    logger.msg({"user_id": from_id}, tag="register", log_level=80)
    helper_global.assign(str(from_id) + "_status", "0,1")
    helper_global.send_intro_template(bot, chat_id, helper_const.DEFAULT_LANG, "register", "register_cmd_text")


_handler = CommandHandler('register', register)
