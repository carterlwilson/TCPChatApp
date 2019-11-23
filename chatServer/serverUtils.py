def buildMessage(command, nickname, channel, messageText):
    message = {}
    message['command'] = command
    message['nickname'] = nickname
    message['channel'] = channel
    message['message'] = messageText
    return message