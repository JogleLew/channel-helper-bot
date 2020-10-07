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
            admin_id  text,
            notify    int,
            button    int
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
        CREATE TABLE button (
            chat_id     text,
            msg_id      text,
            options     text,
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
            date        text,
            user_id     text,
            ori_msg_id  text
        );
        """
    )
    cursor.execute(
        """
        CREATE TABLE blacklist (
            chat_id     text,
            user_id     text,
            name        text,
            PRIMARY KEY (chat_id, user_id)
        );
        """
    )
    cursor.execute(
        """
        CREATE TABLE reaction (
            chat_id     text,
            msg_id      text,
            user_id     text,
            option      int,
            PRIMARY KEY (chat_id, msg_id, user_id)
        );
        """
    )
    cursor.execute("CREATE INDEX record_chat_id_msg_id on record (chat_id, msg_id);")
    cursor.execute("CREATE INDEX record_user_id_ori_msg_id on record (user_id, ori_msg_id);")
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


def delete_channel_config(chat_id):
    script = "DELETE FROM config WHERE chat_id = ?"
    params = [str(chat_id)]
    result = list(execute(script, params))
    return result


def get_all_channel_config():
    script = "SELECT * FROM config"
    params = []
    result = list(execute(script, params))
    return result


def add_channel_config(channel_id, lang, mode, recent, channel_username, admin_id, notify, button):
    script = "INSERT INTO config VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
    params = [str(channel_id), lang, mode, recent, channel_username, str(admin_id), notify, button]
    execute(script, params)


def update_config_by_channel(channel_id, item, value):
    script = "UPDATE config SET %s = ? WHERE chat_id = ?" % item
    params = [value, str(channel_id)]
    execute(script, params)


def add_button_options(chat_id, msg_id, options):
    script = "DELETE FROM button WHERE chat_id = ? AND msg_id = ?"
    params = [str(chat_id), str(msg_id)]
    execute(script, params)
    script = "INSERT INTO button VALUES (?, ?, ?)"
    params = [str(chat_id), str(msg_id), " ".join(options)]
    execute(script, params)


def get_button_options(chat_id, msg_id):
    script = "SELECT options FROM button WHERE chat_id = ? AND msg_id = ?"
    params = [str(chat_id), str(msg_id)]
    result = list(execute(script, params))
    if len(result) > 0:
        return result[0][0].split()
    script = "SELECT options FROM button WHERE chat_id = ? AND msg_id = ?"
    params = [str(chat_id), str(0)]
    result = list(execute(script, params))
    if len(result) > 0:
        return result[0][0].split()
    return helper_const.DEFAULT_BUTTONS


def get_default_button_options(chat_id):
    script = "SELECT options FROM button WHERE chat_id = ? AND msg_id = ?"
    params = [str(chat_id), str(0)]
    result = list(execute(script, params))
    if len(result) == 0:
        return helper_const.DEFAULT_BUTTONS
    return result[0][0].split()


def add_reflect(chat_id, msg_id, comment_id):
    script = "DELETE FROM reflect WHERE chat_id = ? AND msg_id = ?"
    params = [str(chat_id), str(msg_id)]
    execute(script, params)
    script = "INSERT INTO reflect VALUES (?, ?, ?)"
    params = [str(chat_id), str(msg_id), str(comment_id)]
    execute(script, params)


def check_reflect(chat_id, msg_id):
    script = "SELECT * FROM reflect WHERE chat_id = ? AND msg_id = ?"
    params = [str(chat_id), str(msg_id)]
    result = list(execute(script, params))
    if len(result) == 0:
        return False
    return True


def get_reflect_by_msg_id(chat_id, msg_id_or_comment_id):
    script = "SELECT * FROM reflect WHERE chat_id = ? AND (msg_id = ? OR comment_id = ?)"
    params = [str(chat_id), str(msg_id_or_comment_id), str(msg_id_or_comment_id)]
    result = list(execute(script, params))
    if len(result) == 0:
        return None
    return result[0]


def delete_reflect(chat_id, msg_id):
    script = "DELETE FROM reflect WHERE chat_id = ? AND msg_id = ?"
    params = [str(chat_id), str(msg_id)]
    execute(script, params)


def add_record(channel_id, msg_id, username, name, msg_type, msg_content, media_id, date, user_id, ori_msg_id):
    if len(name) > 15:
        name = name[:15] + "..."
    script = "SELECT * FROM record WHERE user_id = ? AND ori_msg_id = ?"
    params = [str(user_id), str(ori_msg_id)]
    result = list(execute(script, params))
    if len(result) == 0:
        script = "INSERT INTO record VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        params = [str(channel_id), str(msg_id), username, name, msg_type, msg_content, media_id, date, str(user_id), str(ori_msg_id)]
        execute(script, params)
        return 0
    else:
        script = "UPDATE record SET type = ?, content = ?, media_id = ? WHERE user_id = ? AND ori_msg_id = ?"
        params = [msg_type, msg_content, media_id, str(user_id), str(ori_msg_id)]
        execute(script, params)
        return 1


def get_comment_id(channel_id, msg_id):
    script = "SELECT comment_id FROM reflect WHERE chat_id = ? and msg_id = ?"
    params = [str(channel_id), str(msg_id)]
    result = list(execute(script, params))
    if len(result) == 0:
        return None
    comment_id = int(result[0][0])
    return comment_id


def get_origin_post(channel_id, msg_id):
    script = "SELECT comment_id FROM reflect WHERE chat_id = ? and msg_id = ?"
    params = [str(channel_id), str(msg_id)]
    result = list(execute(script, params))
    if len(result) == 0:
        return None
    comment_id = result[0][0]
    return comment_id


def get_recent_records(channel_id, msg_id, recent, offset=0):
    script = "SELECT *, ROWID FROM record WHERE chat_id = ? and msg_id = ? ORDER BY date DESC LIMIT ? OFFSET ?"
    params = [str(channel_id), str(msg_id), recent, offset * recent]
    result = list(execute(script, params))
    return result


def get_record_by_rowid(row_id):
    script = "SELECT * FROM record WHERE ROWID = ?"
    params = [row_id]
    result = list(execute(script, params))
    return result


def delete_record_by_rowid(row_id):
    script = "DELETE FROM record WHERE ROWID = ?"
    params = [row_id]
    result = list(execute(script, params))
    return result


def get_base_offset_by_rowid(channel_id, msg_id, row_id):
    script = "SELECT count(*) FROM record WHERE chat_id = ? AND msg_id = ? AND ROWID >= ?"
    params = [str(channel_id), str(msg_id), row_id]
    result = list(execute(script, params))
    return result[0][0]


def get_prev_rowid(channel_id, msg_id, row_id):
    script = "SELECT ROWID FROM record WHERE chat_id = ? AND msg_id = ? AND ROWID > ? ORDER BY ROWID ASC LIMIT 1"
    params = [str(channel_id), str(msg_id), row_id]
    result = list(execute(script, params))
    if result is not None and len(result) == 1:
        return result[0][0]
    return -1


def get_next_rowid(channel_id, msg_id, row_id):
    script = "SELECT ROWID FROM record WHERE chat_id = ? AND msg_id = ? AND ROWID < ? ORDER BY ROWID DESC LIMIT 1"
    params = [str(channel_id), str(msg_id), row_id]
    result = list(execute(script, params))
    if result is not None and len(result) == 1:
        return result[0][0]
    return -1


def get_channel_info_by_user(user_id):
    script = "SELECT chat_id, username FROM config WHERE admin_id = ?"
    params = [str(user_id)]
    result = list(execute(script, params))
    return result


def ban_user(channel_id, user_id, name):
    script = "INSERT INTO blacklist VALUES (?, ?, ?)"
    params = [str(channel_id), str(user_id), name]
    result = list(execute(script, params))
    return result


def unban_user(channel_id, user_id, name):
    script = "DELETE FROM blacklist WHERE chat_id = ? AND user_id = ?"
    params = [str(channel_id), str(user_id)]
    result = list(execute(script, params))
    return result


def check_ban(channel_id, user_id):
    script = "SELECT * FROM blacklist WHERE chat_id = ? AND user_id = ?"
    params = [str(channel_id), str(user_id)]
    result = list(execute(script, params))
    return len(result) > 0


def add_reaction(channel_id, msg_id, user_id, like_id):
    script = "SELECT count(*) FROM reaction WHERE chat_id = ? AND msg_id = ? AND user_id = ?"
    params = [str(channel_id), str(msg_id), str(user_id)]
    result = list(execute(script, params))[0][0]
    if result == 0:
        script = "INSERT INTO reaction VALUES(?, ?, ?, ?)"
        params = [str(channel_id), str(msg_id), str(user_id), like_id]
    else:
        script = "UPDATE reaction SET option = ? WHERE chat_id = ? AND msg_id = ? AND user_id = ?"
        params = [like_id, str(channel_id), str(msg_id), str(user_id)]
    execute(script, params)


def get_reaction_stat(channel_id, msg_id):
    script = "SELECT option, count(*) FROM reaction WHERE chat_id = ? AND msg_id = ? GROUP BY option"
    params = [str(channel_id), str(msg_id)]
    result = list(execute(script, params))
    r = {}
    for like_id, count in result:
        r[like_id] = count
    return r


def clear_reaction(channel_id, msg_id):
    script = "DELETE FROM reaction WHERE chat_id = ? AND msg_id = ?"
    params = [str(channel_id), str(msg_id)]
    result = list(execute(script, params))
    return result


lock = Lock()
filepath = os.path.join(helper_const.DATABASE_DIR, "data.db")
if not os.path.exists(filepath):
    init_database(filepath)
else:
    conn = sqlite3.connect(filepath, check_same_thread=False)
    helper_global.assign("database", conn)

