#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" helper_global.py """
""" Copyright 2018, Jogle Lew """
from threading import Lock
lock = Lock()

class GlobalVar:
    var_set = {}


def assign(var_name, var_value):
    lock.acquire()
    GlobalVar.var_set[var_name] = var_value
    lock.release()


def value(var_name, default_value):
    lock.acquire()
    if not var_name in GlobalVar.var_set:
        GlobalVar.var_set[var_name] = default_value
    result = GlobalVar.var_set[var_name]
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


def records_to_str(records):
    s = value("comment_header", "") + "\n"
    if records is None or len(records) == 0:
        s += value("comment_empty", "")
        return s
    records = records[::-1]
    for record in records:
        username = record[2]
        name = record[3]
        msg_type = record[4]
        msg_content = record[5]
        s += ("<b>%s</b>: " % name)
        if not msg_type == "text":
            s += ("[%s] " % msg_type)
        s += msg_content + "\n"
    return s
