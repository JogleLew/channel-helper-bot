#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" channel_msg.py """
""" Copyright 2018, Jogle Lew """
import helper_const
import helper_global
import helper_database
import telegram
from telegram.utils.helpers import effective_message_type
from telegram.ext import MessageHandler, Filters
if telegram.__version__ < '13.0':
    from telegram.ext import BaseFilter
else:
    from telegram.ext import MessageFilter as BaseFilter
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from ninesix import Logger

parse_entity = helper_global.parse_entity

def add_comment(bot, chat_id, config, message_id, media_group_id=None):
    logger = Logger.logger
    logger.msg({
        "channel_id": chat_id,
        "msg_id": message_id,
        "action": "normal comment"
    }, tag="channel", log_level=80)
    channel_lang = config[1]
    recent = config[3]

    if helper_database.check_reflect(chat_id, message_id):
        return

    # Avoid duplicated comment for media group
    if media_group_id:
       last_media_group = helper_global.value(str(chat_id) + '_last_media_group', '0')
       # print(last_media_group)
       if last_media_group == media_group_id:
           return
       helper_global.assign(str(chat_id) + '_last_media_group', media_group_id)

    # Prepare Keyboard
    motd_keyboard = [[
        InlineKeyboardButton(
            helper_global.value("add_comment", "Add Comment", lang=channel_lang),
            url="http://telegram.me/%s?start=add_%d_%d" % (helper_global.value('bot_username', ''), chat_id, message_id)
        ),
        InlineKeyboardButton(
            helper_global.value("show_all_comments", "Show All", lang=channel_lang),
            url="http://telegram.me/%s?start=show_%s_%d" % (helper_global.value('bot_username', ''), chat_id, message_id)
        )
    ]]
    motd_markup = InlineKeyboardMarkup(motd_keyboard)

    records = helper_database.get_recent_records(chat_id, message_id, recent)

    comment_message = bot.send_message(
        chat_id=chat_id, 
        text=helper_global.records_to_str(records, channel_lang), 
        reply_to_message_id=message_id,
        reply_markup=motd_markup, 
        parse_mode=telegram.ParseMode.HTML
    ).result()
    helper_database.add_reflect(chat_id, message_id, comment_message.message_id)


def add_compact_comment(bot, chat_id, config, message_id, message):
    logger = Logger.logger
    logger.msg({
        "channel_id": chat_id,
        "msg_id": message_id,
        "action": "compact comment"
    }, tag="channel", log_level=80)
    channel_lang = config[1]

    # Fallback media group message
    if message.media_group_id:
        add_comment(bot, chat_id, config, message_id, media_group_id=message.media_group_id)
        return

    if message.forward_from or message.forward_from_chat:
        new_message = deforward(bot, message, channel_lang)
        message_id = new_message.message_id
        message = new_message

    # Prepare Keyboard
    motd_keyboard = [[
        InlineKeyboardButton(
            helper_global.value("add_comment", "Add Comment", lang=channel_lang),
            url="http://telegram.me/%s?start=add_%d_%d" % (helper_global.value('bot_username', ''), chat_id, message_id)
        ), 
        InlineKeyboardButton(
            helper_global.value("show_all_comments", "Show All", lang=channel_lang),
            url="http://telegram.me/%s?start=show_%s_%d" % (helper_global.value('bot_username', ''), chat_id, message_id)
        )
    ]]
    motd_markup = InlineKeyboardMarkup(motd_keyboard)

    try:
        bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=motd_markup
        ).result()
    except telegram.error.BadRequest:
        logger.msg({
            "channel_id": chat_id,
            "msg_id": message_id,
            "action": "compact -> normal"
        }, tag="channel", log_level=80)
        add_comment(bot, chat_id, config, message_id)
    except:
        pass


def add_inplace_comment(bot, chat_id, config, message_id, message, buttons):
    logger = Logger.logger
    logger.msg({
        "channel_id": chat_id,
        "msg_id": message_id,
        "action": "inplace comment"
    }, tag="channel", log_level=80)
    channel_lang = config[1]

    # Fallback media group message
    if message.media_group_id:
        return

    if message.forward_from or message.forward_from_chat:
        new_message = deforward(bot, message, channel_lang)
        message_id = new_message.message_id
        message = new_message

    # Prepare Keyboard
    if buttons and len(buttons) > 0:
        helper_database.add_button_options(chat_id, message_id, buttons)
        helper_database.clear_reaction(chat_id, message_id)

    motd_keyboard = [[
        InlineKeyboardButton(
            value,
            callback_data="like,%s,%s,%d" % (chat_id, message_id, idx)
        )
    for idx, value in enumerate(buttons)]] + ([[
        InlineKeyboardButton(
            helper_global.value("add_comment", "Add Comment", lang=channel_lang),
            url="http://telegram.me/%s?start=add_%d_%d" % (helper_global.value('bot_username', ''), chat_id, message_id)
        ), 
        InlineKeyboardButton(
            helper_global.value("show_all_comments", "Show All", lang=channel_lang),
            url="http://telegram.me/%s?start=show_%s_%d" % (helper_global.value('bot_username', ''), chat_id, message_id)
        )
    ]])
    motd_markup = InlineKeyboardMarkup(motd_keyboard)

    try:
        bot.edit_message_reply_markup(
            chat_id=chat_id,
            message_id=message_id,
            reply_markup=motd_markup
        ).result()
    except:
        return
    helper_database.add_reflect(chat_id, message_id, avoidNone(message.caption if message.caption else message.text))


