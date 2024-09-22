import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

try:
    from bitbacktest.strategy import MovingAverageCrossoverStrategy, MACDStrategy
    from bitbacktest.market import BacktestMarket
    from bitbacktest.data_generater import random_data
except:
    import sys
    sys.path.append(".")
    from src.bitbacktest.strategy import MovingAverageCrossoverStrategy, MACDStrategy
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
strategy = MACDStrategy(market)
param = {
    "short_window": 12 * 60,
    "long_window": 26 * 60,
    "signal_window": 9 * 60,
    "one_order_quantity": 0.001
}
start_cash = 1e6

# Prepare Strategy
strategy.reset_all(param, start_cash)

# Execute backtest
portfolio_result = strategy.backtest(hold_params=["macd_values", "signal_line_values"])
print(portfolio_result)

# Plot graph
strategy.create_backtest_graph(backend="matplotlib")
