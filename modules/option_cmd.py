#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" option_cmd.py """
""" Copyright 2018, Jogle Lew """
import helper_const
import helper_global
import helper_database
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler
from ninesix import Logger

def option(bot, update, args):
    logger = Logger.logger
    if args is None or len(args) == 0:
        lang = helper_const.DEFAULT_LANG
    else:
        lang = args[0]
    chat_id = update.message.chat_id
    logger.msg({
        "user_id": chat_id
    }, tag="option", log_level=80)
    records = helper_database.get_channel_info_by_user(chat_id)
    if records is None or len(records) == 0:
        helper_global.send_intro_template(bot, chat_id, helper_const.DEFAULT_LANG, "option_no_channel", "option_no_channel")
        return

    #Prepare keyboard
    lang_list = helper_const.LANG_LIST
    width = helper_const.LANG_WIDTH
    current_lang = lang
    key = "option"
    motd_keyboard = [[
        InlineKeyboardButton(
            "@" + record[1] if record[1] else "id: " + str(record[0]),
            callback_data="option|%s,%s" % (lang, record[0])
        )
    ] for record in records] + [[
        InlineKeyboardButton(
            helper_global.value("option_finish", "", lang),
            callback_data="option_finish|%s" % lang
        )
    ]] + [[
        InlineKeyboardButton(
            lang_list[width * idx + delta] + (" (*)" if lang_list[width * idx + delta] == current_lang else ""),
            callback_data="%s|%s" % (key, lang_list[width * idx + delta])
        ) for delta in range(width)
    ] for idx in range(len(lang_list) // width)] + [[
        InlineKeyboardButton(
            lang_list[idx] + (" (*)" if lang_list[idx] == current_lang else ""),
            callback_data="%s|%s" % (key, lang_list[idx])
        )
    for idx in range(width * (len(lang_list) // width), len(lang_list))]]

    motd_markup = InlineKeyboardMarkup(motd_keyboard)
    bot.send_message(
        chat_id=chat_id, 
        text=helper_global.value("option_choose_channel", "", lang=lang),
        reply_markup=motd_markup
    )


_handler = CommandHandler('option', option, pass_args=True)