def avoidNone(s):
    if s:
        return str(s)
    return ''


def deforward(bot, msg, lang):
    logger = Logger.logger
    chat_id = msg.chat_id
    message_id = msg.message_id
    logger.msg({
        "channel_id": chat_id,
        "msg_id": message_id,
        "action": "messaage deforward"
    }, tag="channel", log_level=80)

    # Generate forward info
    has_msg_link = False
    if msg.forward_from:
        # Check username existence
        if msg.forward_from.username:
            forward_info = helper_global.value('fwd_source', 'Forwarded from:', lang=lang) + '@%s' % msg.forward_from.username
        else:
            forward_info = helper_global.value('fwd_source', 'Forwarded from:', lang=lang) + '<a href="tg://user?id=%d">%s</a>' % (
                msg.forward_from.id, 
                msg.forward_from.first_name + " " + avoidNone(msg.forward_from.last_name)
            )
    elif msg.forward_from_chat:
        # Check channel public/private
        if msg.forward_from_chat.username:
            forward_info = helper_global.value('fwd_source', 'Forwarded from:', lang=lang) + 'https://t.me/%s/%s' % (
                msg.forward_from_chat.username,
                msg.forward_from_message_id
            )
            has_msg_link = True
        else:
            forward_info = helper_global.value('fwd_source', 'Forwarded from:', lang=lang) + msg.forward_from_chat.title

    message_type = effective_message_type(msg)
    new_msg = None

    # Ignore media group
    if msg.media_group_id:
        return msg

    # Handle by message type
    if message_type == 'text':
        has_content_link = False
        for entity in msg.entities:
            if entity.type == 'url' or entity.type == 'text_link':
                has_content_link = True
                break
        new_msg = bot.send_message(
            chat_id=chat_id,
            text=parse_entity(avoidNone(msg.text), msg.entities) + '\n\n' + forward_info,
            parse_mode='HTML',
            disable_notification=True,
            disable_web_page_preview=(not has_content_link and has_msg_link)
        ).result()
    elif message_type == 'audio': 
        new_msg = bot.send_audio(
            chat_id=chat_id,
            audio=msg.audio.file_id,
            caption=parse_entity(avoidNone(msg.caption), msg.caption_entities) + '\n\n' + forward_info,
            parse_mode='HTML',
            disable_notification=True
        ).result()
    elif message_type == 'document': 
        new_msg = bot.send_document(
            chat_id=chat_id,
            document=msg.document.file_id,
            caption=parse_entity(avoidNone(msg.caption), msg.caption_entities) + '\n\n' + forward_info,
            parse_mode='HTML',
            disable_notification=True
        ).result()
    elif message_type == 'photo': 
        new_msg = bot.send_photo(
            chat_id=chat_id,
            photo=msg.photo[-1].file_id,
            caption=parse_entity(avoidNone(msg.caption), msg.caption_entities) + '\n\n' + forward_info,
            parse_mode='HTML',
            disable_notification=True
        ).result()
    elif message_type == 'sticker': 
        new_msg = bot.send_sticker(
            chat_id=chat_id,
            sticker=msg.sticker.file_id,
            disable_notification=True
        ).result()
    elif message_type == 'video': 
        new_msg = bot.send_video(
            chat_id=chat_id,
            video=msg.video.file_id,
            caption=parse_entity(avoidNone(msg.caption), msg.caption_entities) + '\n\n' + forward_info,
            parse_mode='HTML',
            disable_notification=True
        ).result()
    elif message_type == 'voice': 
        new_msg = bot.send_voice(
            chat_id=chat_id,
            voice=msg.voice.file_id,
            caption=parse_entity(avoidNone(msg.caption), msg.caption_entities) + '\n\n' + forward_info,
            parse_mode='HTML',
            disable_notification=True
        ).result()

    if new_msg:
        bot.delete_message(chat_id=chat_id, message_id=message_id)
        return new_msg
    return msg
    

