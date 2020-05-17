import logging
import requests
import time
from urllib import parse as url_parse

class _Oauth2Token:
    """Manages an up to date Twitch OAUTH2 access token.

    TODO(dizzy): Use the requests module built-in OAUTH2 support?"""

    class Token:
        secret = None
        type = None

    def __init__(self, client_id, client_secret):
        # Cache the Twitch API client ID and associated secret.
        self._client_id = client_id
        self._client_secret = client_secret
        # Set initial values for the cached token properties.
        self._access_token = None
        self._access_type = None
        self._access_expire = None
        # Fetch an initial token.
        self._RefreshToken()

    def GetToken(self):
        self._RefreshToken()
        if not self._access_token or not self._access_type:
            return None

        token = self.Token()
        token.secret = self._access_token
        token.type = self._access_type
        return token

    def _RefreshToken(self):
        # If we already have a valid token, don't do anything.
        if (self._access_expire is not None and
            self._access_expire < time.time()):
            return

        self._access_token = None
        self._access_type = None
        self._access_expire = None

        url = url_parse.urlunsplit(
            ('https', 'id.twitch.tv', 'oauth2/token',
             url_parse.urlencode(
                 {'client_id': self._client_id,
                  'client_secret': self._client_secret,
                  'grant_type': 'client_credentials'}, doseq=True),
             ''))
        req = requests.post(url)
        if req.status_code != 200:
            logging.error('Twitch OAUTH2 call failed: %s %s', req.status_code,
                          req.reason)
            return
        result = req.json()
        if (not result or 'access_token' not in result or
            'expires_in' not in result or 'token_type' not in result):
            logging.error('Unexpected OAUTH2 token response: %r', result)
            return

        self._access_token = result['access_token']
        self._access_type = result['token_type']
        # Compute the time for the token to expire taking a small margin of
        # error to account for the processing time after getting the new token
        # and for the time it would take to refresh the token.
        self._access_expire = time.time() + result['expires_in'] - 60


class Helix:
    """Provides access to Twitch's Helix API."""

    def __init__(self, config):
        self._client_id = config['HELIX']['client_id']
        self._oauth2_token = _Oauth2Token(self._client_id,
                                          config['HELIX']['client_secret'])

    def _GetAuthorization(self):
        """Return the value that should be used for the Authorizatin header."""
        token = self._oauth2_token.GetToken()
        if not token:
            return None
        # For some reason Twitch really wants the token type to start with
        # upper case character.
        return '%s %s' % (token.type[0].upper() + token.type[1:], token.secret)

    def Call(self, command, args=()):
        url = url_parse.urlunsplit(
            ('https', 'api.twitch.tv', 'helix/%s' % command,
             url_parse.urlencode(args, doseq=True), ''))
        authorization = self._GetAuthorization()
        if not authorization:
            return None
        req = requests.get(url, headers={'Client-ID': self._client_id,
                                         'Authorization': authorization})
        if req.status_code != 200:
            logging.error('Twitch API /helix/%s call failed: %s %s', command,
                          req.status_code, req.reason)
            return None
        result = req.json()
        if not result or 'data' not in result:
            logging.error("Twitch API /helix/%s call missing 'data' field",
                          command)
            return None
        return result['data']
