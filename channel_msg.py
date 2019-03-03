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
from telegram.ext import MessageHandler, Filters, BaseFilter
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

def add_comment(bot, chat_id, message_id, media_group_id=None):
    # Avoid duplicated comment for media group
    if media_group_id:
       last_media_group = helper_global.value(str(chat_id) + '_last_media_group', '0')
       print(last_media_group)
       if last_media_group == media_group_id:
           return
       helper_global.assign(str(chat_id) + '_last_media_group', media_group_id)

    # Prepare Keyboard
    motd_keyboard = [[
        InlineKeyboardButton(
            helper_global.value("add_comment", "Add Comment"),
            url="http://telegram.me/%s?start=add_%d_%d" % (helper_global.value('bot_username', ''), chat_id, message_id)
        ),
        InlineKeyboardButton(
            helper_global.value("show_all_comments", "Show All"),
            url="http://telegram.me/%s?start=show_%s_%d" % (helper_global.value('bot_username', ''), chat_id, message_id)
        )
    ]]
    motd_markup = InlineKeyboardMarkup(motd_keyboard)

    config = helper_database.get_channel_config(chat_id)
    if config is None:
        return
    recent = config[3]
    records = helper_database.get_recent_records(chat_id, message_id, recent)

    comment_message = bot.send_message(
        chat_id=chat_id, 
        text=helper_global.records_to_str(records), 
        reply_to_message_id=message_id,
        reply_markup=motd_markup, 
        parse_mode=telegram.ParseMode.HTML
    ).result()
    helper_database.add_reflect(chat_id, message_id, comment_message.message_id)


def add_compact_comment(bot, chat_id, message_id, message):
    # Fallback media group message
    if message.media_group_id:
        add_comment(bot, chat_id, message_id, media_group_id=message.media_group_id)
        return

    if message.forward_from or message.forward_from_chat:
        new_message = deforward(bot, message)
        message_id = new_message.message_id
        message = new_message

    # Prepare Keyboard
    motd_keyboard = [[
        InlineKeyboardButton(
            helper_global.value("add_comment", "Add Comment"),
            url="http://telegram.me/%s?start=add_%d_%d" % (helper_global.value('bot_username', ''), chat_id, message_id)
        ), 
        InlineKeyboardButton(
            helper_global.value("show_all_comments", "Show All"),
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
    except:
        add_comment(bot, chat_id, message_id)


def avoidNone(s):
    if s:
        return str(s)
    return ''


def parse_entity(src, entity_list):
    if entity_list is None or len(entity_list) == 0:
        return src
    head = 0
    p_str = ""
    for entity in entity_list:
        begin_str = ''
        end_str = ''
        if entity.type == 'bold':
            begin_str = '<b>'
            end_str = '</b>'
        elif entity.type == 'code':
            begin_str = '<code>'
            end_str = '</code>'
        elif entity.type == 'italic':
            begin_str = '<i>'
            end_str = '</i>'
        elif entity.type == 'pre':
            begin_str = '<pre>'
            end_str = '</pre>'
        elif entity.type == 'text_link':
            begin_str = '<a href="%s">' % entity.url
            end_str = '</a>'
        p_str += src[head:entity.offset]
        p_str += begin_str
        p_str += src[entity.offset:(entity.offset + entity.length)]
        p_str += end_str
        head = entity.offset + entity.length
    p_str += src[head:]
    return p_str


def deforward(bot, msg):
    chat_id = msg.chat_id
    message_id = msg.message_id

    # Generate forward info
    has_msg_link = False
    if msg.forward_from:
        # Check username existence
        if msg.forward_from.username:
            forward_info = helper_global.value('fwd_source', 'Forwarded from:') + '@%s' % msg.forward_from.username
        else:
            forward_info = helper_global.value('fwd_source', 'Forwarded from:') + '<a href="tg://user?id=%d">%s</a>' % (
                msg.forward_from.id, 
                msg.forward_from.first_name + " " + avoidNone(msg.forward_from.last_name)
            )
    elif msg.forward_from_chat:
        # Check channel public/private
        if msg.forward_from_chat.username:
            forward_info = helper_global.value('fwd_source', 'Forwarded from:') + 'https://t.me/%s/%s' % (
                msg.forward_from_chat.username,
                msg.forward_from_message_id
            )
            has_msg_link = True
        else:
            forward_info = helper_global.value('fwd_source', 'Forwarded from:') + msg.forward_from_chat.title

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
            caption=parse_entity(avoidNone(msg.caption), msg.entities) + '\n\n' + forward_info,
            parse_mode='HTML',
            disable_notification=True
        ).result()
    elif message_type == 'document': 
        new_msg = bot.send_document(
            chat_id=chat_id,
            document=msg.document.file_id,
            caption=parse_entity(avoidNone(msg.caption), msg.entities) + '\n\n' + forward_info,
            parse_mode='HTML',
            disable_notification=True
        ).result()
    elif message_type == 'photo': 
        new_msg = bot.send_photo(
            chat_id=chat_id,
            photo=msg.photo[-1].file_id,
            caption=parse_entity(avoidNone(msg.caption), msg.entities) + '\n\n' + forward_info,
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
            caption=parse_entity(avoidNone(msg.caption), msg.entities) + '\n\n' + forward_info,
            parse_mode='HTML',
            disable_notification=True
        ).result()
    elif message_type == 'voice': 
        new_msg = bot.send_voice(
            chat_id=chat_id,
            voice=msg.voice.file_id,
            caption=parse_entity(avoidNone(msg.caption), msg.entities) + '\n\n' + forward_info,
            parse_mode='HTML',
            disable_notification=True
        ).result()

    if new_msg:
        bot.delete_message(chat_id=chat_id, message_id=message_id)
        return new_msg
    return msg
    

def channel_post_msg(bot, update):
    message = update.channel_post
    # print("Channel ID: %d, Channel Username: %s" % (message.chat_id, message.chat.username))
    chat_id = message.chat_id
    message_id = message.message_id
    config = helper_database.get_channel_config(chat_id)
    if config is None:
        return
    lang, mode, recent = config[1], config[2], config[3]

    # Auto Comment Mode
    if mode == 1: 
        add_comment(bot, chat_id, message_id, media_group_id=message.media_group_id)
    elif mode == 2:
        add_compact_comment(bot, chat_id, message_id, message)

    # Manual Mode
    elif mode == 0 and message.reply_to_message is not None and message.text == "/comment":
        message_id = message.reply_to_message.message_id
        bot.delete_message(chat_id=chat_id, message_id=message.message_id)
        add_compact_comment(bot, chat_id, message_id, message.reply_to_message)


class FilterChannelPost(BaseFilter):
    def filter(self, message):
        return message.chat.type == "channel"


channel_post_filter = FilterChannelPost()
_handler = MessageHandler(channel_post_filter, channel_post_msg)
