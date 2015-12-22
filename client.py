
import asyncore
import socket
import datetime
from commands import *


class GameClient(asyncore.dispatcher):
    def __init__(self, host, port):
        asyncore.dispatcher.__init__(self)
        self.create_socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connect((host, port))

        self.data_to_send = ''
        self.data_to_receive = ''
        self.is_writable = False
        self.is_readable = True

        self.timer = 300
        self.start_ans = 0
        self.end_ans = 0

        self.welcome()

    def cmd_to_send(self):
        cmd = raw_input("cmd:")
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
        print "Welcome to the 21 points game world!!\n"
        print "Please choose 1 if you already have an\naccount, otherwise choose 2\n"
        print "1. login\n"
        print "2. create an account\n"

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
        print "Please login first...\n"
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
        print "In the game lobby, you can create rooms to\nplay games or chat with other players.\n"
        print "Some commands to know:\n"
        print "1. 'cr roomname' -- create new room\n"
        print "2. 'find all' -- find all rooms\n"
        print "3. 'er roomname' -- enter existing room\n"
        print "4. 'qt roomname' -- quit from room\n"
        print "5. chatting mode\n"
        print " 1) 'chatAll msg' -- broadcast to all players\n"
        print " 2) 'chatRoom msg' -- broadcast to players in the room\n"
        print " 3) 'chat username msg' -- chat with somebody\n"

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
            elif chosen_num == '2':
                self.data_to_send = 'qt' + ' '
                self.is_writable = True
            else:
                print "Please choose 1 or 2!"


    def find_rooms(self):
        pass

    def enter_room(self):
        pass

    def quit_room(self):
        pass

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
        elif self.data_to_receive == EXIST_ACCOUNT:
            self.create_account()
        elif self.data_to_receive == NEW_ACCOUNT:
            self.login()
        elif self.data_to_receive == SUCCESS_LOGIN:
            self.game_hints()
        elif self.data_to_receive == SUCCESS_CROOM:
            pass
        elif self.data_to_receive == SUCCESS_EROOM:
            pass
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
        elif START_GAME in self.data_to_receive:
            self.game_answer()
        elif self.data_to_receive == WIN_GAME or self.data_to_receive == LOSE_GAME:
            self.continue_game()
        elif self.data_to_receive == INVALID_COMMAND:
            self.cmd_to_send()


    def handle_write(self):
        self.send(self.data_to_send)
        self.is_writable = False



client1 = GameClient('localhost', 6666)
asyncore.loop()