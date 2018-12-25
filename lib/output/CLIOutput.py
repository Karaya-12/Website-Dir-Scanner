import sys
import time
import platform
import threading
import urllib.parse

from colorama import init, Fore, Back, Style
if platform.system() == "Windows":
    from colorama.win32 import (STDOUT, GetConsoleScreenBufferInfo,
                                FillConsoleOutputCharacter)

from lib.utils.FileUtils import FileUtils
from lib.utils.TerminalSize import get_terminal_size


# Class for Command Line Interface Output
class CLIOutput(object):
    def __init__(self):
        init()
        self.lastLength = 0
        self.errors = 0
        self.lastOutput = ''
        self.basePath = None
        self.lastInLine = False
        self.blacklists = {}
        self.mutex = threading.RLock()

    def inLine(self, string):
        self.erase()
        sys.stdout.write(string)
        sys.stdout.flush()
        self.lastInLine = True

    def erase(self):
        if platform.system() == "Windows":
            csbi = GetConsoleScreenBufferInfo()
            line = "\b" * int(csbi.dwCursorPosition.X)
            sys.stdout.write(line)
            width = csbi.dwCursorPosition.X
            csbi.dwCursorPosition.X = 0
            FillConsoleOutputCharacter(STDOUT, ' ', width,
                                       csbi.dwCursorPosition)
            sys.stdout.write(line)
            sys.stdout.flush()
        else:
            sys.stdout.write("\033[1K")
            sys.stdout.write("\033[0G")

    def newLine(self, string):
        if self.lastInLine == True:
            self.erase()

        if platform.system() == "Windows":
            sys.stdout.write(string)
            sys.stdout.flush()
            sys.stdout.write('\n')
            sys.stdout.flush()
        else:
            sys.stdout.write(string + '\n')

        sys.stdout.flush()
        self.lastInLine = False
        sys.stdout.flush()

    def error(self, reason):
        with self.mutex:
            stripped = reason.strip()
            start = reason.find(stripped[0])
            end = reason.find(stripped[-1]) + 1
            message = reason[0:start]
            message += Style.BRIGHT + Fore.WHITE + Back.RED
            message += reason[start:end]
            message += Style.RESET_ALL
            message += reason[end:]
            self.newLine(message)

    def warning(self, reason):
        message = Style.BRIGHT + Fore.YELLOW + reason + Style.RESET_ALL
        self.newLine(message)

    def header(self, text):
        # Display Scanner Banner Info
        message = Style.BRIGHT + Fore.MAGENTA + text + Style.RESET_ALL
        self.newLine(message)

    def versionAuthor(self, text):
        # Display Scanner Version Control & Author Info
        message = Style.BRIGHT + Fore.BLUE + text + Style.RESET_ALL
        self.newLine(message)

    def config(self, extensions, threads, wordlistSize):
        # Display The User Custom Configuration
        separator = Fore.MAGENTA + ' | ' + Fore.YELLOW
        config = Style.BRIGHT + Fore.YELLOW
        config += "Extensions: {0}".format(Fore.CYAN + extensions +
                                           Fore.YELLOW)
        config += separator
        config += "Threads Number: {0}".format(Fore.CYAN + threads +
                                               Fore.YELLOW)
        config += separator
        config += "Wordlist Size: {0}".format(Fore.CYAN + wordlistSize +
                                              Fore.YELLOW)
        config += Style.RESET_ALL
        self.newLine(config)

    def pathDisplay(self, reports_Path, logs_Path):
        # Display The Default Local Path for Reports & Error Logs
        logs = Style.BRIGHT + Fore.YELLOW
        logs += "Report Path: {0}".format(Fore.CYAN + reports_Path +
                                          Fore.YELLOW)
        logs += "\nError Logs Path: {0}\n".format(Fore.CYAN + logs_Path +
                                                  Fore.YELLOW)
        logs += Style.RESET_ALL
        self.newLine(logs)

    def targetURL(self, target):
        config = Style.BRIGHT + Fore.YELLOW
        config += "\nTarget: {0}\n".format(Fore.CYAN + target + Fore.YELLOW)
        config += Style.RESET_ALL
        self.newLine(config)

    def debug(self, info):
        line = "[{0}] - {1}".format(time.strftime('%H:%M:%S'), info)
        self.newLine(line)

    def addConnectionError(self):
        self.errors += 1

    def lastPath(self, path, index, length):
        with self.mutex:
            percentage = lambda x, y: float(x) / float(y) * 100
            x, _ = get_terminal_size()
            message = "{0:.2f}% - ".format(percentage(index, length))

            if self.errors > 0:
                message += Style.BRIGHT + Fore.RED
                message += "Errors: {0}".format(self.errors)
                message += Style.RESET_ALL
                message += " - "
            message += "Last Request to: {0}".format(path)

            if len(message) > x:
                message = message[:x]
            self.inLine(message)

    def statusReport(self, path, response):
        """
        @brief      Given URL Path Response Status Report

        @pattern      [23:59:59] Status Code (e.g. 302) - File Size (e.g. 222 B)  - /php  ->  Target URL
        """
        with self.mutex:
            contentLength = None
            status = response.status

            # Check Blacklist
            if status in self.blacklists and path in self.blacklists[status]:
                return

            # Format Messages
            try:
                size = int(response.headers['content-length'])
            except (KeyError, ValueError):
                size = len(response.body)
            finally:
                contentLength = FileUtils.sizeIEC(size)

            if self.basePath is None:
                showPath = urllib.parse.urljoin("/", path)
            else:
                showPath = urllib.parse.urljoin("/", self.basePath)
                showPath = urllib.parse.urljoin(showPath, path)

            # Concatenate The URL Response Report Message
            message = '[{0}] {1} - {2} - {3}'.format(
                time.strftime('%H:%M:%S'), status, contentLength.rjust(6, ' '),
                showPath)

            # HTTP Response Code List
            if status == 200:  # OK
                message = Fore.GREEN + message + Style.RESET_ALL
            elif status == 401:  # Unauthorized
                message = Fore.YELLOW + message + Style.RESET_ALL
            elif status == 403:  # Forbidden
                message = Fore.RED + message + Style.RESET_ALL
            # Check If Redirect --> Response Code
            # 301 (Moved Permanently), 302 (Found -> Moved temporarily"), 307 (Temporary Redirect)
            elif (status in [301, 302, 307]) and ('location' in [
                    h.lower() for h in response.headers
            ]):
                message = Fore.CYAN + message + Style.RESET_ALL
                message += '  ->  {0}'.format(response.headers['location'])

            self.newLine(message)
