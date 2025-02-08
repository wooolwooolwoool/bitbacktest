import sys
import os
import time
import json
import threading
from multiprocessing import Process, Queue
import numpy as np
import pandas as pd
import panel as pn
import holoviews as hv
from holoviews.streams import Buffer
from skopt.space import Integer, Real, Categorical
import yaml
import datetime

# Add local module path
sys.path.append(".")
from src.bitbacktest.market import BacktestMarket
from src.bitbacktest.backtester import BayesianBacktester
from src.bitbacktest.data_loader import read_prices_from_sheets
from src.bitbacktest.strategy import BollingerBandsStrategy

# Initialize Panel extension
pn.extension()

# Constants
DATA_PATH = "my_data/BitCoinPrice_interp.xlsx"
DATA_RANGE = ["202408", "202409", "202410", "202411", "202412"]
DATA_INTERVAL = 10

def convert_to_standard_types(data):
    """Convert NumPy data types in a dictionary to standard Python types."""
    if isinstance(data, dict):
        return {k: convert_to_standard_types(v) for k, v in data.items()}
    elif isinstance(data, (np.integer, np.floating)):
        return data.item()
    elif isinstance(data, list):
        return [convert_to_standard_types(item) for item in data]
    return data

def save_result_summary(data_path, data_range, data_interval, params, portfolio_result):
    """Save the result summary to a YAML file."""
    now = datetime.datetime.now()
    summary = {
        "data_path": data_path,
        "data_range": str(data_range),
        "data_interval": str(data_interval),
        "params": convert_to_standard_types(params),
        "portfolio_result": portfolio_result
    }
    now_str = now.strftime("%Y%m%d_%H%M%S")
    with open(f"my_data/result_{now_str}.yaml", "w") as f:
        yaml.dump(summary, f, default_flow_style=False, allow_unicode=True)

# Data stream for real-time plotting
buffer = Buffer(pd.DataFrame({'Times': [], 'Total Value(JPY)': []}), length=200, index=False)
scatter = hv.DynamicMap(hv.Scatter, streams=[buffer])
scatter.opts(title="リアルタイム更新グラフ", xlabel="Time", ylabel="Value", width=700, height=400, size=8, color="blue")

# Flag to manage update state
is_running = [False]

class LogSender:
    """Class to send logs to a queue."""
    def __init__(self, log_queue):
        self.log_queue = log_queue

    def add_log(self, new_row):
        """Add a new log entry."""
        print(new_row)
        try:
            self.log_queue.put(json.dumps(new_row))
        except:
            d = {k: int(v) if isinstance(v, np.int64) else v for k, v in new_row.items()}
            self.log_queue.put(json.dumps(d))

class LogManager:
    """Class to manage logs and display them in a Panel."""
    def __init__(self, log_queue):
        self.log_data = pd.DataFrame(columns=[])
        self.log_pane = pn.pane.DataFrame(self.log_data, height=200)
        self.log_queue = log_queue

    def add_log(self, new_row):
        """Add a new log entry to the DataFrame."""
        self.log_data = pd.concat([self.log_data, pd.DataFrame([new_row])], ignore_index=True)
        self.log_pane.object = self.log_data.tail(100)

    def thread(self):
        """Thread to continuously process log messages."""
        while True:
            msg = self.log_queue.get()
            if msg is None:
                break
            self.add_log(json.loads(msg))

    def stop_thread(self):
        """Stop the log processing thread."""
        self.log_queue.put(None)

# Initialize log manager
log_queue = Queue()
log_sender = LogSender(log_queue)
log_manager = LogManager(log_queue)
log_thread = threading.Thread(target=log_manager.thread, daemon=True)
log_thread.start()

# General settings grid
general_grid = pn.GridSpec(width=800, height=35 * (3 + 1))
general_grid[0, 0] = pn.pane.Str("n_calls")
general_grid[0, 1] = n_calls_w = pn.widgets.IntInput(value=50, disabled=False)
general_grid[1, 0] = pn.pane.Str("start_cash")
general_grid[1, 1] = start_cash_w = pn.widgets.IntInput(value=int(2e5), disabled=False)
general_grid[2, 0] = pn.pane.Str("start_coin")
general_grid[2, 1] = start_coin_w = pn.widgets.FloatInput(value=0, disabled=False)

