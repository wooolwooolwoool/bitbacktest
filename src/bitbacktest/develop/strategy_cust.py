import numpy as np
from ..strategy import MACDStrategy, MovingAverageCrossoverStrategy


class MACForcusBuyStrategy(MovingAverageCrossoverStrategy):

    def execute_trade(self, price: float, signal: str):
        if signal == 'Buy':
            success = self.market.place_market_order(
                'Buy', self.static["one_order_quantity"])
            if success:
                self.market.place_limit_order(
                    "Sell", self.static["one_order_quantity"],
                    price * self.static["profit"])


class MACDForcusBuyStrategy(MACDStrategy):

    def execute_trade(self, price: float, signal: str):
        if signal == 'Buy':
            success = self.market.place_market_order(
                'Buy', self.static["one_order_quantity"])
            if success:
                self.market.place_limit_order(
                    "Sell", self.static["one_order_quantity"],
                    price * self.static["profit"])
