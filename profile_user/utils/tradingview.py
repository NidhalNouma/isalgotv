import requests
from django.conf import settings


from strategies.models import Strategy, StrategySubscriber
from profile_user.models import User_Profile
import environ
env = environ.Env()

TV_SESSION_ID = env('TV_SESSION_ID')


def give_access(strategy_id, profile_id, access, user_profile=None, strategy=None):
    add_or_reemove = "add" if access == True else "remove"
    url = f"https://www.tradingview.com/pine_perm/{add_or_reemove}/"
    try:
        if not strategy:
            strategy = Strategy.objects.get(pk = strategy_id)
        if not user_profile:
            profile = User_Profile.objects.get(pk = profile_id)
        else:
            profile = user_profile
        r = {"error": "", "access": None, 'strategy': strategy, 'user_profile': profile}

        if not profile.tradingview_username:
            r['error'] = "Please set your TradingView username in your profile settings."
            return r
        if not strategy.tradingview_ID:
            r['error'] = "This strategy does not have a TradingView ID. Please contact support."
            return r
        
        if access:
          if profile.has_subscription == False and profile.is_lifetime == False and strategy.premium in ['Premium', 'Elite']:
              if profile.strategies.filter(pk=strategy_id).exists():
                  profile.strategies.remove(strategy)
              r['error'] = "This strategy is premium. Please upgrade your plan to access it."
              r['upgrade'] = True
              return r
          
          if not profile.is_lifetime and strategy.premium == 'Elite':
              if profile.strategies.filter(pk=strategy_id).exists():
                  profile.strategies.remove(strategy)
              r['error'] = "This is an Elite strategy. only availble for lifetime users."
              r['upgrade'] = True
              return r
          
          if strategy.premium == 'VIP':
            if strategy.created_by != profile.user:
                subscriber = StrategySubscriber.objects.filter(strategy=strategy, user_profile=profile).first()
                is_subscribed, _ = subscriber.is_active() if subscriber else (False, None)
                if not is_subscribed:
                    if profile.strategies.filter(pk=strategy_id).exists():
                        profile.strategies.remove(strategy)
                    r['error'] = "This is an Exclusive strategy. Please subscribe to access it."
                    # r['upgrade'] = True
                    return r


        data = {
          "username_recip": profile.tradingview_username,
          "pine_id": f"PUB;{strategy.tradingview_ID}"
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
        # print('data:', response.text, data)
        if response.status_code >= 400:
            error = response.json().get('detail')
            if error:
                raise Exception(error)
        response.raise_for_status() 

        if access:
          profile.strategies.add(strategy)
        else:
          profile.strategies.remove(strategy)

        r["access"] = response.json()
        return r
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        r['error'] =  "We encountered an error while granting access. Please reach out to us so we can assist you promptly!"
        return r
    except Exception as e:
        print(f"An error occurred: {e}")
        r['error'] = str(e)
        return r
    

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
    