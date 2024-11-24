
from binance.spot import Spot as Client
from binance.cm_futures import CMFutures
from binance.um_futures import UMFutures


def check_binance_credentials(api_key, api_secret, trade_type="spot", symbol = "BTCUSDT"):
    """
    Checks API credentials by attempting a test order on Binance.

    Args:
        api_key (str): User's Binance API key.
        api_secret (str): User's Binance API secret.
        symbol (str): Trading pair symbol, e.g., 'BTCUSDT'.
        trade_type (str): Type of trading ('spot', 'usdm', 'coinm').

    """

    try:
        if trade_type == "S": #Spot
            client = Client(api_key, api_secret)
            # Spot market test order

            client.account()
            # client.new_order_test(
            #     symbol=symbol,
            #     side=Client.SIDE_BUY,
            #     type=Client.ORDER_TYPE_MARKET,
            #     quantity=0.01  # Small quantity for test
            # )
        elif trade_type == "U": #USDM
            client = UMFutures(api_key, api_secret)
            # USD-M Futures test order

            client.new_order_test(
                symbol=symbol,
                side=Client.SIDE_BUY,
                type=Client.ORDER_TYPE_MARKET,
                quantity=1  # Adjust quantity according to minimum requirements
            )
        elif trade_type == "C": #COINM
            client = CMFutures(api_key, api_secret)
            # Coin-M Futures test order
            client.account()
            # client.new_order_test(
            #     symbol=symbol,
            #     side=Client.SIDE_BUY,
            #     type=Client.ORDER_TYPE_MARKET,
            #     quantity=1  # Adjust quantity according to minimum requirements
            # )
        else:
            r = {'error': "Invalid trade type specified. Choose 'spot', 'usdm', or 'coinm'.", "valid": False}
            return r

        r = {'message': "API credentials are valid and test order succeeded.", "valid": True}
        return r
    
    except Exception as e:
        r = {'error': "API credentials are not valid", "valid": False}
        return r



def open_trade(binance_account, symbol: str, side: str, quantity: float, trade_type: str = "spot", custom_id: str = None):
    """
    Opens a trade and logs it with a custom ID.

    Args:
        symbol (str): Trading pair symbol, e.g., 'BTCUSDT'.
        side (str): 'BUY' or 'SELL'.
        quantity (float): Quantity to trade.
        trade_type (str): 'spot', 'usdm', or 'coinm'.
        custom_id (str): Custom identifier for the trade.

    Returns:
        dict: Binance API response.
    """
    try:
        client = Client(api_key=binance_account.BINANCE_API_KEY, api_secret=binance_account.BINANCE_SECRET_KEY)

        if trade_type == "spot":
            order_params = {
                "symbol": symbol,
                "side": side,
                "type": "MARKET",
                "quantity": quantity,
            }
            if custom_id:
                order_params["newClientOrderId"] = custom_id

            response = client.create_order(**order_params)

        elif trade_type == "usdm":
            response = client.futures_create_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=quantity
            )
        elif trade_type == "coinm":
            response = client.futures_coin_create_order(
                symbol=symbol,
                side=side,
                type="MARKET",
                quantity=quantity
            )
        else:
            raise ValueError("Invalid trade_type. Use 'spot', 'usdm', or 'coinm'.")

        # Log the trade with your custom ID
        # log_trade(response, custom_id)

        return response

    except Exception as e:
        return {"error": str(e)}



# def close_trade(binance_account, custom_id: str):
#     """
#     Closes a trade based on the custom ID.

#     Args:
#         custom_id (str): Custom identifier for the trade to close.

#     Returns:
#         dict: Binance API response.
#     """
#     try:
#         # Fetch the trade details from your database or storage
#         # trade_details = fetch_trade_by_custom_id(custom_id)

#         client = Client(api_key=binance_account.BINANCE_API_KEY, api_secret=binance_account.BINANCE_SECRET_KEY)
#         if not trade_details:
#             return {"error": f"No trade found with custom ID: {custom_id}"}

#         # Extract necessary details
#         symbol = trade_details["symbol"]
#         side = "SELL" if trade_details["side"] == "BUY" else "BUY"
#         quantity = trade_details["quantity"]
#         trade_type = trade_details["trade_type"]

#         # Place the opposite order to close the trade
#         if trade_type == "spot":
#             response = client.create_order(
#                 symbol=symbol,
#                 side=side,
#                 type="MARKET",
#                 quantity=quantity
#             )
#         elif trade_type == "usdm":
#             response = client.futures_create_order(
#                 symbol=symbol,
#                 side=side,
#                 type="MARKET",
#                 quantity=quantity
#             )
#         elif trade_type == "coinm":
#             response = client.futures_coin_create_order(
#                 symbol=symbol,
#                 side=side,
#                 type="MARKET",
#                 quantity=quantity
#             )
#         else:
#             raise ValueError("Invalid trade_type. Use 'spot', 'usdm', or 'coinm'.")

#         return response

#     except Exception as e:
#         return {"error": str(e)}