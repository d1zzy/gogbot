import logging
import re
import time

from lib import irc

class _Message:
    def __init__(self, sender, text):
        self.sender = sender
        self.text = text
        self.timestamp = time.time()

    def __repr__(self):
        return '_Message(sender=%r,text=%r,timestamp=%r)' % (
            self.sender, self.text, self.timestamp)

class _MessagePool:
    """Pool containing all events issued in the past "max_age" seconds."""
    def __init__(self, max_age):
        self._max_age = max_age
        self._messages = []
        self._idx_sender = {}
        self._idx_text = {}

    def _RemoveExpiredMessages(self):
        now = time.time()
        to_remove = []
        for msg in self._messages:
            if msg.timestamp + self._max_age >= now:
                break
            to_remove.append(msg)

        for msg in to_remove:
            self._messages.pop(0)
            self._idx_sender[msg.sender].pop(0)
            self._idx_text[msg.text].pop(0)

    def CountBySender(self, sender):
        self._RemoveExpiredMessages()
        return len(self._idx_sender.setdefault(sender, []))

    def CountByText(self, text):
        self._RemoveExpiredMessages()
        return len(self._idx_text.setdefault(text, []))

    def RecordMessage(self, msg):
        self._messages.append(msg)
        self._idx_sender.setdefault(msg.sender, []).append(msg)
        self._idx_text.setdefault(msg.text, []).append(msg)

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

        msg = _Message(msg.prefix.split('!', maxsplit=1)[0], parts[1])
        if (self._sender_rate and
            self._pool.CountBySender(msg.sender) >= self._sender_rate):
            self._Log('REJECT:sender-over-limit:%s', msg)
            return True
        if (self._text_rate and
            (not self._text_filter or self._text_filter.match(msg.text)) and
            self._pool.CountByText(msg.text) >= self._text_rate):
            self._Log('REJECT:text-over-limit:%s', msg)
            return True

        self._Log('PASS:%s', msg)
        self._pool.RecordMessage(msg)
        return False
