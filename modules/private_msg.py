#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" private_msg.py """
""" Copyright 2018, Jogle Lew """
import helper_const
import helper_global
import helper_database
import telegram
import threading
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import MessageHandler, Filters
from ninesix import Logger

def add_record(bot, channel_id, msg_id, message):
    logger = Logger.logger
    ori_msg_id = message.message_id
    user = message.from_user
    username = user.username
    user_id = user.id
    name = user.first_name
    if user.last_name:
        name += " " + user.last_name
    date = message.date.strftime("%Y-%m-%d %H:%M:%S")

    msg_type = "text"
    msg_content = ""
    media_id = ""
    if message.text:
        msg_type = "text"
        msg_content = message.text
    elif message.sticker:
        msg_type = 'sticker'
        media_id = message.sticker.file_id
        if message.sticker.emoji:
            msg_content = message.sticker.emoji
    elif message.photo:
        msg_type = 'photo'
        media_id = message.photo[-1].file_id
        if message.caption:
            msg_content = message.caption
    elif message.video:
        msg_type = 'video'
        media_id = message.video.file_id
        if message.caption:
            msg_content = message.caption
    elif message.document:
        msg_type = 'document'
        media_id = message.document.file_id
        if message.document.file_name:
            msg_content = message.document.file_name
    elif message.audio:
        msg_type = 'audio'
        media_id = message.audio.file_id
        if message.audio.title:
            msg_content = message.audio.title
    elif message.voice:
        msg_type = 'voice'
        media_id = message.voice.file_id

    msg_content = helper_global.parse_entity(msg_content, message.entities)

    if message.reply_markup and message.reply_markup.inline_keyboard:
        keyboard = message.reply_markup.inline_keyboard
        if len(keyboard) > 0 and len(keyboard[0]) > 0:
            query = keyboard[0][0]
            if query.callback_data:
                args = query.callback_data.split(",")
                if len(args) == 4 and args[0] == "notify":
                    target_channel_id = int(args[1])
                    target_msg_id = int(args[2])
                    target_row_id = args[3]
                    record = helper_database.get_record_by_rowid(target_row_id)
                    if len(record) > 0 and target_channel_id == int(record[0][0]) and target_msg_id == int(record[0][1]):
                        target_name = record[0][3]
                        target_user_id = record[0][8]
                        config = helper_database.get_channel_config(channel_id)
                        if config is None:
                            return
                        channel_lang, channel_username = config[1], config[4]
                        msg_content = "<b>(➤%s) </b> " % target_name.replace('<', '&lt;').replace('>', '&gt;') + msg_content
                        if channel_username is not None:
                            logger.msg({
                                "channel_id": channel_id,
                                "msg_id": msg_id,
                                "target_user": target_user_id,
                                "action": "notify reply"
                            }, tag="private", log_level=80)
                            bot.send_message(
                                chat_id=target_user_id, 
                                text=helper_global.value("new_reply_message", "You receive a reply message.", lang=channel_lang) + "\n" + helper_global.value("target_message", "", lang=channel_lang) + "https://t.me/%s/%d" % (channel_username, target_msg_id) 
                            )
                        else:
                            link_id = abs(channel_id) % 10000000000
                            bot.send_message(
                                chat_id=target_user_id, 
                                text=helper_global.value("new_reply_message", "You receive a reply message.", lang=channel_lang) + "\n" + helper_global.value("target_message", "", lang=channel_lang) + "https://t.me/c/%d/%d" % (link_id, target_msg_id) 
                            )

    return helper_database.add_record(channel_id, msg_id, username, name, msg_type, msg_content, media_id, date, user_id, ori_msg_id)


