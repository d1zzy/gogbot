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
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s:%(levelname).4s:%(module)s: %(message)s',
        datefmt='%Y%m%d_%H%M%S')

    config = configparser.ConfigParser()
    if list(config.read(args.config)) != [args.config]:
        logging.error('failed to parse config: ', args.config)
        return False
    if 'CONNECTION' not in config.sections():
        logging.error('CONNECTION section missing in config')
        return False
    conn_config = config['CONNECTION']
    con = irc.Connection(conn_config.getboolean('log_traffic', False))
    con.Connect(conn_config['host'], int(conn_config['port']),
                conn_config['nickname'],
                channel=conn_config.get('channel', None),
                server_pass=conn_config.get('password', None),
                activity_timer=int(conn_config.get('activity_timer', 600)))

    chain_plugin = plugin_loader.GetPlugin('chain')
    client = irc.Client(chain_plugin.Handler(con, config))
    try:
        client.Run()
    except KeyboardInterrupt:
        logging.info('CTRL-C caught, exiting...')
    return True


if __name__ == '__main__':
    # Lookup modules starting from the directory of "main.py".
    sys.path.insert(0, os.path.dirname(__file__))
    if main(_ParseArguments()):
        sys.exit(0)
    sys.exit(1)
