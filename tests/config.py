import os

BASE_DIR = os.path.dirname(__file__)
PYTHON_PATH = "python"
SCRIPT_PATH = os.path.join(BASE_DIR, "actions.py")
LOG_PATH = os.path.join(BASE_DIR, "test_remote_exec.log")

LOG = {
    "version": 1,
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': LOG_PATH,
            'mode': 'a',
        },
    },
    'loggers': {
        "remote_exec": {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': True
        },
    }
}
ACTIONS = {
    "action-ok": {"args": [PYTHON_PATH, SCRIPT_PATH, "ok"]},
    "action-file": {"args": [PYTHON_PATH, SCRIPT_PATH, "file"]},
    "action-error": {"args": [PYTHON_PATH, SCRIPT_PATH, "error"]},
    "action-exception": {"args": [PYTHON_PATH, SCRIPT_PATH, "exception"]},
    "action-timeout": {"args": [PYTHON_PATH, SCRIPT_PATH, "timeout"], "timeout": .2},
    "action-returncode": {"args": [PYTHON_PATH, SCRIPT_PATH, "returncode"]},
}
ADDRESS = ('localhost', 6000)
AUTHKEY = b'secret password'
