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

try:
    import pandas as pd
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
        self.graph_buffer = None
        self.log_manager = None
        self.best = {"value": 0, "portfolio": None}

    def _backtest_algorithm(self, params):
        self.count += 1
        print(f"Running test {self.count}/{self.n_calls}")
        param = self.target_params
        for i, k in enumerate(self.keys):
            param[k] = params[i]
        self.strategy.reset_all(param, self.start_cash, self.start_coin)
        result = self.strategy.backtest()
        total_value = result["total_value"]
        trade_count = result["trade_count"]
        result_str = f"param: {param}, total_value: {total_value}"
        if total_value > self.best["value"]:
            self.best["value"] = total_value
            self.best["portfolio"] = result.copy()

        try:
            result_str += f", trade count: {trade_count}"
        except:
            pass
        print(result_str)
        if self.graph_buffer is not None:
            new_data = pd.DataFrame({'Times': [self.count], 'Total Value(JPY)': [total_value]})
            self.graph_buffer.send(new_data)
        if self.df_log_queue is not None:
            d = param
            d["Trade_Count"] = trade_count
            d["Total_Value"] = total_value
            self.df_log_queue.add_log(d)

        return -total_value

    def backtest(self,
                 target_params: dict,
                 start_cash: int,
                 start_coin: float = 0,
                 n_calls: int = 50,
                 random_state: int = 777,
                 graph_buffer=None,
                 df_log_queue=None):
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
        graph_buffer: Buffer object for graph
        df_log_queue: DataFrameLogManager object for log
        """
        self.start_cash = start_cash
        self.start_coin = start_coin
        self.target_params = target_params
        self.n_calls = n_calls
        self.keys = []
        self.graph_buffer = graph_buffer
        self.df_log_queue = df_log_queue
        self.best = {"value": 0, "portfolio": None}
        if self.graph_buffer is not None:
            self.graph_buffer.clear()
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
