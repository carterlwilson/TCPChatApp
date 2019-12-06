import socket
import sys
import pickle
import select
import clientUtils as utils
import client_const as const
import json
try:
   import queue
except ImportError:
   import Queue as queue

class chatClient:

    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.events = queue.Queue()
        self.sock = None
        self.rooms = []
        self.nickname = 'default'

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
        message = {'nickname': data, 'command': const.NICK_CMD, 'channel': self.rooms}
        messageQueue.put(message)

    def run_client(self, outboundMessageQueue, inboundMessageQueue, eventMessageQueue):

        try:
            self.connect_server()
        except:
            print('Could not connect to chat server')
            sys.exit(1)

        inputs = [self.sock]
        outputs = [self.sock]

        if self.sock:
            self.events.put('server_connected')
            self.sock.settimeout(1)

        while inputs:
            #check for any events from the other thread
            readable, writable, exceptional = select.select(inputs, outputs, [])

            if self.sock in readable:
                message_bytes = ''
                message_bytes = self.sock.recv(1024)
                if message_bytes:
                    message = pickle.loads(message_bytes)
                    message = json.loads(message)
                    if message['command'] == const.CLOSE_CONN_CMD:
                        inputs.remove(self.sock)
                        outputs.remove(self.sock)
                        self.sock.close()
                        print('connection closed')
                    elif message['command'] == const.NICK_SET_CMD:
                        print(message['message'])
                        inboundMessageQueue.put(message)
                    elif message['command'] == const.JOIN_SUCCESS_CMD:
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

