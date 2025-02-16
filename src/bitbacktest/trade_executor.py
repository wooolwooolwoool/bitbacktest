import numpy as np
from tqdm import tqdm
from abc import ABC, abstractmethod
from typing import Literal
import os

class TradeExecutor(ABC):
    def __init__(self):
        self.dynamic = {}
        self.static = self.default_param

    def reset_param(self, param):
        self.static = param

    @abstractmethod
    def execute_trade(self, price, signal):
        pass

    @property
    def default_param(self):
        return {}

    def set_market(self, market):
        self.market = market

    def save_trade_count(self, result):
        """Save count of result trade to self.dynamic

        Args:
            result (bool): result of trade
        """
        if not 'trade_count_ok' in self.dynamic.keys():
            self.dynamic['trade_count_ok'] = 0
        if not 'trade_count_ng' in self.dynamic.keys():
            self.dynamic['trade_count_ng'] = 0
        if result:
            self.dynamic['trade_count_ok'] += 1
        else:
            self.dynamic['trade_count_ng'] += 1

class NormalExecutor(TradeExecutor):
    def reset_param(self, param):
        super().reset_param(param)

    @property
    def default_param(self):
        return {
            "one_order_quantity": 0.001,
        }

    def execute_trade(self, price, signal):
        if signal in ['Buy', "Sell"]:
            self.market.place_market_order(signal,
                                           self.static["one_order_quantity"])

class SpreadOrderExecutor(TradeExecutor):
    def reset_param(self, param):
        super().reset_param(param)
        self.dynamic['buy_count'] = 0

    @property
    def default_param(self):
        return {
            "one_order_quantity": 0.001,
            'buy_count_limit': 10
        }

    def execute_trade(self, price, signal):
        if signal == 'Buy' and self.dynamic['buy_count'] < self.static['buy_count_limit']:
            result = self.market.place_market_order(signal,
                                           self.static["one_order_quantity"])
            if result:
                self.dynamic['buy_count'] += 1
            self.save_trade_count(result)
        elif signal == 'Sell' and self.dynamic['buy_count'] > 0:
            result = self.market.place_market_order(signal,
                                           self.static["one_order_quantity"])
            if result:
                self.dynamic['buy_count'] -= 1
            self.save_trade_count(result)