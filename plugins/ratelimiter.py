import bisect
import logging
import re
import time

from lib import event_queue
from lib import irc

class _Message(event_queue.Event):
    def __init__(self, sender, text):
        super().__init__(text)
        self.sender = sender

    def __repr__(self):
        return '_Message(sender=%r,data=%r,timestamp=%r)' % (
            self.sender, self.data, self.timestamp)


class _MessagePool(event_queue.Queue):
    """Pool containing all events issued in the past "max_age" seconds."""
    def __init__(self, max_age):
        super().__init__(max_age)
        self._idx_sender = {}

    def RemoveEvent(self, msg):
        super().RemoveEvent(msg)
        for idx, candidate in enumerate(self._idx_sender.get(msg.sender, [])):
            self._idx_sender[msg.sender].pop(idx)
            break

    def CountBySender(self, sender):
        self._RemoveExpiredEvents()
        return len(self._idx_sender.get(sender, []))

    def CountByText(self, text):
        return super().CountByData(text)

    def RecordMessage(self, msg):
        super().RecordEvent(msg)
        bisect.insort_right(self._idx_sender.setdefault(msg.sender, []), msg)


class Handler(irc.HandlerBase):
    """IRC handler that limits the rate of incoming PRIVMSGs."""

    def __init__(self, conn, config):
        super().__init__(conn)
        self._cfg = config['RATELIMITER'] if 'RATELIMITER' in config.sections() else {}
        self._pool = _MessagePool(self._cfg.getint('max_age'))
        self._sender_rate = self._cfg.getint('rate_per_sender') or None
        self._text_rate = self._cfg.getint('rate_per_text') or None
        self._text_filter = self._cfg.get('text_filter') or None
        if self._text_filter:
            self._text_filter = re.compile(self._text_filter)

    def _Log(self, *args):
        if self._cfg.getboolean('debug'):
            logging.debug(*args)

    def HandlePRIVMSG(self, msg):
        parts = irc.SplitPRIVMSG(msg)
        if len(parts) < 2 or not parts[1]:
            logging.warning('Got invalid PRIVMSG: %r', msg)
            return False

        msg = _Message(msg.sender, parts[1])
        # If a filter is defined then any message not matching is ignored.
        if self._text_filter and not self._text_filter.match(msg.data):
            return False

        if (self._sender_rate and
            self._pool.CountBySender(msg.sender) >= self._sender_rate):
            self._Log('REJECT:sender-over-limit:%s', msg)
            return True
        if (self._text_rate and
            self._pool.CountByText(msg.data) >= self._text_rate):
            self._Log('REJECT:text-over-limit:%s', msg)
            return True

        self._Log('PASS:%s', msg)
        self._pool.RecordMessage(msg)
        return False
