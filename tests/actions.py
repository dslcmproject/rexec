import base64
import json
import os
import sys
import time

BASE_DIR = os.path.dirname(__file__)
TEMP_PATH = os.path.join(BASE_DIR, "action_tempfile")

cmd_arg, = sys.argv[1:]

if cmd_arg == 'error':
    sys.stderr.write("!!!ERROR!!!")
    sys.exit(1)

if cmd_arg == 'exception':
    assert False, "Invalid argument"

if cmd_arg == 'timeout':
    time.sleep(5)
    sys.exit(0)

if cmd_arg == 'returncode':
    sys.exit(1)

request = sys.stdin.read()
request = json.loads(request)
request["name"] = request["name"].replace("request", "response")

if cmd_arg == 'file':
    request["file-content"] = base64.b64encode(b"1234567890" * 1024 * 1024).decode()

result = json.dumps(request)
sys.stdout.write(result)
sys.exit(0)
