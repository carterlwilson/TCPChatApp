import select
import socket
import sys
try:
   import queue
except ImportError:
   import Queue as queue
import json
import pickle
from connection import *
import server_const as const

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.setblocking(0)

server_address = ('0.0.0.0', 1025)
print('starting up on %s port %s' % server_address)
server.bind(server_address)

server.listen(5)

inputs = [server]
outputs = []

messageQueues = {}
rooms = []
sockets = {}
try:
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
                #handles client crash
                try:
                    data = s.recv(1024)
                except socket.error:
                    print("A client has crashed and lost connection.")
                    messageQueues.pop(s.fileno())
                    sockets.pop(s.fileno())
                    if s in readable:
                        readable.remove(s)
                    if s in writable:
                        writable.remove(s)
                    if s in inputs:
                        inputs.remove(s)
                    if s in outputs:
                        outputs.remove(s)
                    print('closing connection')
                    s.close()
                    break
                if data:
                    request = pickle.loads(data)
                    print('received message\n')
                    if request['command'] == const.NICK_CMD:
                        print('received /nick request')
                        sockets = set_nickname(s, request, sockets, messageQueues)

                    elif request['command'] == const.BROADCAST_CMD:
                        broadcast_message(request, sockets, messageQueues, outputs)

                    elif request['command'] == const.JOIN_CMD:
                        sockets = join_room(request, sockets, s, rooms, messageQueues)

                    elif request['command'] == const.DIR_MSG_COMD:
                        send_direct_message(request, sockets, s, messageQueues, outputs)

                    elif request['command'] == const.LIST_ROOMS_CMD:
                        list_rooms(request, rooms, s, messageQueues)

                    elif request['command'] == const.LEAVE_ROOM_CMD:
                        leave_room(request, sockets, s, rooms, messageQueues)

                    elif request['command'] == const.LIST_ROOM_MEMBER_CMD:
                        list_room_members(request, sockets, s, rooms, messageQueues)

                    elif request['command'] == const.CLOSE_CONN_CMD:
                        say_thanks(request, s, messageQueues)

                    if s not in outputs:
                        outputs.append(s)
                else:
                    # Interpret empty result as closed connection
                    print('closing', client_address, 'after reading no data')
                    # Stop listening for input on the connection
                    sockets.pop(s.fileno())
                    close_connection(s, messageQueues, inputs, outputs)     
        
        #handle sockets ready to be written to
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
                    jsonMsg = json.dumps(next_msg)
                    serialized_msg = pickle.dumps(json.dumps(next_msg))
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
            del messageQueues[s.fileno()]

except KeyboardInterrupt:
    for key, socket in sockets.items():
        close_connection(socket['socketConnection'], messageQueues, inputs, outputs)
    
    sockets.clear()
    print("Disconnected from all clients, shutting down server.")
    sys.exit()



