#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" callback_query.py """
""" Copyright 2018, Jogle Lew """
import helper_const
import helper_global
import helper_database
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, \
        InputMediaAudio, InputMediaDocument, InputMediaPhoto, InputMediaVideo
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

    config = helper_database.get_channel_config(channel_id)
    if config is None:
        return
    channel_username = config[4]

    records = helper_database.get_recent_records(channel_id, msg_id, recent, offset)

    # Prepare Keyboard
    msg_buttons = helper_global.records_to_buttons(records, channel_id, msg_id)
    motd_keyboard = msg_buttons + [[
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

    if offset > 0 and len(records) == 0:
        bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            text=helper_global.value("no_prev_page", "")
        )
        return

    prompt_text = helper_global.value("comment_header", "")
    if channel_username is not None and len(channel_username) > 0:
        prompt_text = "https://t.me/%s/%a\n" % (channel_username, msg_id) + prompt_text
    bot.send_message(
        chat_id=ori_chat_id, 
        text=prompt_text, 
        parse_mode=telegram.ParseMode.HTML,
        reply_markup=motd_markup
    )
    bot.delete_message(
        chat_id=chat_id, 
        message_id=origin_message_id
    )


def msg_detail(bot, update, chat_id, origin_message_id, args):
    channel_id = int(args[1])
    msg_id = int(args[2])
    row_id = int(args[3])

    if row_id < 0:
        bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            text=helper_global.value("no_message_detail", "No Message")
        )
        return

    records = helper_database.get_record_by_rowid(row_id)

    if records is None or len(records) == 0:
        bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            text=helper_global.value("no_message_detail", "No Message")
        )
        return

    record = records[0]

    username = record[2]
    name = record[3]
    msg_type = record[4]
    msg_content = record[5]
    media_id= record[6]

    config = helper_database.get_channel_config(channel_id)
    if config is None:
        return
    recent = config[3]
    base_offset = helper_database.get_base_offset_by_rowid(channel_id, msg_id, row_id)
    offset = base_offset // recent

    motd_keyboard = [
        [
            InlineKeyboardButton(
                helper_global.value("msg_from", "Message From: ") + name,
                callback_data="123"
            )
        ],
        [
            InlineKeyboardButton(
                helper_global.value("prev_msg", "Prev Message"),
                callback_data="msg_detail,%d,%d,%d" % (channel_id, msg_id, helper_database.get_next_rowid(channel_id, msg_id, row_id))
            ),
            InlineKeyboardButton(
                helper_global.value("next_msg", "Next Message"),
                callback_data="msg_detail,%d,%d,%d" % (channel_id, msg_id, helper_database.get_prev_rowid(channel_id, msg_id, row_id))
            )
        ],
        [
            InlineKeyboardButton(
                helper_global.value("back_to_msg_list", "Back to message list"),
                callback_data="msg,%d,%d,%d,%d,%d" % (channel_id, msg_id, recent, offset, chat_id)
            )
        ]
    ]
    motd_markup = InlineKeyboardMarkup(motd_keyboard)

    if msg_type == "text":
        bot.send_message(
            chat_id=chat_id, 
            message_id=origin_message_id,
            text=msg_content,
            parse_mode='HTML',
            reply_markup=motd_markup
        )
        bot.delete_message(
            chat_id=chat_id, 
            message_id=origin_message_id
        )
    elif msg_type == "audio" or msg_type == "document" or msg_type == "photo" or msg_type == "video" or msg_type == "sticker" or msg_type == "voice":
        send_func = {
            "audio": bot.send_audio,
            "document": bot.send_document,
            "photo": bot.send_photo,
            "video": bot.send_video,
            "sticker": bot.send_sticker,
            "voice": bot.send_voice
        }
        send_func[msg_type](
            chat_id, 
            media_id,
            caption=msg_content,
            parse_mode='HTML',
            reply_markup=motd_markup
        )
        bot.delete_message(
            chat_id=chat_id, 
            message_id=origin_message_id
        )
    else:
        bot.send_message(
            chat_id=chat_id, 
            message_id=origin_message_id,
            text="[%s] %s" % (msg_type, msg_content),
            parse_mode='HTML',
            reply_markup=motd_markup
        )
        bot.delete_message(
            chat_id=chat_id, 
            message_id=origin_message_id
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
            helper_global.value("option_delete", ""),
            callback_data="option_delete,%s" % args[1]
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
        ),
        InlineKeyboardButton(
            "2",
            callback_data="option,%s,mode,2" % args[1]
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


def option_delete(bot, chat_id, origin_message_id, args):
    channel_id = args[1]
    helper_database.delete_channel_config(channel_id)
    bot.edit_message_text(
        chat_id=chat_id, 
        message_id=origin_message_id,
        text=helper_global.value("option_record_deleted", "")
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
        show_msg(bot, update, origin_message_id, chat_id, args)
    elif args[0] == 'msg_detail':
        msg_detail(bot, update, chat_id, origin_message_id, args)
    elif args[0] == 'option_delete':
        option_delete(bot, chat_id, origin_message_id, args)
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
