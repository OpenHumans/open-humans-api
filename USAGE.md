# USAGE

Usage of functions in ohapi are documented here.

## api.py

### oauth2_auth_url

```py
def oauth2_auth_url(redirect_uri=None, client_id=None, base_url=OH_BASE_URL):
    if not client_id:
        client_id = os.getenv('OHAPI_CLIENT_ID')
        if not client_id:
            raise SettingsError(
                "Client ID not provided! Provide client_id as a parameter, "
                "or set OHAPI_CLIENT_ID in your environment.")
    params = OrderedDict([
        ('client_id', client_id),
        ('response_type', 'code'),
    ])
    if redirect_uri:
        params['redirect_uri'] = redirect_uri

    auth_url = urlparse.urljoin(
        base_url, '/direct-sharing/projects/oauth2/authorize/?{}'.format(
            urlparse.urlencode(params)))

    return auth_url
```

This function constructs an authorization URL for a user to follow. The user will be redirected to Authorize Open Humans data for our external application. An OAuth2 project on Open Humans is required for this to properly work. To learn more about Open Humans OAuth2 projects, go to:
[https://www.openhumans.org/direct-sharing/oauth2-features/](https://www.openhumans.org/direct-sharing/oauth2-features/)

The function accepts in `redirect_uri`, `client_id` and `base_url` as arguments:
* `redirect_uri` : This field is set to `None` by default. However, if provided, it appends it in the URL returned.
* `client_id` : This field is also set to `None` by default however, is a mandatory field for the final URL to work. It uniquely identifies a given OAuth2 project.
* `base_url`: It is this URL `https://www.openhumans.org`

You can provide `CLIENT_ID` in two ways, either by passing it as a parameter or by setting `OHAPI_CLIENT_ID` as an environment variable.

The function then returns the OAuth2 authorization URL thus created which is something like
`https://www.openhumans.org/direct-sharing/projects/oauth2/authorize/?client_id=CLIENT_ID&response_type=code&redirect_uri=REDIRECT_URI`

If you visit the above link (the valid one) you will be asked if you want to authorize the specified project. Authorizing the project successfully will redirect the user's browser to the URL specified as `redirect_uri`.
