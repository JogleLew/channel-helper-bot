#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Channel Helper Bot """
""" helper_string.py """
""" Copyright 2018, Jogle Lew """

import helper_global

helper_string = {
    "development_text": "该功能正在开发中...",
    "permission_denied_text": "你怕不是假的 jogle",
    "reload_cmd_success": "重启好了，很棒棒哦！",
    "reload_cmd_failed": "嗯，好像出现了一些问题呢…",
    "start_cmd_text": "这是由 JogleLew 开发的频道回复助手 Bot 。你可以使用 /help 命令查看详细使用说明。", 
    "help_cmd_text": "欢迎使用 Channel Helper Bot，本 bot 可以为您的频道提供回复和展示评论信息的入口，从而为频道提供互动的平台。\nGithub链接：https://github.com/JogleLew/channel-helper-bot\n使用此 bot 即为允许本 bot 在您的频道内进行发送和编辑操作，并收集和存储评论信息。\n使用步骤：\n1. 使用 /register 命令登记您的频道信息。\n2. 将此 bot 添加为频道管理员。\n3. 完成。如需更改配置请使用 /option 命令。",
    "add_comment": "添加评论",
    "show_all_comments": "显示所有评论",
    "comment_header": "===== 评论区 =====",
    "comment_empty": "空空如也",
    "start_comment_mode": "您已进入评论模式，向我发送消息即可进行评论。使用 /cancel 命令可以中止评论模式。",
    "stop_comment_mode": "您已退出评论模式",
    "comment_success": "评论成功",
    "prev_page": "上一页",
    "next_page": "下一页",
    "no_prev_page": "没有上一页了",
    "no_next_page": "没有下一页了",
    "register_cmd_text": "请从您的频道中转发一条消息给我，以便我获取频道的 ID。",
    "register_cmd_invalid": "这条消息中似乎不包含频道信息呢...请从您的频道中转发一条消息给我",
    "register_cmd_failed": "您的频道信息可能已被记录，如有问题请联系管理员 @JogleLew",
    "register_cmd_success": "您的频道信息已记录，并启用了默认的评论设置。如需修改配置，请使用 /option 命令。\n请将本 bot 添加为频道的管理员，即可开始使用评论功能。",
    "option_no_channel": "您还没有登记过频道信息，请先使用 /register 命令完成登记。",
    "option_finish": "完成配置",
    "option_finished": "配置已完成",
    "option_choose_channel": "请选择一个频道以进行配置",
    "option_choose_item": "请选择一个项目以进行配置\nmode: bot 的工作模式\nrecent: 在频道中显示的评论数量",
    "option_choose_mode_value": "本 bot 有两种工作模式\n模式 0: 手动模式。当频道中新增消息时，bot 不会自动创建评论消息。当频道管理员使用 /comment 回复需要评论的原始消息时，bot 才会创建评论消息。\n模式 1: 自动模式。当频道中新增消息时，bot 自动创建评论消息。\n请选择您所需要的工作模式：",
    "option_choose_recent_value": "在频道中仅显示最近的若干条消息。请选择频道显示的最近条目数量：",
    "option_update_success": "配置更新成功",
    "option_update_failed": "配置更新失败"
}

for item, value in helper_string.items():
    helper_global.assign(item, value)
