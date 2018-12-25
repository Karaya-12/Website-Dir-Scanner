import re
from difflib import SequenceMatcher

from .ScannerException import ScannerException
from lib.utils.RandomUtils import RandomUtils
from thirdparty.sqlmap.DynamicContentParser import DynamicContentParser


class Scanner(object):
    def __init__(self, requester, failedPath=None, suffix=None):
        self.requester = requester
        self.failedPath = failedPath
        # If No Specific Failed Scanning Path is Passed In -> Generate A Random Path
        if failedPath is None or failedPath is "":
            self.failedPath = RandomUtils.randString()
        self.suffix = suffix if suffix is not None else ""

        self.tester = None
        self.redirectRegExp = None
        self.invalidStatus = None
        self.dynamicParser = None
        self.ratio = 0.98
        self.redirectStatusCodes = [301, 302, 307]

        self.setup()

    def setup(self):
        failedFullPath = self.failedPath + self.suffix
        failedResponse = self.requester.request(failedFullPath)

        self.invalidStatus = failedResponse.status
        if self.invalidStatus == 404:
            return None

        # Scanning for Websites' Redirects
        randomFullPath = RandomUtils.randString(
            omit=self.failedPath) + self.suffix
        randomResponse = self.requester.request(randomFullPath)

        if failedResponse.status in self.redirectStatusCodes and failedResponse.redirect and randomResponse.redirect:
            self.redirectRegExp = self.generateRedirectRegExp(
                failedResponse.redirect, randomResponse.redirect)

        # Analyze Response Bodies
        self.dynamicParser = DynamicContentParser(
            self.requester, failedFullPath, failedResponse.body,
            randomResponse.body)
        baseRatio = float("{0:.2f}".format(self.dynamicParser.comparisonRatio))

        # Adjusting The Ratio, If Length is Too Small
        if len(failedResponse) < 2000:
            baseRatio -= 0.1
        if baseRatio < self.ratio:
            self.ratio = baseRatio

    def generateRedirectRegExp(self, redirect_1, redirect_2):
        marks = []
        # Check Out Python Documentation -> class difflib.SequenceMatcher()
        matcher = SequenceMatcher(None, redirect_1, redirect_2)
        # Check Out SequenceMatcher.get_matching_blocks() Function
        for blocks in matcher.get_matching_blocks():
            i = blocks[0]
            n = blocks[2]
            if n == 0:  # Reached The Last Dummy Block
                continue  # Break Out of The Loop
            mark = redirect_1[i:i + n]
            marks.append(mark)
        regexp = "^.*{0}.*$".format(".*".join(map(re.escape, marks)))
        return regexp

    def scanning(self, path, response):
        if self.invalidStatus != response.status:
            return True
        elif self.invalidStatus == 404:  # invalidStatus == status == 404
            return False
        redirectToInvalid = False
        if self.redirectRegExp is not None and response.redirect is not None:
            redirectToInvalid = re.match(self.redirectRegExp,
                                         response.redirect) is not None
            if not redirectToInvalid:  # If Redirection Doesn't Match The Rule, Mark As Found
                return True
        ratio = self.dynamicParser.compareTo(response.body)
        if ratio >= self.ratio:
            return False
        elif redirectToInvalid and ratio >= (self.ratio - 0.15):
            return False
        return True
