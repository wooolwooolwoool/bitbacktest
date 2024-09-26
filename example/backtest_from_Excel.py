import sys
sys.path.append(".")
from src.bitbacktest.strategy import BollingerBandsStrategy
from src.bitbacktest.market import BacktestMarket
from src.bitbacktest.data_loader import read_prices_from_sheets


# Read data for test
price_data = read_prices_from_sheets("my_data/BitCoinPrice_interp.xlsx",
                        ["202405", "202406", "202407", "202408"], 5, use_cache=True)

# Set parameters
market = BacktestMarket(price_data)
strategy = BollingerBandsStrategy(market)
param = {
    'window_size': 337,  # 移動平均の期間
    'num_std_dev': 1.46,   # 標準偏差の倍率
    'buy_count_limit': 5,
    "one_order_quantity": 0.001
}
start_cash = 1e6

# Prepare Strategy
strategy.reset_all(param, start_cash)

# Execute backtest
portfolio_result = strategy.backtest(hold_params=["upper_band", "lower_band"])
print(portfolio_result)

# Plot graph
strategy.create_backtest_graph(backend="matplotlib")
