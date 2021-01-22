import sys

class Incoming(object):
    pass


class InputFile(Incoming):

    def __init__(self, input_file=sys.stdin):
        self.input_file = input_file

    def __iter__(self):
        for line in self.input_file:
            yield line