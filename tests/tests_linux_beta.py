import base64
import json
import multiprocessing
import os
import selectors
import socket
from subprocess import PIPE, Popen
import sys
import time
import unittest

ADDRESS = ("localhost", 5001)
SCRIPT = """
import json
import sys
request = sys.stdin.read()
request = json.loads(request)
request["name"] = request["name"].replace("request", "response")
result = json.dumps(request)
sys.stdout.write(result)
"""


class Process:
    pass


processes = []


def accept(key, selector):
    listener = key.fileobj
    conn, addr = listener.accept()
    
    buffer = b""
    data = conn.recv(1024)
    while data:
        buffer += data
        data = conn.recv(1024)

    p = Process()
    processes.append(p)
    p.conn = conn
    p.in_stream = [buffer, 0]
    p.process = Popen(["python", "-c", SCRIPT], stdin=PIPE, stdout=PIPE)
    p.stdout_chunks = []

    selector.register(p.process.stdin, selectors.EVENT_WRITE, lambda key: send_to_process(key, selector, p))
    selector.register(p.process.stdout, selectors.EVENT_READ, lambda key: receive_from_process(key, selector, p))


def send_to_process(key, selector1, p):
    in_stream = p.in_stream
    chunk = in_stream[0][in_stream[1]:in_stream[1] + 512]
    in_stream[1] += os.write(key.fd, chunk)
    if in_stream[1] >= len(in_stream[0]):
        selector1.unregister(key.fileobj)
        key.fileobj.close()


def receive_from_process(key, selector, p):
    conn, process, stdout_chunks = p.conn, p.process, p.stdout_chunks
    chunk = os.read(key.fd, 32768)
    if chunk:
        stdout_chunks.append(chunk)
        return
    selector.unregister(key.fileobj)
    key.fileobj.close()
    process.wait()
    conn.sendall(b"".join(stdout_chunks))
    conn.close()
    processes.remove(p)


def listen():
    listener = socket.socket()
    listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    listener.bind(ADDRESS)
    listener.listen()
    with selectors.DefaultSelector() as selector:
        selector.register(listener, selectors.EVENT_READ, lambda key: accept(key, selector))
        while selector.get_map():
            ready = selector.select(.1)
            for (key, events) in ready:
                key.data(key)


@unittest.skipIf(sys.platform != 'linux', "Linux beta code")
class TestProcess(unittest.TestCase):
    def test(self):
        in_stream = b'{"name": "sample request"}'
        in_offset = 0
        process = Popen(["python", "-c", SCRIPT], stdin=PIPE, stdout=PIPE)
        stdout_chunks = []
        with selectors.SelectSelector() as selector:
            selector.register(process.stdin, selectors.EVENT_WRITE)
            selector.register(process.stdout, selectors.EVENT_READ)
            while selector.get_map():
                ready = selector.select(.1)
                for key, events in ready:
                    if key.fileobj == process.stdin:
                        chunk = in_stream[in_offset:in_offset + 512]
                        in_offset += os.write(key.fd, chunk)
                        if in_offset >= len(in_stream):
                            selector.unregister(key.fileobj)
                            key.fileobj.close()
                    elif key.fileobj == process.stdout:
                        chunk = os.read(key.fd, 32768)
                        if not chunk:
                            selector.unregister(key.fileobj)
                            key.fileobj.close()
                        stdout_chunks.append(chunk)
                    else:
                        assert False
        process.wait()
        stdout = b"".join(stdout_chunks)
        self.assertEqual(stdout, b'{"name": "sample response"}')


@unittest.skipIf(sys.platform != 'linux', "Linux beta code")
class TestSendProcessReceive(unittest.TestCase):
    def setUp(self):
        self.executor = multiprocessing.Process(target=listen)
        self.executor.start()
        time.sleep(.2)

    def tearDown(self):
        self.executor.terminate()
        self.executor.join()
    
    def test(self):
        payload = base64.b64encode(b"0123456789" * 1000 * 10).decode()
        request_1 = json.dumps({"name": "first request", "payload": payload}).encode()
        request_2 = b'{"name": "second request"}'
        
        with socket.socket() as c_1, socket.socket() as c_2:
            c_1.connect(ADDRESS)
            c_1.sendall(request_1)
            c_1.shutdown(socket.SHUT_WR)

            c_2.connect(ADDRESS)
            c_2.sendall(request_2)
            c_2.shutdown(socket.SHUT_WR)

            r_2 = b""
            data = c_2.recv(1024)
            while data:
                r_2 += data
                data = c_2.recv(1024)
            c_2.close()
            self.assertEqual(r_2, b'{"name": "second response"}')

            r_1 = b""
            data = c_1.recv(1024)
            while data:
                r_1 += data
                data = c_1.recv(1024)
            c_1.close()
            self.assertIn(b'{"name": "first response", "payload": "', r_1)
