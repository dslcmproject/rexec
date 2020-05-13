import os
import runpy
import subprocess
import sys
import time
import unittest

from rexec import check_call

BASE_DIR = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE_DIR, "config.py")
CONFIG = runpy.run_path(CONFIG_PATH)
LOG_PATH = CONFIG["LOG_PATH"]
ADDRESS = CONFIG["ADDRESS"]
AUTHKEY = CONFIG["AUTHKEY"]


@unittest.skipIf(sys.platform != 'win32', "Windows Service tests need Windows")
class Test(unittest.TestCase):
    def tearDown(self):
        try:
            subprocess.check_call(["sc", "stop", "rexec_remote_test"])
        except subprocess.CalledProcessError:
            pass
        time.sleep(2)
        try:
            subprocess.check_call(["sc", "delete", "rexec_remote_test"])
        except subprocess.CalledProcessError:
            pass
        os.remove(LOG_PATH)

    def test_run(self):
        subprocess.check_call(["python", "rexec_install.py", "rexec_remote_test", CONFIG_PATH])
        time.sleep(2)
        subprocess.check_call(["sc", "start", "rexec_remote_test"])
        time.sleep(2)
        result = check_call(ADDRESS, AUTHKEY, "action-ok", {"name": "first-request"})
        self.assertEqual(result, {"name": "first-response"})