def update_comments(bot, channel_id, msg_id, update_mode):
    logger = Logger.logger
    config = helper_database.get_channel_config(channel_id)
    if config is None:
        return
    channel_lang = config[1]
    mode = config[2]
    recent = config[3]
    logger.msg({
        "channel_id": channel_id,
        "msg_id": msg_id,
        "update_mode": update_mode
    }, tag="private", log_level=80)

    # For mode 3
    if mode == 3 and update_mode == 2:
        buttons = helper_database.get_button_options(channel_id, msg_id)
        stat = helper_database.get_reaction_stat(channel_id, msg_id)
        # Prepare Keyboard
        motd_keyboard = [[
            InlineKeyboardButton(
                value + (" (%d)" % stat[idx] if idx in stat else ""),
                callback_data="like,%s,%s,%d" % (channel_id, msg_id, idx)
            )
        for idx, value in enumerate(buttons)]] + [[
            InlineKeyboardButton(
                helper_global.value("add_comment", "Add Comment", lang=channel_lang),
                url="http://telegram.me/%s?start=add_%d_%d" % (helper_global.value('bot_username', ''), channel_id, msg_id)
            ),
            InlineKeyboardButton(
                helper_global.value("show_all_comments", "Show All", lang=channel_lang),
                url="http://telegram.me/%s?start=show_%s_%d" % (helper_global.value('bot_username', ''), channel_id, msg_id)
            )
        ]]
        motd_markup = InlineKeyboardMarkup(motd_keyboard)

        records = helper_database.get_recent_records(channel_id, msg_id, recent)
        origin_post = helper_database.get_origin_post(channel_id, msg_id)

        try:
            bot.edit_message_caption(
                caption=origin_post + "\n\n" + helper_global.records_to_str(records, channel_lang), 
                chat_id=channel_id, 
                message_id=msg_id, 
                parse_mode=telegram.ParseMode.HTML,
                reply_markup=motd_markup
            )
        except:
            bot.edit_message_text(
                text=origin_post + "\n\n" + helper_global.records_to_str(records, channel_lang), 
                chat_id=channel_id, 
                message_id=msg_id, 
                parse_mode=telegram.ParseMode.HTML,
                reply_markup=motd_markup
            )
        return
        
    # update comments in channel
    comment_id = helper_database.get_comment_id(channel_id, msg_id)
    if comment_id is None:
        # If no comment message, just update Like buttons
        buttons = helper_database.get_button_options(channel_id, msg_id)
        stat = helper_database.get_reaction_stat(channel_id, msg_id)
        # Prepare Keyboard
        motd_keyboard = [[
            InlineKeyboardButton(
                value + (" (%d)" % stat[idx] if idx in stat else ""),
                callback_data="like,%s,%s,%d" % (channel_id, msg_id, idx)
            )
        for idx, value in enumerate(buttons)]] + [[
            InlineKeyboardButton(
                helper_global.value("add_comment", "Add Comment", lang=channel_lang),
                url="http://telegram.me/%s?start=add_%d_%d" % (helper_global.value('bot_username', ''), channel_id, msg_id)
            ),
            InlineKeyboardButton(
                helper_global.value("show_all_comments", "Show All", lang=channel_lang),
                url="http://telegram.me/%s?start=show_%s_%d" % (helper_global.value('bot_username', ''), channel_id, msg_id)
            )
        ]]
        motd_markup = InlineKeyboardMarkup(motd_keyboard)
        bot.edit_message_reply_markup(
            chat_id=channel_id,
            message_id=msg_id,
            reply_markup=motd_markup
        )
        return

    # Otherwise
    # Update Like buttons
    if update_mode == 0:
        buttons = helper_database.get_button_options(channel_id, msg_id)
        stat = helper_database.get_reaction_stat(channel_id, msg_id)
        # Prepare Keyboard
        motd_keyboard = [[
            InlineKeyboardButton(
                value + (" (%d)" % stat[idx] if idx in stat else ""),
                callback_data="like,%s,%s,%d" % (channel_id, msg_id, idx)
            )
        for idx, value in enumerate(buttons)]]
        if comment_id - msg_id > 1:
            link_id = abs(channel_id) % 10000000000
            motd_keyboard += [[
                InlineKeyboardButton(
                    helper_global.value("jump_to_comment", "Jump to Comment", lang=channel_lang),
                    url="https://t.me/c/%d/%d" % (link_id, comment_id)
                )
            ]]
        motd_markup = InlineKeyboardMarkup(motd_keyboard)
        bot.edit_message_reply_markup(
            chat_id=channel_id,
            message_id=msg_id,
            reply_markup=motd_markup
        )
        return

    # Update comment message
    records = helper_database.get_recent_records(channel_id, msg_id, recent)

    # Prepare Keyboard
    motd_keyboard = [[
        InlineKeyboardButton(
            helper_global.value("add_comment", "Add Comment", lang=channel_lang),
            url="http://telegram.me/%s?start=add_%d_%d" % (helper_global.value('bot_username', ''), channel_id, msg_id)
        ),
        InlineKeyboardButton(
            helper_global.value("show_all_comments", "Show All", lang=channel_lang),
            url="http://telegram.me/%s?start=show_%s_%d" % (helper_global.value('bot_username', ''), channel_id, msg_id)
        )
    ]]
    motd_markup = InlineKeyboardMarkup(motd_keyboard)

    bot.edit_message_text(
        text=helper_global.records_to_str(records, channel_lang), 
        chat_id=channel_id, 
        message_id=comment_id, 
        parse_mode=telegram.ParseMode.HTML,
        reply_markup=motd_markup
    )


