import logging
import socket

class Message:
    """Encapsulates the various IRC message fields, per the spec.

    The IRC specification (RFC2812) defines each message as made of 3 parts,
    each separated by one single space:
    - prefix (optional), must start with ':' as first character
    - command, either one of the defined IRC commands or a 3 digit code
    - command parameters
    """
    def __init__(self, raw_msg=None):
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
        prefix = None
        if len(parts) >= 2 and parts[0][0] == ':':
            prefix = parts[0][1:]
            parts = parts[1].split(' ', maxsplit=1)

        if len(parts) < 2:
            logging.error('invalid IRC message "%s"' % raw_msg)
            return False

        if prefix:
            sender = prefix.split('!', maxsplit=1)[0].strip()
            if sender:
                self.sender = sender
        self.prefix = prefix
        self.command = parts[0]
        self.command_args = parts[1]
        return True

    def __repr__(self):
        return 'Message(prefix="%s", command="%s", command_args="%s")' % (
                self.prefix, self.command, self.command_args)


class User:
    """Information used to track the status of a chat user."""

    def __init__(self, username):
        self.name = username
        self.mode = ''

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

    def IsModerator(self):
        return 'o' in self.mode


class Connection:
    """Code logic for formatting and parsing IRC messages."""

    _BUFFER_SIZE = 1048576  # 1Mb.
    _MAX_IRC_LINE = 510  # 512 including \r\n.

    def __init__(self):
        self._conn = None
        self._input_buffers = ['']
        self.channel = None
        # List of users, indexed by username.
        self._userlist = {}

    def GetUserList(self):
        return self._userlist

    def Connect(self, host, port, nickname, channel=None, server_pass=None):
        """Connect to an IRC server, authenticate and join a channel."""
        self._conn = socket.socket()
        self._conn.connect((host, port))
        logging.debug('Connected to %s:%s' % (host, port))

        self._conn.send(bytes('CAP REQ :twitch.tv/membership\r\n', 'UTF-8'))
        if server_pass:
            self.SendPass(server_pass)
        self.SendNick(nickname)
        if channel:
            self.JoinChannel(channel)
        logging.debug('Joined %s' % channel)

    def SendPong(self, msg):
        self._conn.send(bytes('PONG %s\r\n' % msg, 'UTF-8'))

    def SendMessage(self, chan, msg):
        self._conn.send(bytes('PRIVMSG %s :%s\r\n' % (chan, msg), 'UTF-8'))

    def SendNick(self, nick):
        self._conn.send(bytes('NICK %s\r\n' % nick, 'UTF-8'))

    def SendPass(self, password):
        self._conn.send(bytes('PASS %s\r\n' % password, 'UTF-8'))

    def JoinChannel(self, chan):
        self._conn.send(bytes('JOIN %s\r\n' % chan, 'UTF-8'))
        self.channel = chan

    def PartChannel(self, chan):
        self._conn.send(bytes('PART %s\r\n' % chan, 'UTF-8'))

    def ReadNextMessage(self):
        """Reads the next IRC message."""
        # Loop until we get a non-empty line (since these are supposed to be
        # ignored by IRC clients).
        line = ''
        while not line:
            # Loop until we get a full line.
            while True:
                lines = self._input_buffers[-1].split('\r\n', maxsplit=1)
                # Got a line separator in the last buffer, yay!
                if len(lines) >= 2:
                    break

                try:
                    data = self._conn.recv(self._BUFFER_SIZE).decode('UTF-8')
                except socket.error as err:
                    logging.info('socket error: %s' % err)
                    return None

                except socket.timeout as err:
                    logging.info('socket timeout: %s' % err)
                    return None

                if not data:
                    return None
                self._input_buffers.append(data)

            # All previous buffers and the first line of the current buffer
            # need to be handled as a single line.
            line = ''.join(self._input_buffers[:-1]) + lines[0]
            # Any remaining data is saved for later processing.
            self._input_buffers = [lines[1]]

            if len(line) > self._MAX_IRC_LINE:
                logging.error('IRC line too long %d > %d' %
                              (len(line), self._MAX_IRC_LINE))
                line = ''

        msg = Message()
        if not msg.Parse(line):
            return None

        return msg


class Client:
    def __init__(self, handler):
        self._handler = handler

    def Run(self):
        """Runs the IRC client, reads any network packets then answers them."""
        while True:
            msg = self._handler.GetConnection().ReadNextMessage()
            if not msg:
                break

            self._handler.HandleMessage(msg)


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

    def HandleMessage(self, msg):
        handler = getattr(self, 'Handle%s' % msg.command.upper(),
                          self.HandleDefault)
        return handler(msg)

    def HandleDefault(self, msg):
        return False

    def HandlePING(self, msg):
        self._conn.SendPong(msg.command_args)
        return True

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


def SplitPRIVMSG(msg):
    """Helper function to be used by HandlePRIVMSG definitions."""
    parts = msg.command_args.split(' ', maxsplit=1)
    if len(parts) < 2:
        logging.error('invalid PRIVMSG message: "%s"' % msg.command_args)
        return None
    if parts[1][0] == ':':
        parts[1] = parts[1][1:]
    return tuple(parts)
