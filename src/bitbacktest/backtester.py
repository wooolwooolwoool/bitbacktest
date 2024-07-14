import pandas as pd
try:
    from IPython.display import display
except:
    pass

from .strategy import *

class Backtester:
    def __init__(self, strategy: Strategy):
        self.strategy = strategy

    def grid_backtest(self, params: list, start_cash: int, start_coin: float = 0):
        self.grid_backtest_params = params
        self.test_results = []
        for i, param in enumerate(params):
            print(f"Running test {i+1}/{len(params)}")
            self.strategy.reset_all(param, start_cash, start_coin)
            portfolio_result = self.strategy.backtest()
            self.test_results.append(portfolio_result)
        return self.test_results

    def print_grid_backtest_result(self):
        df1 = pd.DataFrame(self.grid_backtest_params)
        df2 = pd.DataFrame(self.test_results)
        df_h = pd.concat([df1, df2], axis=1)
        try:
            display(df_h)
        except:
            print(df_h)