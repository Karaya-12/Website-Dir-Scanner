class BaseReport(object):
    def __init__(self, host, port, protocol, basePath, output):
        self.host = host
        self.port = port
        self.protocol = protocol
        self.basePath = basePath
        self.output = output
        self.pathList = []

        # Format The 'basePath' Variable --> Strip '/'
        if self.basePath.endswith('/'):
            self.basePath = self.basePath[:-1]
        if self.basePath.startswith('/'):
            self.basePath = self.basePath[1:]

        self.openReport()

    def addPath(self, path, status, response):
        contentLength = None
        try:
            contentLength = int(response.headers['content-length'])
        except (KeyError, ValueError):
            contentLength = len(response.body)
        self.pathList.append((path, status, contentLength))

    def openReport(self):
        from os import name as os_name
        if os_name == "nt":  # Windows OS
            from os.path import normpath, dirname
            from os import makedirs
            output = normpath(self.output)
            makedirs(dirname(output), exist_ok=True)
            self.output = output
        self.file = open(self.output, 'w+')

    def saveRecord(self):
        self.file.seek(0)
        self.file.truncate(0)
        self.file.flush()
        self.file.writelines(self.recording())
        self.file.flush()

    def close(self):
        self.file.close()

    def recording(self):  # Record Scanning Process --> Override
        """
        Raise Exception: NotImplementedError (if base classes not overridden)
        Check Out Python 3.x Documentation -> NotImplementedError
        * Derived from RuntimeError
        * Abstract methods should raise the exception
        * when derived classes haven't overridden the method.
        """
        raise NotImplementedError
