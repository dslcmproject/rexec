import base64
from multiprocessing import Process
import os
import runpy
import time
import unittest

import rexec

BASE_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE_DIR, "config.py")
CONFIG = runpy.run_path(CONFIG_PATH)
ACTIONS = CONFIG["ACTIONS"]
LOG_PATH = CONFIG["LOG_PATH"]
SERVER_ADDRESS = CONFIG["ADDRESS"]
AUTHKEY = CONFIG["AUTHKEY"]
CLIENT_ADDRESS = ("localhost", 5006)


def run_server():
    s = rexec.Server(CONFIG_PATH)
    s.listen()


class TestActions(unittest.TestCase):
    def test(self):
        actions = rexec.Actions(ACTIONS)
        result = actions.execute("action-ok", b'{"name": "first-request"}')
        self.assertEqual(result, (True, b'{"name": "first-response"}'))


class TestServer(unittest.TestCase):
    def setUp(self):
        self.executor = Process(target=run_server)
        self.executor.start()
        time.sleep(.2)

    def tearDown(self):
        self.executor.terminate()
        self.executor.join()
        os.remove(LOG_PATH)

    def test_ok(self):
        result = rexec.check_call(CLIENT_ADDRESS, SERVER_ADDRESS, AUTHKEY, "action-ok", {"name": "first-request"})
        self.assertEqual(result, {"name": "first-response"})
        result = rexec.check_call(CLIENT_ADDRESS, SERVER_ADDRESS, AUTHKEY, "action-ok", {"name": "second-request"})
        self.assertEqual(result, {"name": "second-response"})

    def test_sendfile(self):
        result = rexec.check_call(CLIENT_ADDRESS, SERVER_ADDRESS, AUTHKEY, "action-file", {"name": "first-request"})
        file_content = base64.b64decode(result["file-content"])
        self.assertEqual(b"1234567890", file_content[:10])

    def test_error(self):
        with self.assertRaises(rexec.RemoteException) as ex:
            rexec.check_call(CLIENT_ADDRESS, SERVER_ADDRESS, AUTHKEY, "action-error", {"name": "first-request"})
        self.assertEqual(str(ex.exception), "b'!!!ERROR!!!'")

    def test_exception(self):
        with self.assertRaises(rexec.RemoteException) as ex:
            rexec.check_call(CLIENT_ADDRESS, SERVER_ADDRESS, AUTHKEY, "action-exception", {"name": "first-request"})
        self.assertIn("AssertionError: Invalid argument", str(ex.exception))

    def test_timeout(self):
        with self.assertRaises(rexec.RemoteException) as ex:
            rexec.check_call(CLIENT_ADDRESS, SERVER_ADDRESS, AUTHKEY, "action-timeout", {"name": "first-request"})
        self.assertEqual("TIMEOUT", str(ex.exception))

    def test_returncode(self):
        with self.assertRaises(rexec.RemoteException) as ex:
            rexec.check_call(CLIENT_ADDRESS, SERVER_ADDRESS, AUTHKEY, "action-returncode", {"name": "first-request"})
        self.assertIn("INVALID RETURNCODE", str(ex.exception))

    def test_invalid_auth(self):
        self.assertRaises(
            rexec.AuthenticationError, rexec.check_call, CLIENT_ADDRESS, SERVER_ADDRESS, b"invalid password", "dummy", {"name": "dummy"})

    def test_invalid_action(self):
        with self.assertRaises(rexec.RemoteException) as ex:
            rexec.check_call(CLIENT_ADDRESS, SERVER_ADDRESS, AUTHKEY, "action-invalid", {"name": "first-request"})
        self.assertIn("INVALID ACTION", str(ex.exception))
