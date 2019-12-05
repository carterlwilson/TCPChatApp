import threading
import sys
import client
import queue
import clientUtils as utils
import client_const as const

class ClientInfo:

    def __int__(self):
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
              'send broadcast - broadcast/<room>/<message>\n' +
              'join channel = join/<channel>\n' + 
              'list all rooms = listRooms\n' + 
              'leave a room = leave/<room>\n' + 
              'show members of a room = members/<room>\n' +
              'send direct message to user = direct/<username>/<message>\n' 
              'close connection with server = close\n\n\n')

    def add_outbound_message(self, message, outbound_message_queue):
        outbound_message_queue.put(message)

    def parse_inbound_messages(self, inbound_message_queue, clientInfo):
        while not inbound_message_queue.empty():
            message = inbound_message_queue.get()

            #if message['command'] == const.JOIN_SUCCESS_CMD:
                #clientInfo.add_room(message['channel'])

            if message['command'] == const.NICK_SET_CMD:
                clientInfo.set_nickname(message['nickname'])

            # if message['command'] == const.LEAVE_ROOM_CMD:
            #     if message['room'] in self.rooms:
            #         clientInfo.remove_room(message['room'])
        return clientInfo

    def parse_menu_choice(self, user_input, outbound_message_queue, nickname):
        input_array = user_input.split('/', 2)

        if input_array[0] == 'quit':
            sys.exit()

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

        else:
            print('invalid command')

        #return self

    def menu_action(self, outbound_message_queue, inbound_message_queue):
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
            clientInfo = self.parse_inbound_messages(inbound_message_queue, clientInfo)
            self.parse_menu_choice(menu_choice, outbound_message_queue, clientInfo.get_nickname())


def main():
    host = 'localhost'
    #host = '34.70.217.186'  #ip address for cloud hosted server
    port = 1025
    outbound_message_queue = queue.Queue()
    inbound_message_queue = queue.Queue()

    menu = MenuClass()
    current_client = client.chatClient(host, port)

    thread_ui = threading.Thread(target=menu.menu_action, args=(outbound_message_queue, inbound_message_queue))
    thread_ui.start()

    thread_client = threading.Thread(target=current_client.run_client, args=(outbound_message_queue,
                                                                             inbound_message_queue))
    thread_client.start()


if __name__ == "__main__":
    main()
