import threading
import sys
import client
import clientUtils as utils
import client_const as const
import os
try:
   import queue
except ImportError:
   import Queue as queue

class ClientInfo:

    def __init__(self):
        self.nickname = ''
        self.rooms = ['home']

    def set_nickname(self, nick):
        self.nickname = nick

    def get_nickname(self):
        return self.nickname

    def add_room(self, room):
        self.rooms.append(room)

    def remove_room(self, room):
        self.rooms.remove(room)


class MenuClass:

    def print_menu(self):
        print('\n\n\nCommands:\n'
              'send broadcast = broadcast/<room>/<message>\n' +
              'join channel = join/<channel>\n' + 
              'list all rooms = listRooms\n' + 
              'leave a room = leave/<room>\n' + 
              'show members of a room = members/<room>\n' +
              'send direct message to user = direct/<username>/<message>\n' 
              'close connection with server = close\n' + 
              're-connect to server = connect/<nickname>\n' +
              'set nickname = nick/<nickname>\n' + 
              'quit program = quit\n\n\n')

    def add_outbound_message(self, message, outbound_message_queue):
        outbound_message_queue.put(message)

    def parse_inbound_messages(self, inbound_message_queue, clientInfo):
        while not inbound_message_queue.empty():
            message = inbound_message_queue.get()

            if message['command'] == const.NICK_SET_CMD:
                clientInfo.set_nickname(message['nickname'])

    def parse_menu_choice(self, user_input, outbound_message_queue, nickname, event_queue):
        input_array = user_input.split('/', 2)

        if input_array[0] == 'quit':
            os._exit(1)

        elif input_array[0] == 'broadcast':
            utils.broadcast_message(nickname, input_array[1], input_array[2], outbound_message_queue)

        elif input_array[0] == 'join':
            message = utils.build_message(const.JOIN_CMD, nickname, input_array[1], '')
            outbound_message_queue.put(message)

        elif input_array[0] == 'direct':
            user = input_array[1]
            message_input = input_array[2]
            utils.send_direct_message(nickname, user, message_input, outbound_message_queue)

        elif input_array[0] == 'listRooms':
            utils.list_rooms(nickname, outbound_message_queue)

        elif input_array[0] == 'leave':
            utils.leave_room(const.LEAVE_ROOM_CMD, nickname, input_array[1], outbound_message_queue)

        elif input_array[0] == 'members':
            utils.list_room_members(nickname, input_array[1], outbound_message_queue)

        elif input_array[0] == 'close':
            utils.close_connection(nickname, outbound_message_queue)

        elif input_array[0] == 'connect':
            event_queue.put(user_input)

        elif input_array[0] == 'nick':
            utils.send_nick(input_array[1], outbound_message_queue)

        else:
            print('invalid command')

    def menu_action(self, outbound_message_queue, inbound_message_queue, event_queue):
        x = True
        clientInfo = ClientInfo()

        print('What would you like your nickname to be?')
        nickname_choice = input()
        utils.send_nick(nickname_choice, outbound_message_queue)

        self.print_menu()
        while x:
            menu_choice = input()
            # This is used to change variables in this thread **IT DOES NOT PRINT MSGS FROM SERVER***,
            # it is a workaround for sharing variables between the two threads like nickname and rooms
            self.parse_inbound_messages(inbound_message_queue, clientInfo)
            self.parse_menu_choice(menu_choice, outbound_message_queue, clientInfo.get_nickname(), event_queue)


def main():
    #host = 'localhost'
    host = '35.225.202.2'  #ip address for cloud hosted server
    port = 1025
    outbound_message_queue = queue.Queue()
    inbound_message_queue = queue.Queue()
    event_queue = queue.Queue()

    current_client = client.chatClient(host, port)
    menu = MenuClass()


    thread_ui = threading.Thread(target=menu.menu_action, args=(outbound_message_queue, inbound_message_queue, event_queue))
    thread_ui.start()

    thread_client = threading.Thread(target=current_client.run_client, args=(outbound_message_queue,
                                                                             inbound_message_queue, event_queue))
    thread_client.start()

    x = True
    while x:
        if not event_queue.empty():
            event = event_queue.get()
            event_array = event.split('/',1)
            if event_array[0] == "connect":
                thread_client = threading.Thread(target=current_client.run_client, args=(outbound_message_queue,
                                                                             inbound_message_queue, event_queue))
                thread_client.start()
                nickname_choice = event_array[1]
                utils.send_nick(nickname_choice, outbound_message_queue)


if __name__ == "__main__":
    main()
