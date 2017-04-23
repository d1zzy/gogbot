# Gwent Twitch Plays

## Installation

First, install the Python for Windows version 3.5.x. Either 64 or 32 bit
version should work:
https://www.python.org/downloads/

Download and install the **pywin32** package. Chose the latest build (highest
build number) and pick the right file for your version of Python, for Python
3.5.x pick the pywin32 package with `py3.5` in its name. Also make sure to
download the version that matches the 32 bit or 64 bit Python you have
(if you installed Python 64 bit then pick the `amd64` file).
https://sourceforge.net/projects/pywin32/files/pywin32/

Place the **gogbot** files in any directory you want.

## Configuration

Copy `config.ini` to `config_private.ini` then edit `config_private.ini` with a
text editor, change the following:
* `nickname`, `channel` and `password` (password is *OAUTH* string that you get
 from http://www.twitchapps.com/tmi/)
* `plugins` inside the `[CHAIN]` section to list `twitch_plays_sv`
* edit the `[TWITCH_PLAYS]` configuration section as needed
* if using `ratelimiter` plugin, edit the `[RATELIMITER]` configuration section
to match what you want

The Gwent Twitch Plays plugin supports passing the current round if a certain
number of people issue "pass" in the last N seconds. You can configure this
time interval and the voting percentage by modifying the twitch_plays_gwent.py
plugin.

## Running

Run `start.bat`, the bot should start and print out some debug messages showing
that it successfully connected to Twitch, authenticated and joined the desired
channel. Type `help` in chat to get the list of available bot commands.

## Configuration Example
```ini
[CONNECTION]
host = irc.twitch.tv
port = 6667
channel = #gogcom
nickname = gogbot
password = oauth:...

[GENERAL]
plugins = ratelimiter twitch_plays_gwent

[RATELIMITER]
debug = true
max_age = 10
rate_per_sender = 5
rate_per_text = 1
text_filter = ^\s*help\s*$

[TWITCH_PLAYS]
require_nickname = false
focus_window = Gwent
```
