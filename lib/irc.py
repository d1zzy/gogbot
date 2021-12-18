import errno
import logging
import selectors
import socket
import time

class Message:
    """Encapsulates the various IRC message fields, per the spec.

    The IRC specification (RFC2812) defines each message as made of 3 parts,
    each separated by one single space:
    - prefix (optional), must start with ':' as first character
    - command, either one of the defined IRC commands or a 3 digit code
    - command parameters
    """
    def __init__(self, raw_msg=None):
        # Store list of tags, if any.
        self.tags = {}
        # Store the prefix with no leading ':'. Can be None if no prefix was
        # present.
        self.prefix = None
        # IRC command string.
        self.command = None
        # IRC command arguments.
        self.command_args = None
        # IRC command sender.
        self.sender = None
        if raw_msg is not None:
            self.Parse(raw_msg)

    def Parse(self, raw_msg):
        parts = raw_msg.split(' ', maxsplit=1)
        tags = None
        prefix = None
        if len(parts) >= 2 and parts[0][0] == '@':
            # Extract the tags.
            tags = parts[0][1:]
            parts = parts[1].split(' ', maxsplit=1)

        if len(parts) >= 2 and parts[0][0] == ':':
            prefix = parts[0][1:]
            parts = parts[1].split(' ', maxsplit=1)
            if len(parts) < 2:
                parts.append('')

        if len(parts) < 2:
            logging.error('Invalid IRC message "%s"' % raw_msg)
            return False

        if tags:
            # Tags are semicolon separated name=value pairs.
            for tag in tags.split(';'):
                tag_parts = tag.split('=', maxsplit=1)
                self.tags[tag_parts[0]] = (
                    tag_parts[1] if len(tag_parts) >= 2 else '')

        if prefix:
            sender = prefix.split('!', maxsplit=1)[0].strip()
            if sender:
                self.sender = sender
        self.prefix = prefix
        self.command = parts[0]
        self.command_args = parts[1]
        return True

    def __repr__(self):
        return 'Message(prefix=%r, command=%r, command_args=%r, sender=%r)' % (
                self.prefix, self.command, self.command_args, self.sender)


class User:
    """Information used to track the status of a chat user."""

    def __init__(self, username):
        self.name = username
        self.mode = ''
        self.tags = {}

    def UpdateMode(self, mode_str):
        # We're fairly limited in what user MODE updates we can process.
        if len(mode_str) != 2 or mode_str[0] not in ('-', '+'):
            logging.warning('Unexpected user MODE change: %r', mode_str)
            return
        plus = mode_str[0] == '+'
        mode = mode_str[1]
        if plus:
            if mode in self.mode:
                logging.warning('We already have mode %c set for %r.',
                                mode, self.username)
                return
            self.mode += mode
        else:
            if mode not in self.mode:
                logging.warning('Mode %c missing for %r.', mode, self.username)
                return
            self.mode = [c for c in self.mode if c != mode]

    def UpdateTags(self, tags):
        self.tags.update(tags)

    def IsModerator(self):
        return ('o' in self.mode or self.tags.get('mod', 0) == 1 or
                # See https://dev.twitch.tv/docs/irc/tags/#userstate-twitch-tags
                any(badge.split('/', maxsplit=1)[0] in ('broadcaster',
                                                        'moderator', 'admin')
                    for badge in self.tags.get('badges', '').split(',')))


