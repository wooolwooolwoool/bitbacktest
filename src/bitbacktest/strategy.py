import numpy as np
from tqdm import tqdm
from abc import ABC, abstractmethod
from typing import Literal
import os

from .market import *


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
            str: Trade signal (ex. "Buy", "Sell" or "Hold")
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

    def trade_limiter(self) -> bool:
        orders = self.market.get_open_orders()
        ret = (os.environ["TRADE_ENABLE"] == "1"
               and int(os.environ["ORDER_NUM_MAX"]) > len(orders))
        return ret

    def backtest(self, hold_params=[]):
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
        self.hold_params = {}
        for p in hold_params:
            self.hold_params[p] = []
        if not "TRADE_ENABLE" in os.environ.keys():
            os.environ["TRADE_ENABLE"] = "1"
        if not "ORDER_NUM_MAX" in os.environ.keys():
            os.environ["ORDER_NUM_MAX"] = "99999"

        for _ in tqdm(range(len(self.market))):
            self.dynamic["count"] += 1
            self.market.set_current_index(self.dynamic["count"] - 1)
            price = self.market.get_current_price()
            signal = self.generate_signals(price)
            if self.trade_limiter():
                self.execute_trade(price, signal)
            self.market.check_order()
            self.market.save_history(price)
            for p in hold_params:
                self.hold_params[p].append(self.dynamic[p]) 
        return self.market.portfolio

    @property
    def backtest_history(self):
        return self.market.hist
    
    def create_backtest_graph(self, output_filename="plot_signal", backend: Literal['plotly', 'matplotlib'] ="matplotlib"):
        
        buy_signals = [
            signal[1] for signal in self.backtest_history["signals"]["Buy"]
        ]
        buy_signals_pos = [
            signal[0] for signal in self.backtest_history["signals"]["Buy"]
        ]
        sell_signals = [
            signal[1] for signal in self.backtest_history["signals"]["Sell"]
        ]
        sell_signals_pos = [
            signal[0] for signal in self.backtest_history["signals"]["Sell"]
        ]
        exe_buy_signals = [
            signal[1] for signal in self.backtest_history["execute_signals"]["Buy"]
        ]
        exe_buy_signals_pos = [
            signal[0] for signal in self.backtest_history["execute_signals"]["Buy"]
        ]
        exe_sell_signals = [
            signal[1] for signal in self.backtest_history["execute_signals"]["Sell"]
        ]
        exe_sell_signals_pos = [
            signal[0] for signal in self.backtest_history["execute_signals"]["Sell"]
        ]
        price_data = self.market.data
        value_hist = self.market.hist["total_value_hist"]

        if backend == "matplotlib":
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')
            
            fig = plt.figure(figsize=(16, 9))
            ax1 = fig.add_subplot()
            ax2 = ax1.twinx()
            ax1.plot(range(len(price_data)), price_data, label="Price Data", color='blue', alpha=0.8)
            
            ax2.plot(range(len(value_hist)), value_hist, label="Total value", color='red', alpha=0.8)
            if len(self.hold_params.keys()) != 0:
                ax3 = ax1.twinx()
                for k, v in self.hold_params.items():
                    ax3.plot(range(len(v)), v, label=k, alpha=0.8)
                ax3.yaxis.set_visible(False)
            ax1.scatter(buy_signals_pos,
                        buy_signals,
                        label="buy_signals",
                        color='c',
                        marker='o',
                        s=100,
                        edgecolors='DarkSlateGrey',
                        alpha=0.4)
            ax1.scatter(exe_buy_signals_pos,
                        exe_buy_signals,
                        label="exec_buy_signals",
                        color='c',
                        marker='o',
                        s=100,
                        edgecolors='DarkSlateGrey',
                        alpha=0.8)
            ax1.scatter(sell_signals_pos,
                        sell_signals,
                        label="sell_signals",
                        color='m',
                        marker='o',
                        s=100,
                        edgecolors='DarkSlateGrey',
                        alpha=0.4)
            ax1.scatter(exe_sell_signals_pos,
                        exe_sell_signals,
                        label="exec_sell_signals",
                        color='m',
                        marker='o',
                        s=100,
                        edgecolors='DarkSlateGrey',
                        alpha=0.8)
                       
            ax1.set_ylabel("BTC Price (JPY)")
            ax2.set_ylabel("Total Value (JPY)")

            plt.xlim(0, len(price_data))

            fig.legend(loc="upper right")
            fig.savefig(output_filename + ".png")

            print(f"save to {output_filename}.png")

        elif backend == "plotly":
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(
                go.Scatter(x=np.array(range(len(price_data))),
                           y=price_data,
                           name="Price Data",
                           mode="lines"))

            if len(self.hold_params.keys()) != 0:
                for k, v in self.hold_params.items():
                    fig.add_trace(
                        go.Scatter(x=np.array(range(len(v))),
                                y=v, name=k, mode="lines"))

            fig.add_trace(go.Scatter(x=np.array(
                range(len(value_hist))), y=value_hist, name="Total_value"),
                          secondary_y=True)

            fig.add_trace(
                go.Scatter(x=np.array(buy_signals_pos),
                           y=buy_signals,
                           name="buy_signals",
                           mode="markers", marker_symbol="circle-open"))
            fig.add_trace(
                go.Scatter(x=np.array(exe_buy_signals_pos),
                           y=exe_buy_signals,
                           name="exe_buy_signals",
                           mode="markers", marker_symbol="circle"))
            
            fig.add_trace(
                go.Scatter(x=np.array(sell_signals_pos),
                           y=sell_signals,
                           name="sell_signals",
                           mode="markers", marker_symbol="circle-open"))
            fig.add_trace(
                go.Scatter(x=np.array(exe_sell_signals_pos),
                           y=exe_sell_signals,
                           name="exe_sell_signals",
                           mode="markers", marker_symbol="circle"))
            
            fig.update_xaxes(title="Sample number")
            fig.update_yaxes(title="BTC Price (JPY)")
            fig.update_yaxes(title="Total Value (BTC)", secondary_y=True)
            fig.update_layout(font={"family": "Meiryo"})
            fig.update_layout(title="Signals")
            fig.update_layout(showlegend=True)
            fig.update_traces(marker=dict(
                size=12, line=dict(width=2, color='DarkSlateGrey'), opacity=0.8))

            fig.write_html(output_filename + ".html")
            
            print(f"save to {output_filename}.html")
        return


