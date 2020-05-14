# rexec

Run Remote Executables
*usefull on Windows*

## Usage

Installation:

```
pip install PyWin32  # PyWin32 is needed
pip install rexec-<last-build-number>.tar.gz
```


Create a service to run executable:

```
rexec_install.py <service-name> <absolute-path-to-config-file>
```

Config file sample:

```
LOG = {
    "version": 1,
    'handlers': {
        'default': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '<full-path-to-log-file>',
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
    "my-action": {"args": ["<executable-path>", "<param-1>", "<param-2>"]},
    "my-action-timeout": {"args": ["<executable-path>", "<param-1>"], "timeout": .2},
}
ADDRESS = ('<daemon-server-ip-or-name>', daemon-port)
AUTHKEY = b'<secret-password>'
```

Start/Stop/Delete the service

```
sc {start|stop|delete} <service-name>
```


#### Client

Sample code:

```
import rexec
output_json = rexec.check_call((<daemon-server>, <daemon-port>), <secret-password>, <action-name>, <input-json>)
```

The client does not need PyWin32


## Tests
 
*If PyWin32 is not installed, some test will skip*

```
git clone https://github.com/dslcmprojects/rexec
cd rexec
python -m unittest
```

To run all the tests on Windows you need to install the package globally in developer mode:

```
pip install -e .
```

Run the Windows tests:

```
python -m unittest tests.test_win32_service
```


## Package

Build a package:

```
python setup.py sdist
```