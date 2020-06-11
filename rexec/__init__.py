import json
import logging.config
from multiprocessing import connection
from multiprocessing.connection import AuthenticationError
import runpy
from subprocess import PIPE, Popen, TimeoutExpired

logger = logging.getLogger("remote_exec")


class RemoteException(Exception):
    pass


def check_call(client_address, server_address, authkey, action, request):
    with connection.Listener(address=("0.0.0.0", client_address[1]), authkey=authkey, family='AF_INET') as listener:
        with connection.Client(server_address, authkey=authkey) as conn:
            conn.send([client_address, action, json.dumps(request).encode()])
        with listener.accept() as conn:
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

    def run_process(self, action, data):
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

    def execute(self, action, data):
        try:
            logger.info("running...")
            output = self.run_process(action, data)
            success = True
            logger.info("run ok")
        except Exception as ex:
            output = str(ex)
            success = False
            logger.info("run error")
        return success, output


class Server:
    def __init__(self, config_path):
        config = runpy.run_path(config_path)
        logging.config.dictConfig(config["LOG"])
        self.address = config["ADDRESS"]
        self.authkey = config["AUTHKEY"]
        self.actions = Actions(config["ACTIONS"])
        self.listener = None

    def _listen(self):
        with connection.Listener(self.address, authkey=self.authkey) as self.listener:
            logger.info("listening: %s", self.listener.address)
            while True:
                logger.info("accepting...")
                with self.listener.accept() as conn:
                    logger.info("connection received: %s", self.listener.last_accepted)
                    response_address, action, data = conn.recv()
                    logger.info("response_address: %s, action: %s", response_address, action)
                    success, output = self.actions.execute(action, data)
                logger.info("connecting...")
                with connection.Client(response_address, authkey=self.authkey) as conn:
                    logger.info("sending...")
                    conn.send([success, output])

    def close(self):
        self.listener.close()

    def listen(self):
        try:
            self._listen()
        except AuthenticationError as ex:
            logger.exception(ex)
