try:
    from bitbacktest.strategy import MACDStrategy
    from bitbacktest.market import BacktestMarket
    from bitbacktest.backtester import BayesianBacktester
    from bitbacktest.data_generater import random_data
except:
    import sys
    sys.path.append(".")
    from src.bitbacktest.strategy import MACDStrategy
    from src.bitbacktest.market import BacktestMarket
    from src.bitbacktest.backtester import BayesianBacktester
    from src.bitbacktest.data_generater import random_data

from skopt.space import Integer, Real, Categorical

# Generate data for test
seed = 111
start_price = 1e7  # start price of bit coin
price_range = 0.001  # Range of price fluctuation
length = 60 * 24 * 7 * 4  # data length
price_data = random_data(start_price, price_range, length, seed)

# Set parameters
target_params = {
    "short_window": Integer(12, 180, name='short_window'),
    "long_window": Integer(48, 720, name='long_window'),
    "signal_window": Integer(6, 180, name='signal_window'),
    "profit": Real(1.005, 1.01),
    "one_order_quantity": 0.001
}
start_cash = 1e6

# Prepare Strategy and Backtester
market = BacktestMarket(price_data)
strategy = MACDStrategy(market)
backtester = BayesianBacktester(strategy)

# Execute backtest
best_value, best_param = backtester.backtest(target_params, start_cash, n_calls=10)

strategy.reset_all(best_param, start_cash)
strategy.backtest(hold_params=["macd_values", "signal_line_values"])

# Plot graph
strategy.create_backtest_graph(backend="matplotlib")