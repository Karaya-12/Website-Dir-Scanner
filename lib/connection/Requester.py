import time
import random
import socket
import requests
from urllib import parse

from .Response import Response
from .RequestException import RequestException


class Requester(object):
    headers = {  # Dictionary for Target URL Header
        'User-agent':  # Set to Firefox 64 on Ubuntu Linux (Karaya_12)
        'Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:64.0) Gecko/20100101 Firefox/64.0',
        'Accept-Language': 'en-us',
        'Accept-Encoding': 'identity',
        'Keep-Alive': '300',
        'Connection': 'keep-alive',
        'Cache-Control': 'max-age=0',
    }

    def __init__(
            self,
            url,
            # General Section
            timeout=30,
            ip=None,
            proxy=None,
            maxRetries=5,
            requestByHostname=None,
            # Optional Section
            delay=0,
            numThreads=1,
            cookie=None,
            userAgent=None,
            redirect=False):

        # Ensure URL End With Backslash
        if not url.endswith('/'):
            url = url + '/'

        parsed = parse.urlparse(url)
        self.basePath = parsed.path

        # Set Protocol to HTTP by Default, If No Protocol is Specified
        if parsed.scheme != 'http' and parsed.scheme != 'https':
            parsed = parse.urlparse('http://' + url)
            self.basePath = parsed.path

        self.protocol = parsed.scheme
        if self.protocol != 'http' and self.protocol != 'https':
            self.protocol = 'http'

        self.host = parsed.netloc.split(':')[0]

        # Resolve DNS to Decrease Overhead
        if ip is not None:
            self.ip = ip
        else:
            try:
                self.ip = socket.gethostbyname(self.host)
            except socket.gaierror:
                raise RequestException({'message': "Couldn't Resolve DNS"})

        self.headers['Host'] = self.host

        # Set to Default 80, 443, If No Port is Specified
        # Port 80 --> World Wide Web HTTP
        # Port 443 -->HTTP Protocol Over TLS/SSL
        try:
            self.port = parsed.netloc.split(':')[1]
        except IndexError:
            self.port = (443 if self.protocol == 'https' else 80)

        # Set Cookie & Custom User Agent
        if cookie is not None:
            self.setHeader('Cookie', cookie)
        if userAgent is not None:
            self.setHeader('userAgent', userAgent)

            # General Section
            timeout = 30,
            ip = None,
            proxy = None,
            maxRetries = 5,
            requestByHostname = None,
            # Optional Section
            delay = 0,
            numThreads = 1,
            cookie = None,
            userAgent = None,
            redirect = False

        # General Section
        self.timeout = timeout
        self.proxy = proxy
        self.maxRetries = maxRetries
        self.requestByHostname = requestByHostname
        # Optional Section
        self.delay = delay
        self.numThreads = numThreads
        self.redirect = redirect
        # Additional Section
        self.pool = None
        self.randomAgents = None
        self.session = requests.Session()

    def setHeader(self, header, content):
        self.headers[header] = content

    def setRandomAgents(self, agents):
        self.randomAgents = list(agents)

    def unsetRandomAgents(self):
        self.randomAgents = None

    def generateURL(self, path):
        """
        @brief      Generate Target Full URL Based On User Settings

        @param      self  The Object
        @param      path  Passed In Later Part of URL

        @return     Target URL
        """
        if self.requestByHostname:
            url = "{0}://{1}:{2}".format(self.protocol, self.host, self.port)
        else:
            url = "{0}://{1}:{2}".format(self.protocol, self.ip, self.port)
            url = parse.urljoin(url, self.basePath)
            # Append Passed In Path to URL
            if not url.endswith('/'):
                url += "/"
            if path.startswith('/'):
                path = path[1:]
            url += path
        return url

    def generateHeader(self):
        """
        @brief      Generate Target URL Header

        @param      self  The Object

        @return     Target URL Header
        """
        headers = dict(self.headers)
        if self.randomAgents is not None:
            headers["User-agent"] = random.choice(self.randomAgents)
        headers["Host"] = self.host
        # Add Custom Port Number Into The Header If It's Non-Standard
        if (self.protocol == "https"
                and self.port != 443) or (self.protocol == "http"
                                          and self.port != 80):
            headers["Host"] += ":{0}".format(self.port)
        return headers

    def request(self, path):
        """
        @brief      Return The 'Response' Object of Target URL

        @param      self  The Object
        @param      path  Passed In Later Part of URL

        @return     'Response' Object
        """
        i = 0
        while i <= self.maxRetries:
            try:
                proxy = None
                if self.proxy is not None:  # User Proxy Setting
                    proxy = {"https": self.proxy, "http": self.proxy}
                url = self.generateURL(path)  # Get Target Full URL
                headers = self.generateHeader()  # Get Target URL Header

                # Send A 'Get' Request, Return A 'Response' Object
                response = self.session.get(
                    url,
                    proxies=proxy,
                    verify=False,
                    allow_redirects=self.redirect,
                    headers=headers,
                    timeout=self.timeout)

                # Get The Target URL 'Response' Object
                result = None
                result = Response(response.status_code, response.reason,
                                  response.headers, response.content)
                time.sleep(self.delay)

                del headers
                # 'break' is only reached when there is no exception in the lines before
                break  # Pull Out of The Loop If No Exception is Caught

            # Catch Possible Errors
            except requests.exceptions.TooManyRedirects as e:  # Too Many Redirects
                raise RequestException({
                    'message':
                    "Too many redirects: {0}".format(e)
                })

            except requests.exceptions.SSLError:  # SSL Error
                raise RequestException({
                    'message':
                    "SSL Error connecting to server.\nTry the -b flag to connect by hostname.."
                })

            except requests.exceptions.ConnectionError as e:  # Connection Error
                if self.proxy is not None:
                    raise RequestException({
                        'message':
                        "Error with the proxy: {0}".format(e)
                    })
                continue

            except (
                    requests.exceptions.
                    ReadTimeout,  # Catch Other Possible Errors
                    requests.exceptions.Timeout,
                    socket.timeout):
                continue

            finally:  # Next Loop
                i = i + 1

        if i > self.maxRetries:  # Reach Max Retries --> Raise Error
            raise RequestException({
                'message':
                'Connection Timeout ! A problem occured during the request to: {0}'
                .format(path)
            })

        return result
