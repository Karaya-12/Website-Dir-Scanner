import os


class FileUtils(object):
    @staticmethod
    def createPath(*pathComponents):
        if pathComponents:
            path = os.path.join(*pathComponents)
        else:
            path = ''
        return path

    """
    File Status Check
    Check Out Python 3.x Documentation
    os.access() --> F_OK, R_OK, W_OK, X_OK
    Return True if access is allowed, False if not.
    """

    @staticmethod
    def exists(fileName):
        return os.access(fileName, os.F_OK)

    @staticmethod
    def canRead(fileName):
        if not os.access(fileName, os.R_OK):
            return False
        try:
            with open(fileName):
                pass
        except IOError:
            return False
        return True

    @staticmethod
    def canWrite(fileName):
        return os.access(fileName, os.W_OK)

    """File Operations"""

    @staticmethod
    def read(fileName):
        result = ''
        with open(fileName, 'r') as fd:
            for line in fd.readlines():
                result += line
        return result

    @staticmethod
    def getLines(fileName):
        with open(fileName, 'r', errors="replace") as fd:
            return fd.read().splitlines()

    """is Dir/File Check"""

    @staticmethod
    def isDir(fileName):
        return os.path.isdir(fileName)

    @staticmethod
    def isFile(fileName):
        return os.path.isfile(fileName)

    @staticmethod
    def createDirectory(directory):
        if not FileUtils.exists(directory):
            os.makedirs(directory)

    @staticmethod
    def sizeIEC(num):
        """
        @brief      Output The File Size in IEC Standard

        @param      num   Length of The File

        @return     Appropriate Format of Size
        """
        base = 1024
        # Find The Modest Unit for Given Length
        for x in ['B ', 'KB', 'MB', 'GB']:
            if (num < base) and (num > -base):
                return "%3.0f %s" % (num, x)
            num /= base
        return "%3.0f %s" % (num, 'TB')

    @staticmethod
    def writeLines(fileName, lines):
        content = None
        if type(lines) is list:
            content = "\n".join(lines)
        else:
            content = lines
        with open(fileName, "w") as f:
            f.writelines(content)
