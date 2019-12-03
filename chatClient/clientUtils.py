import client_const as const

def build_message(command, nickname, channel, message_text):
    message = {'command': command, 'nickname': nickname, 'channel': channel, 'message': message_text}
    return message

def broadcast_message(nickname, channel, message_text, outbound_message_queue):
    message = build_message(const.BROADCAST_CMD, nickname, channel, message_text)
    outbound_message_queue.put(message)


def send_direct_message(nickname, destination_user, message, outbound_message_queue):
    message = build_message(const.DIR_MSG_COMD, nickname, destination_user, message)
    outbound_message_queue.put(message)


def send_nick(data, message_queue, channel):
    message = {'nickname': data, 'command': '/nick', 'channel': channel}
    message_queue.put(message)


def list_rooms(nickname, outbound_message_queue):
    message = build_message(const.LIST_ROOMS_CMD, nickname, 'n/a', 'n/a')
    outbound_message_queue.put(message)


def leave_room(command, nickname, channel, outbound_message_queue):
    message = build_message(const.LEAVE_ROOM_CMD, nickname, channel, 'n/a')
    outbound_message_queue.put(message)


def list_room_members(nickname, room, outbound_message_queue):
    message = build_message(const.LIST_ROOM_MEMBER_CMD, nickname, room, 'n/a')
    outbound_message_queue.put(message)


def close_connection(nickname, outbound_message_queue):
    message = build_message(const.CLOSE_CONN_CMD, nickname, 'n/a', 'n/a')
    outbound_message_queue.put(message)

def format_message(message):
    if message['nickname']:
        message['message'] = message['nickname'] + ': ' + message['message']
    if message['channel']:
        message['message'] = '[' + message['channel'] + '] ' + message['message']
    return message
