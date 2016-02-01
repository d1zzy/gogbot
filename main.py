#!/usr/bin/env python3

import argparse
import configparser
import logging
import os
import sys

from lib import irc
from lib import plugin_loader

def _ParseArguments():
    parser = argparse.ArgumentParser(description='GOG Twitch bot.')
    parser.add_argument('--config', type=str, required=True,
                        help='path to config file')

    return parser.parse_args()

def main(args):
    logging.basicConfig(level=logging.DEBUG)

    config = configparser.ConfigParser()
    if list(config.read(args.config)) != [args.config]:
        logging.error('failed to parse config: ', args.config)
        return False
    if 'CONNECTION' not in config.sections():
        logging.error('CONNECTION section missing in config')
        return False
    conn_config = config['CONNECTION']
    con = irc.Connection()
    con.Connect(conn_config['host'], int(conn_config['port']),
                conn_config['nickname'], conn_config['channel'],
                conn_config['password'])

    if 'GENERAL' not in config.sections():
        logging.error('GENERAL section missing in config')
        return False
    plugin = plugin_loader.GetPlugin(config['GENERAL']['handler'])

    client = irc.Client(plugin.Handler(con, config))
    client.Run()


if __name__ == '__main__':
    # Lookup modules starting from the directory of "main.py".
    sys.path.insert(0, os.path.dirname(__file__))
    if main(_ParseArguments()):
        sys.exit(0)
    sys.exit(1)
