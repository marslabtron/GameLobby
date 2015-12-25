
import socket
import select
import time

try:
    socket_map
except NameError:
    socket_map = {}


def loop(timeout=0.0):
    while socket_map:
        r = []
        w = []
        e = []
        for fd, obj in socket_map.items():
            is_r = obj.readable()
            is_w = obj.writable()
            if is_r:
                r.append(fd)
            if is_w:
                if obj.server_socket and obj.connected:
                    pass
                else:
                    w.append(fd)
        if [] == r == w:
            time.sleep(timeout)
            return

        try:
            r, w, e = select.select(r, w, e, timeout)
        except select.error:
            return

        for fd in r:
            obj = socket_map.get(fd)
            if obj is None:
                continue
            read(obj)

        for fd in w:
            obj = socket_map.get(fd)
            if obj is None:
                continue
            write(obj)


def read(obj):
    try:
        obj.handle_read_event()
    except:
        raise


def write(obj):
    try:
        obj.handle_write_event()
    except:
        raise


class dispatcher:

    server_socket = False
    connected = False
    addr = None

    def __init__(self, sock=None):
        self.map = socket_map

        if sock:
            sock.setblocking(0)
            self.set_socket(sock)
            self.connected = True
            try:
                self.addr = sock.getpeername()
            except socket.error:
                raise
        else:
            self.socket = None

    def set_socket(self, sock):
        self.socket = sock
        self.fileno = sock.fileno()
        self.add_to_map()

    def set_reuse_addr(self):
        # try to re-use a server port if possible
        try:
            self.socket.setsockopt(
                socket.SOL_SOCKET, socket.SO_REUSEADDR,
                self.socket.getsockopt(socket.SOL_SOCKET,
                                       socket.SO_REUSEADDR) | 1
                )
        except socket.error:
            pass

    def add_to_map(self):
        self.map[self.fileno] = self

    def del_from_map(self):
        del self.map[self.fileno]

    def create_socket(self, family, type):
        sock = socket.socket(family, type)
        sock.setblocking(0)
        self.set_socket(sock)

    def bind(self, addr):
        self.addr = addr
        return self.socket.bind(addr)

    def listen(self, num):
        self.server_socket = True
        if num > 5:
            num = 5
        return self.socket.listen(num)

    def accept(self):
        try:
            conn, addr = self.socket.accept()
        except TypeError:
            return None
        else:
            return conn, addr

    def connect(self, address):
        self.socket.connect_ex(address)
        self.addr = address
        self.connected = True


    def send(self, data):
        try:
            result = self.socket.send(data)
            return result
        except socket.error:
            raise

    def recv(self, buffer_size):
        try:
            data = self.socket.recv(buffer_size)
            if not data:
                self.handle_close()
                return ''
            else:
                return data
        except socket.error:
            self.handle_close()    # default: disconnected msg
            return ''

    def close(self):
        self.del_from_map()
        try:
            self.socket.close()
        except socket.error:
            raise

    # overwrite
    def handle_accept(self):
        pass

    # overwrite
    def writable(self):
        return True

    # overwrite
    def readable(self):
        return True

    # overwrite
    def handle_read(self):
        pass

    # overwrite
    def handle_write(self):
        pass

    def handle_close(self):
        self.close()
        return

    def handle_read_event(self):
        if self.server_socket and not self.connected:
            self.handle_accept()
        else:
            self.handle_read()

    def handle_write_event(self):
        if self.server_socket:
            return
        if not self.connected:
            return
        self.handle_write()

    # cheap inheritance, used to pass all other attribute
    # references to the underlying socket object.
    def __getattr__(self, attr):
        try:
            retattr = getattr(self.socket, attr)
        except AttributeError:
            raise AttributeError("%s instance has no attribute '%s'"
                                 %(self.__class__.__name__, attr))
        else:
            return retattr

