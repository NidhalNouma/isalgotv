from binance.spot import Spot
from binance.cm_futures import CMFutures
from binance.um_futures import UMFutures
from binance.error import ClientError

from django.utils import timezone
from datetime import datetime
from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_UP

def check_binance_credentials(api_key, api_secret, trade_type="S"):
    try:
        if trade_type == "S":  # Spot
            client = Spot(api_key, api_secret)
            client.account()
        elif trade_type == "U":  # USDM
            client = UMFutures(api_key, api_secret)
            client.account()
        elif trade_type == "C":  # COINM
            client = CMFutures(api_key, api_secret)
            client.account()
        else:
            return {'error': "Invalid trade type specified. Choose 'spot', 'usdm', or 'coinm'.", "valid": False}

        return {'message': "API credentials are valid.", "valid": True}
    
    except ClientError as e:
        return {"error": e.error_message}
    except Exception as e:
        return {"error": str(e)}
    
def get_exchange_info(api_key, api_secret, trade_type, symbol):
    try:
        if trade_type == "S":  # Spot
            client = Spot(api_key, api_secret)
            response = client.exchange_info(symbol)
            
        elif trade_type == "U":  # USDM
            client = UMFutures(api_key, api_secret)
            response = client.exchange_info()
        elif trade_type == "C":  # COINM
            client = CMFutures(api_key, api_secret)
            response = client.exchange_info()
        else:
            return {'error': "Invalid trade type specified. Choose 'spot', 'usdm', or 'coinm'.", "valid": False}
        
        if isinstance(response, list):
            data_list = response
        else:
            data_list = response.get('symbols', [])
        
        target = symbol.upper()
        for item in data_list:
            inst = item.get('symbol', '')
            if inst.replace('_', '').upper() == target or inst == target:
                return item
        
        return None
    
    except Exception as e:
        raise Exception(e)


def get_account_balance(binance_account, asset: str):
    try:
        trade_type = binance_account.type
        balances = {}

        if trade_type == "S":  # Spot
            client = Spot(api_key=binance_account.apiKey, api_secret=binance_account.secretKey)
            account_info = client.account()
            for balance in account_info['balances']:
                balances[balance['asset']] = float(balance['free'])
        elif trade_type in ["U", "C"]:  # USDM or COINM Futures
            if trade_type == "U":
                client = UMFutures(key=binance_account.apiKey, secret=binance_account.secretKey)
            else:
                client = CMFutures(key=binance_account.apiKey, secret=binance_account.secretKey)
            account_info = client.account()
            for balance in account_info['assets']:
                balances[balance['asset']] = float(balance['availableBalance'])
        else:
            raise ValueError("Invalid trade type. Use 'spot', 'usdm', or 'coinm'.")

        return {"asset": asset, "balance": balances.get(asset, 0.0)}
    
    except ClientError as e:
        raise ValueError(e.error_message)
    except Exception as e:
        raise ValueError(str(e))

def get_decimals_from_step(size_str):
    """
    Determine the number of decimal places allowed by a step size,
    stripping any trailing zeros in the step definition.
    """
    d = Decimal(size_str)
    # Normalize to remove any trailing zeros (e.g., '0.10000000' -> '0.1')
    d_norm = d.normalize()
    exp = d_norm.as_tuple().exponent
    return max(-exp, 0)

def adjust_trade_quantity(binance_account, symbol_info, side ,quote_order_qty):
    try:
        base_asset = symbol_info.get('baseAsset')
        quote_asset = symbol_info.get('quoteAsset')

        base_balance = get_account_balance(binance_account, base_asset)["balance"]
        quote_balance = get_account_balance(binance_account, quote_asset)["balance"]

        # find the filters
        price_filter = next(f for f in symbol_info['filters'] if f['filterType']=='PRICE_FILTER')
        lot_filter   = next(f for f in symbol_info['filters'] if f['filterType']=='LOT_SIZE')

        quote_decimals = get_decimals_from_step(price_filter['tickSize'])
        base_decimals   = get_decimals_from_step(lot_filter['stepSize'])

        print("Base asset:", base_asset, base_decimals)
        print("Quote asset:", quote_asset, quote_decimals)
            
        try:
            precision = int(base_decimals)
        except (TypeError, ValueError):
            precision = 8  # fallback precision
        quant = Decimal(1).scaleb(-precision)  
        
        # Fetch balance based on the trade type
        if binance_account.type == "S":  # Spot
            print("Base balance:", base_balance)
            print("Quote balance:", quote_balance)

            if side.upper() == "BUY":
                if float(quote_balance) <= 0:
                    raise ValueError("Insufficient quote balance.")
                # elif quote_balance < quote_order_qty:
                #     return quote_balance
                # Format quantity to max base_decimals and return as string
                qty_dec = Decimal(str(quote_order_qty)).quantize(quant, rounding=ROUND_UP)
                return format(qty_dec, f'.{precision}f')
            
            elif side.upper() == "SELL":
                if float(base_balance) <= 0:
                    raise ValueError("Insufficient base balance.")
                elif float(base_balance) < float(quote_order_qty):
                    # Format quantity to max base_decimals and return as string
                    qty_dec = Decimal(str(base_balance)).quantize(quant, rounding=ROUND_DOWN)
                    return format(qty_dec, f'.{precision}f')
                # Format quantity to max base_decimals and return as string
                qty_dec = Decimal(str(quote_order_qty)).quantize(quant, rounding=ROUND_UP)
                return format(qty_dec, f'.{precision}f')
            
            return quote_order_qty
        
        elif binance_account.type == "U":  # USDM Futures
            qty_dec = Decimal(str(quote_order_qty)).quantize(quant, rounding=ROUND_UP)
            return format(qty_dec, f'.{precision}f')
        
        elif binance_account.type == "C":  # COINM Futures
            quant = 0
            qty_dec = Decimal(str(quote_order_qty)).quantize(quant, rounding=ROUND_UP)
            return format(qty_dec, f'.{precision}f')
        else:
            return quote_order_qty
    
    except Exception as e:
        raise ValueError(str(e))

