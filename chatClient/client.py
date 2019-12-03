import socket
import sys
import pickle
import select
import queue
import clientUtils as utils


class chatClient:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.events = queue.Queue()
        self.sock = None
        self.rooms = []
        self.nickname = 'carter'

    def connect_server(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.connect((str(self.host), int(self.port)))
        self.sock.setblocking(0)

    def send_message(self, data):
        self.sock.send(pickle.dumps(data))

    def process_response(self, data):
        if data:
            response_data = pickle.loads(data)
            return response_data['message']

    def add_outbound_broadcast(self, message, messageQueue):
        if message:
            messageQueue.put(message)

    def send_nick(self, data, messageQueue):
        message = {'nickname': data, 'command': '/nick', 'channel': self.channel}
        messageQueue.put(message)
        # try:
        #     self.sock.send(pickle.dumps(message))
        # except:
        #     print('could not send nick message')

    def run_client(self, outboundMessageQueue, inboundMessageQueue):

        try:
            self.connect_server()
        except:
            print('Could not connect to chat server')
            sys.exit(1)

        # self.sendNick(self.nickname,outboundMessageQueue)

        inputs = [self.sock]
        outputs = [self.sock]

        if self.sock:
            self.events.put('server_connected')
            self.sock.settimeout(1)

        while inputs:
            readable, writable, exceptional = select.select(inputs, outputs, [])

            if self.sock in readable:
                message_bytes = ''
                message_bytes = self.sock.recv(1024)
                if message_bytes:
                    message = pickle.loads(message_bytes)
                    if message['command'] == const.CLOSE_CONN_CMD:
                        inputs.remove(self.sock)
                        outputs.remove(self.sock)
                        self.sock.close()
                        print('connection closed')
                    elif message['command'] == 'nicknameSet':
                        print(message['message'])
                    elif message['command'] == '/joinSuccess':
                        inboundMessageQueue.put(message)
                        print(message['message'])
                    elif message['message']:
                        message = utils.format_message(message)
                        print(message['message'])
                    
                else:
                # Interpret empty result as closed connection
                # Stop listening for input on the connection
                    if self.sock in outputs:
                        outputs.remove(self.sock)
                    inputs.remove(self.sock)
                    # Remove message queue
                    self.sock.close()
                    print('Connection has been broken on the server end and closed.')


            if self.sock in writable:
                if not outboundMessageQueue.empty():
                    self.send_message(outboundMessageQueue.get())