def add_like_buttons(bot, channel_lang, config, chat_id, message_id, message, buttons):
    logger = Logger.logger
    logger.msg({
        "channel_id": chat_id,
        "msg_id": message_id,
        "action": "add like buttons"
    }, tag="channel", log_level=80)
    flag = 1
    ref = helper_database.get_reflect_by_msg_id(chat_id, message_id)
    if ref is not None:
        flag = 0
        message_id = ref[1]

    # Fallback media group message
    if message.media_group_id:
        add_comment(bot, chat_id, config, message_id, media_group_id=message.media_group_id)
        return

    if message.forward_from or message.forward_from_chat:
        new_message = deforward(bot, message, channel_lang)
        message_id = new_message.message_id
        message = new_message

    # Prepare Keyboard
    helper_database.add_button_options(chat_id, message_id, buttons)
    helper_database.clear_reaction(chat_id, message_id)
    motd_keyboard = [[
        InlineKeyboardButton(
            value,
            callback_data="like,%s,%s,%d" % (chat_id, message_id, idx)
        )
    for idx, value in enumerate(buttons)]] + ([[
        InlineKeyboardButton(
            helper_global.value("add_comment", "Add Comment", lang=channel_lang),
            url="http://telegram.me/%s?start=add_%d_%d" % (helper_global.value('bot_username', ''), chat_id, message_id)
        ), 
        InlineKeyboardButton(
            helper_global.value("show_all_comments", "Show All", lang=channel_lang),
            url="http://telegram.me/%s?start=show_%s_%d" % (helper_global.value('bot_username', ''), chat_id, message_id)
        )
    ]] if flag == 1 else [[]])
    motd_markup = InlineKeyboardMarkup(motd_keyboard)

    bot.edit_message_reply_markup(
        chat_id=chat_id,
        message_id=message_id,
        reply_markup=motd_markup
    )


def channel_post_msg(bot, update):
    logger = Logger.logger
    message = update.channel_post
    if message is None:
        return
    chat_id = message.chat_id
    message_id = message.message_id
    config = helper_database.get_channel_config(chat_id)
    if config is None:
        return
    lang, mode, recent, button_mode = config[1], config[2], config[3], config[7]

    # Manual Mode
    if message.reply_to_message is not None and message.text.startswith("/comment"):
        logger.msg({
            "channel_id": chat_id,
            "msg_id": message_id,
            "mode": mode,
            "button": button_mode,
            "action": "/comment"
        }, tag="channel", log_level=90)
        message_id = message.reply_to_message.message_id
        bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        if not helper_database.check_reflect(chat_id, message_id) and message.reply_to_message.reply_markup is None:
            add_compact_comment(bot, chat_id, config, message_id, message.reply_to_message)
        if not button_mode == 0:
            buttons = message.text.split()[1:]
            if button_mode == 1 and len(buttons) == 0:
                buttons = helper_database.get_default_button_options(chat_id)
            add_like_buttons(bot, lang, config, chat_id, message_id, message, buttons)

    # Force Comment for Special Cases
    elif message.reply_to_message is not None and message.text == "/forcecomment":
        logger.msg({
            "channel_id": chat_id,
            "msg_id": message_id,
            "mode": mode,
            "button": button_mode,
            "action": "/forcecomment"
        }, tag="channel", log_level=90)
        message_id = message.reply_to_message.message_id
        bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        helper_database.delete_reflect(chat_id, message_id)
        add_compact_comment(bot, chat_id, config, message_id, message.reply_to_message)

    # Set default buttons
    elif message.text is not None and message.text.startswith("/defaultbuttons"):
        logger.msg({
            "channel_id": chat_id,
            "msg_id": message_id,
            "mode": mode,
            "button": button_mode,
            "action": "/defaultbuttons"
        }, tag="channel", log_level=90)
        buttons = message.text.split()[1:]
        bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        helper_database.add_button_options(chat_id, 0, buttons)

    # Auto Comment Mode
    elif mode == 1: 
        logger.msg({
            "channel_id": chat_id,
            "msg_id": message_id,
            "mode": mode,
            "button": button_mode,
            "action": "new channel post"
        }, tag="channel", log_level=90)
        add_comment(bot, chat_id, config, message_id, media_group_id=message.media_group_id)
        if button_mode == 1:
            add_like_buttons(bot, lang, config, chat_id, message_id, message, helper_database.get_default_button_options(chat_id))
    elif mode == 2:
        logger.msg({
            "channel_id": chat_id,
            "msg_id": message_id,
            "mode": mode,
            "button": button_mode,
            "action": "new channel post"
        }, tag="channel", log_level=90)
        if button_mode == 1:
            add_like_buttons(bot, lang, config, chat_id, message_id, message, helper_database.get_default_button_options(chat_id))
        else:
            add_compact_comment(bot, chat_id, config, message_id, message)
    elif mode == 3:
        logger.msg({
            "channel_id": chat_id,
            "msg_id": message_id,
            "mode": mode,
            "button": button_mode,
            "action": "new channel post"
        }, tag="channel", log_level=90)
        add_inplace_comment(bot, chat_id, config, message_id, message, (helper_database.get_default_button_options(chat_id) if button_mode == 1 else []))


class FilterChannelPost(BaseFilter):
    def filter(self, message):
        return message.chat.type == "channel"


channel_post_filter = FilterChannelPost()
_handler = MessageHandler(channel_post_filter, channel_post_msg)
