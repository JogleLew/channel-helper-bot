#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" helper_main.py """
""" Copyright 2018, Jogle Lew """
import json
import logging
import traceback
import importlib
import datetime
import helper_global
import helper_database
import telegram
import telegram.bot
from telegram.ext import messagequeue as mq
from telegram.ext import Updater, CommandHandler
from telegram.utils.request import Request

# config logger
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# import constant, strings, database
helper_const = importlib.import_module('helper_const')
helper_string = importlib.import_module('helper_string')
helper_database = importlib.import_module('helper_database')

# load admin list
helper_global.assign('admin_list', [])


def reload_admin_list():
    global admin_list
    admin_list = helper_const.BOT_OWNER
    helper_global.assign('admin_list', admin_list)


reload_admin_list()

# config bot
class MQBot(telegram.bot.Bot):
    '''A subclass of Bot which delegates send method handling to MQ'''
    def __init__(self, *args, is_queued_def=True, mqueue=None, **kwargs):
        super(MQBot, self).__init__(*args, **kwargs)
        # below 2 attributes should be provided for decorator usage
        self._is_messages_queued_default = is_queued_def
        self._msg_queue = mqueue or mq.MessageQueue()

    def __del__(self):
        try:
            self._msg_queue.stop()
        except:
            pass
        super(MQBot, self).__del__()

    @mq.queuedmessage
    def send_message(self, *args, **kwargs):
        '''Wrapped method would accept new `queued` and `isgroup`
        OPTIONAL arguments'''
        return super(MQBot, self).send_message(*args, **kwargs)

    @mq.queuedmessage
    def edit_message_text(self, *args, **kwargs):
        '''Wrapped method would accept new `queued` and `isgroup`
        OPTIONAL arguments'''
        return super(MQBot, self).edit_message_text(*args, **kwargs)
 
 
q = mq.MessageQueue(all_burst_limit=3, all_time_limit_ms=3000)
request = Request(con_pool_size=8)
bot = MQBot(token=helper_const.BOT_TOKEN, request=request, mqueue=q)
bot_username = bot.get_me().username
helper_global.value('bot', bot)
helper_global.value('bot_username', bot_username)
updater = Updater(bot=bot)
dispatcher = updater.dispatcher
job_queue = updater.job_queue


def check_admin(check_id):
    admin_list = helper_global.value('admin_list', [])
    if check_id in admin_list:
        return True
    return False


# initial reload command
def bot_reload(bot, update):
    global helper_const
    global helper_string
    global helper_database
    global command_module
    if not check_admin(update.message.from_user.id):
        permission_denied = helper_global.value("permission_denied_text", "")
        bot.send_message(chat_id=update.message.chat_id, text=permission_denied)
        return

    ## update constant
    helper_const = importlib.reload(helper_const)
    helper_string = importlib.reload(helper_string)
    helper_database = importlib.reload(helper_database)
    reload_admin_list()

    ## remove old handlers
    for current_module in command_module:
        dispatcher.remove_handler(current_module._handler)

    ## reload modules and update handlers
    try:
        command_module = []
        for module_name in helper_const.MODULE_NAME:
            current_module = importlib.import_module(module_name)
            current_module = importlib.reload(current_module)
            command_module.append(current_module)
            dispatcher.add_handler(current_module._handler)
        
        success_text = helper_global.value("reload_cmd_success", "")
        bot.send_message(chat_id=update.message.chat_id, text=success_text)
    except Exception as e:
        failed_text = helper_global.value("reload_cmd_failed", "")
        bot.send_message(chat_id=update.message.chat_id, text=failed_text)
        bot.send_message(chat_id=update.message.chat_id, text=traceback.print_exc())

reload_handler = CommandHandler('reload', bot_reload)
dispatcher.add_handler(reload_handler)

# initial other commands
command_module = []
for module_name in helper_const.MODULE_NAME:
    current_module = importlib.import_module(module_name)
    command_module.append(current_module)
    dispatcher.add_handler(current_module._handler)

# check whether bot is in channel every day at 0:00
def check_channel_access(bot, job):
    configs = helper_database.get_all_channel_config()
    for config in configs:
        channel_id = int(config[0])
        admin_id = int(config[5])
        try:
            chat_members = bot.get_chat_administrators(chat_id=channel_id)
        except:
            helper_database.delete_channel_config(channel_id)
            try:
                bot.send_message(chat_id=admin_id, text=helper_global.value("register_delete_info", ""))
            except:
                pass


job_queue.run_daily(check_channel_access, datetime.time(0, 0))

updater.start_polling()

