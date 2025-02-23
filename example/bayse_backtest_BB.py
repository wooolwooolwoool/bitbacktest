
import sys, os
sys.path.append(".")
from src.bitbacktest.market import BacktestMarket
from src.bitbacktest.backtester import BayesianBacktester
from src.bitbacktest.data_loader import read_prices_from_sheets
from src.bitbacktest.strategy import BacktestStrategy

from src.bitbacktest.signal_generator import BollingerBandsSG
from src.bitbacktest.trade_executor import SpreadOrderExecutor

from skopt.space import Integer, Real, Categorical

def convert_to_standard_types(data):
    import numpy as np
    """辞書内のNumPyのデータ型をPython標準の型に変換"""
    if isinstance(data, dict):
        return {k: convert_to_standard_types(v) for k, v in data.items()}
    elif isinstance(data, (np.integer, np.floating)):
        return data.item()  # numpyの数値をPythonの数値に変換
    elif isinstance(data, list):
        return [convert_to_standard_types(item) for item in data]
    return data

def save_result_summary(data_path, data_range, data_interval, params, portfolio_result):
    import datetime, yaml
    now = datetime.datetime.now()
    yml = {
            "data_path": data_path,
            "data_range": str(data_range),
            "data_interval": str(data_interval),
            "params": convert_to_standard_types(params),
            "portfolio_result": portfolio_result
        }
    now_str = now.strftime("%Y%m%d_%H%M%S")
    with open(f"my_data/result_{now_str}.yaml", "w") as f:
        yaml.dump(yml, f, default_flow_style=False, allow_unicode=True)

data_path = "my_data/BitCoinPrice_interp.xlsx"
datetime_range = (datetime.datetime(2024, 11, 20, 12, 00),
                  datetime.datetime(2025,  2, 28, 12, 00))
data_interval = 10

# Read data for test
price_data = read_prices_from_sheets(data_path,
                        datetime_range, data_interval, use_cache=True)
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

print(strategy.default_param)


if True:
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
strategy.create_backtest_graph(backend="matplotlib")
