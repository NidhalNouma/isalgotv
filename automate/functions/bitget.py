import requests
import hmac
import hashlib
import time
import requests
import json
from datetime import datetime

def create_signature(secret_key, method, endpoint, timestamp, body=''):
    """ Create a HMAC SHA256 signature. """
    what = timestamp + method.upper() + endpoint + (json.dumps(body) if body else '')
    return hmac.new(secret_key.encode(), what.encode(), hashlib.sha256).hexdigest()

def get_utc_timestamp():
    """ Returns the current UTC timestamp as a string. """
    return datetime.utcnow().isoformat(timespec='milliseconds')

def check_bitget_credentials(api_key, api_secret, passphrase, api_url="https://api.bitget.com"):
    """
    Checks API credentials by attempting to fetch account details from Bitget.

    Args:
        api_key (str): User's Bitget API key.
        api_secret (str): User's Bitget API secret.
        passphrase (str): Passphrase for API (required by Bitget).
        api_url (str): Base URL for Bitget API.

    Returns:
        dict: A dictionary containing either a validation success message or an error message.
    """
    headers = {
        "ACCESS-KEY": api_key,
        "ACCESS-SIGN": api_secret,  # In production, this needs to be a HMAC SHA256 signature.
        "ACCESS-TIMESTAMP": "current timestamp",  # This needs to be the current UTC timestamp.
        "ACCESS-PASSPHRASE": passphrase,
        "Content-Type": "application/json"
    }

    try:
        # Test endpoint for fetching account info (modify accordingly if different endpoint is needed)
        response = requests.get(f"{api_url}/api/spot/v1/account/accounts", headers=headers)
        if response.status_code == 200:
            r = {'message': "API credentials are valid.", "valid": True}
        else:
            r = {'error': "API credentials are not valid", "valid": False, 'status_code': response.status_code}
        return r

    except Exception as e:
        r = {'error': "Failed to connect to Bitget API: " + str(e), "valid": False}
        return r