class ParameterManager:
    """Class to manage parameter settings."""
    def __init__(self, params):
        self.params = params
        self.widgets = {}
        self.param_pane = self._create_widgets()

    def _create_widgets(self):
        """Create widgets for parameter settings."""
        grid = pn.GridSpec(width=800, height=35 * (len(self.params.items()) + 1))
        grid[0, 0] = pn.pane.Str("Key")
        grid[0, 1] = pn.pane.Str("Type")
        grid[0, 2] = pn.pane.Str("Lower")
        grid[0, 3] = pn.pane.Str("Upper")
        grid[0, 4] = pn.pane.Str("Value")
        for i, (key, value) in enumerate(self.params.items()):
            grid[i+1, 0] = pn.pane.Str(key)
            grid[i+1, 1] = param_type = pn.widgets.Select(options=["Integer", "Real", "Constant"], value="Constant")
            grid[i+1, 2] = lower = pn.widgets.FloatInput(value=value[0] if isinstance(value, tuple) else None, disabled=True)
            grid[i+1, 3] = upper = pn.widgets.FloatInput(value=value[1] if isinstance(value, tuple) else None, disabled=True)
            grid[i+1, 4] = constant = pn.widgets.FloatInput(value=value if not isinstance(value, tuple) else None, disabled=False)

            def update_visibility(event, u=upper, l=lower, c=constant):
                if event.new == "Constant":
                    u.disabled, l.disabled, c.disabled = True, True, False
                else:
                    u.disabled, l.disabled, c.disabled = False, False, True

            param_type.param.watch(update_visibility, "value")
            self.widgets[key] = (param_type, upper, lower, constant)
        return pn.Column(grid)

    def get_params(self):
        """Get the current parameter values."""
        result = {}
        for key, (param_type, upper, lower, constant) in self.widgets.items():
            if param_type.value == "Constant":
                result[key] = constant.value
            elif param_type.value == "Integer":
                result[key] = Integer(int(lower.value), int(upper.value))
            elif param_type.value == "Real":
                result[key] = Real(lower.value, upper.value)
        return result

# Initial parameters
target_params = {
    'window_size': 10,
    'num_std_dev': 1.0,
    'reverse': 1,
    "buy_count_limit": 10,
    "one_order_quantity": 0.001
}

param_manager = ParameterManager(target_params)

def update_data():
    """Update data and run backtest."""
    price_data = read_prices_from_sheets(DATA_PATH, DATA_RANGE, DATA_INTERVAL, use_cache=True)
    os.environ["ORDER_NUM_MAX"] = "10"
    target_params = param_manager.get_params()

    market = BacktestMarket(price_data, fee_rate=0)
    strategy = BollingerBandsStrategy(market)
    backtester = BayesianBacktester(strategy)

    best_value, best_param = backtester.backtest(
        target_params,
        start_cash=start_cash_w.value,
        start_coin=start_coin_w.value,
        n_calls=n_calls_w.value,
        graph_buffer=buffer,
        log_sender=log_sender
    )

def start_update(event):
    """Start or stop the update process."""
    if not is_running[0]:
        is_running[0] = True
        thread = threading.Thread(target=update_data, daemon=True)
        thread.start()
        button.name = "実行中..."
    else:
        log_manager.stop_thread()
        button.name = "停止"

# Create and configure the button
button = pn.widgets.Button(name="グラフ更新を開始", button_type="primary")
button.on_click(start_update)

# Layout the Panel app
layout = pn.Column(
    pn.pane.Markdown("# バックテスト"),
    general_grid,
    pn.pane.Markdown("## パラメータ設定"),
    param_manager.param_pane,
    button,
    pn.panel(scatter),
    pn.pane.Markdown("## ログ"),
    log_manager.log_pane,
)

# Serve the app
layout.servable()