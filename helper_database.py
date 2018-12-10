#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" helper_database.py """
""" Copyright 2018, Jogle Lew """
import os
import sqlite3
import helper_const
import helper_global
from threading import Lock

def init_database(filepath):
    conn = sqlite3.connect(filepath, check_same_thread=False)
    helper_global.assign("database", conn)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE config (
            chat_id   text  PRIMARY KEY,
            lang      text,
            mode      int,
            recent    int,
            username  text,
            admin_id  text
        );
        """
    )
    cursor.execute(
        """
        CREATE TABLE reflect (
            chat_id     text,
            msg_id      text,
            comment_id  text,
            PRIMARY KEY (chat_id, msg_id)
        );
        """
    )
    cursor.execute(
        """
        CREATE TABLE record (
            chat_id     text,
            msg_id      text,
            username    text,
            name        text,
            type        text,
            content     text,
            media_id    text,
            date        text
        );
        """
    )
    conn.commit()


def execute(sql, params):
    lock.acquire()
    try:
        conn = helper_global.value("database", None)
        if conn is None:
            return
        cursor = conn.cursor()
        result = cursor.execute(sql, params)
        conn.commit()
    except Exception as e:
        lock.release()
        raise e
    lock.release()
    return result


def get_channel_config(chat_id):
    script = "SELECT * FROM config WHERE chat_id = ?"
    params = [str(chat_id)]
    result = list(execute(script, params))
    if len(result) == 0:
        return None
    return result[0]


def add_channel_config(channel_id, lang, mode, recent, channel_username, admin_id):
    script = "INSERT INTO config VALUES (?, ?, ?, ?, ?, ?)"
    params = [str(channel_id), lang, mode, recent, channel_username, str(admin_id)]
    execute(script, params)


def update_config_by_channel(channel_id, item, value):
    script = "UPDATE config SET %s = ? WHERE chat_id = ?" % item
    params = [value, str(channel_id)]
    execute(script, params)


def add_reflect(chat_id, msg_id, comment_id):
    script = "INSERT INTO reflect VALUES (?, ?, ?)"
    params = [str(chat_id), str(msg_id), str(comment_id)]
    execute(script, params)


def add_record(channel_id, msg_id, username, name, msg_type, msg_content, media_id, date):
    script = "INSERT INTO record VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    params = [str(channel_id), str(msg_id), username, name, msg_type, msg_content, media_id, date]
    execute(script, params)


def get_comment_id(channel_id, msg_id):
    script = "SELECT comment_id FROM reflect where chat_id = ? and msg_id = ?"
    params = [str(channel_id), str(msg_id)]
    result = list(execute(script, params))
    if len(result) == 0:
        return
    comment_id = int(result[0][0])
    return comment_id


def get_recent_records(channel_id, msg_id, recent, offset=0):
    script = "SELECT * FROM record where chat_id = ? and msg_id = ? ORDER BY date DESC LIMIT ? OFFSET ?"
    params = [str(channel_id), str(msg_id), recent, offset * recent]
    result = list(execute(script, params))
    return result


def get_channel_info_by_user(user_id):
    script = "SELECT chat_id, username FROM config where admin_id = ?"
    params = [str(user_id)]
    result = list(execute(script, params))
    return result


lock = Lock()
filepath = os.path.join(helper_const.DATABASE_DIR, "data.db")
if not os.path.exists(filepath):
    init_database(filepath)
else:
    conn = sqlite3.connect(filepath, check_same_thread=False)
    helper_global.assign("database", conn)

