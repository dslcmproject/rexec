import json
import logging.config
from multiprocessing import connection
from multiprocessing.connection import AuthenticationError
import runpy
from subprocess import PIPE, Popen, TimeoutExpired

logger = logging.getLogger("remote_exec")


class RemoteException(Exception):
    pass


def check_call(address, authkey, action, request):
    with connection.Client(address, authkey=authkey) as conn:
        conn.send([action, json.dumps(request).encode()])
        success, output = conn.recv()
        if not success:
            raise RemoteException(output)
        return json.loads(output.decode())


class Actions:
    """
    Action is considered successfull if:
    - stderr is empty and return code is zero
    """
    DEFAULT_PARAMS = {
        "timeout": 60
    }

    def __init__(self, actions):
        self.actions = actions

    def __call__(self, action, data):
        try:
            params = self.actions[action]
        except KeyError:
            raise Exception("INVALID ACTION")
        params = {**self.DEFAULT_PARAMS, **params}
        process = Popen(params["args"], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        try:
            output, error = process.communicate(input=data, timeout=params["timeout"])
            if error:
                raise Exception(error)
            if process.returncode:
                raise Exception("INVALID RETURNCODE: {}".format(process.returncode))
            return output
        except TimeoutExpired:
            process.kill()
            process.communicate()
            raise Exception("TIMEOUT")


class Server:
    def __init__(self, config_path):
        config = runpy.run_path(config_path)
        logging.config.dictConfig(config["LOG"])
        self.address = config["ADDRESS"]
        self.authkey = config["AUTHKEY"]
        self.actions = Actions(config["ACTIONS"])
        self.listener = None

    def close(self):
        self.listener.close()

    def _listen(self):
        with connection.Listener(self.address, authkey=self.authkey) as self.listener:
            logger.info("listening: %s", self.listener.address)
            while True:
                with self.listener.accept() as conn:
                    logger.info("connection received: %s", self.listener.last_accepted)
                    action, data = conn.recv()
                    try:
                        output = self.actions(action, data)
                        success = True
                    except Exception as ex:
                        output = str(ex)
                        success = False
                    conn.send([success, output])

    def listen(self):
        try:
            self._listen()
        except AuthenticationError as ex:
            logger.exception(ex)
