import configparser


class CustomConfigParser(configparser.ConfigParser):
    """Getting Command Line User Custom Arguments with 'configparser'"""

    def __init__(self):
        configparser.ConfigParser.__init__(self)

    """
    Check Out Python 3 Documentation --> ConfigParser
    Modify Default get/getint/getfloat/getboolean(section, option, *, raw=False, vars=None[, fallback])
    """

    def try_get(self, section, option, default, allowed=None):
        try:
            result = configparser.ConfigParser.get(self, section, option)
            if allowed is not None:
                return result if result in allowed else default
            else:
                return result
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def try_getint(self, section, option, default, allowed=None):
        try:
            result = configparser.ConfigParser.getint(self, section, option)
            if allowed is not None:
                return result if result in allowed else default
            else:
                return result
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def try_getfloat(self, section, option, default, allowed=None):
        try:
            result = configparser.ConfigParser.getfloat(self, section, option)
            if allowed is not None:
                return result if result in allowed else default
            else:
                return result
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default

    def try_getboolean(self, section, option, default, allowed=None):
        try:
            result = configparser.ConfigParser.getboolean(
                self, section, option)
            if allowed is not None:
                return result if result in allowed else default
            else:
                return result
        except (configparser.NoSectionError, configparser.NoOptionError):
            return default
