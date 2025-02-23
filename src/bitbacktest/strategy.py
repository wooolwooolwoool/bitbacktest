import numpy as np
from tqdm import tqdm
from typing import Literal
import os


class Strategy():
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
    def backtest(self, hold_params=[], axis=None):
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
        self.axis = axis
        for p in hold_params:
            self.hold_params[p] = []
        if not "TRADE_ENABLE" in os.environ.keys():
            os.environ["TRADE_ENABLE"] = "1"
        if not "ORDER_NUM_MAX" in os.environ.keys():
            os.environ["ORDER_NUM_MAX"] = "99999"

        for i in tqdm(range(len(self.market))):
            self.dynamic["count"] += 1
            self.market.set_current_index(self.dynamic["count"] - 1)
            price = self.market.get_current_price()
            signal = self.generate_signals(price)
            if self.trade_limiter():
                self.execute_trade(price, signal)
            self.market.check_order()
            self.market.save_history(price)
            for p in hold_params:
                if p in self.signal_generator.dynamic.keys():
                    self.hold_params[p].append(self.signal_generator.dynamic[p])
                elif p in self.trade_executor.dynamic.keys():
                    self.hold_params[p].append(self.trade_executor.dynamic[p])
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

    def create_backtest_graph(self, output_filename="plot_signal",
            backend: Literal['plotly', 'matplotlib', "holoviews"] ="matplotlib",
            save_graph: bool = True, width=1200, height=1000):
        graph_obj = None

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
        dates = self.market.dates
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
            if save_graph:
                fig.savefig(output_filename + ".png")
                print(f"save to {output_filename}.png")

            graph_obj = fig

        elif backend == "plotly":
            import plotly.graph_objects as go
            from plotly.subplots import make_subplots
            import numpy as np

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

            if save_graph:
                fig.write_html(output_filename + ".html")
                print(f"save to {output_filename}.html")

            graph_obj = fig
        elif backend == "holoviews":
            import holoviews as hv
            from holoviews import opts
            import numpy as np
            from bokeh.models import LinearAxis, Range1d
            from bokeh.models import DatetimeTickFormatter

            # Holoviewsの拡張機能を有効化
            hv.extension('bokeh')

            graphs = []
            axis_plot = {'Price': [], 'Value': [], "Additional": []}

            additional_max = None
            additional_min = None

            if len(self.hold_params.keys()) != 0:
                i = 0
                for k, v in self.hold_params.items():
                    if self.axis is not None and self.axis[i] == "Additional":
                        if additional_max is None:
                            additional_max = max(v)
                        else:
                            additional_max = max([max(v), additional_max])
                        if additional_min is None:
                            additional_min = min(v)
                        else:
                            additional_min = min([min(v), additional_min])
                    i += 1
            if additional_max is None:
                additional_min = 0
                additional_max = 1

            # フックを使って2軸を適用
            def modify_doc(plot, element):
                p = plot.state

                # 右Y軸を追加（重複しないようにチェック）
                if len(p.yaxis) < 2:
                    # 既存のラベルを変更
                    p.yaxis[0].axis_label = "BTC Price (JPY)"
                    p.y_range = Range1d(start=min(price_data), end=max(price_data))
                    # 右Y軸を設定（Total Value (JPY)）
                    p.extra_y_ranges = {}
                    p.extra_y_ranges["right"] = Range1d(start=min(value_hist), end=max(value_hist))
                    p.extra_y_ranges["right_2"] = Range1d(start=additional_min, end=additional_max)
                    right_axis = LinearAxis(y_range_name="right", axis_label="Total Value (JPY)")
                    p.add_layout(right_axis, 'right')
                    right_axis_2 = LinearAxis(y_range_name="right_2", axis_label="Additional")
                    p.add_layout(right_axis_2, 'right')

                # Total Valueの折れ線を右Y軸に関連付け
                for r in p.renderers:
                    if r.name == "Total Value":
                        r.y_range_name = "right"
                    elif r.name in axis_plot["Value"]:
                        r.y_range_name = "right"
                    elif r.name in axis_plot["Additional"]:
                        # print(r.name, axis_plot["Additional"])
                        r.y_range_name = "right_2"
                    else:
                        pass
                        # r.y_range_name = "left"

                # **背景にグリッド線を追加**
                p.xgrid.grid_line_color = "gray"  # X軸のグリッド線をグレーに
                p.ygrid.grid_line_color = "gray"  # Y軸のグリッド線をグレーに
                p.xgrid.grid_line_alpha = 0.5  # X軸グリッド線の透明度（0:透明 ～ 1:不透明）
                p.ygrid.grid_line_alpha = 0.5  # Y軸グリッド線の透明度

            # 価格データの折れ線グラフ
            graphs.append(hv.Curve((dates, price_data),
                    label="Price Data").opts(color='blue', yaxis='left',
                    ylim=(min(price_data), max(price_data))))

            # 総価値データの折れ線グラフ（第2Y軸）
            graphs.append(hv.Curve((dates, value_hist),
                    label="Total Value").opts(color='red', yaxis='right',
                    ylim=(min(value_hist), max(value_hist))))

            if len(self.hold_params.keys()) != 0:
                i = 0
                for k, v in self.hold_params.items():
                    if self.axis is not None:
                        axis_plot[self.axis[i]].append(k)
                    graphs.append(hv.Curve((dates, v),
                            label=k).opts(yaxis='left'))
                    i += 1

            if len(buy_signals_pos) != 0:
                # 買いシグナルのマーカー
                buy_signals_pos_dates = [dates[i] for i in buy_signals_pos]
                graphs.append(hv.Scatter((buy_signals_pos_dates, buy_signals), label="buy_signals").opts(
                    marker='circle', size=20, line_color='blue',
                    fill_color=None, alpha=0.5))

            if len(exe_buy_signals_pos) != 0:
                # 実行された買いシグナルのマーカー
                exe_buy_signals_pos_dates = [dates[i] for i in exe_buy_signals_pos]
                graphs.append(hv.Scatter((exe_buy_signals_pos_dates, exe_buy_signals), label="exe_buy_signals").opts(
                    marker='circle', size=20, line_color='gray', color='blue', alpha=0.5))

            if len(sell_signals_pos) != 0:
                # 売りシグナルのマーカー
                sell_signals_pos_dates = [dates[i] for i in sell_signals_pos]
                graphs.append(hv.Scatter((sell_signals_pos_dates, sell_signals), label="sell_signals").opts(
                    marker='circle', size=20, line_color='red',
                    fill_color=None, alpha=0.5))

            if len(exe_sell_signals_pos) != 0:
                # 実行された売りシグナルのマーカー
                exe_sell_signals_pos_dates = [dates[i] for i in exe_sell_signals_pos]
                graphs.append(hv.Scatter((exe_sell_signals_pos_dates, exe_sell_signals), label="exe_sell_signals").opts(
                    marker='circle', size=20, line_color='gray', color='red', alpha=0.5))

            # グラフを重ね合わせ
            overlay = graphs[0]
            for g in graphs[1:]:
                overlay *= g

            my_datetime_fmt = DatetimeTickFormatter(seconds="%H:%M:%S",
                                    minutes="%H:%M:%S",
                                    hours="%H:%M:%S",
                                    days="%Y/%m/%d",
                                    months="%Y/%m",
                                    years="%Y")
            # グラフの設定
            overlay = overlay.opts(
                # opts.Curve(yaxis='left', xlim=(dates[0], dates[-1]),
                #     ylim=(min(price_data), max(price_data)), hooks=[modify_doc], xformatter=my_datetime_fmt),  # 左側のY軸
                opts.Curve(yaxis='right', hooks=[modify_doc], xformatter=my_datetime_fmt),  # 右側のY軸
                # opts.Curve(yaxis='left', xlim=(dates[0], dates[-1]),
                #     ylim=(min(price_data), max(price_data)), hooks=[modify_doc], xformatter=my_datetime_fmt),  # 左側のY軸
                # opts.Curve(yaxis='left', xlim=(dates[0], dates[-1]),
                #     ylim=(min(price_data), max(price_data)), xformatter=my_datetime_fmt),  # 左側のY軸
                # opts.Curve(yaxis='left', xlim=(dates[0], dates[-1]),
                #     ylim=(min(price_data), max(price_data)), xformatter=my_datetime_fmt),  # 左側のY軸
                opts.Overlay(
                    title="Backtest Result",
                    legend_position='top_left',
                    fontsize={'title': 12, 'labels': 10},
                    width=width,
                    height=height
                )
            )

            if save_graph:
                # HTMLとして保存
                hv.save(overlay, output_filename + '.html')
                print(f"save to {output_filename}.html")

            graph_obj = overlay
        return graph_obj
