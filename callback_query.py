#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" callback_query.py """
""" Copyright 2018, Jogle Lew """
import helper_const
import helper_global
import helper_database
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackQueryHandler

def show_msg(bot, update, origin_message_id, chat_id, args):
    channel_id = int(args[1])
    msg_id = int(args[2])
    recent = int(args[3])
    offset = int(args[4])
    ori_chat_id = int(args[5])

    if offset < 0:
        bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            text=helper_global.value("no_next_page", "")
        )
        return

    # Prepare Keyboard
    motd_keyboard = [[
        InlineKeyboardButton(
            helper_global.value("prev_page", "Prev Page"),
            callback_data="msg,%d,%d,%d,%d,%d" % (channel_id, msg_id, recent, offset + 1, ori_chat_id)
        ),
        InlineKeyboardButton(
            helper_global.value("next_page", "Next Page"),
            callback_data="msg,%d,%d,%d,%d,%d" % (channel_id, msg_id, recent, offset - 1, ori_chat_id)
        )
    ]]
    motd_markup = InlineKeyboardMarkup(motd_keyboard)
    records = helper_database.get_recent_records(channel_id, msg_id, recent, offset)

    if offset > 0 and len(records) == 0:
        bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            text=helper_global.value("no_prev_page", "")
        )
        return

    bot.edit_message_text(
        chat_id=ori_chat_id, 
        message_id=origin_message_id,
        text=helper_global.records_to_str(records), 
        parse_mode=telegram.ParseMode.HTML,
        reply_markup=motd_markup
    )


def option_fiinish(bot, chat_id, origin_message_id):
    bot.edit_message_text(
        chat_id=chat_id, 
        message_id=origin_message_id,
        text=helper_global.value("option_finished", "") 
    )


def option_item(bot, chat_id, origin_message_id, args):
    # Prepare Keyboard
    motd_keyboard = [[
        InlineKeyboardButton(
            "mode",
            callback_data="option,%s,mode" % args[1]
        ),
        InlineKeyboardButton(
            "recent",
            callback_data="option,%s,recent" % args[1]
        )
    ]] + [[
        InlineKeyboardButton(
            helper_global.value("option_finish", ""),
            callback_data="option_finish"
        )
    ]]

    motd_markup = InlineKeyboardMarkup(motd_keyboard)

    bot.edit_message_text(
        chat_id=chat_id, 
        message_id=origin_message_id,
        text=helper_global.value("option_choose_item", ""),
        reply_markup=motd_markup
    )


def option_mode(bot, chat_id, origin_message_id, args):
    # Prepare Keyboard
    motd_keyboard = [[
        InlineKeyboardButton(
            "0",
            callback_data="option,%s,mode,0" % args[1]
        ),
        InlineKeyboardButton(
            "1",
            callback_data="option,%s,mode,1" % args[1]
        )
    ]] + [[
        InlineKeyboardButton(
            helper_global.value("option_finish", ""),
            callback_data="option_finish"
        )
    ]]

    motd_markup = InlineKeyboardMarkup(motd_keyboard)

    bot.edit_message_text(
        chat_id=chat_id, 
        message_id=origin_message_id,
        text=helper_global.value("option_choose_mode_value", ""),
        reply_markup=motd_markup
    )

    
def option_recent(bot, chat_id, origin_message_id, args):
    # Prepare Keyboard
    motd_keyboard = [[
        InlineKeyboardButton(
            "5",
            callback_data="option,%s,recent,5" % args[1]
        ),
        InlineKeyboardButton(
            "10",
            callback_data="option,%s,recent,10" % args[1]
        ),
        InlineKeyboardButton(
            "15",
            callback_data="option,%s,recent,15" % args[1]
        ),
        InlineKeyboardButton(
            "20",
            callback_data="option,%s,recent,20" % args[1]
        )
    ]] + [[
        InlineKeyboardButton(
            helper_global.value("option_finish", ""),
            callback_data="option_finish"
        )
    ]]

    motd_markup = InlineKeyboardMarkup(motd_keyboard)

    bot.edit_message_text(
        chat_id=chat_id, 
        message_id=origin_message_id,
        text=helper_global.value("option_choose_recent_value", ""),
        reply_markup=motd_markup
    )


def option_update(bot, update, chat_id, origin_message_id, args):
    try:
        helper_database.update_config_by_channel(args[1], args[2], args[3])
        bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            text=helper_global.value("option_update_success", "")
        )
    except:
        bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            text=helper_global.value("option_update_failed", "")
        )
    option_item(bot, chat_id, origin_message_id, args)


def callback_query(bot, update):
    callback_data = update.callback_query.data
    origin_message_id = update.callback_query.message.message_id
    chat_id = update.callback_query.message.chat_id
    args = callback_data.split(',')
    if args[0] == 'msg':
        show_msg(bot, update, origin_message_id, chat_id, args);
    elif args[0] == 'option_finish':
        option_fiinish(bot, chat_id, origin_message_id)
    elif args[0] == 'option':
        if len(args) == 2:
            option_item(bot, chat_id, origin_message_id, args)
        elif len(args) == 3 and args[2] == "mode":
            option_mode(bot, chat_id, origin_message_id, args)
        elif len(args) == 3 and args[2] == "recent":
            option_recent(bot, chat_id, origin_message_id, args)
        elif len(args) == 4:
            option_update(bot, update, chat_id, origin_message_id, args)


_handler = CallbackQueryHandler(callback_query)
