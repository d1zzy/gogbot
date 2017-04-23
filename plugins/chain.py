import logging

from lib import config
from lib import irc
from lib import plugin_loader

class Handler(irc.HandlerBase):
    """IRC handler that delegates handling to a chain of handlers."""

    def __init__(self, conn, conf):
        super().__init__(conn)
        section = config.GetSection(conf, 'GENERAL')
        if 'plugins' not in section:
            raise Exception('"plugins" setting not found')
        self._handlers = self._LoadPlugins(section['plugins'], conn, conf)
        if not self._handlers:
            raise Exception('empty list of plugins to load')

    @staticmethod
    def _LoadPlugins(plugins, conn, conf):
        result = []
        for name in plugins.split():
            name = name.strip()
            if not name:
                continue
            result.append(plugin_loader.GetPlugin(name).Handler(conn, conf))
        return result

    def HandleDefault(self, msg):
        # Distribute the message to the chained plugins.
        for handler in self._handlers:
            if handler.HandleMessage(msg):
                return True
        return False
