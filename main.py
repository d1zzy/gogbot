#!/usr/bin/env python3

import logging
import sys

from lib import irc

try:
    from config_private import *
except ImportError:
    print('Could not import config_private. Did you forget to copy (and modify) config.py to '
          'config_private.py?')
    sys.exit(1)

def main(argv):
    logging.basicConfig(level=logging.DEBUG)

    con = irc.Connection()
    con.Connect(HOST, PORT, NICK, CHAN, PASS)
    client = irc.Client(irc.Handler(con))
    client.Run()


if __name__ == '__main__':
    if (main(sys.argv)):
        sys.exit(0)
    sys.exit(1)
