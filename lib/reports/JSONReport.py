import json

from lib.reports.BaseReport import BaseReport


class JSONReport(BaseReport):
    def addPath(self, path, status, response):  # Override
        contentLength = None
        try:
            contentLength = int(response.headers['content-length'])
        except (KeyError, ValueError):
            contentLength = len(response.body)
        # response.redirect Appended
        self.pathList.append((path, status, contentLength, response.redirect))

    def recording(self):  # Override
        headerPattern = '{0}://{1}:{2}/{3}'.format(self.protocol, self.host,
                                                   self.port, self.basePath)
        record = {headerPattern: []}
        # self.pathList.append((path, status, contentLength))
        for path, status, contentLength, redirect in self.pathList:
            entry = {
                'status': status,
                'path': path,
                'content-length': contentLength,
                'redirect': redirect
            }
            record[headerPattern].append(entry)
        return json.dumps(record, sort_keys=True, indent=4)
