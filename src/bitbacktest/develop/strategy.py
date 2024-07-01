import numpy as np
from ..strategy import Strategy

class MACForcusBuyStrategy(Strategy):
    def reset_param(self, param):
        self.short_window = param["short_window"]
        self.long_window = param["long_window"]
        self.profit = param["profit"]
        self.one_order_quantity = param["one_order_quantity"]
        self.count = 0

    def generate_signals(self, price):
        if self.count < (self.long_window + 1):
            return None  # Not enough data for calculation
        price_hist = self.market.get_price_hist()[-1 * (self.long_window + 1):]

        short_mavg = np.mean(price_hist[-self.short_window:])
        long_mavg = np.mean(price_hist[-self.long_window:])

        short_mavg_old = np.mean(price_hist[-1 * (self.short_window + 1):-1])
        long_mavg_old = np.mean(price_hist[-1 * (self.long_window + 1):-1])

        if short_mavg > long_mavg and short_mavg_old < long_mavg_old and long_mavg > long_mavg_old:
            return 'Buy'
        elif short_mavg < long_mavg and short_mavg_old > long_mavg_old:
            return 'Sell'
        else:
            return None

    def execute_order(self, price, signal):
        if signal == 'Buy':
            success = self.market.execute_order('Buy', self.one_order_quantity)
            if success:
                self.market.add_order("Sell", self.one_order_quantity, price * self.profit)
