from lib.reports.BaseReport import BaseReport


class SimpleReport(BaseReport):
    def recording(self):  # Override
        record = ''
        # self.pathList.append((path, status, contentLength))
        for path, _, _ in self.pathList:
            record += '{0}://{1}:{2}/'.format(self.protocol, self.host,
                                              self.port)
            # basePath or basePath/path
            record += ('{0}\n'.format(path) if self.basePath is '' else
                       '{0}/{1}\n'.format(self.basePath, path))
        return record
