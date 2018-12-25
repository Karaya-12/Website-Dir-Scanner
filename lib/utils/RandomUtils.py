import string
import random


class RandomUtils(object):
    """Generate A Random String for Scanner Test Path"""

    @classmethod
    def randString(cls, n=12, omit=None):
        # Generate A Sequence Which Consists of All ASCII Letters & Digits
        # Check Out Python Documentation -> string
        # string.ascii_letters --> Concatenation of the 'ascii_lowercase' & 'ascii_uppercase'
        # Result: abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ
        scope = string.ascii_letters + string.digits
        if omit:
            scope = list(set(scope) - set(omit))
        # Take Random Choices from Generated Sequence
        return ''.join(random.choice(scope) for i in range(n))