def open_binance_trade(binance_account, symbol: str, side: str, quantity: float, custom_id: str = None):
    try:
        trade_type = binance_account.type
        sys_info = get_exchange_info(binance_account.apiKey, binance_account.secretKey, trade_type, symbol)
        # print(sys_info)

        if not sys_info:
            raise Exception('Symbol was not found!')
        
        currency_asset = sys_info.get('quoteAsset')
        order_symbol = sys_info.get('symbol')

        adjusted_quantity =  adjust_trade_quantity(binance_account, sys_info, side, float(quantity))
        print("Adjusted quantity:", adjusted_quantity)

        order_params = {
            "symbol": symbol,
            "side": str.upper(side),
            "type": "MARKET",
            "quantity": adjusted_quantity,
            # "reduceOnly": "true",
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
            currency_asset = sys_info.get('baseAsset')
        else:
            raise ValueError("Invalid trade type. Use 'spot', 'usdm', or 'coinm'.")
        
        order_id = response["orderId"]
        order_details = get_order_details(binance_account, symbol, order_id)
            
        if order_details:
            return {
                'message': f"Trade opened with order ID {order_id}.",
                'order_id': order_id,
                'symbol': symbol,
                "side": side.upper(),
                'qty': order_details.get('volume', adjusted_quantity),
                'price': order_details.get('price', '0'),
                'time': order_details.get('time', ''),
                'fees': order_details.get('fees', ''),
                'currency': currency_asset,
            }
        else:
            return {
                'message': f"Trade opened with order ID {response.get('orderId')}.",
                'order_id': response.get('orderId'),
                'symbol': response.get('symbol', symbol),
                "side": side.upper(),
                'price': (response['fills'][0].get('price') if response.get('fills') and len(response['fills']) > 0 else response.get('price', '')),
                # 'fees': response['fills'][0]['commission'],
                'qty': (
                    response.get('executedQty')
                    if float(response.get('executedQty', 0)) > 0
                    else adjusted_quantity
                ),
                'currency': currency_asset,
            }

    
    except ClientError as e:
        raise ValueError(e.error_message)
    except Exception as e:
        raise ValueError(str(e))

def close_binance_trade(binance_account, symbol: str, side: str, quantity: float):
    try:
        t_side = "SELL" if side.upper() == "BUY" else "BUY"
        trade_type = binance_account.type

        sys_info = get_exchange_info(binance_account.apiKey, binance_account.secretKey, trade_type, symbol)
        # print(sys_info)

        if not sys_info:
            raise Exception('Symbol was not found!')
        
        quote_asset = sys_info.get('quoteAsset')
        order_symbol = sys_info.get('symbol')

        adjusted_quantity =  adjust_trade_quantity(binance_account, sys_info, t_side, float(quantity))
        print("Adjusted quantity:", adjusted_quantity)

        order_params = {
            "symbol": symbol,
            "side": str.upper(t_side),
            "type": "MARKET",
            "quantity": adjusted_quantity,
            # "reduceOnly": "true",
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
            raise ValueError("Invalid trade_type. Use 'spot', 'usdm', or 'coinm'.")
    

        if response.get('msg') is not None:
            raise Exception(response.get('msg'))

        return {
            'message': f"Trade closed for order ID {response.get('orderId')}.",
            "symbol": symbol,

            "id": response.get('orderId'),
            "closed_order_id": response["orderId"],
            "side": t_side.upper(),
            # Use executedQty if present and > 0, else use adjusted_quantity
            'qty': (
                response.get('executedQty')
                if float(response.get('executedQty', 0)) > 0
                else adjusted_quantity
            ),
            'price': (response['fills'][0].get('price') if response.get('fills') and len(response['fills']) > 0 else response.get('price', '')),
        }
    
    except ClientError as e:
        raise ValueError(e.error_message)
    except Exception as e:
        raise ValueError(str(e))
        

def get_order_details(binance_account, symbol, order_id):

    try:
        trade_type = binance_account.type

        params = {
            "symbol": symbol,
            "orderId": order_id
        }


        trade_type = binance_account.type
        if trade_type == "S":
            client = Spot(api_key=binance_account.apiKey, api_secret=binance_account.secretKey)
            response = client.my_trades(**params)

        elif trade_type == "U":
            client = UMFutures(key=binance_account.apiKey, secret=binance_account.secretKey)
            response = client.get_account_trades(**params)
        elif trade_type == "C":
            client = CMFutures(key=binance_account.apiKey, secret=binance_account.secretKey)
            response = client.get_account_trades(**params)
        else:
            raise ValueError("Invalid trade_type. Use 'spot', 'usdm', or 'coinm'.")
        
        if isinstance(response, dict) and response.get('msg') is not None:
            raise Exception(response.get('msg'))
        
        if isinstance(response, list):
            if not response:
                return None
            if len(response) > 1:
                total_qty = sum(float(t.get('qty', 0)) for t in response)
                total_commission = sum(float(t.get('commission', 0)) for t in response)
                # Use the last fill as the base record
                trade = response[-1]
                trade['qty'] = str(total_qty)
                trade['commission'] = str(total_commission)
            else:
                trade = response[0]
        else:
            trade = response
        
        if trade:

            sym_info = get_exchange_info(binance_account.apiKey, binance_account.secretKey, trade_type, symbol)

            fees = float(trade.get('commission'))
            # Convert fees from ADA to USDT using avg_price

            if trade_type != "C":
                if str(trade.get('commissionAsset')) == sym_info.get('baseAsset'):
                    try:
                        fee_ada = Decimal(str(fees))
                        price_usdt = Decimal(str(trade.get('price', '0')))
                        fees = fee_ada * price_usdt
                    except (InvalidOperation, ValueError):
                        pass

            ts_s = trade.get('time') / 1000  # e.g. 1683474419
            dt_naive = datetime.fromtimestamp(ts_s)
            dt_aware = timezone.make_aware(dt_naive, timezone=timezone.utc)

            
            r = {
                'order_id': str(trade.get('orderId')),
                'symbol': str(trade.get('symbol')),
                'volume': str(trade.get('qty')),
                'side': str(trade.get('side')),
                
                'time': dt_aware,
                'price': str(trade.get('price')),

                'profit': str(trade.get('realizedPnl', None)),

                'fees': str(fees),

                'commission': str(trade.get('commission')),
                'commissionAsset': str(trade.get('commissionAsset')),
            }

            return r 
        
        return None

    except ClientError as e:
        raise ValueError(e.error_message)
    except Exception as e:
        raise ValueError(str(e))

def get_binance_order_details(account, trade):

    trade_id = trade.closed_order_id

    try:
        result = get_order_details(account, trade.symbol, trade_id)

        if result:
            # Convert price and volume to Decimal for accurate calculation
            try:
                price_dec = Decimal(str(result.get('price', '0')))
            except (InvalidOperation, ValueError):
                price_dec = Decimal('0')
            try:
                volume_dec = Decimal(str(result.get('volume', '0')))
            except (InvalidOperation, ValueError):
                volume_dec = Decimal('0')

            if result.get('profit') in (None, '', 'None'):
                if price_dec != 0:
                    side_upper = trade.side.upper()
                    if side_upper in ("B", "BUY"):
                        profit = (price_dec - Decimal(str(trade.entry_price))) * volume_dec
                    elif side_upper in ("S", "SELL"):
                        profit = (Decimal(str(trade.entry_price)) - price_dec) * volume_dec
                    else:
                        profit = Decimal("0")
                else:
                    profit = Decimal("0")
            else:
                profit = result.get('profit')

            res = {
                'order_id': str(result.get('order_id')),
                'symbol': str(result.get('symbol')),
                'volume': str(result.get('volume')),
                'side': str(result.get('side')),

                'open_price': str(trade.entry_price),
                'close_price': str(result.get('price')),

                'open_time': str(trade.entry_time),
                'close_time': str(result.get('time')), 

                'fees': str(result.get('fees')), 
                'profit': str(profit),

                'commission': str(result.get('commission')),
                'commissionAsset': str(result.get('commissionAsset')),
            }

            return res
        
        return None

    except Exception as e:
        print("Error:", e)
        return None