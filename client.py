
import lazy_asyncore
import socket
import datetime
import sys
from commands import *


class GameClient(lazy_asyncore.dispatcher):
    def __init__(self, host, port):
        lazy_asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))

        self.data_to_send = ''
        self.data_to_receive = ''
        self.is_writable = False
        self.is_readable = True

        self.start_ans = 0
        self.end_ans = 0

        self.welcome()

    def cmd_to_send(self):
        cmd = raw_input("cmd:")
        if cmd == READY_START or cmd == QUIT_ROOM or cmd == MSG or cmd == LOGOUT:
            cmd += ' '
        self.data_to_send = cmd
        self.is_writable = True

    def game_answer(self):
        self.start_ans = datetime.datetime.now()
        ans = raw_input("ans:")
        self.end_ans = datetime.datetime.now()
        delta_time = (self.end_ans - self.start_ans)
        self.data_to_send = ans + '\n' + str(delta_time.seconds)
        self.is_writable = True

    def welcome(self):
        print "Welcome to the 21 points game world!!"
        print "Please choose 1 if you already have an\naccount, otherwise choose 2"
        print "1. login"
        print "2. create an account"

        chosen_num = '0'
        while chosen_num != '1' and chosen_num != '2':
            chosen_num = raw_input("Your choice:")
            if chosen_num == '1':
                self.login()
            elif chosen_num == '2':
                self.create_account()
            else:
                print "Please choose 1 or 2!"

    def login(self):
        print "Please login first..."
        name = raw_input("User Name:")
        pwd = raw_input("Password:")

        self.data_to_send = LOGIN + ' ' + name + '\n' + pwd
        self.is_writable = True

    def create_account(self):
        print "Create new account..."
        name = raw_input("User Name:")
        pwd = raw_input("Password:")
        confirm_pwd = raw_input("Confirm Password:")

        self.data_to_send = ACCOUNT + ' ' + name + '\n' + pwd + '\n' + confirm_pwd
        self.is_writable = True

    def game_hints(self):
        print "In the game lobby, you can create rooms to\nplay games or chat with other players."
        print "Some commands to know:"
        print "1. 'cr roomname' -- create new room"
        print "2. 'find all' -- find all rooms"
        print "3. 'er roomname' -- enter existing room"
        print "4. 'qt roomname' -- quit from room"
        print "5. 'logout' -- logout the lobby"
        print "6. 'start' -- be ready for the game"
        print "7. '21game answer' -- send your answer"
        print "8. chatting mode"
        print " 1) 'chatAll msg' -- broadcast to all players"
        print " 2) 'chatRoom msg' -- broadcast to players in the room"
        print " 3) 'chat username msg' -- chat with somebody"
        print " 4) 'msg' -- receive messages"

        self.cmd_to_send()

    def continue_game(self):
        print "Continue or not?"
        print "1. continue"
        print "2. quit room"

        chosen_num = '0'
        while chosen_num != '1' and chosen_num != '2':
            chosen_num = raw_input("Your choice:")
            if chosen_num == '1':
                print CONTINUE_GAME
                self.cmd_to_send()
            elif chosen_num == '2':
                self.data_to_send = QUIT_ROOM + ' '
                self.is_writable = True
            else:
                print "Please choose 1 or 2!"

    def writable(self):
        return self.is_writable

    def readable(self):
        return self.is_readable

    def handle_close(self):
        self.close()

    def handle_read(self):
        self.data_to_receive = self.recv(1024)
        print self.data_to_receive
        if self.data_to_receive == INCORRECT_PWD:
            self.login()
        elif self.data_to_receive == ALREADY_ONLINE:
            self.login()
        elif self.data_to_receive == EXIST_ACCOUNT:
            self.create_account()
        elif self.data_to_receive == NEW_ACCOUNT:
            self.login()
        elif self.data_to_receive == SUCCESS_LOGIN:
            self.game_hints()
        elif self.data_to_receive == SUCCESS_LOGOUT:
            self.welcome()
        elif self.data_to_receive == SUCCESS_CROOM:
            self.cmd_to_send()
        elif self.data_to_receive == SUCCESS_EROOM:
            self.cmd_to_send()
        elif self.data_to_receive == ONLY_ROOM or self.data_to_receive == NOT_IN_ROOM:
            self.cmd_to_send()
        elif self.data_to_receive == SUCCESS_QROOM or self.data_to_receive == DISMISS_ROOM:
            self.cmd_to_send()
        elif CURRENT_ROOMS in self.data_to_receive:
            self.cmd_to_send()
        elif self.data_to_receive == FAIL_CROOM:
            self.cmd_to_send()
        elif self.data_to_receive == FAIL_EROOM:
            self.cmd_to_send()
        elif self.data_to_receive == FAIL_QROOM:
            self.cmd_to_send()
        elif self.data_to_receive == READY_GAME:
            pass
        elif START_GAME in self.data_to_receive:
            self.game_answer()
        elif self.data_to_receive == WRONG_EXPRESSION:
            self.continue_game()
        elif self.data_to_receive == WIN_GAME or self.data_to_receive == LOSE_GAME:
            self.continue_game()
        elif CHAT_MSG in self.data_to_receive:
            self.cmd_to_send()
        elif self.data_to_receive == INVALID_COMMAND:
            self.cmd_to_send()
        else:
            self.cmd_to_send()

    def handle_write(self):
        self.send(self.data_to_send)
        self.is_writable = False


client = GameClient(sys.argv[1], int(sys.argv[2]))
lazy_asyncore.loop()