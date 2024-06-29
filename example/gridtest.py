from bitbacktest.strategy import MovingAverageCrossoverStrategy
from bitbacktest.backtester import Backtester
from bitbacktest.data_generater import random_data

# Generate data for test
seed = 111
start_price = 1e7           # start price of bit coin
price_range = 0.001         # Range of price fluctuation
length = 60 * 24 * 7 * 16   # data length
price_data = random_data(start_price, price_range, length, seed)

# Set parameters
params = [{"short_window": 30, "long_window": 100,  "profit": 1.01, "one_order_quantity": 0.01},
          {"short_window": 30, "long_window": 500,  "profit": 1.01, "one_order_quantity": 0.01},
          {"short_window": 30, "long_window": 1000, "profit": 1.01, "one_order_quantity": 0.01},
          {"short_window": 60, "long_window": 100,  "profit": 1.01, "one_order_quantity": 0.01},
          {"short_window": 60, "long_window": 500,  "profit": 1.01, "one_order_quantity": 0.01},
          {"short_window": 60, "long_window": 1000, "profit": 1.01, "one_order_quantity": 0.01}]
start_cash = 1e6

# Prepare Strategy and Backtester
strategy = MovingAverageCrossoverStrategy()
backtester = Backtester(strategy)

# Execute backtest
backtester.grid_backtest(price_data, params, start_cash)
# Print result
backtester.print_grid_backtest_result()
