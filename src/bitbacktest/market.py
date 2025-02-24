from abc import ABC, abstractmethod
from typing import Literal
import numpy as np
import json
import requests
import time
import hashlib
import hmac
from datetime import datetime


class Order():

    def __init__(self, side, quantity, price):
        self.side = side
        self.quantity = quantity
        self.price = price
        self.order_id = datetime.now().timestamp()


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
        pass

    @abstractmethod
    def place_market_order(self, side: Literal['Buy', 'Sell'],
                           quantity: float) -> bool:
        """
        Place a market order
        :param side: Buy or Sell
        :param quantity: quantity of order
        :return: True if success, False if failed
        """
        return True

    @abstractmethod
    def place_limit_order(self, side: Literal['Buy', 'Sell'], quantity: float,
                          price: float) -> bool:
        """
        Place a limit order
        :param side: Buy or Sell
        :param quantity: quantity of order
        :param price: price of order
        :return: True if success, False if failed
        """
        return True

    def place_order(self,
                    order_type: Literal["Limit", "Market"],
                    side: Literal['Buy', 'Sell'],
                    quantity: float,
                    price: float = -1):
        if order_type == "Limit" and price > 0:
            return self.place_limit_order(side, quantity, price)
        elif order_type == "Market":
            return self.place_market_order(side, quantity)
        else:
            return False

    def _checkout_position(self, order, current_positions):
        tmp_profit = 0
        if order["side"] == "BUY":
            for current_position in current_positions:
                if current_position["side"] == "SELL":
                    if current_position["size"] > order["size"]:
                        current_position["size"] -= order["size"]
                        tmp_profit += ((current_position["price"] - order["price"]) * order["size"])
                        order["size"] = 0
                    else:
                        order["size"] -= current_position["size"]
                        tmp_profit += (current_position["price"] - order["price"]) * current_position["size"]
                        current_positions.remove(current_position)
                else:
                    pass
                if order["size"] == 0:
                    break
        else:
            for current_position in current_positions:
                if current_position["side"] == "BUY":
                    if current_position["size"] > order["size"]:
                        current_position["size"] -= order["size"]
                        tmp_profit += ((order["price"] - current_position["price"]) * order["size"])
                        order["size"] = 0
                    else:
                        order["size"] -= current_position["size"]
                        tmp_profit += ((order["price"] - current_position["price"]) * current_position["size"])
                        current_positions.remove(current_position)
                else:
                    pass
                if order["size"] == 0:
                    break
        if order["size"] > 0:
            current_positions.append(order)
        return tmp_profit

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


