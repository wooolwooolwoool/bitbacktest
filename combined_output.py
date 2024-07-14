# Combined Python file
# Import statements
from .market import *
from abc import ABC, abstractmethod
from datetime import datetime
from tqdm import tqdm
from typing import Literal
import hashlib
import hmac
import json
import numpy as np
import requests
import time

# Function and Class definitions
class Market(ABC):
    def __init__(self):
        self.portfolio = {}
        self.hist = {}
        self.order = []
        self.index = 0

    @abstractmethod
    def get_current_price(self):
        pass

    def get_price_hist(self):
        pass

    def reset_portfolio(self, start_cash: float, start_coin: float):
        self.portfolio = {"trade_count": 0, 'cash': start_cash, 'position': start_coin, 'total_value': start_cash}
        self.hist = {"signals": {"Buy": [], "Sell": []},
                     "execute_signals": {"Buy": [], "Sell": []},
                     "total_value_hist": [],
                     "total_pos_hist": []}

    @abstractmethod
    def place_market_order(self, side: Literal['Buy', 'Sell'], quantity: float) -> bool:
        """
        Place a market order
        :param side: Buy or Sell
        :param quantity: quantity of order
        :return: True if success, False if failed
        """
        return True

    @abstractmethod
    def place_limit_order(self, side: Literal['Buy', 'Sell'], quantity: float, price: float) -> bool:
        """
        Place a limit order
        :param side: Buy or Sell
        :param quantity: quantity of order
        :param price: price of order
        :return: True if success, False if failed
        """
        return True
    
    def place_order(self, order_type: Literal["Limit", "Market"], side: Literal['Buy', 'Sell'], quantity: float, price: float=-1):
        if order_type == "Limit" and price > 0:
            return self.place_limit_order(side, quantity, price)
        elif order_type == "Market":
            return self.place_market_order(side, quantity)
        else:
            return False

    @abstractmethod
    def get_open_orders(self):
        return self.order
        
    @abstractmethod
    def cancel_order(self, order_id: int) -> bool:
        """
        Cancel an order
        :param order_id: order id
        :return: True if success, False if failed
        """
        return True

    def save_history(self, price: float):
        self.portfolio['total_value'] = self.portfolio['cash'] + self.portfolio['position'] * price
        self.hist["total_value_hist"].append(self.portfolio['total_value'])
        self.hist["total_pos_hist"].append(self.portfolio['position'])

