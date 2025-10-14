# if account type == F it uses the contract value as the size of the trade and not the base asset

import time

from automate.functions.brokers.broker import CryptoBrokerClient
from automate.functions.brokers.types import *

from okx import OkxRestClient



class OkxClient(CryptoBrokerClient):

    def __init__(self, account=None, api_key=None, api_secret=None, passphrase=None, account_type="S", current_trade=None):
        super().__init__(account, api_key, api_secret, passphrase, account_type, current_trade)
        
        self.api = OkxRestClient(apikey=self.api_key, apisecret=self.api_secret, passphrase=self.passphrase)

        self.inst_type = 'FUTURES' if self.account_type == 'F' else 'SWAP' if self.account_type == 'P' else 'SPOT'


    @staticmethod
    def check_credentials(api_key, api_secret, passphrase, account_type="S"):
        try:
            client = OkxClient(api_key=api_key, api_secret=api_secret, account_type=account_type, passphrase=passphrase)
            account = client.get_account_info()

            if account:
                return {'message': "API credentials are valid.", "valid": True}
            else:
                return {'message': "API credentials are invalid.", "valid": False}

        except Exception as e:
            print("ClientError:", e)
            return {"error": str(e), "valid": False}
        
    def get_account_info(self):
        try:
            account = self.api.account.get_account_config()

            if account.get('code') != '0':
                raise Exception(account.get('msg'))

            return account.get('data')

        except Exception as e:
            raise Exception(e)
        
    def get_account_balance(self, symbol:str = None):
        try:
            account = self.api.account.get_balance()
            
            if account.get('code') != '0':
                raise Exception(account.get('msg'))

            data =  account.get('data')

            if isinstance(data, List):
                data = data[0]

            balances = {}
            for balance in data.get('details'):
                if symbol and balance["ccy"] not in symbol:
                    continue
                balances[balance["ccy"]] = {
                    "available": float(balance.get('availBal', 0)),
                    "equity": float(balance.get('availEq', 0)),
                    "locked": float(0 if balance.get("borrowFroz", 0) == '' else balance.get("borrowFroz", 0))
                }

            return balances

        except Exception as e:
            raise Exception(e)
        
    def get_exchange_info(self, symbol):
        try:
            symbol = self.adjust_symbol_name(symbol=symbol)
            
            info = self.api.publicdata.get_instruments(instType=self.inst_type , instId=symbol)

            if info.get('code') != '0':
                raise Exception(info.get('msg'))
            
            data = info.get('data')

            if isinstance(data, List):
                data = data[0]

            # print(data)

            symbol = data.get("instId")
            base_asset = data.get("baseCcy") 
            quote_asset = data.get("quoteCcy")

            if base_asset == '':
                base_asset = data.get('ctValCcy')
            if quote_asset == '':
                quote_asset = data.get('settleCcy')


            base_decimals = self.get_decimals_from_step(data.get("lotSz"))
            quote_decimals = self.get_decimals_from_step(data.get("tickSz"))
            
            # print(data)
            return {
                "symbol": symbol,
                "base_asset": base_asset,
                "quote_asset": quote_asset,
                "base_decimals": base_decimals,
                "quote_decimals": quote_decimals,

                "min_qty": data.get("minSz", None),
                "contract_val": data.get("ctVal", None),
            }
        
        except Exception as e:
            raise Exception(e)


    def get_current_price(self, symbol):
        try:
            info = self.api.marketdata.get_ticker(symbol)

            if info.get('code') != '0':
                raise Exception(info.get('msg'))
            
            data = info.get('data')

            if isinstance(data, List):
                price = data[0].get('last')
                return price

            raise Exception('Price not found!')
        
        except Exception as e:
            raise Exception(e)

    def open_trade(self, symbol, side, quantity, custom_id='', oc=False) -> OpenTrade:
        try:

            sys_info = self.get_exchange_info(symbol)
            print(sys_info)

            if not sys_info:
                raise Exception('Symbol was not found!')
            
            currency_asset = sys_info.get('quote_asset')
            base_asset = sys_info.get('base_asset')
            order_symbol = sys_info.get('symbol')
            adjusted_quantity =  self.adjust_trade_quantity(sys_info, side, quantity)

            print("Adjusted quantity:", adjusted_quantity)

            params = {
                "instId": order_symbol,
                "side": str.lower(side),
                "sz": adjusted_quantity,
                "ordType": "market",
                'tdMode': 'cash' if self.account_type == 'S' else 'isolated',
                "clOrdId": custom_id,    
            }

            if self.account_type != 'S':
                # if not oc and self.account_type == 'P':
                #     contract_val = sys_info.get('contract_val', 1)
                #     contract_size = float(adjusted_quantity) / float(contract_val) 
                #     params['sz'] = str(contract_size)

                params['ccy'] = currency_asset
                params["posSide"] = "long" if str.lower(side) == "buy" else "short" if str.lower(side) == "sell" else "net"
                if oc:
                    params["posSide"] = "short" if str.lower(side) == "buy" else "long" if str.lower(side) == "sell" else "net"
                    params["reduceOnly"] = True
            else:
                params['tgtCcy'] = 'base_ccy' 

            # print(params)

            request = self.api.trade.place_order(**params)
            end_exe = time.perf_counter()
            data = request.get('data')

            # print(request)
            if request.get('code') != '0' and data == None:
                raise Exception(request.get('msg'))
            
            if isinstance(data, List):
                data = data[0]

            order_id = data.get("ordId")

            if data.get('sCode', '0') != '0':
                raise Exception(data.get('sMsg'))

            if not self.current_trade:
                order_details = self.get_order_info(order_symbol, order_id)
                trade_details = None 
            else :
                order_details = self.get_final_trade_details(self.current_trade, order_id)
                trade_details = order_details


            # print(order_details)
            # print(trade_details)

            if order_details:
                return {
                    'message': f"Trade opened with order ID {order_id}.",
                    'order_id': order_id,
                    'closed_order_id': order_id,
                    'symbol': symbol,
                    "side": side.upper(),
                    'qty': order_details.get('volume', adjusted_quantity),
                    'price': order_details.get('price', '0'),
                    'time': order_details.get('time', ''),
                    'fees': order_details.get('fees', ''),
                    'currency': order_details.get('currency') if order_details.get('currency') is not None else currency_asset,

                    'trade_details': trade_details,
                    "end_exe": end_exe
                }
            else:
                return {
                    'message': f"Trade opened with order ID {order_id}.",
                    'order_id': order_id,
                    'closed_order_id': order_id,
                    'symbol': symbol,
                    "side": side.upper(),
                    'price': 0,
                    'qty': adjusted_quantity,
                    'currency': currency_asset,
                    "end_exe": end_exe
                }

        except Exception as e:
            return {'error': str(e)}

    def close_trade(self, symbol, side, quantity) -> CloseTrade:
        if self.account_type == "S":
            opposite_side = "sell" if side.lower() == "buy" else "buy"
        else:
            opposite_side = "sell" if side.lower() == "buy" else "buy"
            # opposite_side = side.lower()
        try:
            trade = self.open_trade(symbol, opposite_side, quantity, oc = True)
            if trade.get('error') is not None:
                raise Exception(trade.get('error'))
            return trade
        except Exception as e:
            return {'error': str(e)}

    def get_order_info(self, symbol, order_id):
        try:
            request = self.api.trade.get_order(instId=symbol, ordId=order_id)

            if request.get('code') != '0':
                raise Exception(request.get('msg'))
            
            data = request.get('data')

            if isinstance(data, List):
                data = data[0]

            # print(data)
            fees = self.calculate_fees(symbol, data.get('fillPx', '0'), data.get('fee'), data.get('feeCcy'))

            if data:
                res = {
                    'order_id': str(data.get('ordId')),
                    'symbol': str(data.get('instId')),
                    'volume': str(data.get('sz')),
                    'side': str(data.get('side')),
                    
                    'time': self.convert_timestamp(data.get('fillTime')),
                    'price': str(data.get('fillPx')),

                    'profit': str(data.get('pnl')) if self.account_type != 'S' else None,

                    'fees': str(fees),

                    'currency': data.get('ccy') if self.account_type != 'S' else None,

                    'additional_info': {
                        'fee': data.get('fee'),
                        'feeCcy': data.get('feeCcy'),
                    }
                }

                return res
        except Exception as e:
            raise Exception(e)

    def get_trading_pairs(self):
        try:
            info = self.api.marketdata.get_tickers(instType=self.inst_type)

            if info.get('code') != '0':
                raise Exception(info.get('msg'))
            
            data = info.get('data')

            pairs = [s.get('instId') for s in data]

            return pairs
        except Exception as e:
            raise Exception(e)

    def get_history_candles(self, symbol, interval, limit = 500):
        try:
            okx_intervals = {
                '1m': '1m',
                '3m': '3m',
                '5m': '5m',
                '15m': '15m',
                '30m': '30m',
                '45m': '45m',
                '1h': '1H',
                '2h': '2H',
                '4h': '4H',
                '6h': '6H',
                '12h': '12H',
                '1d': '1D',
                '1W': '1W',
                '1M': '1M'
            }
            
            info = self.api.marketdata.get_history_candlesticks(instId=symbol, bar=okx_intervals.get(interval, '1m'), limit=limit)

            if info.get('code') != '0':
                raise Exception(info.get('msg'))
            
            data = info.get('data')

            candles = []
            for c in data:
                candles.append({
                    'timestamp': self.convert_timestamp(c[0]),
                    'open': float(c[1]),
                    'high': float(c[2]),
                    'low': float(c[3]),
                    'close': float(c[4]),
                    # 'volume': float(c[5]),
                })
            return candles
        except Exception as e:
            raise Exception(e)

    def get_order_book(self, symbol, limit = 100):
        try:
            if limit > 400:
                limit = 400
            info = self.api.marketdata.get_full_orderbook(instId=symbol, sz=limit)

            if info.get('code') != '0':
                raise Exception(info.get('msg'))
            
            data = info.get('data')

            if isinstance(data, List):
                data = data[0]

            order_book = {
                'bids': [{"price":float(b[0]), "qty":float(b[1])} for b in data.get('bids', [])],
                'asks': [{"price":float(b[0]), "qty":float(b[1])} for b in data.get('asks', [])],
                'time': self.convert_timestamp(data.get('ts'))
            }

            return order_book
        except Exception as e:
            raise Exception(e)
        
        