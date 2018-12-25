import threading


class ReportController(object):
    def __init__(self):
        self.outputs = []
        self.lock = threading.RLock()

    def addReport(self, output):
        self.outputs.append(output)

    def addPath(self, path, status, response):
        with self.lock:
            for output in self.outputs:
                output.addPath(path, status, response)

    def saveReport(self):
        with self.lock:
            for output in self.outputs:
                output.saveRecord()

    def close(self):
        for output in self.outputs:
            output.close()
