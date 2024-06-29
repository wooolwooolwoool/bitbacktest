import pandas as pd
try:
    from IPython.display import display
except:
    pass

from .strategy import *

class Backtester:
    def __init__(self, strategy_class: Strategy):
        self.strategy_class = strategy_class

    def grid_backtest(self, price_data: np.ndarray, params: list, start_cash: int):
        self.grid_backtest_params = params
        self.test_results = []
        for i, param in enumerate(params):
            print(f"Running test {i+1}/{len(params)}")
            self.strategy_class.reset_all(param, start_cash)
            portfolio_result = self.strategy_class.backtest(price_data)
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