import sys, os
sys.path.append(".")
from src.bitbacktest.strategy import BacktestStrategy

from src.bitbacktest.signal_generator import BollingerBandsSG
from src.bitbacktest.trade_executor import SpreadOrderExecutor
from src.bitbacktest.market import BacktestMarket
from src.bitbacktest.data_generater import random_data
from src.bitbacktest.backtester import BayesianBacktester
from skopt.space import Integer, Real, Categorical

# Generate data for test
seed = 111
start_price = 1e7  # start price of bit coin
price_range = 0.001  # Range of price fluctuation
length = 60 * 24 * 7 * 1  # data length: 60 min * 24 hour * 7 days * 4weeks
price_data = random_data(start_price, price_range, length, seed)

os.environ["ORDER_NUM_MAX"] = "10"
# Set parameters
target_params = {
    'window_size': Integer(10, 300),
    'num_std_dev': Real(1.0, 5.0),
    'reverse': Integer(0, 1),
    "buy_count_limit": 10,
    "one_order_quantity": 0.001
}
start_cash = 2e5
# Prepare Strategy and Backtester
market = BacktestMarket(price_data, fee_rate=0)
signal_gene = BollingerBandsSG()
trade_exec = SpreadOrderExecutor()

strategy = BacktestStrategy(market, signal_gene, trade_exec)

if False:
    # execute optimize
    backtester = BayesianBacktester(strategy)

    # Execute backtest
    best_value, best_param = backtester.backtest(target_params, start_cash, start_coin=0.01, n_calls=10)
else:
    best_param = {
        'window_size': 300,
        'num_std_dev': 1.37,
        "buy_count_limit": 10,
        'reverse': 1,
        "one_order_quantity": 0.002
    }

strategy.reset_all(best_param, start_cash)
portfolio_result = strategy.backtest(hold_params=["upper_band", "lower_band"])
print(portfolio_result)
print(f"Profit rate: {portfolio_result['total_value'] / start_cash}")

# Plot graph
# strategy.create_backtest_graph(backend="matplotlib")
# strategy.create_backtest_graph(backend="plotly")
strategy.create_backtest_graph(backend="holoviews")

