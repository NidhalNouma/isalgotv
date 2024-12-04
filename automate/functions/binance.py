from binance.spot import Spot 
from binance.cm_futures import CMFutures
from binance.um_futures import UMFutures

from binance.error import ClientError


def check_binance_credentials(api_key, api_secret, trade_type="S"):

    try:
        if trade_type == "S": #Spot
            client = Spot(api_key, api_secret)
            client.account()
        elif trade_type == "U": #USDM
            client = UMFutures(api_key, api_secret)
            client.account()

        elif trade_type == "C": #COINM
            client = CMFutures(api_key, api_secret)
            client.account()

        else:
            r = {'error': "Invalid trade type specified. Choose 'spot', 'usdm', or 'coinm'.", "valid": False}
            return r

        r = {'message': "API credentials are valid.", "valid": True}
        return r
    
    except ClientError as e:   
        return {"error": e.error_message}
    
    except Exception as e:   
        return {"error": str(e)}



def open_binance_trade(binance_account, symbol: str, side: str, quantity: float, custom_id: str = None):

    try:
        trade_type = binance_account.type
        order_params = {
            "symbol": symbol,
            "side": str.upper(side),
            "type": "MARKET",
            "quantity": quantity,
        }

        if trade_type == "S":
            client = Spot(api_key=binance_account.apiKey, api_secret=binance_account.secretKey)
            response = client.new_order(**order_params)

        elif trade_type == "U":
            client = UMFutures(key=binance_account.apiKey, secret=binance_account.secretKey)
            response = client.new_order(**order_params)

        elif trade_type == "C":
            client = CMFutures(key=binance_account.apiKey, secret=binance_account.secretKey)
            response = client.new_order(**order_params)

        else:
            raise ValueError("Invalid trade type. Use 'spot', 'usdm', or 'coinm'.")

        return response

    except ClientError as e:   
        raise ValueError(e.error_message)

    except Exception as e:   
        raise ValueError(str(e))



def close_binance_trade(binance_account, trade_type, symbol, side, quantity):
    try:
        t_side = "SELL" if side == "B" else "BUY"

        order_params = {
            "symbol": symbol,
            "side": str.upper(t_side),
            "type": "MARKET",
            "quantity": quantity,
        }

        # Place the opposite order to close the trade
        if trade_type == "S":
            client = Spot(api_key=binance_account.apiKey, api_secret=binance_account.secretKey)
            response = client.new_order(**order_params)

        elif trade_type == "U":
            client = UMFutures(key=binance_account.apiKey, secret=binance_account.secretKey)
            response = client.new_order(**order_params)

        elif trade_type == "M":
            client = CMFutures(key=binance_account.apiKey, secret=binance_account.secretKey)
            response = client.new_order(**order_params)

        else:
            raise ValueError("Invalid trade_type. Use 'spot', 'usdm', or 'coinm'.")

        return response

    except ClientError as e:   
        raise ValueError(e.error_message)

    except Exception as e:   
        raise ValueError(str(e))