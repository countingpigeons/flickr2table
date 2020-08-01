from counting_pigeons_config import FlickrConfig
from requests_oauthlib import OAuth1Session


client_key = FlickrConfig.apikey
client_secret = FlickrConfig.secret
base_request_token_url = FlickrConfig.base_request_token_url
base_authorization_url = FlickrConfig.base_authorization_url
base_access_token_url = FlickrConfig.base_access_token_url
oauth_callback_url = FlickrConfig.oauth_callback_url
request_token_url = (base_request_token_url + '?oauth_callback=' +
                     oauth_callback_url)
oauth_flow = {}
request_token = ''
request_token_secret = ''
verifier = ''
resource_owner_key = ''
resource_owner_secret = ''


def get_request_token(oauth, request_token_url):

    fetch_response = oauth.fetch_request_token(request_token_url)
    request_token = fetch_response.get('oauth_token')
    request_token_secret = fetch_response.get('oauth_token_secret')

    return request_token, request_token_secret, oauth


def get_access_token(oauth, base_access_token_url):

    oauth_tokens = oauth.fetch_access_token(base_access_token_url)
    resource_owner_key = oauth_tokens.get('oauth_token')
    resource_owner_secret = oauth_tokens.get('oauth_token_secret')

    return resource_owner_key, resource_owner_secret, oauth


# request token
oauth = OAuth1Session(client_key, client_secret=client_secret,
                      signature_type='auth_header')
request_token, request_token_secret, oauth = \
    get_request_token(oauth,
                      request_token_url)

# send user to authorize
authorization_url = oauth.authorization_url(base_authorization_url)
print('Please go here and authorize,', authorization_url)

authorization_response = input('Paste the entire response url here:')
authorization_response_parsed = \
    oauth.parse_authorization_response(authorization_response)
verifier = authorization_response_parsed.get('oauth_verifier')

oauth_flow['request_token'] = request_token
oauth_flow['request_token_secret'] = request_token_secret
oauth_flow['verifier'] = verifier

# get access token
oauth = OAuth1Session(client_key,
                      client_secret=client_secret,
                      resource_owner_key=request_token,
                      resource_owner_secret=request_token_secret,
                      verifier=verifier)

resource_owner_key, resource_owner_secret, oauth = \
    get_access_token(oauth, base_access_token_url)

oauth_flow['resource_owner_key'] = resource_owner_key
oauth_flow['resource_owner_secret'] = resource_owner_secret

print('oauth_flow')
print(oauth_flow)
