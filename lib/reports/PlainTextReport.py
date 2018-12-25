from lib.reports.BaseReport import BaseReport
from lib.utils.FileUtils import FileUtils


class PlainTextReport(BaseReport):
    def recording(self):  # Override
        """
        @report_pattern
        HTTP Response Status Code + Package Size + URL + Path
        """

        record = ''
        # self.pathList.append((path, status, contentLength))
        for path, status, contentLength in self.pathList:
            record += '{0}  '.format(status)
            record += '{0}  '.format(
                FileUtils.sizeIEC(contentLength).rjust(6, ' '))
            record += '{0}://{1}:{2}/'.format(self.protocol, self.host,
                                              self.port)
            record += ('{0}\n'.format(path) if self.basePath is '' else
                       '{0}/{1}\n'.format(self.basePath, path))
        return record
