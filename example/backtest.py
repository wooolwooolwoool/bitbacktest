import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import datetime

from bitbacktest.strategy import MovingAverageCrossoverStrategy
from bitbacktest.backtester import Backtester
from bitbacktest.data_generater import random_data

# Generate data for test
seed = 111
start_price = 1e7           # start price of bit coin
price_range = 0.001         # Range of price fluctuation
length = 60 * 24 * 7 * 4   # data length
price_data = random_data(start_price, price_range, length, seed)

# Set parameters
strategy = MovingAverageCrossoverStrategy()
param = {"short_window": 30, "long_window": 100,  "profit": 1.01, "one_order_quantity": 0.01}
start_cash = 1e6

# Prepare Strategy
strategy.reset_all(param, start_cash)

# Execute backtest
portfolio_result = strategy.backtest(price_data)
print(portfolio_result)

# Plot result
print("Plotting result...")
buy_signals = [signal[1] for signal in strategy.backtest_history["signals"]["Buy"]]
buy_signals_pos = [signal[0] for signal in strategy.backtest_history["signals"]["Buy"]]
exe_buy_signals = [signal[1] for signal in strategy.backtest_history["execute_signals"]["Buy"]]
exe_buy_signals_pos = [signal[0] for signal in strategy.backtest_history["execute_signals"]["Buy"]]

short_window = param["short_window"]
long_window = param["long_window"]
short_mean = np.convolve(price_data, np.ones(short_window)/short_window, mode="full")[short_window:len(price_data)]
long_mean = np.convolve(price_data, np.ones(long_window)/long_window, mode="full")[long_window:len(price_data)]

fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(go.Scatter(x=np.array(range(len(price_data))), y=price_data, name="Price Data", mode="lines"))
fig.add_trace(go.Scatter(x=np.array(range(len(long_mean)))+long_window, y=long_mean, name="long_mean", mode="lines"))
fig.add_trace(go.Scatter(x=np.array(range(len(short_mean)))+short_window, y=short_mean, name="short_mean", mode="lines"))
fig.add_trace(go.Scatter(x=np.array(buy_signals_pos), y=buy_signals, name="buy_signals", mode="markers"))
fig.add_trace(go.Scatter(x=np.array(exe_buy_signals_pos), y=exe_buy_signals, name="exe_buy_signals", mode="markers"))
fig.add_trace(go.Scatter(x=np.array(range(len(strategy.backtest_history["total_pos_hist"]))), y=strategy.backtest_history["total_pos_hist"], name="Position"), secondary_y=True)

fig.update_xaxes(title="Sample number")
fig.update_yaxes(title="Price (JPY)")
fig.update_yaxes(title="Position (BTC)", secondary_y=True)
fig.update_layout(font={"family":"Meiryo"})
fig.update_layout(title="Signals")
fig.update_layout(showlegend=True)
fig.update_traces(marker=dict(size=12, line=dict(width=2, color='DarkSlateGrey'), opacity=0.8))

timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
filename = f"plot_{timestamp}.html"
fig.write_html(filename)

print(f"Saved graph to {filename}")