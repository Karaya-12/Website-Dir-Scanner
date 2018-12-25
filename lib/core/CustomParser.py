from argparse import ArgumentParser

from thirdparty.oset.pyoset import oset
from lib.utils.FileOps import FileOps
from lib.utils.FileUtils import FileUtils
from lib.utils.CustomConfigParser import CustomConfigParser


class CustomParser(object):
    """
    @brief      Parse The Arguments In The Command Line
    __init__() --> Class initialization
    parseConfig() --> Parse the local directory 'default.conf'
    parseArgument --> Parse the console passed arguments

    @return     args --> ArgumentParser Result
    args Elements
    * Mandatory
    url, urlList, extensions
    * Connection
    timeout, ip, httpProxy, maxRetries, requestByHostname
    * Optional
    delay, recursive, suppressEmpty, scanSubdirs, excludeSubdirs
    numThreads, excludeStatusCodes, cookie, userAgent
    noFollowRedirects, headers, useRandomAgents
    * Reports
    simpleOutputFile, plainTextOutputFile, jsonOutputFile
    * Dictionary
    wordlist, lowercase, forceExtensions
    """

    def __init__(self, script_path):
        self.script_path = script_path
        self.parseConfig()  # Load The Local Preset Config First
        # Load The Command Line Passed In Arguments, Override Default Config
        args = self.parseArguments()

        # Load Command Line Passed In URL (List)
        if args.url is None:
            # If Using URL List
            if args.urlList is not None:
                with FileOps(args.urlList) as urlList:
                    # Exit Scanner If URL List Can't Be Loaded
                    if not urlList.exists():  # Existence Check
                        print("The URL List is Missing...")
                        exit(0)
                    if not urlList.isValid():  # Validation Check
                        print("The URL List is Invalid...")
                        exit(0)
                    if not urlList.canRead():  # Readability Check
                        print("The URL List is Not Readable...")
                        exit(0)
                    # Call getLines() Method In FileOps Module
                    # Parse The URL List Into The Scanner
                    self.urlList = list(urlList.getLines())
            else:  # Missing Target URL --> Exit
                print(
                    "Target URL (List) is Missing ...\n" +
                    "Restart The Scanner With Proper '[-u|--url] <Target URL>' Usage\n"
                )
                exit(0)
        else:  # No Passed In URL --> Set to None
            self.urlList = [args.url]

        # Check Command Line Extensions
        if args.extensions is None:
            print("At Least One Extension Must Be Specified\n" +
                  "Exiting...\n")
            exit(0)

        # Exit Scanner If Wordlist Can't Be Loaded
        with FileOps(args.wordlist) as wordlist:
            if not wordlist.exists():
                print("Wordlist is Missing...")
                exit(0)
            if not wordlist.isValid():
                print("The Wordlist is Invalid...")
                exit(0)
            if not wordlist.canRead():
                print("The Wordlist is Not Readable...")
                exit(0)

        # Load The Custom HTTP Proxy
        if args.httpProxy is not None:
            if args.httpProxy.startswith('http://'):
                self.proxy = args.httpProxy
            else:
                self.proxy = 'http://{0}'.format(args.httpProxy)
        else:
            self.proxy = None

        # Threads Number Must >= 1
        if args.numThreads < 1:
            print("Must Have At Least 1 Thread, Please Restart...")
            exit(0)
        self.numThreads = args.numThreads

        # Load The Custom Headers
        if args.headers is not None:
            try:
                self.headers = dict(
                    (key.strip(), value.strip())
                    for (key, value) in (header.split(':', 1)
                                         for header in args.headers))
            except Exception:
                print("Invalid Headers...")
                exit(0)
        else:
            self.headers = {}

        # Load The Custom Excluded Status Codes
        if args.excludeStatusCodes is not None:
            try:
                self.excludeStatusCodes = list(
                    oset([
                        int(excludeStatusCode.strip())
                        if excludeStatusCode else None for excludeStatusCode in
                        args.excludeStatusCodes.split(',')
                    ]))
            except ValueError:
                self.excludeStatusCodes = []
        else:
            self.excludeStatusCodes = []

        # Load The Subdirs of Website
        if args.scanSubdirs is not None:
            self.scanSubdirs = list(
                # Using Third Party --> oset/pyoset Module
                oset([
                    subdir.strip() for subdir in args.scanSubdirs.split(',')
                ]))
            # Strip All '/' From The Custom Sub Directories
            for i in range(len(self.scanSubdirs)):
                while self.scanSubdirs[i].startswith("/"):  # Front
                    self.scanSubdirs[i] = self.scanSubdirs[i][1:]
                while self.scanSubdirs[i].endswith("/"):  # End
                    self.scanSubdirs[i] = self.scanSubdirs[i][:-1]
            # Add Backslash for Each Sub Directories
            self.scanSubdirs = list(
                oset([subdir + "/" for subdir in self.scanSubdirs]))
        else:
            self.scanSubdirs = None

        # Load The Exluded Sub Directories
        # Must Be Used In Conjunction With Recursive Mode
        if args.excludeSubdirs is not None:
            if not args.recursive:
                print(
                    "Be Aware: Exclude Dirs Must Be Used In Conjunction With Recursive Mode (-r|--recursive)"
                )
                exit(0)
            else:  # Load The Excluded Sub Directories
                self.excludeSubdirs = list(
                    oset([
                        subdir.strip()
                        for subdir in args.excludeSubdirs.split(',')
                    ]))
                # Strip All '/' From The Custom Sub Directories
                for i in range(len(self.excludeSubdirs)):
                    while self.excludeSubdirs[i].startswith("/"):
                        self.excludeSubdirs[i] = self.excludeSubdirs[i][1:]
                    while self.excludeSubdirs[i].endswith("/"):
                        self.excludeSubdirs[i] = self.excludeSubdirs[i][:-1]
                self.excludeSubdirs = list(oset(self.excludeSubdirs))
        else:
            self.excludeSubdirs = None

        # Initialize The Reminants Down Below

        # Mandatory Section Arguments
        self.extensions = list(
            oset([
                extension.strip() for extension in args.extensions.split(',')
            ]))

        # Connection Section Arguments
        self.timeout = args.timeout
        self.ip = args.ip
        self.maxRetries = args.maxRetries
        self.requestByHostname = args.requestByHostname

        # Optional Section Arguments
        self.delay = args.delay
        self.recursive = args.recursive
        self.suppressEmpty = args.suppressEmpty
        self.cookie = args.cookie
        self.userAgent = args.userAgent
        self.useRandomAgents = args.useRandomAgents
        self.redirect = args.noFollowRedirects

        # Reports Section Arguments
        self.simpleOutputFile = args.simpleOutputFile
        self.plainTextOutputFile = args.plainTextOutputFile
        self.jsonOutputFile = args.jsonOutputFile

        # Dictionary Section Arguments
        self.wordlist = args.wordlist
        self.lowercase = args.lowercase
        self.forceExtensions = args.forceExtensions

    def parseConfig(self):
        config = CustomConfigParser()

        # Parse & Load The Local Preset Config 'default.conf'
        configPath = FileUtils.createPath(self.script_path, "default.conf")
        config.read(configPath)

        # 'General' Section -> Use The Default Setting (if not overridden)
        self.saveHome = config.try_getboolean(  # saveHome
            "general", "save-logs-home", False)
        self.failedScanPath = config.try_get(  # Failed Test Path
            "general", "scanner-fail-path", "").strip()

        # 'Connection' Section -> Use The Default Setting (if not overridden)
        self.timeout = config.try_getint("connection", "timeout", 30)  # 1
        self.ip = config.try_get("connection", "ip", None)  # 2
        self.proxy = config.try_get("connection", "httpProxy", None)  # 3
        self.maxRetries = config.try_getint("connection", "maxRetries", 5)  # 4
        self.requestByHostname = config.try_getboolean(  # 5
            "connection", "requestByHostname", False)

        # 'Optional' Section -> Use The Default Setting (if not overridden)
        self.delay = config.try_getfloat("optional", "delay", 0)  # 1
        self.recursive = config.try_getboolean(  # 2
            "optional", "recursive", False)
        self.numThreads = config.try_getint(  # 3
            "optional", "numThreads", 10, list(range(1, 50)))
        self.suppressEmpty = config.try_getboolean(  # 4
            "optional", "suppressEmpty", False)
        self.scanSubdirs = config.try_get("optional", "scanSubdirs", None)  # 5
        self.excludeSubdirs = config.try_get(  # 6
            "optional", "excludeSubdirs", None)
        self.excludeStatusCodes = config.try_get(  # 7
            "optional", "excludeStatusCodes", None)
        self.cookie = config.try_get("optional", "cookie", None)  # 8
        self.userAgent = config.try_get("connection", "user-agent", None)  # 9
        self.redirect = config.try_getboolean(  # 10
            "optional", "noFollowRedirects", False)
        self.headers = config.try_get("optional", "headers", None)  # 11
        self.useRandomAgents = config.try_get(  # 12
            "connection", "random-user-agents", False)

        # 'Reports' Section -> Use The Default Setting (if not overridden)
        self.autoSave = config.try_getboolean("reports", "autosave-report",
                                              False)
        self.autoSaveFormat = config.try_get("reports",
                                             "autosave-report-format", "plain",
                                             ["simple", "plain", "json"])

        # 'Dictionary' Section -> Use The Default Setting (if not overridden)
        self.wordlist = config.try_get(  #1
            "dictionary", "wordlist",
            FileUtils.createPath(self.script_path, "db", "dicc.txt"))
        self.lowercase = config.try_getboolean(  #2
            "dictionary", "lowercase", False)
        self.forceExtensions = config.try_get(  # 3
            "dictionary", "forceExtensions", False)

    def parseArguments(self):
        """
        Check Out Python 3 Documentation -->
        argparse.add_argument() & add_argument_group() Methods
        """
        # Command Line Usage Pattern
        usage = 'Usage: %prog [-u|--url] target [-e|--extensions] extensions [options]'
        argParser = ArgumentParser(usage)

        # I. "Mandatory" Section Arguments: -u, --ls, -e
        mandatory = argParser.add_argument_group("Mandatory")
        # 1. Option: -u --> URL
        mandatory.add_argument(
            '-u',
            '--url',
            help="Target URL",
            action='store',
            type=str,
            dest='url')
        # 2. Option: --ls --> URL List
        mandatory.add_argument(
            '--ls',
            '--url-list',
            help="Import Local Target URL List (e.g. ./Temp.txt)",
            action='store',
            type=str,
            dest='urlList')
        # 3. Option: -e --> File Extensions
        mandatory.add_argument(
            '-e',
            '--extensions',
            help="Extension List Separated By Comma (e.g. php, asp)",
            action='store',
            type=str,
            dest='extensions')

        # II. "Connection" Section Arguments: --timeout, --ip, --proxy,  --max-retries, -b
        connection = argParser.add_argument_group("Connection Settings")
        # 1. Option: --timeout --> Connection Timeout
        connection.add_argument(
            '--timeout',
            help="Connection Timeout",
            action='store',
            type=int,
            dest='timeout',
            default=self.timeout)
        # 2. Option: --ip --> Resolve Name to IP Address
        connection.add_argument(
            '--ip',
            help="Resolve Name to IP Address",
            action='store',
            dest='ip')
        # 3. Option: --proxy --> HTTP Proxy
        connection.add_argument(
            '--proxy',
            '--http-proxy',
            help="Http Proxy (e.g. localhost:8080)",
            action='store',
            type=str,
            dest='httpProxy',
            default=self.proxy)
        # 4. Option: --max-retries --> Max Retry Times
        connection.add_argument(
            '--max-retries',
            help="Max Retry Times",
            action='store',
            type=int,
            dest='maxRetries',
            default=self.maxRetries)
        # 5. Option: -b --> Request by Hostname
        connection.add_argument(
            '-b',
            '--request-by-hostname',
            help=
            "Force Request by Hostname (Boolean Value, By default DirScanner will request by IP)",
            action='store_true',
            dest='requestByHostname',
            default=self.requestByHostname)

        # III. "Optional" Section Arguments
        # -d, -r, -t, -x, -c, ,-ua, -fr, -hdr
        # --suppress-empty, --scan-subdirs, --exclude-subdir
        optional = argParser.add_argument_group("Optional Settings")
        # 1. Option: -d --> Delay
        optional.add_argument(
            '-d',
            '--delay',
            help="Delay Between Requests (Float Value)",
            type=float,
            action='store',
            dest='delay',
            default=self.delay)
        # 2. Option: -r --> Recursive Mode
        optional.add_argument(
            '-r',
            '--recursive',
            help="Recursive Brute Force (Boolean Value)",
            action='store_true',
            dest='recursive',
            default=self.recursive)
        # 3. Option: -t --> Threads
        optional.add_argument(
            '-t',
            '--threads',
            help="Number of Threads (Range: 1 ~ 50)",
            action='store',
            type=int,
            dest='numThreads',
            default=self.numThreads)
        # 4. Option: --suppress-empty --> Suppress Empty
        optional.add_argument(
            '--suppress-empty',
            '--suppress-empty',
            help="Suppress Empty (Boolean Value)",
            action='store_true',
            dest='suppressEmpty')
        # 5. Option: --scan-subdirs --> Subdirs of Website
        optional.add_argument(
            '--scan-subdirs',
            '--scan-subdirs',
            help="Scan Subdirectories of Target -u|--url (Separate by Comma)",
            action='store',
            dest='scanSubdirs')
        # 6. Option: --exclude-subdir --> Exclude The Following Subdirectories
        optional.add_argument(
            '--exclude-subdirs',
            '--exclude-subdirs',
            help=
            "Exclude The Following Subdirectories During Recursive Scanning (Separate by Comma)\n"
            +
            "Be Aware: Exclude Dirs Can Only Be Used With Recursive Mode (-r|--recursive)",
            action='store',
            dest='excludeSubdirs')
        # 7. Option: -x --> Exclude Status Code
        optional.add_argument(
            '-x',
            '--exclude-status',
            help="Exclude Status Code (Separate by Comma, e.g. 301, 500)",
            action='store',
            dest='excludeStatusCodes',
            default=self.excludeStatusCodes)
        # 8. Option: -c --> Website Cookie
        optional.add_argument(
            '-c',
            '--cookie',
            help="Website Cookie",
            action='store',
            type=str,
            dest='cookie')
        # 9. Option: --ua --> User Agent
        optional.add_argument(
            '--ua',
            '--user-agent',
            help="User Agent",
            action='store',
            type=str,
            dest='userAgent',
            default=self.userAgent)
        # 10. Option: --fr --> Follow Redirects
        optional.add_argument(
            '--fr',
            '--follow-redirects',
            help="Follow Redirects (Boolean Value)",
            action='store_true',
            dest='noFollowRedirects',
            default=self.redirect)
        # 11. Option: -hdr --> Headers
        optional.add_argument(
            '-hdr',
            '--headers',
            help="Add Custom Headers to The Command Line\n" +
            "(e.g. --headers 'Referer: example.com'; --headers 'User-Agent: IE'",
            action='append',
            type=str,
            dest='headers')
        # 12. Option: --random-agents --> Random User Agents
        optional.add_argument(
            '--random-agents',
            '--random-user-agents',
            help="Random User Agents",
            action='store_true',
            dest='useRandomAgents')

        # IV. "Reports" Section Arguments
        # 3 Output Versions --> Simple/Plain Text/JSON Reports
        reports = argParser.add_argument_group("Reports")
        # 1. Option: --simple-report --> Using Simple Report
        reports.add_argument(
            '--simple-report',
            help="Record Paths Only",
            action='store',
            dest='simpleOutputFile')
        # 2. Option: --plain-text-report --> Using Plain Text Report
        reports.add_argument(
            '--plain-text-report',
            help="Record Paths With Status Codes",
            action='store',
            dest='plainTextOutputFile')
        # 3. Option: --json-report --> Using JSON Report
        reports.add_argument(
            '--json-report',
            help="Record Paths With JSON File",
            action='store',
            dest='jsonOutputFile')

        # V. "Dictionary" Section Arguments: -w, -l, -f
        dictionary = argParser.add_argument_group("Dictionary Settings")
        # 1. Option: -w --> Word List
        dictionary.add_argument(
            '-w',
            '--wordlist',
            help="Wordlist",
            action='store',
            dest='wordlist',
            default=self.wordlist)
        # 2. Option: -l --> Lowercase
        dictionary.add_argument(
            '-l',
            '--lowercase',
            help="Lowercase (Boolean Value)",
            action='store_true',
            dest='lowercase',
            default=self.lowercase)
        # 3. Option: -f --> Force Extensions
        dictionary.add_argument(
            '-f',
            '--force-extensions',
            help="Force Extensions for Every Wordlist Entry",
            action='store_true',
            dest='forceExtensions',
            default=self.forceExtensions)

        args = argParser.parse_args()
        return args
