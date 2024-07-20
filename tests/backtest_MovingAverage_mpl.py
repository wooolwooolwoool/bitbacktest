import numpy as np
import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

import sys

sys.path.append(".")
from src.bitbacktest.strategy import MovingAverageCrossoverStrategy
from src.bitbacktest.market import BacktestMarket
from src.bitbacktest.data_generater import random_data

# Generate data for test
seed = 111
start_price = 1e7  # start price of bit coin
price_range = 0.001  # Range of price fluctuation
length = 60 * 24 * 7 * 4  # data length: 60 min * 24 hour * 7 days * 4weeks
price_data = random_data(start_price, price_range, length, seed)

# Set parameters
market = BacktestMarket(price_data)
strategy = MovingAverageCrossoverStrategy(market)
param = {
    "short_window": 360,
    "long_window": 720,
    "profit": 1.01,
    "one_order_quantity": 0.01
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
short_mean = np.convolve(price_data,
                         np.ones(short_window) / short_window,
                         mode="full")[short_window:len(price_data)]
long_mean = np.convolve(price_data,
                        np.ones(long_window) / long_window,
                        mode="full")[long_window:len(price_data)]

# グラフサイズを設定
fig = plt.figure(figsize=(16, 12))
gs = GridSpec(3, 1, height_ratios=[4, 1, 1], hspace=0.05)

# メインのグラフ
ax1 = fig.add_subplot(gs[0, 0])
ax2 = ax1.twinx()

# 価格データ
ax1.plot(range(len(price_data)), price_data, label="Price Data", color='blue')
# 長期移動平均
ax1.plot(np.array(range(len(long_mean))) + long_window,
         long_mean,
         label="long_mean",
         color='red')
# 短期移動平均
ax1.plot(np.array(range(len(short_mean))) + short_window,
         short_mean,
         label="short_mean",
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

# ポジションの履歴
# ax2.plot(range(len(strategy.backtest_history["total_pos_hist"])),
#          strategy.backtest_history["total_pos_hist"],
#          label="Position",
#          color='brown')

# 軸ラベルとタイトルの設定
ax1.set_ylabel("Price (JPY)")
ax2.set_ylabel("Position (BTC)")
ax1.legend(loc="upper left")
ax2.legend(loc="upper right")

# 長期移動平均と短期移動平均の差のグラフ
mean_diff = short_mean[:len(long_mean)] - long_mean
ax3 = fig.add_subplot(gs[2, 0])
ax3.plot(range(len(mean_diff)),
         mean_diff,
         label="Short Mean - Long Mean",
         color='brown')
ax3.axhline(y=0, color='black', linewidth=0.7, linestyle='--')
window = 500
diff_mean = np.convolve(mean_diff, np.ones(window) / window,
                        mode="full")[window:len(mean_diff)]
ax3.plot(range(len(diff_mean)), diff_mean, label="Mean", color='blue')

# 0が中心になるようにy軸の範囲を設定
y_min = np.min(mean_diff)
y_max = np.max(mean_diff)
y_abs_max = max(abs(y_min), abs(y_max))
ax3.set_ylim(-y_abs_max, y_abs_max)

ax3.set_xlabel("Sample number")
ax3.set_ylabel("Short Mean - Long Mean")
ax3.legend(loc="upper left")

# 全体のタイトル
fig.suptitle("Signals")

# フォントの設定
plt.rcParams['font.family'] = 'Meiryo'

# サブプロット間のスペースを調整
fig.subplots_adjust(hspace=0.1)

filename = "plot_signal_MA.png"
fig.savefig(filename)

print("Finish!!!")
