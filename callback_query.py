#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" callback_query.py """
""" Copyright 2018, Jogle Lew """
import helper_const
import helper_global
import helper_database
import option_cmd
import private_msg
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

    config = helper_database.get_channel_config(channel_id)
    if config is None:
        return
    channel_lang = config[1]
    channel_username = config[4]

    if offset < 0:
        bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            text=helper_global.value("no_next_page", "", lang=channel_lang)
        )
        return

    records = helper_database.get_recent_records(channel_id, msg_id, recent, offset)

    # Prepare Keyboard
    msg_buttons = helper_global.records_to_buttons(records, channel_id, msg_id)
    motd_keyboard = msg_buttons + [[
        InlineKeyboardButton(
            helper_global.value("prev_page", "Prev Page", lang=channel_lang),
            callback_data="msg,%d,%d,%d,%d,%d" % (channel_id, msg_id, recent, offset + 1, ori_chat_id)
        ),
        InlineKeyboardButton(
            helper_global.value("next_page", "Next Page", lang=channel_lang),
            callback_data="msg,%d,%d,%d,%d,%d" % (channel_id, msg_id, recent, offset - 1, ori_chat_id)
        )
    ]]
    motd_markup = InlineKeyboardMarkup(motd_keyboard)

    if offset > 0 and len(records) == 0:
        bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            text=helper_global.value("no_prev_page", "", lang=channel_lang)
        )
        return

    prompt_text = helper_global.value("comment_header", "", lang=channel_lang)
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

    config = helper_database.get_channel_config(channel_id)
    if config is None:
        return
    channel_lang = config[1]
    recent = config[3]
    admin_id = config[5]

    if row_id < 0:
        bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            text=helper_global.value("no_message_detail", "No Message", lang=channel_lang)
        )
        return

    records = helper_database.get_record_by_rowid(row_id)

    if records is None or len(records) == 0:
        bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            text=helper_global.value("no_message_detail", "No Message", lang=channel_lang)
        )
        return

    record = records[0]

    username = record[2]
    name = record[3]
    msg_type = record[4]
    msg_content = record[5]
    media_id= record[6]
    user_id = int(record[8])

    base_offset = helper_database.get_base_offset_by_rowid(channel_id, msg_id, row_id)
    offset = base_offset // recent

    msg_from_button = [
        [
            InlineKeyboardButton(
                helper_global.value("msg_from", "Message From: ", lang=channel_lang) + name,
                callback_data="blank"
            )
        ]
    ]
    admin_operation_button = [
        [
            InlineKeyboardButton(
                helper_global.value("delete_msg", "Delete Message", lang=channel_lang),
                callback_data="msg_delete,%d,%d,%d,%d,%d,%d" % (row_id, channel_id, msg_id, recent, offset, chat_id)
            ),
            InlineKeyboardButton(
                helper_global.value("unban_user", "Unban User", lang=channel_lang),
                callback_data="user_unban,%d,%d,%s" % (channel_id, user_id, name)
            ) if helper_database.check_ban(channel_id, user_id) else \
            InlineKeyboardButton(
                helper_global.value("ban_user", "Ban User", lang=channel_lang),
                callback_data="user_ban,%d,%d,%s" % (channel_id, user_id, name)
            )
        ]
    ] if str(chat_id) == str(admin_id) else []
    motd_keyboard = msg_from_button + admin_operation_button + [
        [
            InlineKeyboardButton(
                helper_global.value("prev_msg", "Prev Message", lang=channel_lang),
                callback_data="msg_detail,%d,%d,%d" % (channel_id, msg_id, helper_database.get_next_rowid(channel_id, msg_id, row_id))
            ),
            InlineKeyboardButton(
                helper_global.value("next_msg", "Next Message", lang=channel_lang),
                callback_data="msg_detail,%d,%d,%d" % (channel_id, msg_id, helper_database.get_prev_rowid(channel_id, msg_id, row_id))
            )
        ],
        [
            InlineKeyboardButton(
                helper_global.value("back_to_msg_list", "Back to message list", lang=channel_lang),
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


def option_finish(bot, lang, chat_id, origin_message_id):
    bot.edit_message_text(
        chat_id=chat_id, 
        message_id=origin_message_id,
        text=helper_global.value("option_finished", "", lang=lang) 
    )


def option_item(bot, lang, chat_id, origin_message_id, args):
    # Prepare Keyboard
    motd_keyboard = [[
        InlineKeyboardButton(
            "mode",
            callback_data="option|%s,%s,mode" % (lang, args[1])
        ),
        InlineKeyboardButton(
            "recent",
            callback_data="option|%s,%s,recent" % (lang, args[1])
        ),
        InlineKeyboardButton(
            "notify",
            callback_data="option|%s,%s,notify" % (lang, args[1])
        )
    ]] + [[
        InlineKeyboardButton(
            "lang",
            callback_data="option|%s,%s,lang" % (lang, args[1])
        )
    ]] + [[
        InlineKeyboardButton(
            helper_global.value("option_delete", "", lang=lang),
            callback_data="option_delete|%s,%s" % (lang, args[1])
        )
    ]] + [[
        InlineKeyboardButton(
            helper_global.value("option_finish", "", lang=lang),
            callback_data="option_finish|%s" % lang
        )
    ]]

    motd_markup = InlineKeyboardMarkup(motd_keyboard)

    bot.edit_message_text(
        chat_id=chat_id, 
        message_id=origin_message_id,
        text=helper_global.value("option_choose_item", "", lang=lang),
        reply_markup=motd_markup
    )


def option_mode(bot, lang, chat_id, origin_message_id, args):
    # Prepare Keyboard
    motd_keyboard = [[
        InlineKeyboardButton(
            "0",
            callback_data="option|%s,%s,mode,0" % (lang, args[1])
        ),
        InlineKeyboardButton(
            "1",
            callback_data="option|%s,%s,mode,1" % (lang, args[1])
        ),
        InlineKeyboardButton(
            "2",
            callback_data="option|%s,%s,mode,2" % (lang, args[1])
        )
    ]] + [[
        InlineKeyboardButton(
            helper_global.value("option_finish", "", lang=lang),
            callback_data="option_finish|%s" % lang
        )
    ]]

    motd_markup = InlineKeyboardMarkup(motd_keyboard)

    bot.edit_message_text(
        chat_id=chat_id, 
        message_id=origin_message_id,
        text=helper_global.value("option_choose_mode_value", "", lang=lang),
        reply_markup=motd_markup
    )

    
def option_recent(bot, lang, chat_id, origin_message_id, args):
    # Prepare Keyboard
    motd_keyboard = [[
        InlineKeyboardButton(
            "5",
            callback_data="option|%s,%s,recent,5" % (lang, args[1])
        ),
        InlineKeyboardButton(
            "10",
            callback_data="option|%s,%s,recent,10" % (lang, args[1])
        ),
        InlineKeyboardButton(
            "15",
            callback_data="option|%s,%s,recent,15" % (lang, args[1])
        ),
        InlineKeyboardButton(
            "20",
            callback_data="option|%s,%s,recent,20" % (lang, args[1])
        )
    ]] + [[
        InlineKeyboardButton(
            helper_global.value("option_finish", "", lang=lang),
            callback_data="option_finish|%s" % lang
        )
    ]]

    motd_markup = InlineKeyboardMarkup(motd_keyboard)

    bot.edit_message_text(
        chat_id=chat_id, 
        message_id=origin_message_id,
        text=helper_global.value("option_choose_recent_value", "", lang=lang),
        reply_markup=motd_markup
    )


def option_notify(bot, lang, chat_id, origin_message_id, args):
    # Prepare Keyboard
    motd_keyboard = [[
        InlineKeyboardButton(
            "0",
            callback_data="option|%s,%s,notify,0" % (lang, args[1])
        ),
        InlineKeyboardButton(
            "1",
            callback_data="option|%s,%s,notify,1" % (lang, args[1])
        )
    ]] + [[
        InlineKeyboardButton(
            helper_global.value("option_finish", "", lang=lang),
            callback_data="option_finish|%s" % lang
        )
    ]]

    motd_markup = InlineKeyboardMarkup(motd_keyboard)

    bot.edit_message_text(
        chat_id=chat_id, 
        message_id=origin_message_id,
        text=helper_global.value("option_choose_notify_value", "", lang=lang),
        reply_markup=motd_markup
    )


def option_lang(bot, lang, chat_id, origin_message_id, args):
    # Prepare Keyboard
    motd_keyboard = [[
        InlineKeyboardButton(
            c_lang,
            callback_data="option|%s,%s,lang,%s" % (lang, args[1], c_lang)
        )
    for c_lang in helper_const.LANG_LIST]] + [[
        InlineKeyboardButton(
            helper_global.value("option_finish", "", lang=lang),
            callback_data="option_finish|%s" % lang
        )
    ]]

    motd_markup = InlineKeyboardMarkup(motd_keyboard)

    bot.edit_message_text(
        chat_id=chat_id, 
        message_id=origin_message_id,
        text=helper_global.value("option_choose_lang_value", "", lang=lang),
        reply_markup=motd_markup
    )


def option_delete(bot, lang, chat_id, origin_message_id, args):
    channel_id = args[1]
    helper_database.delete_channel_config(channel_id)
    bot.edit_message_text(
        chat_id=chat_id, 
        message_id=origin_message_id,
        text=helper_global.value("option_record_deleted", "", lang=lang)
    )


def option_update(bot, update, lang, chat_id, origin_message_id, args):
    try:
        helper_database.update_config_by_channel(args[1], args[2], args[3])
        bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            text=helper_global.value("option_update_success", "", lang=lang)
        )
    except:
        bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            text=helper_global.value("option_update_failed", "", lang=lang)
        )
    option_item(bot, lang, chat_id, origin_message_id, args)


def option_index(bot, lang, chat_id, origin_message_id, args):
    records = helper_database.get_channel_info_by_user(chat_id)
    if records is None or len(records) == 0:
        bot.send_message(
            chat_id=chat_id, 
            text=helper_global.value("option_no_channel", "", lang=lang)
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
    bot.edit_message_text(
        chat_id=chat_id, 
        message_id=origin_message_id,
        text=helper_global.value("option_choose_channel", "", lang=lang),
        reply_markup=motd_markup
    )


def msg_delete(bot, update, chat_id, origin_message_id, args):
    row_id = int(args[1])
    channel_id = int(args[2])
    msg_id = int(args[3])
    msg_args = ["msg"] + args[2:]
    config = helper_database.get_channel_config(channel_id)
    if config is None:
        return
    channel_lang = config[1]
    helper_database.delete_record_by_rowid(row_id)
    bot.answer_callback_query(
        callback_query_id=update.callback_query.id,
        text=helper_global.value("delete_success", "", lang=channel_lang)
    )
    private_msg.update_dirty_msg(channel_id, msg_id)
    show_msg(bot, update, origin_message_id, chat_id, msg_args)


def user_ban(bot, update, chat_id, origin_message_id, args):
    channel_id = int(args[1])
    user_id = int(args[2])
    name = args[3]
    config = helper_database.get_channel_config(channel_id)
    if config is None:
        return
    channel_lang = config[1]
    try:
        helper_database.ban_user(channel_id, user_id, name)
    except:
        bot.answer_callback_query(
            callback_query_id=update.callback_query.id,
            text=helper_global.value("user_banned_failed", "", lang=channel_lang)
        )
    bot.answer_callback_query(
        callback_query_id=update.callback_query.id,
        text=helper_global.value("user_banned", "", lang=channel_lang)
    )


def user_unban(bot, update, chat_id, origin_message_id, args):
    channel_id = int(args[1])
    user_id = int(args[2])
    name = args[3]
    helper_database.unban_user(channel_id, user_id, name)
    bot.answer_callback_query(
        callback_query_id=update.callback_query.id,
        text=helper_global.value("user_unbanned", "", lang=lang)
    )


def callback_query(bot, update):
    callback_data = update.callback_query.data
    origin_message_id = update.callback_query.message.message_id
    chat_id = update.callback_query.message.chat_id
    args = callback_data.split(',')
    if "|" in args[0]:
        lang = args[0].split("|")[1]
    if args[0] == 'msg':
        show_msg(bot, update, origin_message_id, chat_id, args)
    elif args[0] == 'msg_detail':
        msg_detail(bot, update, chat_id, origin_message_id, args)
    elif args[0] == 'msg_delete':
        msg_delete(bot, update, chat_id, origin_message_id, args)
    elif args[0] == 'user_ban':
        user_ban(bot, update, chat_id, origin_message_id, args)
    elif args[0] == 'user_unban':
        user_unban(bot, update, chat_id, origin_message_id, args)
    elif args[0].startswith('option_delete'):
        option_delete(bot, lang, chat_id, origin_message_id, args)
    elif args[0].startswith('option_finish'):
        option_finish(bot, lang, chat_id, origin_message_id)
    elif args[0].startswith('option'):
        if len(args) == 1:
            option_index(bot, lang, chat_id, origin_message_id, args)
        if len(args) == 2:
            option_item(bot, lang, chat_id, origin_message_id, args)
        elif len(args) == 3 and args[2] == "mode":
            option_mode(bot, lang, chat_id, origin_message_id, args)
        elif len(args) == 3 and args[2] == "recent":
            option_recent(bot, lang, chat_id, origin_message_id, args)
        elif len(args) == 3 and args[2] == "notify":
            option_notify(bot, lang, chat_id, origin_message_id, args)
        elif len(args) == 3 and args[2] == "lang":
            option_lang(bot, lang, chat_id, origin_message_id, args)
        elif len(args) == 4:
            option_update(bot, update, lang, chat_id, origin_message_id, args)


_handler = CallbackQueryHandler(callback_query)
