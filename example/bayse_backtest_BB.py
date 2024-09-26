
import sys
sys.path.append(".")
from src.bitbacktest.market import BacktestMarket
from src.bitbacktest.backtester import BayesianBacktester
from src.bitbacktest.data_loader import read_prices_from_sheets
from src.bitbacktest.strategy import BollingerBandsStrategy

from skopt.space import Integer, Real, Categorical

# Read data for test
price_data = read_prices_from_sheets("my_data/BitCoinPrice_interp.xlsx",
                        ["202405", "202406", "202407", "202408"], 5, use_cache=True)

# Set parameters
target_params = {
    'window_size': Integer(20, 1000),  # 移動平均の期間
    'num_std_dev': Real(1,2),   # 標準偏差の倍率
    'buy_count_limit': 999,
    "one_order_quantity": 0.001
}
start_cash = 1e6

# Prepare Strategy and Backtester
market = BacktestMarket(price_data)
strategy = BollingerBandsStrategy(market)
backtester = BayesianBacktester(strategy)

# Execute backtest
best_value, best_param = backtester.backtest(target_params, start_cash, n_calls=50)

strategy.reset_all(best_param, start_cash)
strategy.backtest(hold_params=["upper_band", "lower_band"])

# Plot graph
strategy.create_backtest_graph(backend="matplotlib")