class MovingAverageCrossoverStrategy(Strategy):

    def reset_param(self, param):
        super().reset_param(param)
        self.dynamic["price_hist"] = np.array([])

    def generate_signals(self, price):
        self.dynamic["price_hist"] = np.append(self.dynamic["price_hist"],
                                               price)
        if len(self.dynamic["price_hist"]) < (self.static["long_window"] + 1):
            return "Hold"  # Not enough data for calculation

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
            return "Hold"

    def execute_trade(self, price, signal):
        if signal in ['Buy', "Sell"]:
            self.market.place_market_order(signal,
                                           self.static["one_order_quantity"])


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
            emashort = self._calculate_ema(price,
                                           self.dynamic["emashort_values"],
                                           self.static["short_window"])
            emalong = self._calculate_ema(price,
                                          self.dynamic["emalong_values"],
                                          self.static["long_window"])

            # calcurate MACD
            macd = emashort - emalong

            # calucurate signal line
            if self.dynamic["macd_values"] == 0:
                signal_line = macd
            else:
                signal_line = self._calculate_ema(
                    macd, self.dynamic["signal_line_values"],
                    self.static["signal_window"])

        self.dynamic["prices"] = price

        self.dynamic["emashort_values"] = emashort
        self.dynamic["emalong_values"] = emalong
        self.dynamic["macd_values_old"] = self.dynamic["macd_values"]
        self.dynamic["macd_values"] = macd
        self.dynamic["signal_line_values_old"] = self.dynamic[
            "signal_line_values"]
        self.dynamic["signal_line_values"] = signal_line

        # generate signal
        signal = "Hold"
        if self.dynamic["macd_values_old"] is not None:
            if self.dynamic["macd_values_old"] <= self.dynamic[
                    "signal_line_values_old"] and macd > signal_line:
                signal = "Buy"
            elif self.dynamic["macd_values_old"] >= self.dynamic[
                    "signal_line_values_old"] and macd < signal_line:
                signal = "Sell"
        return signal

    def execute_trade(self, price, signal):
        if signal in ['Buy', "Sell"]:
            self.market.place_market_order(signal,
                                           self.static["one_order_quantity"])

class BollingerBandsStrategy(Strategy):
        
    def reset_param(self, param):
        """BollingerBandsSignal
        param = {
            'window_size': window_size,  # 移動平均の期間
            'num_std_dev': num_std_dev   # 標準偏差の倍率
        }
        """
        super().reset_param(param)
        # 動的なパラメータは self.dynamic に保持
        self.dynamic = {
            'prices': np.array([]),          # 価格の履歴
            'mean': 0,             # 移動平均
            'squared_sum': 0,      # 二乗和（標準偏差計算用）
            'buy_count': 0         # 売買数
        }

    def generate_signals(self, price):
        # 現在価格をリストに追加
        self.dynamic['prices'] = np.append(self.dynamic['prices'], price)

        # ウィンドウサイズを超えた場合、古いデータを削除
        if len(self.dynamic['prices']) > self.static['window_size']:
            self.dynamic['prices'] = self.dynamic['prices'][1:]

        # 現在のウィンドウ内の価格に基づいて移動平均と標準偏差を計算
        if len(self.dynamic['prices']) >= self.static['window_size']:
            mean = np.mean(self.dynamic['prices'])  # 平均を計算
            std_dev = np.std(self.dynamic['prices'])  # 標準偏差を計算
        else:
            self.dynamic['upper_band'] = None
            self.dynamic['lower_band'] = None
            return "Hold"  # データが十分にない場合はシグナルを出さない

        # ボリンジャーバンドの上下限を計算
        self.dynamic['upper_band'] = mean + self.static['num_std_dev'] * std_dev
        self.dynamic['lower_band'] = mean - self.static['num_std_dev'] * std_dev

        # シグナルを判定
        if price > self.dynamic['upper_band']:
            return "Sell"  # 上限を超えたら売りシグナル
        elif price < self.dynamic['lower_band']:
            return "Buy"   # 下限を割ったら買いシグナル
        else:
            return "Hold"  # それ以外は保持

    def execute_trade(self, price, signal):
        if signal == 'Buy' and self.dynamic['buy_count'] < self.static['buy_count_limit']:
            result = self.market.place_market_order(signal,
                                           self.static["one_order_quantity"])
            if result:
                self.dynamic['buy_count'] += 1
        elif signal == 'Sell' and self.dynamic['buy_count'] > 0:
            result = self.market.place_market_order(signal,
                                           self.static["one_order_quantity"])
            if result:
                self.dynamic['buy_count'] -= 1
            
