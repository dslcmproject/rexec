import sys

from rexec.win_service import WinService


if __name__ == '__main__':
    WinService.install(*sys.argv[1:])
