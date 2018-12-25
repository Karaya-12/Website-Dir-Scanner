import gc
import os
import sys
import time

from queue import Queue
from threading import Lock

from .SkipTargetInterrupt import SkipTargetInterrupt
from lib.utils.FileUtils import FileUtils
from lib.connection.Requester import Requester
from lib.connection.RequestException import RequestException
from lib.core.Fuzzer import Fuzzer
from lib.core.Dictionary import Dictionary
from lib.core.ReportController import ReportController
from lib.reports.SimpleReport import SimpleReport
from lib.reports.JSONReport import JSONReport
from lib.reports.PlainTextReport import PlainTextReport

# Version Control of Website Dir Scanner
Major_Verison = 1
Minor_Version = 1
Revision = 0
Version_Pattern = {
    "Major_Verison": Major_Verison,
    "Minor_Version": Minor_Version,
    "Revision": Revision
}


class Controller(object):
    def __init__(self, script_path, arguments, output):
        # Load The Local Custom Banner, Version & Author Info
        global Version_Pattern
        path_banner = FileUtils.createPath(script_path, "sources",
                                           "CLI_Banner.txt")
        path_version_author = FileUtils.createPath(script_path, "sources",
                                                   "CLI_Version_Author.txt")
        CLI_Banner = open(path_banner).read()
        CLI_Version_Author = open(path_version_author).read().format(
            **Version_Pattern)
        self.output = output
        self.output.header(CLI_Banner)
        self.output.versionAuthor(CLI_Version_Author)

        self.arguments = arguments
        self.script_path = script_path
        self.savePath = script_path
        self.blacklists = self.getBlacklists()

        self.recursive = self.arguments.recursive
        self.suppressEmpty = self.arguments.suppressEmpty
        self.excludeSubdirs = (arguments.excludeSubdirs
                               if arguments.excludeSubdirs is not None else [])
        self.excludeStatusCodes = self.arguments.excludeStatusCodes
        self.DirQue = Queue()  # Standard FIFO Queue --> Storing Dirs

        self.fuzzer = None
        self.batch = False
        self.batchSession = None
        self.exit = False

        # Custom Save Path, Reports Path
        if self.arguments.saveHome:
            self.savePath = self.saveHomeOption()
        # Error Logs Path
        self.errorLog = None
        self.errorLogPath = None
        self.errorLogLock = Lock()
        self.errorLogPath = self.getErrorPath()
        self.errorLog = open(self.errorLogPath, "w")

        # Reports & Local Directory Paths
        self.reportsPath = None
        self.directoryPath = None

        self.dictionary = Dictionary(
            self.arguments.wordlist, self.arguments.extensions,
            self.arguments.lowercase, self.arguments.forceExtensions)

        # Auto Save Check
        if self.arguments.autoSave and len(self.arguments.urlList) > 1:
            self.setupBatchReports()
            self.output.newLine("\nAutoSave Path: {0}".format(
                self.batchDirectoryPath))

        # Random Agents Check
        if self.arguments.useRandomAgents:
            self.randomAgents = FileUtils.getLines(
                FileUtils.createPath(script_path, "db", "user-agents.txt"))

        # Print Out The Custom Extension, Threads Number & Dictionary Size
        self.printBasicConf()
        self.dirScanning()  # Main Directory Scanning Method

        self.output.warning("\nScanning Completed !")  # Scanning Completed

    def getBlacklists(self):
        """
        @brief      Get The Local Preset Status Code Related Blacklist

        @param      self  The Object

        @return     Target Blacklist Dictionary
        """
        blacklists = {}  # Target Dictionary (Consists of Status Code Lists)
        # 400 -> Bad Request, 403 -> Forbidden, 500 ->Internal Server Error
        db_Path = FileUtils.createPath(self.script_path, 'db')  # Local DB Path
        for status in [400, 403, 500]:
            blacklistFileName = FileUtils.createPath(  # Join Status Code as Filename (e.g. 403_blacklist.txt)
                db_Path, '{}_blacklist.txt'.format(status))
            blacklists[status] = []  # Status Code List Contained In Dictionary

            if not FileUtils.canRead(blacklistFileName):
                continue  # Skip Unreadable File
            for line in FileUtils.getLines(blacklistFileName):
                if line.lstrip().startswith('#'):
                    continue  # Skip Comments In The File
                blacklists[status].append(line)

        return blacklists

    def getSavePath(self):
        basePath = None
        basePath = os.path.expanduser('~')

        dirPath = None
        if os.name == 'nt':
            dirPath = "DirScanner"
        else:
            dirPath = ".DirScanner"

        return FileUtils.createPath(basePath, dirPath)

    def saveHomeOption(self):
        # If saveHome == True --> Get 'savePath' Path
        savePath = self.getSavePath()
        if not FileUtils.exists(savePath):  # Check Existence
            FileUtils.createDirectory(savePath)
        if FileUtils.exists(
                savePath) and not FileUtils.isDir(savePath):  # Check Status
            self.output.error(
                "NOT Available ! {} is a File, Should be a Directory.\nPlease Check Again."
                .format(savePath))
            exit(1)
        if not FileUtils.canWrite(savePath):  # Check Writability
            self.output.error(
                "Directory {} is Not Writable.\nPlease Check Again.".format(
                    savePath))
            exit(1)
        return savePath

    def getErrorPath(self):
        fileName = "errors-{0}.log".format(time.strftime('%y-%m-%d_%H-%M-%S'))
        errorLogPath = FileUtils.createPath(
            FileUtils.createPath(self.savePath, "logs", fileName))
        return errorLogPath

    def getReportsPath(self, requester):
        if self.arguments.autoSave:  # Default True
            basePath = ('/'
                        if requester.basePath is '' else requester.basePath)
            basePath = basePath.replace(os.path.sep, '.')[1:-1]

            # Generate File Name & Directory Path
            fileName = None
            directoryPath = None
            if self.batch:
                fileName = requester.host
                directoryPath = self.batchDirectoryPath
            else:
                fileName = ('{}_'.format(basePath)
                            if basePath is not '' else '')
                fileName += time.strftime('%y-%m-%d_%H-%M-%S')
                directoryPath = FileUtils.createPath(self.savePath, 'reports',
                                                     requester.host)

            if not FileUtils.exists(directoryPath):
                FileUtils.createDirectory(directoryPath)
                if not FileUtils.exists(directoryPath):
                    self.output.error("Cannot Create Reports Folder {}".format(
                        directoryPath))
                    sys.exit(1)

            # Generate Reports File Path
            outputFile = FileUtils.createPath(directoryPath, fileName)

            # Rename If Duplicate File is Found In Target Directory
            if FileUtils.exists(outputFile):
                i = 2
                while FileUtils.exists(outputFile + "_" + str(i)):
                    i += 1
                outputFile += "_" + str(i)

        return outputFile, directoryPath

    def printBasicConf(self):
        """Call Output Config Method"""
        self.output.config(', '.join(self.arguments.extensions),
                           str(self.arguments.numThreads),
                           str(len(self.dictionary)))

    def setupBatchReports(self):
        self.batch = True
        self.batchSession = "Batch-{0}".format(
            time.strftime('%y-%m-%d_%H-%M-%S'))
        self.batchDirectoryPath = FileUtils.createPath(
            self.savePath, "reports", self.batchSession)

        if not FileUtils.exists(self.batchDirectoryPath):
            FileUtils.createDirectory(self.batchDirectoryPath)
            if not FileUtils.exists(self.batchDirectoryPath):
                self.output.error("Cannot Create Batch Folder {}".format(
                    self.batchDirectoryPath))
                sys.exit(1)

        if FileUtils.canWrite(self.batchDirectoryPath):
            FileUtils.createDirectory(self.batchDirectoryPath)
            targetsFile = FileUtils.createPath(self.batchDirectoryPath,
                                               "Target-URL-List.txt")
            FileUtils.writeLines(targetsFile, self.arguments.urlList)
        else:
            self.output.error("Cannnot Write Batch Folder {}.".format(
                self.batchDirectoryPath))
            sys.exit(1)

    def setupReports(self, requester):
        if self.arguments.autoSave:  # Default True
            # Auto Save Format Option
            if FileUtils.canWrite(self.directoryPath):
                report = None
                if self.arguments.autoSaveFormat == 'simple':
                    report = SimpleReport(requester.host, requester.port,
                                          requester.protocol,
                                          requester.basePath, self.reportsPath)
                if self.arguments.autoSaveFormat == 'json':
                    report = JSONReport(requester.host, requester.port,
                                        requester.protocol, requester.basePath,
                                        self.reportsPath)
                else:  # PlainTextReport
                    report = PlainTextReport(
                        requester.host, requester.port, requester.protocol,
                        requester.basePath, self.reportsPath)
                self.reportController.addReport(report)
            else:
                self.output.error("Cannot Write Reports to {}".format(
                    self.directoryPath))
                sys.exit(1)

        # Save Format Option
        if self.arguments.simpleOutputFile is not None:  # Simple Format
            self.reportController.addReport(
                SimpleReport(requester.host, requester.port,
                             requester.protocol, requester.basePath,
                             self.arguments.simpleOutputFile))
        if self.arguments.plainTextOutputFile is not None:  # Plain Text Format
            self.reportController.addReport(
                PlainTextReport(requester.host, requester.port,
                                requester.protocol, requester.basePath,
                                self.arguments.plainTextOutputFile))
        if self.arguments.jsonOutputFile is not None:  # JSON Format
            self.reportController.addReport(
                JSONReport(requester.host, requester.port, requester.protocol,
                           requester.basePath, self.arguments.jsonOutputFile))

    def matchCallback(self, path):
        self.index += 1
        if path.status is not None:
            # Target Path Status Code is Not In Excluded State Code & Blacklists
            if path.status not in self.excludeStatusCodes and (
                    self.blacklists.get(path.status) is None
                    or path.path not in self.blacklists.get(
                        path.status)) and not (self.suppressEmpty and
                                               (len(path.response.body) == 0)):
                self.output.statusReport(path.path, path.response)
                self.addDirectory(path.path)
                self.reportController.addPath(
                    self.currentDirectory + path.path, path.status,
                    path.response)
                self.reportController.saveReport()
                del path

    def notFoundCallback(self, path):
        self.index += 1
        self.output.lastPath(path, self.index, len(self.dictionary))
        del path

    def errorCallback(self, path, errorMsg):
        self.output.addConnectionError()
        del path

    def appendErrorLog(self, path, errorMsg):
        with self.errorLogLock:
            line = time.strftime('[%y-%m-%d %H:%M:%S] - ')
            line += self.currentUrl + " - " + path + " - " + errorMsg
            # message line + 'os.linesep' --> Separate (Terminate) lines on the current platform
            self.errorLog.write(line + os.linesep)
            self.errorLog.flush()

    def handleInterrupt(self):
        """Handle The KeyboardInterrupt Caused by User"""
        self.output.warning(
            'CTRL+C Detected: Pausing Threads.\n"+"Please Wait...')
        self.fuzzer.pauseEvent()

        try:
            while True:
                msg = "[e]xit / [c]ontinue"
                if not self.DirQue.empty():
                    msg += " / [n]ext"
                if len(self.arguments.urlList) > 1:
                    msg += " / [s]kip target"
                self.output.inLine(msg + ': ')
                option = input()

                if option.lower() == 'e':
                    self.exit = True
                    self.fuzzer.stop()
                    raise KeyboardInterrupt
                elif option.lower() == 'c':
                    self.fuzzer.startEvent()
                    return
                elif not self.DirQue.empty() and option.lower() == 'n':
                    self.fuzzer.stop()
                    return
                elif len(self.arguments.urlList) > 1 and option.lower() == 's':
                    raise SkipTargetInterrupt
                else:
                    continue
        except KeyboardInterrupt:
            self.exit = True
            raise KeyboardInterrupt

    def processPaths(self):
        while True:
            try:
                while not self.fuzzer.wait(0.3):
                    continue
                break
            except (KeyboardInterrupt, SystemExit):
                self.handleInterrupt()  # Handle User KeyboardInterrupt

    def wait(self):
        while not self.DirQue.empty():  # If All Dir Have Been Traversed
            self.index = 0
            self.currentDirectory = self.DirQue.get()
            self.output.warning('[{1}] Starting: {0}'.format(
                self.currentDirectory, time.strftime('%H:%M:%S')))
            self.fuzzer.requester.basePath = self.basePath + self.currentDirectory
            self.output.basePath = self.basePath + self.currentDirectory
            self.fuzzer.start()
            self.processPaths()
        return

    def addDirectory(self, path):
        if not self.recursive:
            return False
        if path.endswith('/'):
            if path in [directory + '/' for directory in self.excludeSubdirs]:
                return False
            self.DirQue.put(self.currentDirectory + path)
            return True
        else:
            return False

    def dirScanning(self):
        try:
            for url in self.arguments.urlList:
                try:
                    # Check Out Python 3 Documentation --> gc Module
                    # Basic Usage: gc.collect(generation=2)
                    gc.collect()
                    # Instantiate The Requester with CLI Arguments
                    try:
                        self.requester = Requester(
                            url,
                            # General Section
                            timeout=self.arguments.timeout,
                            ip=self.arguments.ip,
                            proxy=self.arguments.proxy,
                            maxRetries=self.arguments.maxRetries,
                            requestByHostname=self.arguments.requestByHostname,
                            # Optional Section
                            delay=self.arguments.delay,
                            numThreads=self.arguments.numThreads,
                            cookie=self.arguments.cookie,
                            userAgent=self.arguments.userAgent,
                            redirect=self.arguments.redirect)
                        self.requester.request("/")
                    except RequestException as e:
                        self.output.error(e.args[0])
                        raise SkipTargetInterrupt

                    self.reportController = ReportController()
                    self.currentUrl = url
                    # Display Target URL
                    self.output.targetURL(self.currentUrl)
                    # Display Target Reports & Error Logs Path
                    self.reportsPath, self.directoryPath = self.getReportsPath(
                        self.requester)
                    self.output.pathDisplay(self.reportsPath,
                                            self.errorLogPath)

                    # Initialize Directories Queue With Start Path
                    self.basePath = self.requester.basePath
                    if self.arguments.useRandomAgents:
                        self.requester.setRandomAgents(self.randomAgents)
                    # Parse The Header Dictionary & Set The Header
                    for key, value in self.arguments.headers.items():
                        self.requester.setHeader(key, value)
                    # Add Sub Directories Into The 'DirQue' If Exist
                    if self.arguments.scanSubdirs is not None:
                        for subdir in self.arguments.scanSubdirs:
                            self.DirQue.put(subdir)
                    else:
                        self.DirQue.put('')
                    # Set Up Scanner Report Function
                    self.setupReports(self.requester)

                    matchCallbacks = [self.matchCallback]
                    notFoundCallbacks = [self.notFoundCallback]
                    errorCallbacks = [self.errorCallback, self.appendErrorLog]

                    # Setup Fuzzer
                    self.fuzzer = Fuzzer(
                        self.requester,
                        self.dictionary,
                        threads=self.arguments.numThreads,
                        failedScanPath=self.arguments.failedScanPath,
                        matchCallbacks=matchCallbacks,
                        notFoundCallbacks=notFoundCallbacks,
                        errorCallbacks=errorCallbacks)

                    try:
                        self.wait()
                    except RequestException as e:
                        self.output.error(
                            "Fatal Error Occured During Dir Scanning Process: "
                            + e.args[0])
                        raise SkipTargetInterrupt
                except SkipTargetInterrupt:
                    continue
                finally:
                    self.reportController.saveReport()

        except KeyboardInterrupt:  # Ctrl+c -> e
            self.output.error("\nScanning Canceled by Current User ...")
            exit(0)
        finally:
            if not self.errorLog.closed:
                self.errorLog.close()
            self.reportController.close()
