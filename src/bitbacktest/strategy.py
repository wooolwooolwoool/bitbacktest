import numpy as np
from tqdm import tqdm
from abc import ABC, abstractmethod
from typing import Literal
import os


class Strategy(ABC):
    """Trading Strategy

    Args:
        ABC (_type_): _description_
    """

    def __init__(self, market, signal_generator, trade_executor):
        self.market = market
        self.signal_generator = signal_generator
        self.trade_executor = trade_executor
        self.trade_executor.set_market(self.market)
        self.dynamic = {}

    @property
    def default_param(self) -> dict:
        return {
            **self.signal_generator.default_param,
            **self.trade_executor.default_param,
        }

    def get_all_dynamic(self) -> dict:
        self.dynamic = {
            **self.dynamic,
            **self.signal_generator.dynamic,
            **self.trade_executor.dynamic
        }
        return self.dynamic

    def set_all_dynamic(self) -> dict:
        self.signal_generator.dynamic = self.dynamic
        self.trade_executor.dynamic = self.dynamic

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
        self.signal_generator.reset_param(param)
        self.trade_executor.reset_param(param)

    def generate_signals(self, price: float) -> str:
        """Generate Trade Signal
        Generate trade signal based on price, parameters, etc.
        Implemente The logic to generate signals.

        Args:
            price (float): Current bitcoin price

        Returns:
            str: Trade signal (ex. "Buy", "Sell" or "Hold")
        """
        return self.signal_generator.generate_signals(price)

    def execute_trade(self, price: float, signal: str):
        """Executing an trade Based on a Signal
        Implements the logic to execute an order

        Args:
            price (float): Current bitcoin price
            signal (str): Trade Signal
        """
        self.trade_executor.execute_trade(price, signal)

    def trade_limiter(self) -> bool:
        orders = self.market.get_open_orders()
        ret = (os.environ["TRADE_ENABLE"] == "1"
               and int(os.environ["ORDER_NUM_MAX"]) > len(orders))
        return ret

class BacktestStrategy(Strategy):
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
                self.hold_params[p].append(self.get_all_dynamic()[p])
        return self.market.portfolio

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
        value_hist = self.backtest_history["total_value_hist"]

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