def update_dirty_list():
    lock.acquire()
    dirty_list = helper_global.value("dirty_list", [])
    bot = helper_global.value("bot", None)
    for item in dirty_list:
        channel_id, msg_id, update_mode = item
        threading.Thread(
            target=update_comments,
            args=(bot, channel_id, msg_id, update_mode)
        ).start()
    helper_global.assign("dirty_list", [])
    lock.release()


def check_channel_message(bot, message):
    logger = Logger.logger
    chat_id = message.chat_id
    if not message.forward_from_chat:
        helper_global.send_intro_template(bot, chat_id, helper_const.DEFAULT_LANG, "register_invalid", "register_cmd_invalid")
        return
    chat_type = message.forward_from_chat.type
    if not chat_type == "channel":
        helper_global.send_intro_template(bot, chat_id, helper_const.DEFAULT_LANG, "register_invalid", "register_cmd_invalid")
        return
    channel_username = message.forward_from_chat.username
    channel_id = message.forward_from_chat.id
    user_id = message.from_user.id
    logger.msg({
        "user_id": chat_id,
        "channel_id": channel_id,
        "action": "check channel"
    }, tag="private", log_level=90)
    bot_id = int(helper_const.BOT_TOKEN.split(":")[0])
    try:
        chat_members = bot.get_chat_administrators(chat_id=channel_id).result()
        chat_member_ids = [member.user.id for member in chat_members]
        if not user_id in chat_member_ids:
            helper_global.send_intro_template(bot, chat_id, helper_const.DEFAULT_LANG, "register_not_admin", "register_cmd_not_admin")
            return
        for member in chat_members:
            if member.user.id == bot_id:
                post_permission = member.can_post_messages if member.can_post_messages else False
                edit_permission = member.can_edit_messages if member.can_edit_messages else False
                delete_permission = member.can_delete_messages if member.can_delete_messages else False
                if not post_permission or not edit_permission or not delete_permission:
                    helper_global.send_intro_template(bot, chat_id, helper_const.DEFAULT_LANG, "register_no_permission", "register_cmd_no_permission")
                    return
                break
    except:
        helper_global.send_intro_template(bot, chat_id, helper_const.DEFAULT_LANG, "register_no_info", "register_cmd_no_info")
        return
    try:
        helper_database.add_channel_config(channel_id, helper_const.DEFAULT_LANG, 1, 10, channel_username, chat_id, 1, 1)
    except:
        helper_global.assign(str(chat_id) + "_status", "0,0")
        helper_global.send_intro_template(bot, chat_id, helper_const.DEFAULT_LANG, "register_failed", "register_cmd_failed")
        return

    helper_global.assign(str(chat_id) + "_status", "0,0")
    helper_global.send_intro_template(bot, chat_id, helper_const.DEFAULT_LANG, "register_success", "register_cmd_success")


