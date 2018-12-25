import threading
from urllib import parse

from lib.utils.FileOps import FileOps
from thirdparty.oset.pyoset import oset


class Dictionary(object):
    def __init__(self,
                 path,
                 extensions,
                 lowercase=False,
                 forcedExtensions=False):
        self.entries = []
        self.currentIndex = 0
        self.lowercase = lowercase
        self.condition = threading.RLock()
        self._extensions = extensions
        self._path = path
        self._forcedExtensions = forcedExtensions
        self.dictionaryFile = FileOps(self.path)
        self.generate()

    @property
    def extensions(self):
        return self._extensions

    @extensions.setter
    def extensions(self, value):
        self._extensions = value

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, path):
        self._path = path

    @classmethod
    # A class method receives the class as implicit first argument
    # just like an instance method receives the instance
    # It can be called either on the class (e.g. C.f()) or on an instance (e.g. C().f())
    def urlQuote(cls, string):
        """Quote Given String to URL Pattern, Using parse.quote()"""
        # Check Out Python Documentation --> urllib.parse.quote()
        # urllib.parse.urlencode() -> Takes in Python dictionaries
        # urllib.parse.quote() -> Takes in String
        return parse.quote(string, safe=":/~?%&+-=$")

    def generate(self):
        """
        @brief      1. If keyword %EXT% is found -->
                       Append lines with REPLACED extension
                    2. If keyword %EXT% not found & is File-->
                       Append lines with REPLACED extension & one line with '/'
                    3. If The keyword %EXT% not found & is Directory -->
                       Append lines as they were

        @result     Generate The 'self.entries'
        """
        result = []
        for line in self.dictionaryFile.getLines():
            if line.lstrip().startswith("#"):
                continue  # Skip All Comments In The Dict
            # Process The Preset Wordlist
            # --> Replace Every Preset %EXT% With Target Extension
            # e.g. about.%EXT% -> about.php
            #      access_admin.%EXT% -> access_admin.php
            if "%EXT%" in line:
                for extension in self._extensions:
                    # Replace "EXT" to Given Extension
                    quoted = self.urlQuote(line.replace('%EXT%', extension))
                    result.append(quoted)
            # No "%EXT%" & forcedExtensions == True & Is File (Not Ended With '/')
            elif self._forcedExtensions and not line.rstrip().endswith("/"):
                quoted = self.urlQuote(line)
                for extension in self._extensions:
                    if extension.strip() == '':  # No extension is given
                        result.append(quoted)
                    else:  # Append the given extension
                        result.append(quoted + '.' + extension)
                if quoted.strip() not in ['']:
                    result.append(quoted + "/")
            else:  # Append lines as they were
                result.append(self.urlQuote(line))

        # "oset" library provides inserted ordered and unique collection
        if self.lowercase:
            self.entries = list(oset(map(lambda l: l.lower(), result)))
        else:
            self.entries = list(oset(result))

        del (result)

    def nextWithIndex(self, basePath=None):
        self.condition.acquire()
        try:
            result = self.entries[self.currentIndex]
        except IndexError:  # No Further Items
            self.condition.release()
            raise StopIteration  # Raise the StopIteration exception
        self.currentIndex = self.currentIndex + 1
        currentIndex = self.currentIndex

        self.condition.release()
        return currentIndex, result

    def reset2zero(self):
        self.condition.acquire()
        self.currentIndex = 0  # Reset Current Index to 0
        self.condition.release()

    def __next__(self, basePath=None):
        # Called to implement the built-in function next()
        _, path = self.nextWithIndex(basePath)  # Omit The First Argument
        return path

    def __len__(self):
        # Called to implement the built-in function len()
        return len(self.entries)
