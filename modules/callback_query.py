#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" callback_query.py """
""" Copyright 2018, Jogle Lew """
import helper_const
import helper_global
import helper_database
import modules.option_cmd as option_cmd
import modules.private_msg as private_msg
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, \
        InputMediaAudio, InputMediaDocument, InputMediaPhoto, InputMediaVideo
from telegram.ext import CallbackQueryHandler
from ninesix import Logger

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
                callback_data="user_unban,%d,%d,%s,%d,%d" % (channel_id, user_id, "", msg_id, row_id)
            ) if helper_database.check_ban(channel_id, user_id) else \
            InlineKeyboardButton(
                helper_global.value("ban_user", "Ban User", lang=channel_lang),
                callback_data="user_ban,%d,%d,%s,%d,%d" % (channel_id, user_id, "", msg_id, row_id)
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


def option_item(bot, update, lang, chat_id, origin_message_id, args):
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
        ),
        InlineKeyboardButton(
            "button",
            callback_data="option|%s,%s,button" % (lang, args[1])
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

    bot.answer_callback_query(
        callback_query_id=update.callback_query.id
    )
    bot.edit_message_text(
        chat_id=chat_id, 
        message_id=origin_message_id,
        text=helper_global.value("option_choose_item", "", lang=lang),
        reply_markup=motd_markup
    )


def option_key(bot, update, key, values, lang, chat_id, origin_message_id, args):
    config = helper_database.get_channel_config(args[1])
    if config is None or len(config) == 0:
        return
    key2idx = {
        "lang": 1,
        "mode": 2,
        "recent": 3,
        "notify": 6,
        "button": 7
    }
    # Prepare Keyboard
    width = helper_const.LANG_WIDTH
    motd_keyboard = [[
        InlineKeyboardButton(
            values[idx * width + delta] + (" (*)" if str(values[idx * width + delta]) == str(config[key2idx[key]]) else ""),
            callback_data="option|%s,%s,%s,%s" % (lang, args[1], key, values[idx * width + delta])
        ) for delta in range(width)
    ] for idx in range(len(values) // width)] + [[
        InlineKeyboardButton(
            values[idx] + (" (*)" if str(values[idx]) == str(config[key2idx[key]]) else ""),
            callback_data="option|%s,%s,%s,%s" % (lang, args[1], key, values[idx])
        ) 
    for idx in range(width * (len(values) // width), len(values))]] + [[
        InlineKeyboardButton(
            helper_global.value("option_back", "", lang=lang),
            callback_data="option|%s,%s" % (lang, args[1])
        )
    ]]

    motd_markup = InlineKeyboardMarkup(motd_keyboard)

    text = helper_global.value("option_choose_%s_value" % key, "", lang=lang)
    if key == "button":
        text = text % (", ".join(helper_database.get_default_button_options(args[1])))
    bot.answer_callback_query(
        callback_query_id=update.callback_query.id
    )
    bot.edit_message_text(
        chat_id=chat_id, 
        message_id=origin_message_id,
        text=text,
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
    option_item(bot, update, lang, chat_id, origin_message_id, args)


def option_index(bot, update, lang, chat_id, origin_message_id, args):
    records = helper_database.get_channel_info_by_user(chat_id)
    if records is None or len(records) == 0:
        bot.send_message(
            chat_id=chat_id, 
            text=helper_global.value("option_no_channel", "", lang=lang)
        )
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
    bot.answer_callback_query(
        callback_query_id=update.callback_query.id
    )
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
    msg_id = int(args[4])
    row_id = int(args[5])
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
    msg_detail(bot, update, chat_id, origin_message_id, ["msg_detail", channel_id, msg_id, row_id])


def user_unban(bot, update, chat_id, origin_message_id, args):
    channel_id = int(args[1])
    user_id = int(args[2])
    name = args[3]
    msg_id = int(args[4])
    row_id = int(args[5])
    config = helper_database.get_channel_config(channel_id)
    if config is None:
        return
    channel_lang = config[1]
    helper_database.unban_user(channel_id, user_id, name)
    bot.answer_callback_query(
        callback_query_id=update.callback_query.id,
        text=helper_global.value("user_unbanned", "", lang=channel_lang)
    )
    msg_detail(bot, update, chat_id, origin_message_id, ["msg_detail", channel_id, msg_id, row_id])


def reaction(bot, update, chat_id, origin_message_id, user_id, args):
    channel_id = int(args[1])
    msg_id = int(args[2])
    like_id = int(args[3])
    config = helper_database.get_channel_config(channel_id)
    if config is None:
        return
    channel_lang, mode = config[1], config[2]
    buttons = helper_database.get_button_options(channel_id, msg_id)
    helper_database.add_reaction(channel_id, msg_id, user_id, like_id)
    private_msg.update_dirty_msg(channel_id, msg_id, update_mode=(2 if mode == 3 else 0))
    bot.answer_callback_query(
        callback_query_id=update.callback_query.id,
        text=helper_global.value("like_recorded", "", lang=channel_lang) % buttons[like_id]
    )


def intro_template(bot, update, lang, chat_id, origin_message_id, key, text_key):
    lang_list = helper_const.LANG_LIST
    width = helper_const.LANG_WIDTH
    current_lang = lang
    motd_keyboard = [[
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
    bot.answer_callback_query(
        callback_query_id=update.callback_query.id
    )
    bot.edit_message_text(
        chat_id=chat_id, 
        message_id=origin_message_id,
        text=helper_global.value(text_key, "", lang=current_lang),
        reply_markup=motd_markup
    )


def callback_query(bot, update):
    logger = Logger.logger
    callback_data = update.callback_query.data
    if update.callback_query.message is None:
        bot.answer_callback_query(
            callback_query_id=update.callback_query.id
        )
        return
    origin_message_id = update.callback_query.message.message_id
    chat_id = update.callback_query.message.chat_id
    user_id = update.callback_query.from_user.id
    args = callback_data.split(',')
    logger.msg({
        "channel_id": chat_id,
        "msg_id": origin_message_id,
        "user_id": user_id,
        "callback": callback_data
    }, tag="callback", log_level=90)
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
    elif args[0] == 'like':
        reaction(bot, update, chat_id, origin_message_id, user_id, args)
    elif args[0].startswith('register'):
        item = args[0].split("|")[0]
        item_config = {
            "register": "register_cmd_text",
            "register_invalid": "register_cmd_invalid",
            "register_not_admin": "register_cmd_not_admin",
            "register_no_permission": "register_cmd_no_permission",
            "register_no_info": "register_cmd_no_info",
            "register_failed": "register_cmd_failed",
            "register_success": "register_cmd_success",
        }
        intro_template(bot, update, lang, chat_id, origin_message_id, item, item_config[item])
    elif args[0].startswith('start'):
        intro_template(bot, update, lang, chat_id, origin_message_id, "start", "start_cmd_text")
    elif args[0].startswith('help'):
        intro_template(bot, update, lang, chat_id, origin_message_id, "help", "help_cmd_text")
    elif args[0].startswith('option_no_channel'):
        intro_template(bot, update, lang, chat_id, origin_message_id, "option_no_channel", "option_no_channel")
    elif args[0].startswith('option_delete'):
        option_delete(bot, lang, chat_id, origin_message_id, args)
    elif args[0].startswith('option_finish'):
        option_finish(bot, lang, chat_id, origin_message_id)
    elif args[0].startswith('option'):
        if len(args) == 1:
            option_index(bot, update, lang, chat_id, origin_message_id, args)
        if len(args) == 2:
            option_item(bot, update, lang, chat_id, origin_message_id, args)
        elif len(args) == 3:
            item_config = {
                "mode": ["0", "1", "2"],
                "recent": ["5", "10", "15", "20"],
                "notify": ["0", "1"],
                "lang": helper_const.LANG_LIST,
                "button": ["0", "1", "2"]
            }
            key = args[2]
            values = item_config[key]
            option_key(bot, update, key, values, lang, chat_id, origin_message_id, args)
        elif len(args) == 4:
            option_update(bot, update, lang, chat_id, origin_message_id, args)
    else:
        bot.answer_callback_query(
            callback_query_id=update.callback_query.id
        )


_handler = CallbackQueryHandler(callback_query)
