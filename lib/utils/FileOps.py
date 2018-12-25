from lib.utils.FileUtils import FileUtils


class FileOps(object):
    def __init__(self, *pathComponents):
        self._path = FileUtils.createPath(*pathComponents)
        self.content = None

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        raise NotImplementedError

    def isValid(self):
        return FileUtils.isFile(self.path)

    def exists(self):
        return FileUtils.exists(self.path)

    def canRead(self):
        return FileUtils.canRead(self.path)

    def canWrite(self):
        return FileUtils.canWrite(self.path)

    def read(self):
        return FileUtils.read(self.path)

    def getLines(self):
        for line in FileUtils.getLines(self.path):
            yield line

    def __enter__(self):
        return self

    def __exit__(self, type, value, tb):
        pass