class BacktestMarket(Market):

    def __init__(self, data: np.ndarray,
                dates = None,
                fee_rate: float = 0.0015,
                is_fx = False):
        super().__init__()
        self.data = data
        self.index = 0
        self.fee_rate = fee_rate
        self.is_fx = is_fx
        if dates is None:
            self.dates = np.arange(len(data))
        else:
            self.dates = dates

    def reset_portfolio(self, start_cash: float, start_coin: float):
        self.portfolio = {
            "trade_count": 0,
            'cash': start_cash,
            'position': start_coin,
            'positions_fx': [],
            'total_value': start_cash,
            'profit_rate': 0
        }
        self.hist = {
            "signals": {
                "Buy": [],
                "Sell": []
            },
            "execute_signals": {
                "Buy": [],
                "Sell": []
            },
            "total_value_hist": [],
            "total_pos_hist": []
        }
        self.order = []
        self.index = 0
        self.start_cash = start_cash

    def save_history(self, price: float):
        if self.is_fx:
            self.portfolio['total_value'] = self.portfolio[
                'cash'] + self._calc_current_value(price, self.portfolio['positions_fx'])
        else:
            self.portfolio['total_value'] = self.portfolio[
                'cash'] + self.portfolio['position'] * price
        self.portfolio['profit_rate'] = self.portfolio['total_value'] / self.start_cash
        self.hist["total_value_hist"].append(self.portfolio['total_value'])
        self.hist["total_pos_hist"].append(self.portfolio['position'])

    def _calc_current_value(self, current_price, current_positions):
        current_value = 0
        for current_position in current_positions:
            if current_position["side"] == "BUY":
                current_value += (current_price - current_position["price"]) * current_position["size"]
            else:
                current_value += (current_position["price"] - current_price) * current_position["size"]
        return current_value

    def set_current_index(self, index: int):
        self.index = index

    def get_current_price(self):
        return self.data[self.index]

    def get_price_hist(self):
        return self.data[:self.index]

    def __len__(self):
        return len(self.data)

    def get_open_orders(self):
        return self.order

    def cancel_order(self, order_id: int) -> bool:
        orders = self.get_open_orders()
        for order in orders:
            if order.order_id == order_id:
                self.order.remove(order)
                return True
        return False

    def _calculate_margin(self, position: float, price: float, lot_size: float = 1.0, leverage: float = 1.0) -> float:
        """
        必要な証拠金を計算する関数。
        """
        position_size = abs(position) * lot_size  # ポジションの通貨量
        margin_required = (position_size * price) / leverage  # 必要証拠金
        return margin_required

    def _execute_order_fx(self, quantity: float, price: float, side) -> bool:
        # order = {"side": "BUY", "size": 0, "price": 0}
        current_position = 0
        for pos in self.portfolio['positions_fx']:
            if pos["side"] == "BUY":
                current_position += pos["size"]
            else:
                current_position -= pos["size"]
        tmp_position = current_position + quantity
        if self.portfolio['cash'] >= self._calculate_margin(tmp_position, price):
            order = {"size": quantity, "price": price, "side": side}
            self.portfolio['cash'] += self._checkout_position(order, self.portfolio['positions_fx'])
            self.portfolio["trade_count"] += 1
            return True
        else:
            return False

    def _execute_buy_order_fx(self, quantity: float, price: float) -> bool:
        return self._execute_order_fx(quantity, price, "BUY")

    def _execute_sell_order_fx(self, quantity: float, price: float) -> bool:
        return self._execute_order_fx(quantity, price, "SELL")

    def _execute_buy_order_normal(self, quantity: float, price: float) -> bool:
        if self.portfolio['cash'] >= quantity * price:
            self.portfolio['cash'] -= quantity * price
            self.portfolio['position'] += quantity
            self.portfolio['position'] -= quantity * self.fee_rate
            self.portfolio["trade_count"] += 1
            return True  # Buy order executed successfully
        else:
            return False  # Insufficient funds

    def _execute_sell_order_normal(self, quantity: float, price: float) -> bool:
        if self.portfolio['position'] >= quantity:
            self.portfolio['cash'] += quantity * price
            self.portfolio['position'] -= quantity
            self.portfolio['position'] -= quantity * self.fee_rate
            self.portfolio["trade_count"] += 1
            return True  # Sell order executed successfully
        else:
            return False  # Insufficient funds

    def _execute_buy_order(self, quantity: float, price: float) -> bool:
        if self.is_fx:
            return self._execute_buy_order_fx(quantity, price)
        else:
            return self._execute_buy_order_normal(quantity, price)

    def _execute_sell_order(self, quantity: float, price: float) -> bool:
        if self.is_fx:
            return self._execute_sell_order_fx(quantity, price)
        else:
            return self._execute_sell_order_normal(quantity, price)

    def place_market_order(self, side: Literal['Buy', 'Sell'],
                           quantity: float) -> bool:
        price = self.get_current_price()
        self.hist["signals"][side].append((self.index, price))
        if side == 'Buy':
            ret = self._execute_buy_order(quantity, price)
        elif side == 'Sell':
            ret = self._execute_sell_order(quantity, price)
        else:
            ret = False
        if ret:
            self.hist["execute_signals"][side].append((self.index, price))
        return ret

    def place_limit_order(self, side: Literal['Buy', 'Sell'], quantity: float,
                          price: float) -> bool:
        self.order.append(Order(side, quantity, price))
        return True

    def check_order(self):
        price = self.get_current_price()
        for order in self.order:
            if (order.side == "Sell" and price >= order.price) or \
               (order.side == "Buy" and price <= order.price):
                if self.place_market_order(order.side, order.quantity):
                    self.order.remove(order)


