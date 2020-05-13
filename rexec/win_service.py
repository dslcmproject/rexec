import pickle

import win32service
import win32serviceutil

import rexec


def class_path(class_object):
    module_name = pickle.whichmodule(class_object, class_object.__name__)
    return module_name + "." + class_object.__name__


class WinService(win32serviceutil.ServiceFramework):
    CONFIG_PATH_PARAM = "config_path"

    def __init__(self, args):
        self._svc_name_, = args
        super().__init__(args)
        self.config_path = win32serviceutil.GetServiceCustomOption(self._svc_name_, self.CONFIG_PATH_PARAM)
        self.server = None

    def SvcDoRun(self):
        self.server = rexec.Server(self.config_path)
        self.server.listen()

    def SvcStop(self):
        self.server.close()
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)

    @classmethod
    def install(cls, service_name, config_path):
        win32serviceutil.InstallService(class_path(cls), service_name, service_name)
        win32serviceutil.SetServiceCustomOption(service_name, cls.CONFIG_PATH_PARAM, config_path)
