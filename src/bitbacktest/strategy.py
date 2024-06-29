import numpy as np
import tqdm
from abc import ABC, abstractmethod

from .oder import *
from .market import *


def in_notebook():
    try:
        from IPython import get_ipython
        if 'IPKernelApp' not in get_ipython().config:
            return False
    except:
        return False
    return True

if in_notebook():
    from tqdm.notebook import tqdm
else:
    from tqdm import tqdm


class Strategy(ABC):
    def __init__(self):
        market = DammyMarket()
        self.order_execution = OrderExecution(market)
        self.count = 0

    @abstractmethod
    def reset_param(self, param: dict):
        pass

    def reset_all(self, param: dict, start_cash: int):
        self.count = 0
        self.reset_param(param)
        self.order_execution.reset_portfolio(start_cash)

    @abstractmethod
    def generate_signals(self, price: float) -> str:
        return ""


    @abstractmethod
    def execute_order(self, price, signal):
        pass
    
    def backtest(self, price_data: np.ndarray):
        self.market = BacktestMarket(price_data)
        self.order_execution.set_market(self.market)
        for price in tqdm(self.market.get_data(), total=len(self.market.get_data())):
            self.market.set_current_index(self.count)
            signal = self.generate_signals(price)
            self.execute_order(price, signal)
            self.order_execution.check_order()
            self.order_execution.save_history(price)
            self.count += 1
        return self.order_execution.portfolio
    
    @property
    def backtest_history(self):
        return self.order_execution.hist

class MovingAverageCrossoverStrategy(Strategy):
    def __init__(self):
        super().__init__()

    def reset_param(self, param):
        self.short_window = param["short_window"]
        self.long_window = param["long_window"]
        self.profit = param["profit"]
        self.one_order_quantity = param["one_order_quantity"]
        self.count = 0

    def generate_signals(self, price):
        if self.count < (self.long_window + 1):
            return None  # Not enough data for calculation
        price_hist = self.market.get_data()[-1 * (self.long_window + 1):]

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
            self.order_execution.hist["signals"]['Buy'].append((self.count, price))
            success = self.order_execution.execute_order('Buy', self.one_order_quantity)
            if success:
                self.order_execution.hist["execute_signals"]['Buy'].append((self.count, price))
                self.order_execution.add_order("Sell", self.one_order_quantity, price * self.profit)
