import logging

from lib import irc

class Handler(irc.HandlerBase):
    """IRC handler that logs most messages."""

    def __init__(self, conn, config):
        super().__init__(conn)

    def HandleDefault(self, msg):
        logging.debug('default handling (%s,%s,%s)' %
                      (msg.prefix, msg.command, msg.command_args))
        return False
