
import asyncore
import socket
import json
import datetime
import threading
from random import randint
from commands import *


class MsgHandler(asyncore.dispatcher):
    def __init__(self, socket):
        asyncore.dispatcher.__init__(self, socket)
        self.is_writable = False
        self.is_readable = True
        self.data_to_send = ''
        self.data_to_receive = ''

        self.client = {
            'address': '127.0.0.1',

            'logtime': 0,
            'name': 'visitor',
            'is_online': False,

            'room_id': -1,
            'is_owner': False,

            'ready': False,
            'answer': -1,
            'ans_time': -1,
            'game_reply': LOSE_GAME
        }

    def attach_server(self, server):
        self.server = server

    def writable(self):
        return self.is_writable

    def readable(self):
        return self.is_readable

    def handle_write(self):
        self.send(self.data_to_send)
        self.is_writable = False

    def handle_read(self):
        self.data_to_receive = self.recv(1024)
        flag, response = self.handle_received_msg()
        if response != DEALED_MSG:
            self.data_to_send = response
            self.is_writable = True

    def handle_received_msg(self):
        data = self.data_to_receive
        space_index = data.find(' ')
        if space_index == -1:
            return INVALID_FLAG, INVALID_COMMAND
        event_flag = data[:space_index]
        msg = data[space_index+1:]

        if event_flag == LOGIN:
            return LOGIN, self.__handle_login_msg(msg)
        elif event_flag == ACCOUNT:
            return ACCOUNT, self.__handle_account_msg(msg)
        elif event_flag == CHAT_ALL:
            return CHAT_ALL, self.__handle_chatAll_msg(msg)
        elif event_flag == CHAT_ROOM:
            return CHAT_ROOM, self.__handle_chatRoom_msg(msg)
        elif event_flag == CHAT:
            return CHAT, self.__handle_chat_msg(msg)
        elif event_flag == CREATE_ROOM:
            return CREATE_ROOM, self.__handle_create_room_msg(msg)
        elif event_flag == ENTER_ROOM:
            return ENTER_ROOM, self.__handle_enter_room_msg(msg)
        elif event_flag == FIND_ROOMS:
            return FIND_ROOMS, self.__handle_find_rooms_msg(msg)
        elif event_flag == QUIT_ROOM:
            return QUIT_ROOM, self.__handle_quit_room_msg(msg)
        elif event_flag == READY_START:
            return READY_START, self.__handle_ready_game_msg(msg)
        elif event_flag == GAME:
            return GAME, self.__handle_21game_msg(msg)
        else:
            return INVALID_FLAG, INVALID_COMMAND

    def __handle_login_msg(self, msg):
        data = str(msg)
        [user_name, pwd] = data.split('\n')

        with open(self.server.database, 'r') as file:
            users = json.load(file)

        for user in users['accounts']:
            if user['name'] == user_name and user['pwd'] == pwd:
                self.client['name'] = user_name
                self.client['is_online'] = True
                self.client['logtime'] = datetime.datetime.now()
                return SUCCESS_LOGIN
        return INCORRECT_PWD

    def __handle_account_msg(self, msg):
        data = str(msg)
        [user_name, pwd, confirm_pwd] = data.split('\n')

        if pwd != confirm_pwd:
            return CONFIRM_PWD

        with open(self.server.database, 'r') as file:
            users = json.load(file)

        for user in users['accounts']:
            if user['name'] == user_name:
                return EXIST_ACCOUNT

        new_account = {'name': user_name, 'pwd': pwd, 'online_time': 0}
        users['accounts'].append(new_account)
        with open(self.server.database, 'w') as file:
            json.dump(users, file)
        return NEW_ACCOUNT

    def __handle_chatAll_msg(self, msg):
        data = str(msg)
        msg_handlers = self.server.msg_handlers
        for handler in msg_handlers:
            handler.data_to_send = data
            handler.is_writable = True
        return data

    def __handle_chatRoom_msg(self, msg):
        pass

    def __handle_chat_msg(self, msg):
        data = str(msg)
        self.data_to_send = data

    def __handle_create_room_msg(self, msg):
        room_name = str(msg)
        rooms = self.server.rooms
        for room in rooms:
            if room.name == room_name:
                return FAIL_CROOM
        self.client['room_id'] = room_name
        self.client['is_owner'] = True
        rooms.append(Room(room_name, self.client['name'], [self.client['name']]))

        return SUCCESS_CROOM

    def __handle_enter_room_msg(self, msg):
        room_name = str(msg)
        rooms = self.server.rooms
        for room in rooms:
            if room.name == room_name:
                room.number += 1
                room.members.append(self.client['name'])
                self.client['room_id'] = room_name
                return SUCCESS_EROOM
        return FAIL_EROOM

    def __handle_find_rooms_msg(self, msg):
        data = str(msg)
        if data != 'all':
            return INVALID_COMMAND
        rooms_info = CURRENT_ROOMS + '\n'
        rooms = self.server.rooms
        for room in rooms:
            rooms_info += 'room name: %s\n' % room.name
            rooms_info += 'room owner: %s\n' % room.owner
            rooms_info += 'player number: %s\n\n' % room.number
        return rooms_info

    def __handle_quit_room_msg(self, msg):
        data = str(msg)
        room_name = self.client['room_id']
        if data and data != room_name:
            return FAIL_QROOM

        room = self.server.find_room(room_name)
        rooms = self.server.rooms
        if self.client['is_owner']:
            for member in room.members:
                msg_handler = self.server.find_handler(member)
                msg_handler.client['room_id'] = -1
                msg_handler.data_to_send = DISMISS_ROOM
                msg_handler.is_writable = True
            rooms.remove(room)
        else:
            self.client['room_id'] = -1
            room.members.remove(self.client['name'])
            room.number -= 1
            self.data_to_send = SUCCESS_QROOM
            self.is_writable = True

        return DEALED_MSG

    def __handle_ready_game_msg(self, msg):

        self.client['ready'] = True
        room = self.server.find_room(self.client['room_id'])
        for member in room.members:
            msg_handler = self.server.find_handler(member)
            if not msg_handler.client['ready']:
                return READY_GAME
        room.game_flag = True
        self.server.start_game(room)
        return READY_GAME

    def __handle_21game_msg(self, msg):
        data = str(msg)
        [ans, ans_time] = data.split('\n')

        try:
            answer = eval(ans)
            answer_time = float(ans_time)
        except IOError as e:
            return WRONG_EXPRESSION

        self.client['answer'] = answer
        self.client['ans_time'] = answer_time

        game_over = True
        room = self.server.find_room(self.client['room_id'])
        members = room.members
        for member in members:
            msg_handler = self.server.find_handler(member)
            if msg_handler.client['answer'] == -1:
                game_over = False
                break

        if game_over:
            room.game_flag = False
            self.server.announce_results(room)
        return DEALED_MSG


