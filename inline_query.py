#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" inline_query.py """
""" Copyright 2020, Jogle Lew """
import re
import helper_const
import helper_global
import helper_database
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram import InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import InlineQueryHandler
from ninesix import Logger

def inline_caps(bot, update):
    user_id = update.inline_query.from_user.id
    args = helper_global.value(str(user_id) + "_status", "0,0")
    params = args.split(",")
    channel_id = int(params[0])
    msg_id = int(params[1])

    if channel_id == 0:
        bot.answer_inline_query(update.inline_query.id, [])
        return

    config = helper_database.get_channel_config(channel_id)
    if config is None:
        bot.answer_inline_query(update.inline_query.id, [])
        return
    channel_lang = config[1]
    recent = config[3]

    query = update.inline_query.query
    if len(query.strip()) == 0:
        bot.answer_inline_query(
            update.inline_query.id, [], 
            switch_pm_text=helper_global.value("reply_prompt", "comment here first", lang=channel_lang), 
            switch_pm_parameter="0", 
            cache_time=0, 
            is_personal=True
        )
        return

    records = helper_database.get_recent_records(channel_id, msg_id, recent, 0)
    results = []
    for idx, record in enumerate(records):
        name = record[3]
        content = record[5]
        msg_user_id = record[8]
        row_id = int(record[10])
        results.append(
            InlineQueryResultArticle(
                id=idx,
                title=name,
                description=re.sub("<.*?>", "", content).replace('&lt;', '<').replace('&gt;', '>'),
                input_message_content=InputTextMessageContent(
                    message_text= query.replace('<', '&lt;').replace('>', '&gt;'),
                    parse_mode='HTML'
                ),
                reply_markup=InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        helper_global.value("reply_to", "Reply to: ", lang=channel_lang) + name,
                        callback_data="notify,%d,%d,%d" % (channel_id, msg_id, row_id)
                    )
                ]])
            )
        )
    bot.answer_inline_query(
            update.inline_query.id, results,
            switch_pm_text=helper_global.value("reply_prompt", "comment here first", lang=channel_lang), 
            switch_pm_parameter="0", 
            cache_time=0, 
            is_personal=True
    )

_handler = InlineQueryHandler(inline_caps)

