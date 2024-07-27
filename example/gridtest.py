try:
          from bitbacktest.strategy import MovingAverageCrossoverStrategy
          from bitbacktest.market import BacktestMarket
          from bitbacktest.backtester import Backtester
          from bitbacktest.data_generater import random_data
except:
          import sys
          sys.path.append(".")
          from src.bitbacktest.strategy import MovingAverageCrossoverStrategy
          from src.bitbacktest.market import BacktestMarket
          from bitbacktest.backtester import Backtester
          from src.bitbacktest.data_generater import random_data

# Generate data for test
seed = 111
start_price = 1e7  # start price of bit coin
price_range = 0.001  # Range of price fluctuation
length = 60 * 24 * 7 * 4  # data length
price_data = random_data(start_price, price_range, length, seed)

# Set parameters
params = [
    {
        "short_window": 30,
        "long_window": 120,
        "profit": 1.01,
        "one_order_quantity": 0.01
    },
    {
        "short_window": 30,
        "long_window": 720,
        "profit": 1.01,
        "one_order_quantity": 0.01
    },
    {
        "short_window": 30,
        "long_window": 1440,
        "profit": 1.01,
        "one_order_quantity": 0.01
    },
    {
        "short_window": 60,
        "long_window": 120,
        "profit": 1.01,
        "one_order_quantity": 0.01
    },
    {
        "short_window": 60,
        "long_window": 720,
        "profit": 1.01,
        "one_order_quantity": 0.01
    },
    {
        "short_window": 60,
        "long_window": 1440,
        "profit": 1.01,
        "one_order_quantity": 0.01
    },
]
start_cash = 1e6

# Prepare Strategy and Backtester
market = BacktestMarket(price_data)
strategy = MovingAverageCrossoverStrategy(market)
backtester = Backtester(strategy)

# Execute backtest
backtester.backtest(params, start_cash)
# Print result
backtester.print_backtest_result()
