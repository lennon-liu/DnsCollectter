import sys

class Outgoing(object):

    def __init__(self, *args, **kwargs):
        pass

    def take(self, obj):
        raise NotImplementedError

    def cleanup(self):
        pass


class OutputFile(Outgoing):

    def __init__(self, output_file=sys.stdout, *args, **kwargs):
        super(OutputFile, self).__init__()
        self.output_file = output_file

    def take(self, obj):
        self.output_file.write(obj)
        self.output_file.write("\n")
        self.output_file.flush()