# System Python Interpreter Check
import sys
if sys.version_info < (3, 0):  # Only Python 3.x is Supported
    sys.stdout.write("Sorry, Websit Dir Scanner Requires Python 3\n")
    sys.exit(1)
import os

from lib.core.CustomParser import CustomParser
from lib.output.CLIOutput import CLIOutput
from lib.controller.Controller import Controller


class Scanner(object):
    def __init__(self):
        # Get The Current Script Dirname --> dirname(realpath())
        # os.path.realpath(__file__)
        # --> Return the canonical path of the specified filename
        self.script_path = (os.path.dirname(os.path.realpath(__file__)))
        self.arguments = CustomParser(self.script_path)
        self.output = CLIOutput()
        self.controller = Controller(self.script_path, self.arguments,
                                     self.output)


# Scanner Starts From System Console
if __name__ == '__main__':
    main = Scanner()