class Connection:
    """Code logic for formatting and parsing IRC messages."""

    _BUFFER_SIZE = 1048576  # 1Mb.
    _MAX_IRC_LINE = 2046  # 2048 including \r\n.

    def __init__(self, log_traffic=False):
        self._log_traffic = log_traffic
        self._conn = None
        self._activity_timer = None
        self._conn_timeout = None
        self._selector = None
        self._input_buffer = ''
        self.channel = None
        # List of users, indexed by username.
        self._userlist = {}

    def GetUserList(self):
        return self._userlist

    def UpdateUserList(self, userlist):
        """Set the user list to contain ony the users listed in "userlist"."""
        # Drop any usernames not listed.
        new_list = {}
        for user in userlist:
            logging.info('[NAMES] User %r joined %r.', user, self.channel)
            new_list[user] = self._userlist.get(user, User(user))
        self._userlist = new_list

    def SendRaw(self, text):
        """Some some raw IRC line."""
        if self._log_traffic:
            logging.debug('< %r', text)
        self._conn.send(bytes('%s\r\n' % text, 'UTF-8'))

    def Connect(self, host, port, nickname, channel=None, server_pass=None,
                activity_timer=600):
        """Connect to an IRC server, authenticate and join a channel."""
        self._conn = socket.socket()
        self._conn.connect((host, port))
        self._conn.setblocking(False)
        self._activity_timer = activity_timer
        self._conn_timeout = time.time() + self._activity_timer
        logging.debug('Connected to %s:%s' % (host, port))
        # Initialize selector used to wait for read data.
        self._selector = selectors.DefaultSelector()
        self._selector.register(self._conn, selectors.EVENT_READ)

        # Ask for the Twitch commands/membership/tags capabilities.
        self.SendRaw('CAP REQ :twitch.tv/commands')
        self.SendRaw('CAP REQ :twitch.tv/membership')
        self.SendRaw('CAP REQ :twitch.tv/tags')
        if server_pass:
            self.SendPass(server_pass)
        self.SendNick(nickname)
        if channel:
            self.JoinChannel(channel)
        logging.debug('Joined %s' % channel)

    def SendPong(self, msg):
        self.SendRaw('PONG %s' % msg)

    def SendMessage(self, chan, msg):
        self.SendRaw('PRIVMSG %s :%s' % (chan, msg))

    def SendWhisper(self, recipient, msg):
        self.SendRaw('PRIVMSG #jtv :/w %s %s' % (recipient, msg))
        #self.SendRaw('WHISPER %s :%s' % (recipient, msg))

    def SendNick(self, nick):
        self.SendRaw('NICK %s' % nick)

    def SendPass(self, password):
        self.SendRaw('PASS %s' % password)

    def JoinChannel(self, chan):
        self.SendRaw('JOIN %s' % chan)
        self.channel = chan
        # When joining a channel also send an empty MODE command, Twitch waits
        # for this before sending the user list.
        self.SendRaw('MODE %s' % chan)

    def PartChannel(self, chan):
        self.SendRaw('PART %s' % chan)

    def _CloseConnectionInput(self):
        """Closes the input part of the connection."""
        self._selector.unregister(self._conn)
        self._selector = None
        socket.shutdown(socket.SHUT_RD)

    def _ReadMoreData(self, timeout):
        # Wait for data to be available.
        for key, mask in self._selector.select(timeout=timeout):
            # There's only one file descriptor registered, no need to check
            # which file descriptor received the event.
            try:
                # Exhaust all input data.
                while True:
                    data = key.fileobj.recv(self._BUFFER_SIZE)
                    if not data:
                        # Socket closed.
                        self._CloseConnectionInput()
                        return False
                    self._input_buffer += data.decode(encoding='utf-8')
                    # We got some bytes, reset the activity timer.
                    self._conn_timeout = time.time() + self._activity_timer
            except socket.error as err:
                ec = err.args[0]
                if ec == errno.EAGAIN or ec == errno.EWOULDBLOCK:
                    break
                if ec == errno.ECONNRESET:
                    # Connection forcibly closed.
                    self._CloseConnectionInput()
                    return False
                raise

        # Connection activity timeout reached.
        if time.time() >= self._conn_timeout:
            # Close connection.
            logging.error('Connection timed out, closing.')
            self._CloseConnectionInput()
            return False

        return True

    def ReadNextLine(self, timeout):
        """Reads the next IRC line."""
        now = time.time()
        end_time = now + timeout
        while True:
            # Timeout exit condition.
            now = time.time()
            if now >= end_time:
                raise TimeoutError('timeout waiting for new message')

            if '\r\n' not in self._input_buffer:
                if not self._selector:
                    logging.info('connection closed')
                    return None
                self._ReadMoreData(end_time - now)

            parts = self._input_buffer.split('\r\n', maxsplit=1)
            if len(parts) < 2:
                continue

            line, self._input_buffer = parts
            if len(line) > self._MAX_IRC_LINE:
                logging.error('IRC line too long %d > %d' %
                              (len(line), self._MAX_IRC_LINE))
                continue

            break

        if self._log_traffic:
            logging.debug('> %r' % line)
        return line


class Client:
    _TICK_INTERVAL = 1  # Call HandleTick() every 1 second.

    def __init__(self, handler):
        self._handler = handler

    def Run(self):
        """Runs the IRC client, reads any network packets then answers them."""
        next_tick = time.time() + self._TICK_INTERVAL
        while True:
            now = time.time()
            if now >= next_tick:
                self._handler.HandleTick()
                next_tick += self._TICK_INTERVAL
                continue

            try:
                line = self._handler.GetConnection().ReadNextLine(
                        next_tick - now)
            except TimeoutError:
                continue

            if line is None:
                # Connection closed.
                break

            msg = Message()
            if not msg.Parse(line):
                # Invalid formatted message, skip.
                continue

            self._handler.HandleMessage(msg)


class _PingHandlerMixin:
    """Handle PING messages."""

    def HandlePING(self, msg):
        self._conn.SendPong(msg.command_args)
        return True


