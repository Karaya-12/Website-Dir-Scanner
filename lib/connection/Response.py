class Response(object):
    def __init__(self, status, reason, headers, body):
        self.status = status
        self.reason = reason
        self.headers = headers
        self.body = body

    def __str__(self):
        return self.body

    def __int__(self):
        return self.status

    def __eq__(self, other):
        return self.status == other.status and self.body == other.body

    def __cmp__(self, other):
        return (self.body > other) - (self.body < other)

    def __len__(self):
        return len(self.body)

    def __hash__(self):
        return hash(self.body)

    def __del__(self):
        del self.body
        del self.headers
        del self.status
        del self.reason

    @property
    def redirect(self):
        headers = dict(
            (key.lower(), value) for key, value in self.headers.items())
        return headers.get("location")

    @property
    def bsPrettify(self):
        try:
            from BeautifulSoup import BeautifulSoup
        except ImportError:
            raise Exception(
                "BeautifulSoup is required. Check out ./sources/requirement.txt"
            )
        bs = BeautifulSoup(self.body, 'html.parser')
        return bs.prettify()
