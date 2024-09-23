import pandas as pd
try:
    from IPython.display import display
except:
    pass

from .strategy import *
try:
    from skopt import gp_minimize
    from skopt.space import Integer, Real, Categorical
except:
    pass


class GridBacktester:

    def __init__(self, strategy: Strategy):
        self.strategy = strategy

    def backtest(self, params: list, start_cash: int, start_coin: float = 0):
        self.grid_backtest_params = params
        self.test_results = []
        for i, param in enumerate(params):
            print(f"Running test {i+1}/{len(params)}")
            self.strategy.reset_all(param, start_cash, start_coin)
            portfolio_result = self.strategy.backtest()
            self.test_results.append(portfolio_result)
        return self.test_results

    def print_backtest_result(self):
        df1 = pd.DataFrame(self.grid_backtest_params)
        df2 = pd.DataFrame(self.test_results)
        df_h = pd.concat([df1, df2], axis=1)
        try:
            display(df_h)
        except:
            print(df_h)


class BayesianBacktester:

    def __init__(self, strategy: Strategy):
        self.strategy = strategy
        self.count = 0

    def _backtest_algorithm(self, params):
        self.count += 1
        print(f"Running test {self.count}/{self.n_calls}")
        param = self.target_params
        for i, k in enumerate(self.keys):
            param[k] = params[i]
        self.strategy.reset_all(param, self.start_cash, self.start_coin)
        result = self.strategy.backtest()
        total_value = result["total_value"]
        print(f"param: {param}, total_value: {total_value}")
        return -total_value

    def backtest(self,
                 target_params: dict,
                 start_cash: int,
                 start_coin: float = 0,
                 n_calls: int = 50,
                 random_state: int = 777):
        """
        params: dict of params. Optimization parameters should be Integer, Real or Categorical.
            example,
            target_params = {
                "short_window": Integer(12, 180, name='short_window'),
                "long_window": Integer(48, 720, name='long_window'),
                "signal_window": Real(6, 180, name='signal_window'),
                "profit": Real(1.01, 1.02, name='profit'),
                "one_order_quantity": 0.001
            }
        start_cash: int, start cash
        start_coin: float, start coin
        n_calls: int, number of calls
        random_state: int, random state
        """
        self.start_cash = start_cash
        self.start_coin = start_coin
        self.target_params = target_params
        self.n_calls = n_calls
        self.keys = []
        param_ranges_variable = []

        for k in self.target_params.keys():
            t = type(target_params[k])
            if t is Integer or t is Real or t is Categorical:
                param_ranges_variable.append(target_params[k])
                self.keys.append(k)

        # execute
        result = gp_minimize(func=self._backtest_algorithm,
                             dimensions=param_ranges_variable,
                             n_calls=n_calls,
                             random_state=random_state)

        self.best_params = target_params
        for i, k in enumerate(self.keys):
            self.best_params[k] = result.x[i]
        self.best_value = -result.fun
        print(f"Best Parameters: {self.best_params}")
        print(f"Best Total Value: {self.best_value}")

        return self.best_value, self.best_params