class BitflyerMarket(Market):
    def __init__(self):
        super().__init__()
        self.apikey = None
        self.secret = None
        self.API_URL = 'https://api.bitflyer.jp'
        self.product_code = 'BTC_JPY'

    def set_apikey(self, apikey, secret):
        self.apikey = apikey
        self.secret = secret

    def place_market_order(self, side, quantity):
        # 成行注文を出す
        if self.apikey is None or self.secret is None:
            raise ValueError("API key and secret must be set before placing an order.")

        endpoint = '/v1/me/sendchildorder'
        order_url = self.API_URL + endpoint

        order_data = {
            'product_code': self.product_code,
            'child_order_type': 'MARKET',
            'side': side,
            'size': quantity,
        }
        body = json.dumps(order_data)
        headers = self.header('POST', endpoint=endpoint, body=body)

        response = requests.post(order_url, headers=headers, data=body)
        return response.json()

    def place_limit_order(self, side: Literal['Buy', 'Sell'], quantity: float, price: float):
        if self.apikey is None or self.secret is None:
            raise ValueError("API key and secret must be set before placing an order.")

        # 指値注文を出す
        endpoint = '/v1/me/sendchildorder'
        order_url = self.API_URL + endpoint

        order_data = {
            'product_code': self.product_code,
            'child_order_type': 'LIMIT',
            'side': side,
            'price': price,
            'size': quantity,
        }
        body = json.dumps(order_data)
        headers = self.header('POST', endpoint=endpoint, body=body)

        response = requests.post(order_url, headers=headers, data=body)
        if responce.code == "200":
            return True
        else:
            return False


    def cancel_order(self, side: Literal['Buy', 'Sell'], order_id: int):
        return True

    def header(method: str, endpoint: str, body: str) -> dict:
        timestamp = str(time.time())
        if body == '':
            message = timestamp + method + endpoint
        else:
            message = timestamp + method + endpoint + body
        signature = hmac.new(self.secret.encode('utf-8'), message.encode('utf-8'),
                            digestmod=hashlib.sha256).hexdigest()
        headers = {
            'Content-Type': 'application/json',
            'ACCESS-KEY': self.API_KEY,
            'ACCESS-TIMESTAMP': timestamp,
            'ACCESS-SIGN': signature
        }
        return headers

    def get_open_orders():
        # 出ている注文一覧を取得
        endpoint = '/v1/me/getchildorders'
        
        params = {
            'product_code': 'BTC_JPY',
            'child_order_state': 'ACTIVE',  # 出ている注文だけを取得
        }
        endpoint_for_header = endpoint + '?'
        for k, v in params.items():
            endpoint_for_header += k + '=' + v
            endpoint_for_header += '&'
        endpoint_for_header = endpoint_for_header[:-1]
        
        headers = header('GET', endpoint=endpoint_for_header, body="")

        response = requests.get(API_URL + endpoint, headers=headers, params=params)
        orders = response.json()
        return orders
    class Strategy(ABC):
    """Trading Strategy

    Args:
        ABC (_type_): _description_
    """

    def __init__(self, market: Market):
        self.market = market

    @abstractmethod
    def reset_param(self, param: dict):
        """Reset parameter
        Reset parameters. Implement the process of setting parameters in this method.
        "self.static" are values to set as AWS env.
        "self.dynamic" are values to save to DynamoDB.

        Args:
            param (dict): parameter
        """
        self.static = param
        self.dynamic = {}
        pass

    def reset_all(self, param: dict, start_cash: int, start_coin: float = 0):
        """Reset parameter and portfolio
        Must be called before the backtest is executed.

        Args:
            param (dict): parameter
            start_cash (int): start cash
            start_coin (float): start coin
        """
        self.reset_param(param)
        self.market.reset_portfolio(start_cash, start_coin)
        self.dynamic["count"] = 0

    @abstractmethod
    def generate_signals(self, price: float) -> str:
        """Generate Trade Signal
        Generate trade signal based on price, parameters, etc.
        Implemente The logic to generate signals.

        Args:
            price (float): Current bitcoin price

        Returns:
            str: Trade signal (ex. "Buy", "Sell")
        """
        return ""

    @abstractmethod
    def execute_trade(self, price: float, signal: str):
        """Executing an trade Based on a Signal
        Implements the logic to execute an order 

        Args:
            price (float): Current bitcoin price
            signal (str): Trade Signal
        """
        pass

    def backtest(self):
        """Running a back test
        Backtest flow is
        1. get current price
        2. generate_signals() method
        3. execute_trade() method
        4. save data and go to next

        Returns:
            _type_: Result of backtest
        """
        self.dynamic["count"] = 0
        self.market.set_current_index(0)
        for _ in tqdm(range(len(self.market))):
            self.dynamic["count"] += 1
            self.market.set_current_index(self.dynamic["count"] - 1)
            price = self.market.get_current_price()
            signal = self.generate_signals(price)
            self.execute_trade(price, signal)
            self.market.check_order()
            self.market.save_history(price)
        return self.market.portfolio

    @property
    def backtest_history(self):
        return self.market.hist


class MovingAverageCrossoverStrategy(Strategy):

    def reset_param(self, param):
        super().reset_param(param)
        self.dynamic["price_hist"] = np.array([])

    def generate_signals(self, price):
        self.dynamic["price_hist"] = np.append(self.dynamic["price_hist"],
                                               price)
        if len(self.dynamic["price_hist"]) < (self.static["long_window"] + 1):
            return None  # Not enough data for calculation

        short_mavg = np.mean(
            self.dynamic["price_hist"][-self.static["short_window"]:])
        long_mavg = np.mean(
            self.dynamic["price_hist"][-self.static["long_window"]:])

        short_mavg_old = np.mean(
            self.dynamic["price_hist"][-1 *
                                       (self.static["short_window"] + 1):-1])
        long_mavg_old = np.mean(
            self.dynamic["price_hist"][-1 *
                                       (self.static["long_window"] + 1):-1])

        self.dynamic["price_hist"] = np.delete(self.dynamic["price_hist"], 0)

        if short_mavg > long_mavg and short_mavg_old < long_mavg_old and long_mavg > long_mavg_old:
            return 'Buy'
        elif short_mavg < long_mavg and short_mavg_old > long_mavg_old:
            return 'Sell'
        else:
            return ""

    def execute_trade(self, price, signal):
        if signal in ['Buy', "Sell"]:
            self.market.place_market_order(signal,
                                           self.static["one_order_quantity"])


