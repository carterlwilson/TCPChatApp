import select
import socket
import sys
import queue
import json
import pickle
from model.connection import *

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(0)

server_address = ('0.0.0.0', 1025)
print('starting up on %s port %s' % server_address)
server.bind(server_address)

server.listen()

inputs = [server]
outputs = []

messageQueues = {}
rooms = []
sockets = {}

while inputs:
    readable, writable, exceptional = select.select(inputs, outputs, inputs)

    for s in readable:

        if s is server:
            newConnection, client_address = s.accept()
            if newConnection:
                newConnection.setblocking(0)
                inputs.append(newConnection)

                socketDataObj = build_new_connection(newConnection, client_address, newConnection.fileno())

                sockets[socketDataObj['socketId']] = socketDataObj

                messageQueues[newConnection.fileno()] = queue.Queue()

                print('connected to client')

        else:
            data = s.recv(1024)
            if data:
                request = pickle.loads(data)
                print('received message\n')
                if request['command'] == '/nick':
                    print('received /nick request')
                    sockets = set_nickname(s, request, sockets, messageQueues)

                elif request['command'] == '/broadcast':
                    broadcast_message(request, sockets, messageQueues, outputs)

                elif request['command'] == '/join':
                    sockets = join_room(request, sockets, s, rooms, messageQueues)

                elif request['command'] == '/direct':
                    send_direct_message(request, sockets, s, messageQueues, outputs)

                elif request['command'] == '/listRooms':
                    list_rooms(request, rooms, s, messageQueues)

                elif request['command'] == '/leaveRoom':
                    leave_room(request, sockets, s, rooms, messageQueues)

                elif request['command'] == '/roomMembers':
                    list_room_members(request, sockets, s, rooms, messageQueues)

                elif request['command'] == '/close':
                    say_thanks(request, s, messageQueues)

                if s not in outputs:
                    outputs.append(s)
            else:
                # Interpret empty result as closed connection
                print('closing', client_address, 'after reading no data')
                # Stop listening for input on the connection
                if s in outputs:
                    outputs.remove(s)
                inputs.remove(s)
                # Remove message queue
                messageQueues.pop(s.fileno())
                sockets.pop(s.fileno())
                print('closing connection')
                s.close()

    for s in writable:
        try:
            next_msg = ''
            key = s.fileno()
            socketQueue = messageQueues[key]
            if not socketQueue.empty():
                next_msg = socketQueue.get()
        except:
            if s in outputs:
                outputs.remove(s)
        else:
            if next_msg:
                serialized_msg = pickle.dumps(next_msg)
                s.sendall(serialized_msg)

    # Handle "exceptional conditions"
    for s in exceptional:
        print('handling exceptional condition for', s.getpeername())
        # Stop listening for input on the connection
        inputs.remove(s)
        if s in outputs:
            outputs.remove(s)
        s.close()

        # Remove message queue
        del messageQueues[s]