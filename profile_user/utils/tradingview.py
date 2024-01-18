import requests
from django.conf import settings

import environ
env = environ.Env()

TV_SESSION_ID = env('TV_SESSION_ID')


def give_access(strategy_tv_id, tradingview_username, access):
    add_or_reemove = "add" if access == True else "remove"
    url = f"https://www.tradingview.com/pine_perm/{add_or_reemove}/"
    try:
        data = {
          "username_recip": tradingview_username,
          "pine_id": f"PUB;{strategy_tv_id}"
          }
        
        headers = {
            "accept": "application/json, text/javascript, */*; q=0.01",
            "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
            "Origin": "https://www.tradingview.com",
            "X-Requested-With": "XMLHttpRequest",
            "Access-Control-Allow-Origin": "*",
            "Cookie": 'cookiePrivacyPreferenceBannerProduction=notApplicable; cookiesSettings={"analytics":true,"advertising":true}; _ga=GA1.2.1919076691.1665405462; _gid=GA1.2.1935234837.1671368309; _sp_ses.cf1a=*; g_state={"i_l":1,"i_p":1671455043401}; theme=dark; device_t=MUtNeTowLHdtdDI6MQ.8OvR7Ve4nbBrueFRdfPd_F7kMFXRcUbGRxMarVYYung; sessionid=' 
                + TV_SESSION_ID 
                + '; etg=5fd4ffe4-2278-48ff-a088-7906be0f1636; cachec=5fd4ffe4-2278-48ff-a088-7906be0f1636; png=5fd4ffe4-2278-48ff-a088-7906be0f1636; tv_ecuid=5fd4ffe4-2278-48ff-a088-7906be0f1636; _sp_id.cf1a=fac826df-f914-48bb-b54d-dccd1879f5f4.1664371720.12.1671447948.1671399850.d61b1ebf-b1c8-44f7-8dc1-7a32b363ef9f',
          }

        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None  
    

def username_search(tradingview_username):
    url = "https://www.tradingview.com/username_hint"

    try:
        params = {
          "s": tradingview_username,
          }
        
        headers = {
            "accept": "*/*",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers":
            "Content-Type, Authorization, X-Requested-With",
          }

        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status() 
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return None 
    