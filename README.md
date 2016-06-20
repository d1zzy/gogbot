# gogbot &mdash; GOG Twitch Channel Bot

This is a simple Python 3 written IRC bot for serving the needs
of the #gogcom Twitch channel.

It's currently in very early stages of development, it supports:
* basic connection, authentication and joining a Twitch channel
* skeleton code structure that allows extending through subclassing for
additional IRC command support and/or changing the behavior of commands
already handled (ex. changing `PRIVMSG` behavior to support !bot commands)
* support for configured runtime plugins (module) loading
* various (game specific) TwitchPlays modules

## Installation

* install Python 3
* download this code in some directory
* copy `config.ini` to `config_private.ini` and update it as necessary (you
need at least to update the `PASS` value with a valid OAuth token for the
configured `NICK`)
* run the bot with a command like `python3 main.py --config config_private.ini`
* for TwitchPlays functionality see the relevant documentation in the "docs"
directory
