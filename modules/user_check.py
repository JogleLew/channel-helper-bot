def in_channel(bot, channel_id, user_id):
    return bot.get_chat_member(chat_id=channel_id, user_id=user_id).status in ["creator", "administrator", "member"]


def is_creator(bot, channel_id, user_id):
    return bot.get_chat_member(chat_id=channel_id, user_id=user_id).status is "creator"