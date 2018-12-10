#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" sql_cmd.py """
""" Copyright 2018, Jogle Lew """
import helper_const
import helper_global
import helper_database
from telegram.ext import CommandHandler

def sql(bot, update, args):
    from_id = update.message.from_user.id
    if not from_id in helper_const.BOT_OWNER:
        return
    script = " ".join(args)
    text = ""
    try:
        result = helper_database.execute(script, ())
        text = "执行成功，结果:\n" + str(list(result))
    except Exception as e:
        text = "执行失败 " + str(e)
    bot.send_message(chat_id=update.message.chat_id, text=text)


_handler = CommandHandler('sql', sql, pass_args=True)