class BitflyerMarket(Market):

    def __init__(self):
        super().__init__()
        self.apikey = None
        self.secret = None
        self.API_URL = 'https://api.bitflyer.jp'
        self.product_code = 'FX_BTC_JPY'

    def set_apikey(self, apikey, secret):
        self.apikey = apikey
        self.secret = secret

    def place_market_order(self, side, quantity):
        # 成行注文を出す
        if self.apikey is None or self.secret is None:
            raise ValueError(
                "API key and secret must be set before placing an order.")

        endpoint = '/v1/me/sendchildorder'
        order_url = self.API_URL + endpoint

        order_data = {
            'product_code': self.product_code,
            'child_order_type': 'MARKET',
            'side': side.upper(),
            'size': quantity,
        }
        body = json.dumps(order_data)
        headers = self.header('POST', endpoint=endpoint, body=body)

        res = requests.post(order_url, headers=headers, data=body)
        if 'child_order_acceptance_id' in res.json():
            return True
        else:
            return False

    def place_limit_order(self, side: Literal['Buy', 'Sell'], quantity: float,
                          price: float):
        if self.apikey is None or self.secret is None:
            raise ValueError(
                "API key and secret must be set before placing an order.")

        # 指値注文を出す
        endpoint = '/v1/me/sendchildorder'
        order_url = self.API_URL + endpoint

        order_data = {
            'product_code': self.product_code,
            'child_order_type': 'LIMIT',
            'side': side.upper(),
            'price': int(price),
            'size': quantity,
        }
        body = json.dumps(order_data)
        headers = self.header('POST', endpoint=endpoint, body=body)

        res = requests.post(order_url, headers=headers, data=body)
        if 'child_order_acceptance_id' in res.json():
            return True
        else:
            return False

    def cancel_order(self, order_id: int):
        return True

    def header(self, method: str, endpoint: str, body: str) -> dict:
        timestamp = str(time.time())
        if body == '':
            message = timestamp + method + endpoint
        else:
            message = timestamp + method + endpoint + body
        signature = hmac.new(self.secret.encode('utf-8'),
                             message.encode('utf-8'),
                             digestmod=hashlib.sha256).hexdigest()
        headers = {
            'Content-Type': 'application/json',
            'ACCESS-KEY': self.apikey,
            'ACCESS-TIMESTAMP': timestamp,
            'ACCESS-SIGN': signature
        }
        return headers

    def get_open_orders(self):
        # 出ている注文一覧を取得
        endpoint = '/v1/me/getchildorders'

        params = {
            'product_code': self.product_code,
            'child_order_state': 'ACTIVE',  # 出ている注文だけを取得
        }
        endpoint_for_header = endpoint + '?'
        for k, v in params.items():
            endpoint_for_header += k + '=' + v
            endpoint_for_header += '&'
        endpoint_for_header = endpoint_for_header[:-1]

        headers = self.header('GET', endpoint=endpoint_for_header, body="")

        response = requests.get(self.API_URL + endpoint,
                                headers=headers,
                                params=params)
        orders = response.json()
        return orders

    def get_complete_orders(self):
        # 出ている注文一覧を取得
        endpoint = '/v1/me/getchildorders'

        params = {
            'product_code': self.product_code,
            'child_order_state': 'COMPLETED',  # 出ている注文だけを取得
        }
        endpoint_for_header = endpoint + '?'
        for k, v in params.items():
            endpoint_for_header += k + '=' + v
            endpoint_for_header += '&'
        endpoint_for_header = endpoint_for_header[:-1]

        headers = self.header('GET', endpoint=endpoint_for_header, body="")

        response = requests.get(self.API_URL + endpoint,
                                headers=headers,
                                params=params)
        orders = response.json()
        return orders

    def get_current_price(self):
        # 現在の市場価格を取得
        endpoint = '/v1/ticker?product_code={self.product_code}'
        response = requests.get(self.API_URL + endpoint)
        price = float(response.json()['ltp'])
        return price

    def get_executions(self, count=100, before=None, after=None):
        endpoint = "/v1/me/getexecutions"

        params = {
            'product_code': self.product_code,
            'count': str(int(count)),  # 出ている注文だけを取得
        }
        if before is not None:
            params['before'] = str(before)
        if after is not None:
            params['after'] = str(after)
        endpoint_for_header = endpoint + '?'
        for k, v in params.items():
            endpoint_for_header += k + '=' + v
            endpoint_for_header += '&'
        endpoint_for_header = endpoint_for_header[:-1]

        headers = self.header('GET', endpoint=endpoint_for_header, body="")

        response = requests.get(self.API_URL + endpoint,
                                headers=headers,
                                params=params)
        executions = response.json()
        return executions

    def get_executions_all(self, count=100):
        executions = self.get_executions(count=count)
        before = executions[-1]["id"]
        while True:
            tmp_executions = self.get_executions(count=count, before=before)
            if len(tmp_executions) == 0:
                break
            executions += tmp_executions
            executions = sorted(executions, key=lambda x: x['exec_date'])
            before = executions[0]["id"]
            print(len(executions))
        return executions

    def calc_profits(self, executions):
        orders = sorted(executions, key=lambda x: x['exec_date'])
        profits = []
        # position  = {"side": "BUY", "size": 0, "price": 0, "exec_date": "2025-01-24T17:22:42.133"}
        current_positions = []
        date_format = "%Y-%m-%dT%H:%M:%S.%f"
        dates = []
        for order in orders:
            profit = self._checkout_position(order, current_positions)
            profits.append(profit)
            dates.append(datetime.strptime(order["exec_date"], date_format))
        return dates, profits
