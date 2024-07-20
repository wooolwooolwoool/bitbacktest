import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

import sys

sys.path.append(".")
from src.bitbacktest.strategy import MACDStrategy
from src.bitbacktest.market import BacktestMarket
from src.bitbacktest.data_generater import random_data


class MACDForcusBuyStrategy(MACDStrategy):

    def execute_trade(self, price: float, signal: str):
        if signal == 'Buy' and 0 > self.dynamic["macd_values"]:
            success = self.market.place_market_order(
                'Buy', self.static["one_order_quantity"])
            if success:
                self.market.place_limit_order(
                    "Sell", self.static["one_order_quantity"],
                    price * self.static["profit"])


# Generate data for test
seed = 111
start_price = 1e7  # start price of bit coin
price_range = 0.001  # Range of price fluctuation
length = 60 * 24 * 7 * 4  # data length: 60 min * 24 hour * 7 days * 4weeks
price_data = random_data(start_price, price_range, length, seed)

# Set parameters
market = BacktestMarket(price_data)
strategy = MACDForcusBuyStrategy(market)
param = {
    "short_window": 120,
    "long_window": 360,
    "signal_window": 240,
    "one_order_quantity": 0.01,
    "profit": 1.01
}
start_cash = 1e6

# Prepare Strategy
strategy.reset_all(param, start_cash)

# Execute backtest
portfolio_result = strategy.backtest()
print(portfolio_result)

# Plot result
print("Plotting result...")
buy_signals = [
    signal[1] for signal in strategy.backtest_history["signals"]["Buy"]
]
buy_signals_pos = [
    signal[0] for signal in strategy.backtest_history["signals"]["Buy"]
]
exe_buy_signals = [
    signal[1] for signal in strategy.backtest_history["execute_signals"]["Buy"]
]
exe_buy_signals_pos = [
    signal[0] for signal in strategy.backtest_history["execute_signals"]["Buy"]
]

short_window = param["short_window"]
long_window = param["long_window"]
signal_window = param["signal_window"]


def ema(data, window):
    alpha = 2 / (window + 1.0)
    ema_data = np.zeros_like(data)
    ema_data[0] = data[0]
    for i in range(1, len(data)):
        ema_data[i] = alpha * data[i] + (1 - alpha) * ema_data[i - 1]
    return ema_data


short_window = param["short_window"]
long_window = param["long_window"]
signal_window = param["signal_window"]

buy_signals = [
    signal[1] for signal in strategy.backtest_history["signals"]["Buy"]
]
buy_signals_pos = [
    signal[0] for signal in strategy.backtest_history["signals"]["Buy"]
]
exe_buy_signals = [
    signal[1] for signal in strategy.backtest_history["execute_signals"]["Buy"]
]
exe_buy_signals_pos = [
    signal[0] for signal in strategy.backtest_history["execute_signals"]["Buy"]
]

emashort = ema(price_data, short_window)
emalong = ema(price_data, long_window)
macd = emashort - emalong
signal_line = ema(macd, signal_window)

fig = plt.figure(figsize=(32, 18))
gs = GridSpec(2, 1, height_ratios=[4, 1], hspace=0.05)

ax1 = fig.add_subplot(gs[0, 0])
ax2 = ax1.twinx()

# 価格データ
ax1.plot(range(len(price_data)), price_data, label="Price Data", color='blue')
# MACD
ax2.plot(range(len(macd)), macd, label="MACD", color='red')
# シグナルライン
ax2.plot(range(len(signal_line)),
         signal_line,
         label="Signal Line",
         color='green')
# 買いシグナル
ax1.scatter(buy_signals_pos,
            buy_signals,
            label="buy_signals",
            color='purple',
            marker='o',
            s=100,
            edgecolors='DarkSlateGrey',
            alpha=0.8)
# 実行買いシグナル
# ax1.scatter(exe_buy_signals_pos,
#             exe_buy_signals,
#             label="exe_buy_signals",
#             color='orange',
#             marker='o',
#             s=100,
#             edgecolors='DarkSlateGrey',
#             alpha=0.8)

# MACDとSignal lineの差のグラフ
macd_diff = macd - signal_line
ax3 = fig.add_subplot(gs[1, 0])
ax3.plot(range(len(macd_diff)),
         macd_diff,
         label="MACD - Signal Line",
         color='brown')
ax3.set_xlabel("Sample number")
ax3.set_ylabel("MACD - Signal Line")
ax3.legend(loc="upper left")
# 0が中心になるようにy軸の範囲を設定
y_min = np.min(macd_diff)
y_max = np.max(macd_diff)
y_abs_max = max(abs(y_min), abs(y_max))
ax3.set_ylim(-y_abs_max, y_abs_max)
ax3.axhline(y=0, color='black', linewidth=0.7, linestyle='--')  # y=0の線を追加

# 軸ラベルとタイトルの設定
ax1.set_xlabel("Sample number")
ax1.set_ylabel("Price (JPY)")
ax2.set_ylabel("MACD / Signal Line")
fig.suptitle("Signals")
ax1.legend(loc="upper left")
ax2.legend(loc="upper right")

# フォントの設定
plt.rcParams['font.family'] = 'Meiryo'

#plt.show()
filename = "plot_signal.png"
fig.savefig(filename)