class GameServer(asyncore.dispatcher):
    def __init__(self, host, port):
        # communications
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.set_reuse_addr()
        self.bind((host, port))
        self.listen(5)

        self.database = DATABASE
        self.msg_handlers = []
        self.rooms = []

        self.time_limit = 15
        self.points = 21

    def handle_accept(self):
        sock, addr = self.accept()
        print 'Incoming connection from %s' % repr(addr)
        msg_handler = MsgHandler(sock)
        msg_handler.client["address"] = addr
        self.msg_handlers.append(msg_handler)
        msg_handler.attach_server(self)

    def start_game(self, room):
        # now_time = datetime.datetime.time(datetime.datetime.now())
        # hour = now_time.hour
        # min = now_time.minute
        # second = now_time.second
        #
        # if min == 0:
        #     self.loop_game()
        # elif 0 < min < 30:
        #     remaining_time = (29 - min) * 60 + (59 - second)
        #     threading.Timer(remaining_time, self.loop_game()).start()
        # elif min == 30:
        #     self.loop_game()
        # else:
        #     remaining_time = (59 - min) * 60 + (59 - second)
        threading.Timer(15, self.loop_game, [room]).start()

    def loop_game(self, room):
        if not room.game_flag:
            return

        a = randint(0, 9)
        b = randint(0, 9)
        c = randint(0, 9)
        d = randint(0, 9)

        for member in room.members:
            msg_handler = self.find_handler(member)
            abcd = '%d %d %d %d' % (a, b, c, d)
            msg_handler.data_to_send = START_GAME + '\n' + abcd
            msg_handler.is_writable = True

        # threading.Timer(20, self.announce_results).start() # game results

    def find_handler(self, name):
        msg_handlers = self.msg_handlers
        for msg_handler in msg_handlers:
            if msg_handler.client['name'] == name:
                return msg_handler

    def find_room(self, room_id):
        rooms = self.rooms
        for room in rooms:
            if room.name == room_id:
                return room

    def announce_results(self, room):
        members = room.members
        best_answer = 0
        best_time = self.time_limit
        winner = 'nobody'
        for member in members:
            msg_handler = self.find_handler(member)
            answer = msg_handler.client['answer']
            ans_time = msg_handler.client['ans_time']
            if best_answer < answer <= self.points and ans_time < best_time:
                best_answer = answer
                best_time = ans_time
                winner = msg_handler
        if winner != 'nobody':
            winner.client['game_reply'] = WIN_GAME

        for member in members:
            msg_handler = self.find_handler(member)
            msg_handler.data_to_send = msg_handler.client['game_reply']
            msg_handler.is_writable = True

            msg_handler.client['answer'] = -1
            msg_handler.client['ans_time'] = -1
            msg_handler.client['game_reply'] = LOSE_GAME
            msg_handler.client['ready'] = False

        # threading.Timer(60, self.loop_game).start()     # next game


class Room(object):
    def __init__(self, name, owner, members):
        self.name = name
        self.owner = owner
        self.members = members
        self.number = 1
        self.game_flag = False


server = GameServer('localhost', 6666)
asyncore.loop()