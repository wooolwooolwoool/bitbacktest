import sys
sys.path.append("/content/bitbacktest")

from src.bitbacktest.strategy import MACDStrategy
from src.bitbacktest.market import BacktestMarket
from src.bitbacktest.data_generater import random_data
from src.bitbacktest.strategy import Strategy
from src.bitbacktest.backtester import BayesianBacktester

start_cash = 2e5
market = BacktestMarket(back_data)
strategy = MACDForcusBuyStrategy(market)
backtester = BayesianBacktester(strategy)

target_params = {
   "short_window": Integer(32, 360, name='short_window'),
   "long_window": Integer(240, 720, name='long_window'),
   "signal_window": Integer(8, 360, name='signal_window'),
   "profit": 1.01,
   "one_order_quantity": 0.001
}

backtester.backtest(target_params, start_cash, n_calls=100)