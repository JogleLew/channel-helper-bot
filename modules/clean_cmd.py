#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" clean_cmd.py """
""" Copyright 2018, Jogle Lew """
import json
import datetime
import helper_const
import helper_global
import helper_database
from telegram.ext import CommandHandler
from telegram.error import TimedOut, NetworkError

def get_invalid_channel_access(bot):
    configs = helper_database.get_all_channel_config()
    invalid_list = []
    for config in configs:
        channel_id = int(config[0])
        admin_id = int(config[5])
        try:
            chat_members = bot.get_chat_administrators(chat_id=channel_id).result()
        except TimedOut:
            pass
        except NetworkError:
            pass
        except:
            invalid_list.append(config)
    return invalid_list


def check_channel_access(bot, job):
    invalid_list = get_invalid_channel_access(bot)
    for owner_id in helper_const.BOT_OWNER:
        bot.send_message(chat_id=owner_id, text=str(invalid_list))


def clean(bot, update, args, job_queue):
    from_id = update.message.from_user.id
    if not from_id in helper_const.BOT_OWNER:
        return
    if len(args) == 1 and args[0] == "check":
        invalid_list = get_invalid_channel_access(bot)
        bot.send_message(chat_id=from_id, text=helper_global.value("clean_cmd_start", ""))
        bot.send_message(chat_id=from_id, text=str(invalid_list))
    if len(args) == 2 and args[0] == "touch":
        channel_id = int(args[1])
        chat_members = bot.get_chat_administrators(chat_id=channel_id).result()
        for member in chat_members:
            if member.user.username and member.user.username == helper_global.value('bot_username', ''):
                bot.send_message(chat_id=from_id, text='%s %s %s' % (member.can_post_messages, member.can_edit_messages, member.can_delete_messages))
    if len(args) == 2 and args[0] == "delete":
        channel_id = int(args[1])
        helper_database.delete_channel_config(channel_id)
        bot.send_message(chat_id=from_id, text=helper_global.value("clean_cmd_deleted", ""))
    if len(args) == 2 and args[0] == "auto":
        job = helper_global.value("check_daily_job", None)
        if job is None:
            job = job_queue.run_daily(check_channel_access, datetime.time(0, 0))
        if args[1] == "on":
            job.enabled = True 
        elif args[1] == "off":
            job.enabled = False
        helper_global.assign("check_daily_job", job)
        bot.send_message(chat_id=from_id, text=helper_global.value("clean_cmd_set", ""))


_handler = CommandHandler('clean', clean, pass_args=True, pass_job_queue=True)
