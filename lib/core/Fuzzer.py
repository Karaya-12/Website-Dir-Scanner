import threading

from .Path import Path
from .Scanner import Scanner
from lib.connection.RequestException import RequestException


class Fuzzer(object):
    def __init__(self,
                 requester,
                 dictionary,
                 threads=1,
                 failedScanPath=None,
                 matchCallbacks=[],
                 notFoundCallbacks=[],
                 errorCallbacks=[]):

        self.requester = requester
        self.dictionary = dictionary
        self.failedScanPath = failedScanPath
        self.basePath = self.requester.basePath
        self.threads = []
        self.numThreads = threads if len(self.dictionary) >= threads else len(
            self.dictionary)
        self.running = False
        self.scanners = {}
        self.defaultScanner = None
        self.matchCallbacks = matchCallbacks
        self.notFoundCallbacks = notFoundCallbacks
        self.errorCallbacks = errorCallbacks
        self.matches = []
        self.errors = []

    def setupScanners(self):
        if self.scanners is not None:
            self.scanners = {}  # Scanner Dictionary
        # 3 Types of Scanners --> Default (No Suffix), Dir ('/'), Specific Extensions ('.ext')
        self.defaultScanner = Scanner(self.requester, self.failedScanPath, "")
        self.scanners['/'] = Scanner(self.requester, self.failedScanPath, "/")
        for extension in self.dictionary.extensions:
            self.scanners[extension] = Scanner(
                self.requester, self.failedScanPath, "." + extension)

    def setupThreads(self):
        self.threads = []
        for _ in range(self.numThreads):
            newThread = threading.Thread(target=self.thread_proc)
            newThread.daemon = True
            self.threads.append(newThread)

    def scannerType(self, path):  # Get One of Total 3 Types
        if path.endswith('/'):  # Dir ('/')
            return self.scanners['/']
        for extension in list(self.scanners.keys()):
            if path.endswith(extension):  # Specific Extensions
                return self.scanners[extension]
        # By default, returns empty tester
        return self.defaultScanner  # Default Type

    def start(self):
        self.setupScanners()
        self.setupThreads()
        self.index = 0
        self.dictionary.reset2zero()
        self.runningThreadsCount = len(self.threads)
        self.running = True

        self.scanEvent = threading.Event()
        self.scanEvent.clear()  # Set Event to False
        self.pausedSemaphore = threading.Semaphore(0)
        self.exit = False

        for thread in self.threads:
            thread.start()
        self.startEvent()

    def startEvent(self):
        """Set Event to True"""
        self.scanEvent.set()

    def pauseEvent(self):
        """Set Event to False"""
        self.scanEvent.clear()
        for thread in self.threads:
            if thread.is_alive():
                # Set Alive Thread Semaphore to 0
                self.pausedSemaphore.acquire()

    def stop(self):
        self.running = False
        self.startEvent()

    def wait(self, timeout=None):
        for thread in self.threads:
            if timeout is None:
                thread.join()
            else:  # Have Custom Timeout
                thread.join(timeout)  # Use Custom Timeout As Parameter
                if thread.is_alive():
                    return False
        return True

    def scanning(self, path):
        """Scan Given Path from The Dictionary"""
        response = self.requester.request(path)
        result = None
        # Call scanning() In Scanner Module
        if self.scannerType(path).scanning(path, response):
            result = (None if response.status == 404 else response.status)
        return result, response

    def thread_proc(self):
        self.scanEvent.wait()
        try:
            path = next(self.dictionary)
            while path is not None:
                try:
                    status, response = self.scanning(path)
                    result = Path(path=path, status=status, response=response)

                    if status is not None:
                        self.matches.append(result)
                        for callback in self.matchCallbacks:
                            callback(result)
                    else:
                        for callback in self.notFoundCallbacks:
                            callback(result)

                    del status
                    del response

                except RequestException as e:
                    for callback in self.errorCallbacks:
                        # Check Out /connection/Requester Module Line 228
                        dict_ReqEx = dict(e.args[0])
                        callback(path, dict_ReqEx.get('message'))
                    continue

                finally:
                    if not self.scanEvent.isSet():
                        self.pausedSemaphore.release()
                        self.scanEvent.wait()
                    path = next(self.dictionary)
                    if not self.running:
                        break
        except StopIteration:
            return
        finally:
            self.runningThreadsCount -= 1  # Stop Thread
