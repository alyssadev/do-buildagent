import requests
from datetime import datetime, timedelta


class DigitalOceanClient:
    def __init__(self, client_id, client_secret, domain="http://localhost:5000"):
        """
        Create a new LoginClient.  These clients do not make any requests
        on creation, and can safely be created and thrown away as needed.
        :param client_id: The OAuth Client ID for this client.
        :type client_id: str
        :param client_secret: The OAuth Client Secret for this client.
        :type client_secret: str
        :param base_url: The URL for DO OAuth server.  This should not be
                         changed.
        :type base_url: str
        """
        self.base_url = 'https://cloud.digitalocean.com/v1/oauth'
        self.authorize_url = f'{self.base_url}/authorize'
        self.redirect_uri = f'{domain}/login'
        self.client_id = client_id
        self.client_secret = client_secret

    def get_authorize_oauth_url(self):
        scope = 'read%20write'

        full_url = (
            f'{self.authorize_url}?redirect_uri={self.redirect_uri}'
            f'&client_id={self.client_id}'
            f'&scope={scope}&response_type=code'
        )
        return full_url

    def finish_oauth(self, code):
        url = f'{self.base_url}/token'
        data = {
            'grant_type': 'authorization_code',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'code': code,
            'redirect_uri': self.redirect_uri,
        }
        r = requests.post(url, data=data)

        if r.status_code != 200:
            raise ApiError('Oauth Token Exchange Failed', r)

        token = r.json()['access_token']
        scope = r.json()['scope']
        expiry = datetime.now() + timedelta(seconds=r.json()['expires_in'])
        refresh_token = r.json()['refresh_token']

        return token, scope, expiry, refresh_token

    def refresh_oauth_token(self, refresh_token):
        r = requests.post(f'{self.base_url}/token', data={
            'grant_type': 'refresh_token',
            'refresh_token': refresh_token,
        })

        if r.status_code != 200:
            raise ApiError('Refresh failed', r)

        try:
            token = r.json()['access_token']
            scope = r.json()['scope']
            expiry = datetime.now() + timedelta(seconds=r.json()['expires_in'])
            refresh_token = r.json()['refresh_token']
        except KeyError:
            raise ApiError('Failed to get auth token')

        return token, scope, expiry, refresh_token


class ApiError(RuntimeError):
    """
    An API Error is any error returned from the API.  These
    typically have a status code in the 400s or 500s.  Most
    often, this will be caused by invalid input to the API.
    """
    def __init__(self, message, status=400, json=None):
        super(ApiError, self).__init__(message)
        self.status = status
        self.json = json
        self.errors = []
        if json and 'errors' in json and isinstance(json['errors'], list):
            self.errors = [e['reason'] for e in json['errors']]
