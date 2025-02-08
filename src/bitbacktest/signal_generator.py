import numpy as np
from tqdm import tqdm
from abc import ABC, abstractmethod
from typing import Literal
import os

class SignalGenerator(ABC):
    def __init__(self):
        self.dynamic = {}
        self.static = self.default_param

    def reset_param(self, param):
        self.static = param

    @property
    def default_param(self):
        return {}

    @abstractmethod
    def generate_signals(self, price):
        pass

class MovingAverageCrossoverSG(SignalGenerator):
    @property
    def default_param(self):
        return {
            "short_window": 50,
            "long_window": 100,
        }

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


class MACDSG(SignalGenerator):
    @property
    def default_param(self):
        return {
            "short_window": 50,
            "long_window": 100,
            "signal_window": 75
        }

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
            self.place_market_order(signal,
                                           self.static["one_order_quantity"])

class BollingerBandsSG(SignalGenerator):
    @property
    def default_param(self):
        return {
            "window_size": 300,
            "num_std_dev": 1.5,
            "reverse": 1
        }

    def reset_param(self, param):
        """BollingerBandsSignal
        param = {
            'window_size': window_size,  # 移動平均の期間
            'num_std_dev': num_std_dev,   # 標準偏差の倍率
            'reverse': reverse   # 売買を逆転 0 or 1
        }
        """
        super().reset_param(param)
        # 動的なパラメータは self.dynamic に保持
        self.dynamic = {
            'prices': np.array([], dtype=np.int32),          # 価格の履歴
            'mean': 0,             # 移動平均
            'squared_sum': 0,      # 二乗和（標準偏差計算用）
            'buy_count': 0         # 売買数
        }

    def generate_signals(self, price):
        # 現在価格をリストに追加
        self.dynamic['prices'] = np.append(self.dynamic['prices'], int(price))

        # ウィンドウサイズを超えた場合、古いデータを削除
        if len(self.dynamic['prices']) > self.static['window_size']:
            self.dynamic['prices'] = self.dynamic['prices'][1:]

        # 現在のウィンドウ内の価格に基づいて移動平均と標準偏差を計算
        if len(self.dynamic['prices']) >= 2:
            mean = np.mean(self.dynamic['prices'])  # 平均を計算
            std_dev = np.std(self.dynamic['prices'])  # 標準偏差を計算
        else:
            self.dynamic['upper_band'] = None
            self.dynamic['lower_band'] = None
            return "Hold"  # データが十分にない場合はシグナルを出さない

        # ボリンジャーバンドの上下限を計算
        self.dynamic['upper_band'] = mean + self.static['num_std_dev'] * std_dev
        self.dynamic['lower_band'] = mean - self.static['num_std_dev'] * std_dev

        if len(self.dynamic['prices']) < self.static['window_size']:
            return "Hold"  # データが十分にない場合はシグナルを出さない

        # シグナルを判定
        #print(self.static.keys(), "reverse" in self.static.keys(), os.environ["reverse"] == "1", str(self.static["reverse"]))
        if price > self.dynamic['upper_band']:
            if "reverse" in self.static.keys() and str(int(self.static["reverse"])) == "1":
                return "Buy"   # 上限を超えたら買いシグナル
            else:
                return "Sell"  # 上限を超えたら売りシグナル
        elif price < self.dynamic['lower_band']:
            if "reverse" in self.static.keys() and str(int(self.static["reverse"])) == "1":
                return "Sell"  # 下限を割ったら売りシグナル
            else:
                return "Buy"   # 下限を割ったら買いシグナル
        else:
            return "Hold"  # それ以外は保持