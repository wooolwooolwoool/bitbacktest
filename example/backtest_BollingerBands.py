import sys
sys.path.append(".")
from src.bitbacktest.strategy import BollingerBandsStrategy
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
strategy = BollingerBandsStrategy(market)
param = {
    'window_size': 1000,  # 移動平均の期間
    'num_std_dev': 2,   # 標準偏差の倍率
    "one_order_quantity": 0.001,
    'buy_count_limit': 999
}
start_cash = 1e6

# Prepare Strategy
strategy.reset_all(param, start_cash)

# Execute backtest
portfolio_result = strategy.backtest(hold_params=["upper_band", "lower_band"])
print(portfolio_result)

# Plot graph
strategy.create_backtest_graph(backend="matplotlib")
