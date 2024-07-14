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
        self.dynamic["price_hist"] = np.append(self.dynamic["price_hist"], price)
        if len(self.dynamic["price_hist"]) < (self.static["long_window"] + 1):
            return None  # Not enough data for calculation

        short_mavg = np.mean(self.dynamic["price_hist"][-self.static["short_window"]:])
        long_mavg = np.mean(self.dynamic["price_hist"][-self.static["long_window"]:])

        short_mavg_old = np.mean(self.dynamic["price_hist"][-1 * (self.static["short_window"] + 1):-1])
        long_mavg_old = np.mean(self.dynamic["price_hist"][-1 * (self.static["long_window"] + 1):-1])

        self.dynamic["price_hist"] = np.delete(self.dynamic["price_hist"], 0)

        if short_mavg > long_mavg and short_mavg_old < long_mavg_old and long_mavg > long_mavg_old:
            return 'Buy'
        elif short_mavg < long_mavg and short_mavg_old > long_mavg_old:
            return 'Sell'
        else:
            return None

    def execute_trade(self, price, signal):
        if signal in ['Buy', "Sell"]:
            self.market.place_market_order(signal, self.static["one_order_quantity"])

class MACDStrategy(Strategy):
    def reset_param(self, param):
        super().reset_param(param)
        self.dynamic["count"] = 0
        self.dynamic["prices"] = None
        self.dynamic["emashort_values"] = None
        self.dynamic["emalong_values"] = None
        self.dynamic["macd_values"] = None
        self.dynamic["signal_line_values"] = None

    def _calculate_ema(self, current_price, previous_ema, window):
        alpha = 2 / (window + 1.0)
        return alpha * current_price + (1 - alpha) * previous_ema
    
    def generate_signals(self, price):
        if self.dynamic["prices"] is None:
            # Initialize
            emashort = emalong = price
            macd = signal_line = 0.0
        else:
            # calcurate EMA
            emashort = self._calculate_ema(price, self.dynamic["emashort_values"], self.static["short_window"])
            emalong = self._calculate_ema(price, self.dynamic["emalong_values"], self.static["long_window"])

            # calcurate MACD
            macd = emashort - emalong

            # calucurate signal line
            if self.dynamic["macd_values"] == 0:
                signal_line = macd
            else:
                signal_line = self._calculate_ema(macd, self.dynamic["signal_line_values"], self.static["signal_window"])

        self.dynamic["prices"] = price

        self.dynamic["emashort_values"] = emashort
        self.dynamic["emalong_values"] = emalong
        self.dynamic["macd_values_old"] = self.dynamic["macd_values"]
        self.dynamic["macd_values"] = macd
        self.dynamic["signal_line_values_old"] = self.dynamic["signal_line_values"]
        self.dynamic["signal_line_values"] = signal_line

        # generate signal
        signal = None
        if self.dynamic["macd_values_old"] is not None:
            if self.dynamic["macd_values_old"] <= self.dynamic["signal_line_values_old"] and macd > signal_line:
                signal = "Buy"
            elif self.dynamic["macd_values_old"] >= self.dynamic["signal_line_values_old"] and macd < signal_line:
                signal = "Sell"
        return signal
    
    def execute_trade(self, price, signal):
        if signal in ['Buy', "Sell"]:
            self.market.place_market_order(signal, self.static["one_order_quantity"])