import logging

from lib import irc

class Handler(irc.HandlerBase):
    """IRC handler that logs most messages."""

    def __init__(self, conn, config):
        super().__init__(conn)

    def HandleTick(self):
        logging.debug('default handling tick')
        return False

    def HandleDefault(self, msg):
        logging.debug('default handling %r' % msg)
        return False