def private_msg(bot, update):
    logger = Logger.logger
    message = update.edited_message if update.edited_message else update.message
    chat_id = message.chat_id
    args = helper_global.value(str(chat_id) + "_status", "0,0")
    logger.msg({
        "user_id": chat_id,
        "status": args
    }, tag="private", log_level=90)

    params = args.split(",")
    channel_id = int(params[0])
    msg_id = int(params[1])
    if channel_id == 0:
        if msg_id == 1:
            check_channel_message(bot, message)
        return

    # Check comment message
    comment_exist = helper_database.check_reflect(channel_id, msg_id)
    config = helper_database.get_channel_config(channel_id)
    if config is None:
        return
    channel_lang = config[1]
    mode, recent, username, admin_id, notify = config[2], config[3], config[4], config[5], config[6]
    logger.msg({
        "user_id": chat_id,
        "channel_id": channel_id,
        "msg_id": msg_id,
        "action": "add comment"
    }, tag="private", log_level=90)

    # For Auto Mode = 2
    if not comment_exist:
        logger.msg({
            "user_id": chat_id,
            "channel_id": channel_id,
            "msg_id": msg_id,
            "action": "add comment area"
        }, tag="private", log_level=80)
        comment_message = bot.send_message(
            chat_id=channel_id, 
            text=helper_global.value("comment_refreshing", "Refreshing...", lang=channel_lang), 
            reply_to_message_id=msg_id,
            parse_mode=telegram.ParseMode.HTML
        ).result()
        helper_database.add_reflect(channel_id, msg_id, comment_message.message_id)
        #bot.edit_message_reply_markup(
        #    chat_id=channel_id,
        #    message_id=msg_id,
        #    reply_markup=None
        #)
        update_dirty_msg(channel_id, msg_id, update_mode=0)

    result = add_record(bot, channel_id, msg_id, message)

    # Update Dirty List
    update_dirty_msg(channel_id, msg_id, update_mode=(2 if mode == 3 else 1))
    if notify == 1 and not int(chat_id) == int(admin_id):
        logger.msg({
            "user_id": chat_id,
            "channel_id": channel_id,
            "msg_id": msg_id,
            "admin_id": admin_id,
            "action": "notify channel owner"
        }, tag="private", log_level=80)
        if username is not None:
            bot.send_message(
                chat_id=admin_id, 
                text=helper_global.value("new_comment_message", "You have a new comment message.", lang=channel_lang) + "\n" + helper_global.value("target_message", "", lang=channel_lang) + "https://t.me/%s/%d" % (username, msg_id) 
            )
        else:
            link_id = abs(channel_id) % 10000000000
            bot.send_message(
                chat_id=admin_id, 
                text=helper_global.value("new_comment_message", "You have a new comment message.", lang=channel_lang) + "\n" + helper_global.value("target_message", "", lang=channel_lang) + "https://t.me/c/%d/%d" % (link_id, msg_id) 
            )

    if result == 0:
        bot.send_message(chat_id=chat_id, text=helper_global.value("comment_success", "Success!", lang=channel_lang))
    elif result == 1:
        bot.send_message(chat_id=chat_id, text=helper_global.value("comment_edit_success", "Success!", lang=channel_lang))


def update_dirty_msg(channel_id, msg_id, update_mode=1):
    lock.acquire()
    dirty_list = helper_global.value("dirty_list", [])
    if not (channel_id, msg_id, update_mode) in dirty_list:
        dirty_list.append((channel_id, msg_id, update_mode))
    helper_global.assign("dirty_list", dirty_list)
    lock.release()


def set_interval(func, sec):
    def func_wrapper():
        set_interval(func, sec)
        func()
    t = threading.Timer(sec, func_wrapper)
    t.start()
    return t


refresh_status = helper_global.value("refresh_status", False)
if not refresh_status:
    set_interval(update_dirty_list, helper_const.MIN_REFRESH_INTERVAL)
    helper_global.assign("refresh_status", True)
lock = threading.Lock()
_handler = MessageHandler(Filters.private, private_msg, edited_updates=True)
