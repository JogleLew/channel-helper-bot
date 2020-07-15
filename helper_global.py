#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" helper_global.py """
""" Copyright 2018, Jogle Lew """
import helper_const
from threading import Lock
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

lock = Lock()

class GlobalVar:
    var_set = {}


def assign(var_name, var_value, lang=helper_const.DEFAULT_LANG):
    lock.acquire()
    if not lang in GlobalVar.var_set:
        GlobalVar.var_set[lang] = {}
    GlobalVar.var_set[lang][var_name] = var_value
    lock.release()


def value(var_name, default_value, lang=helper_const.DEFAULT_LANG):
    if lang == "all":
        result = ""
        for lang_item in helper_const.LANG_LIST:
            result += value(var_name, default_value, lang=lang_item) + "\n\n"
        return result
    if not lang in GlobalVar.var_set:
        lang = helper_const.DEFAULT_LANG
    lock.acquire()
    if not var_name in GlobalVar.var_set[lang]:
        GlobalVar.var_set[lang][var_name] = default_value
    result = GlobalVar.var_set[lang][var_name]
    lock.release()
    return result


def get_sender_name(message):
    real_sender = message.from_user
    if message.forward_from:
        real_sender = message.forward_from
    username = real_sender.first_name
    if real_sender.last_name:
        username = username + " " + real_sender.last_name
    if message.forward_from_chat:
        username = message.forward_from_chat.title
    return username


def records_to_str(records, lang):
    s = value("comment_header", "", lang=lang) + "\n"
    if records is None or len(records) == 0:
        s += value("comment_empty", "", lang=lang)
        return s
    records = records[::-1]
    for record in records:
        username = record[2]
        name = record[3].replace('<', '&lt;').replace('>', '&gt;')
        msg_type = record[4]
        msg_content = record[5]
        s += ("<b>%s</b>: " % name)
        if not msg_type == "text":
            s += ("[%s] " % msg_type)
        s += msg_content + "\n"
    return s


def records_to_buttons(records, channel_id, msg_id):
    b = []
    if records is None or len(records) == 0:
        return b
    records = records[::-1]
    for idx, record in enumerate(records):
        username = record[2]
        name = record[3]
        msg_type = record[4]
        msg_content = record[5]
        row_id = record[10]
        s = ("%s: " % name)
        if not msg_type == "text":
            s += ("[%s] " % msg_type)
        s += msg_content
        button = [[
            InlineKeyboardButton(
                s,
                callback_data="msg_detail,%d,%d,%d" % (channel_id, msg_id, row_id)
            )
        ]]
        b += button
    return b


def parse_entity(src, entity_list):
    if entity_list is None or len(entity_list) == 0:
        return src.replace('<', '&lt;').replace('>', '&gt;')

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
        elif entity.type == 'strikethrough':
            begin_str = '<del>'
            end_str = '</del>'
        elif entity.type == 'pre':
            begin_str = '<pre>'
            end_str = '</pre>'
        elif entity.type == 'text_link':
            begin_str = '<a href="%s">' % entity.url
            end_str = '</a>'
        p_str += src[head:entity.offset].replace('<', '&lt;').replace('>', '&gt;')
        p_str += begin_str
        p_str += src[entity.offset:(entity.offset + entity.length)].replace('<', '&lt;').replace('>', '&gt;')
        p_str += end_str
        head = entity.offset + entity.length
    p_str += src[head:]
    return p_str


def send_intro_template(bot, chat_id, lang, key, text_key):
    # Prepare Keyboard
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
    bot.send_message(
        chat_id=chat_id, 
        text=value(text_key, "", lang=current_lang),
        reply_markup=motd_markup
    )
