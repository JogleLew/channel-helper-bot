#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" option_cmd.py """
""" Copyright 2018, Jogle Lew """
import helper_const
import helper_global
import helper_database
import telegram
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler

def option(bot, update, args):
    if args is None or len(args) == 0:
        lang = helper_const.DEFAULT_LANG
    else:
        lang = args[0]
    chat_id = update.message.chat_id
    records = helper_database.get_channel_info_by_user(chat_id)
    if records is None or len(records) == 0:
        bot.send_message(
            chat_id=chat_id, 
            text=helper_global.value("option_no_channel", "", lang="all")
        )
        return

    #Prepare keyboard
    motd_keyboard = [[
        InlineKeyboardButton(
            "@" + record[1] if record[1] else "id: " + str(record[0]),
            callback_data="option|%s,%s" % (lang, record[0])
        )
    ] for record in records] + [[
        InlineKeyboardButton(
            lang,
            callback_data="option|%s" % lang
        )
    for lang in helper_const.LANG_LIST]] + [[
        InlineKeyboardButton(
            helper_global.value("option_finish", "", lang),
            callback_data="option_finish|%s" % lang
        )
    ]]

    motd_markup = InlineKeyboardMarkup(motd_keyboard)
    bot.send_message(
        chat_id=chat_id, 
        text=helper_global.value("option_choose_channel", "", lang=lang),
        reply_markup=motd_markup
    )


_handler = CommandHandler('option', option, pass_args=True)
