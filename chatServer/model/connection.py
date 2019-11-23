import serverUtils as utils


def build_new_connection(connection, client_address, socketId):
    socket_data = {'nickname': '', 'socketConnection': connection, 'address': client_address, 'messages': [],
                   'rooms': [], 'socketId': socketId}

    return socket_data


def broadcast_message(request, sockets, message_queues, outputs):
    rooms = request['channel']
    # socketId = request['socketId']

    for key, socketOut in sockets.items():
        socket_id = socketOut['socketId']
        socket_rooms = sockets[socket_id]['rooms']
        for room in socket_rooms:
            if room in rooms:
                message_queues[socket_id].put(request)
                outputs.append(sockets[socket_id]['socketConnection'])


def send_response(response, socket_messages):
    socket_messages.put(response)


def join_room(request, sockets, socket, channels, message_queues):
    room = request['channel']
    socket_id = socket.fileno()

    if room not in channels:
        channels.append(room)

    sockets[socket_id]['rooms'].append(room)

    response_text = 'successfully joined room' + room

    response = utils.buildMessage('/joinSuccess', request['nickname'], room, response_text)
    message_queues[socket_id].put(response)

    return sockets


def leave_room(request, sockets, socket, rooms, message_queues):
    socket_id = socket.fileno()
    room = request['channel']
    if room in sockets[socket_id]['rooms']:
        sockets[socket_id]['rooms'].remove(room)
        response_text = 'You have left room: ' + room
    else:
        response_text = 'You were never in that room'

    response = utils.buildMessage('/leaveRoom', request['nickname'], room, response_text)
    message_queues[socket_id].put(response)


def list_rooms(request, rooms, socket, message_queues):
    if rooms:
        response_text = ''
        for room in rooms:
            response_text += ('\n' + room)

    else:
        response_text = 'No Rooms created yet'
    message = utils.buildMessage(request['command'], request['nickname'], request['channel'], response_text)
    message_queues[socket.fileno()].put(message)


def list_room_members(request, sockets, s, rooms, message_queues):
    socket_id = s.fileno()
    room = request['channel']

    if room in rooms:
        response_message = ''

        for key, socket in sockets.items():
            if room in socket['rooms']:
                response_message += "\n" + socket['nickname']

    else:
        response_message = 'That room does not exist!'

    message = utils.buildMessage('/roomMembers', request['nickname'], room, response_message)
    message_queues[socket_id].put(message)


def set_nickname(socket, request, sockets, message_queues):
    nickname = request['nickname']
    socket_id = socket.fileno()

    sockets[socket_id]['nickname'] = nickname

    message = {'nickname': nickname, 'command': 'nicknameSet', 'message': 'Nickname set in server as ' + nickname}

    message_queues[socket_id].put(message)
    return sockets
    # for key in sockets:
    #         if (sockets[key]['socketId'] == socketId):
    #                 sockets[key]['messages'].append(message)


def send_direct_message(request, sockets, s, message_queues, outputs):
    destination = request['channel']

    user_present = False

    for key, socket in sockets.items():

        if socket['nickname'] == destination:
            message_queues[socket['socketId']].put(utils.buildMessage('/direct', request['nickname'], destination,
                                                                      request['message']))
            outputs.append(socket['socketConnection'])
            user_present = True

    if not user_present:
        message = 'No user found with that nickname'
        message_queues[s.fileno()].put(utils.buildMessage('/direct', request['nickname'], destination,
                                                          message))


def say_thanks(request, s, message_queues):
    message = 'Thanks for chatting ' + request['nickname'] + '!'
    message_queues[s.fileno()].put(utils.buildMessage('/close', request['nickname'], 'n/a/', message))
