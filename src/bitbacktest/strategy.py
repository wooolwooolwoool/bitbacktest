import numpy as np
import tqdm
from abc import ABC, abstractmethod

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
    """Trading Strategy

    Args:
        ABC (_type_): _description_
    """
    def __init__(self, market: Market):
        self.market = market
        self.count = 0

    @abstractmethod
    def reset_param(self, param: dict):
        """Reset parameter
        Reset parameters. Implement the process of setting parameters in this method.

        Args:
            param (dict): parameter
        """
        pass

    def reset_all(self, param: dict, start_cash: int):
        """Reset parameter and portfolio
        Must be called before the backtest is executed.

        Args:
            param (dict): parameter
            start_cash (int): start cash
        """
        self.count = 0
        self.reset_param(param)
        self.market.reset_portfolio(start_cash)

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
    def execute_order(self, price, signal):
        """Executing an Order Based on a Signal
        Implements the logic to execute an order 

        Args:
            price (_type_): Current bitcoin price
            signal (_type_): Trade Signal
        """
        pass
    
    def backtest(self):
        """Running a back test
        Backtest flow is
        1. get current price
        2. generate_signals() method
        3. execute_order() method
        4. save data and go to next

        Returns:
            _type_: Result of backtest
        """
        self.count = 0
        self.market.set_current_index(0)
        for _ in tqdm(range(len(self.market))):
            self.market.set_current_index(self.count)
            price = self.market.get_current_price()            
            signal = self.generate_signals(price)
            self.execute_order(price, signal)
            self.market.check_order()
            self.market.save_history(price)
            self.count += 1
        return self.market.portfolio
    
    @property
    def backtest_history(self):
        return self.market.hist

class MovingAverageCrossoverStrategy(Strategy):
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

        if short_mavg > long_mavg and short_mavg_old < long_mavg_old:
            return 'Buy'
        elif short_mavg < long_mavg and short_mavg_old > long_mavg_old:
            return 'Sell'
        else:
            return None

    def execute_order(self, price, signal):
        if signal in ['Buy', "Sell"]:
            self.market.execute_order(signal, self.one_order_quantity)