class _JoinPartHandlerMixin:
    """Handle JOIN/PART messages."""

    def HandleJOIN(self, msg):
        if not msg.sender:
            logging.warning('[JOIN] Unexpected message format: %r', msg)
            return False
        if msg.command_args != self._conn.channel:
            logging.warning('[JOIN] Received for another channel: %r',
                            msg.command_args)
            return False
        # Process the JOIN by adding the user to the userlist.
        userlist = self._conn.GetUserList()
        if msg.sender in userlist:
            logging.warning('[JOIN] User %r already part of channel %r',
                            msg.sender, self._conn.channel)
            return False
        userlist[msg.sender] = User(msg.sender)
        logging.info('[JOIN] User %r joined %r.', msg.sender,
                     self._conn.channel)
        return True

    def HandlePART(self, msg):
        if not msg.sender:
            logging.warning('[PART] Unexpected message format: %r', msg)
            return False
        if msg.command_args != self._conn.channel:
            logging.warning('[PART] Received for another channel: %r',
                            msg.command_args)
            return False
        # Process the PART by removing the user from the userlist.
        userlist = self._conn.GetUserList()
        if msg.sender not in userlist:
            logging.warning('[PART] User %r not part of channel %r',
                            msg.sender, self._conn.channel)
            return False
        del userlist[msg.sender]
        logging.info('[PART] User %r left %r.', msg.sender, self._conn.channel)
        return True


class _ModeHandlerMixin:
    """Handle the MODE message."""

    def HandleMODE(self, msg):
        parts = msg.command_args.split()
        if not msg.sender or msg.sender != 'jtv' or len(parts) != 3:
            logging.warning('[MODE] Unexpected message format: %r', msg)
            return False
        chan, mode, target = parts
        if chan != self._conn.channel:
            logging.warning('[MODE] Received for another channel: %r', chan)
            return False

        # Apply the mode change to the target user.
        user = self._conn.GetUserList().get(target)
        if not user:
            logging.warning('[MODE] User %r not part of channel %r',
                            target, self._conn.channel)
            return False
        user.UpdateMode(mode)
        logging.info('[MODE] User %r updated %r to mode %r on %r.', msg.sender,
                     target, user.mode, self._conn.channel)
        return True


class _UserListHandlerMixin:
    """Handles userlists that are received through multiple 353 messages."""

    def __init__(self, conn):
        super().__init__(conn)
        # The temporary userlist being built while receiving a stream of
        # type 353 messages.
        self._tmp_list = None

    def Handle353(self, msg):
        # First 353 message, starts a new sequence.
        if self._tmp_list is None:
            self._tmp_list = []
        parts = msg.command_args.split(':', maxsplit=1)
        if len(parts) != 2 or not parts[0].endswith('%s ' % self._conn.channel):
            logging.error('Invalid 353 type message format: %r', msg)
            return False
        # Everything after the first ':' should be a space delimited list of
        # nicknames. We drop any @+ status from the listed usernames, twitch
        # doesn't use this feature anyways.
        self._tmp_list.extend(name.lstrip('@+')
                              for name in parts[1].split(' ')
                              if name)
        return True

    def Handle366(self, msg):
        if self._tmp_list is None:
            logging.error('Unexpected 366/RPL_ENDOFNAMES without a preceeding '
                          '353/RPL_NAMREPLY')
            return False
        # End of user list, update the known channel userlist.
        self._conn.UpdateUserList(self._tmp_list)
        # Reset the list to prepare for the next sequence.
        self._tmp_list = None
        return True


class _UserTagsHandlerMixin:
    """Handle usertags in messages."""

    def HandlePRIVMSG(self, msg):
        if not msg.sender:
            # Strange, no sender.
            return False

        if not msg.tags:
            # Nothing to do.
            return False

        userlist = self._conn.GetUserList()
        if msg.sender not in userlist:
            logging.warning('[PRIVMSG] User %r not part of channel %r',
                            msg.sender, self._conn.channel)
            userlist[msg.sender] = User(msg.sender)
        userlist[msg.sender].UpdateTags(msg.tags)

        # Let other handlers fully handle PRIVMSG.
        return False


class HandlerBase:
    """Base IRC message handler class.

    Should be derived to change default behaviour and/or add handling for
    commands not already handled. All handler methods are of the form
    Handle<type> where <type> is an IRC message type, in capital letters. They
    all receive the IRC message they are supposed to handle. A special
    HandleDefault() is used to handle any messages types that have no specific
    handler. Every Handle*() function should return True/False, True meaning
    that the message has been successfully handled.
    """
    def __init__(self, conn):
        self._conn = conn

    def GetConnection(self):
        return self._conn

    def HandleTick(self):
        """Handle the time tick."""
        return False

    def HandleMessage(self, msg):
        handler = getattr(self, 'Handle%s' % msg.command.upper(),
                          self.HandleDefault)
        return handler(msg)

    def HandleDefault(self, msg):
        return False


class CoreHandler(_PingHandlerMixin,
                  _JoinPartHandlerMixin,
                  _ModeHandlerMixin,
                  _UserListHandlerMixin,
                  _UserTagsHandlerMixin,
                  HandlerBase):
    """Handles core functions, always invoked."""
    pass


def SplitPRIVMSG(msg):
    """Helper function to be used by HandlePRIVMSG definitions."""
    parts = msg.command_args.split(' ', maxsplit=1)
    if len(parts) < 2:
        logging.error('invalid PRIVMSG message: "%s"' % msg.command_args)
        return None
    if parts[1][0] == ':':
        parts[1] = parts[1][1:]
    return tuple(parts)
