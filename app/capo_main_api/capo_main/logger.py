import sys
import os

class Logger(object):
    def __init__(self):
        self.terminal = sys.stdout
        self.log = open(os.path.dirname(os.path.abspath(__file__))+"/../log/api_main_log.txt", "a")

    def write(self, message):
        self.terminal.write(message)
        self.log.write(message)

    def flush(self):
        # this flush method is needed for python 3 compatibility.
        # this handles the flush command by doing nothing.
        # you might want to specify some extra behavior here.
        pass
