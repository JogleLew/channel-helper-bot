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

def option(bot, update):
    from_id = update.message.from_user.id
    chat_id = update.message.chat_id
    records = helper_database.get_channel_info_by_user(from_id)
    if records is None or len(records) == 0:
        bot.send_message(
            chat_id=chat_id, 
            text=helper_global.value("option_no_channel", "")
        )
        return

    #Prepare keyboard
    motd_keyboard = [[
        InlineKeyboardButton(
            "@" + record[1] if record[1] else "id: " + str(record[0]),
            callback_data="option,%s" % record[0]
        )
    ] for record in records] + [[
        InlineKeyboardButton(
            helper_global.value("option_finish", ""),
            callback_data="option_finish"
        )
    ]]

    motd_markup = InlineKeyboardMarkup(motd_keyboard)
    bot.send_message(
        chat_id=chat_id, 
        text=helper_global.value("option_choose_channel", ""),
        reply_markup=motd_markup
    )


_handler = CommandHandler('option', option)
