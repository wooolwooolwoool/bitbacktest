from bitbacktest.strategy import MovingAverageCrossoverStrategy
from bitbacktest.backtester import Backtester
from bitbacktest.data_generater import random_data

seed = 111
start_price = 1e7
price_range = 0.001
length = 60 * 24 * 7 * 16
price_data = random_data(start_price, price_range, length, seed)

params = [{"short_window": 30, "long_window": 100, "profit": 1.01, "one_order_quantity": 0.01},
          {"short_window": 30, "long_window": 500, "profit": 1.01, "one_order_quantity": 0.01},
          {"short_window": 30, "long_window": 1000, "profit": 1.01, "one_order_quantity": 0.01},
          {"short_window": 60, "long_window": 100, "profit": 1.01, "one_order_quantity": 0.01},
          {"short_window": 60, "long_window": 500, "profit": 1.01, "one_order_quantity": 0.01},
          {"short_window": 60, "long_window": 1000, "profit": 1.01, "one_order_quantity": 0.01}]
start_cash = 1e6

strategy = MovingAverageCrossoverStrategy()
backtester = Backtester(strategy)

backtester.grid_backtest(price_data, params, start_cash)
backtester.print_grid_backtest_result()
