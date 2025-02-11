import sys
import os
import json
import threading
from multiprocessing import Queue
import numpy as np
import pandas as pd
import panel as pn
import holoviews as hv
from holoviews.streams import Buffer
from skopt.space import Integer, Real, Categorical
import yaml
import datetime
import traceback

# Add local module path
sys.path.append(".")
from src.bitbacktest.market import BacktestMarket
from src.bitbacktest.backtester import BayesianBacktester
from src.bitbacktest.data_loader import read_prices_from_sheets
from src.bitbacktest.strategy import BacktestStrategy

from src.bitbacktest.signal_generator import SignalGenerator
from src.bitbacktest.trade_executor import TradeExecutor

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from util import LogBox, DataFrameLogManager

logbox = LogBox()

custom_classes = {'SignalGenerator': {}, 'TradeExecutor': {}}

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

# Initialize log manager
log_manager = DataFrameLogManager()
log_queue = log_manager.get_log_queue()
log_thread = log_manager.start_thread()

# General settings grid
general_grid = pn.GridSpec(width=800, height=20 * (3 + 1))
general_grid[0, 0] = pn.pane.Str("n_calls")
general_grid[0, 1] = n_calls_w = pn.widgets.IntInput(value=10, disabled=False)
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
        grid = pn.GridSpec(width=800, height=50 * (len(self.params.items()) + 1))
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

param_manager = None
price_data = None

datetime_range_picker = pn.widgets.DatetimeRangePicker(
    name='Datetime Range Picker', value=(datetime.datetime(2024, 8, 2, 12, 10), datetime.datetime(2024, 12, 2, 12, 22))
)

def exec_optimize():
    try:
        """Update data and run backtest."""
        global price_data
        logbox.update_log("Start optimize")
        logbox.update_log("Data loading...")
        datetime_range = datetime_range_picker.value
        dates, price_data = read_prices_from_sheets(DATA_PATH, datetime_range,
                                         DATA_INTERVAL, use_cache=True, with_date=True)
        os.environ["ORDER_NUM_MAX"] = "10"
        target_params = param_manager.get_params()

        market = BacktestMarket(price_data, fee_rate=0)
        signal_gene = custom_classes['SignalGenerator'][signal_generator_select.value]()
        trade_exec = custom_classes['TradeExecutor'][trade_executor_select.value]()

        logbox.update_log("Strategy parameters:")
        logbox.update_log(f"{target_params}")

        strategy = BacktestStrategy(market, signal_gene, trade_exec)
        backtester = BayesianBacktester(strategy)

        best_value, best_param = backtester.backtest(
            target_params,
            start_cash=start_cash_w.value,
            start_coin=start_coin_w.value,
            n_calls=n_calls_w.value,
            graph_buffer=buffer,
            log_sender=log_queue
        )
        logbox.update_log(f"Best value: {best_value}")
    except Exception as e:
        logbox.update_log(f"Error: {e}")
        logbox.update_log(traceback.format_exc())
    is_running[0] = False

def start_optimize(event):
    """Start or stop the update process."""
    if not is_running[0]:
        is_running[0] = True
        backtest_thread = threading.Thread(target=exec_optimize, daemon=True)
        backtest_thread.start()
        button.name = "Cancel"
    else:
        log_manager.stop_thread()
        is_running[0] = False
        button.name = "Start"

# Create and configure the button
button = pn.widgets.Button(name="Start Optimize", button_type="primary")
button.on_click(start_optimize)

# Function to dynamically import classes from custom_src
def get_custom_classes():
    """Get SignalGenerator and TradeExecutor classes from custom_src."""
    base_src_path = 'src/bitbacktest'
    custom_src_path = 'my_data/custom_src'
    for src_path in [base_src_path, custom_src_path]:
        if os.path.exists(src_path):
            for file in os.listdir(src_path):
                if file.endswith('.py'):
                    module_name = file[:-3]
                    module_path = f'{src_path.replace("/", ".")}.{module_name}'
                    try:
                        module = __import__(module_path, fromlist=[''])
                        for name, obj in module.__dict__.items():
                            if isinstance(obj, type):
                                if issubclass(obj, SignalGenerator) and obj != SignalGenerator:
                                    custom_classes['SignalGenerator'][name] = obj
                                elif issubclass(obj, TradeExecutor) and obj != TradeExecutor:
                                    custom_classes['TradeExecutor'][name] = obj
                    except Exception as e:
                        logbox.update_log(f"Error importing {module_name}: {e}")
                        logbox.update_log(traceback.format_exc())
    return custom_classes

# Dropdown widgets for custom classes
custom_classes = get_custom_classes()
signal_generator_select = pn.widgets.Select(name='Signal Generator', options=list(custom_classes['SignalGenerator'].keys()))
trade_executor_select = pn.widgets.Select(name='Trade Executor', options=list(custom_classes['TradeExecutor'].keys()))


@pn.depends(signal_generator_select.param.value)
@pn.depends(trade_executor_select.param.value)
def update_params(event):
    """Update the parameter settings."""
    global param_manager
    market = BacktestMarket([])
    signal_gene = custom_classes['SignalGenerator'][signal_generator_select.value]()
    trade_exec = custom_classes['TradeExecutor'][trade_executor_select.value]()
    strategy = BacktestStrategy(market, signal_gene, trade_exec)

    param_manager = ParameterManager(strategy.default_param)
    logbox.update_log(f"Updated parameters: {target_params}")
    return param_manager.param_pane


# File upload widget
file_input = pn.widgets.FileInput(name='Upload .py file', accept='.py')

def save_file(event):
    """Save uploaded file to my_data/custom_src directory."""
    global custom_classes, signal_generator_select, trade_executor_select
    os.makedirs('my_data/custom_src', exist_ok=True)
    if file_input.value is not None:
        file_path = os.path.join('my_data/custom_src', file_input.filename)
        with open(file_path, 'wb') as f:
            f.write(file_input.value)
        logbox.update_log(f"File {file_input.filename} saved to {file_path}")
    custom_classes = get_custom_classes()
    signal_generator_select = pn.widgets.Select(name='Signal Generator', options=list(custom_classes['SignalGenerator'].keys()))
    trade_executor_select = pn.widgets.Select(name='Trade Executor', options=list(custom_classes['TradeExecutor'].keys()))

file_input.param.watch(save_file, 'value')

# Add file upload and dropdowns to the layout
page = pn.Row(
    pn.Column(
        pn.pane.Markdown("# バックテスト"),
        pn.pane.Markdown("## カスタムファイルアップロード"),
        file_input,
        pn.pane.Markdown("## カスタムクラス選択"),
        pn.Row(
            signal_generator_select,
            trade_executor_select,
        ),
        general_grid,
        pn.pane.Markdown("## パラメータ設定"),
        update_params,
        button,
        pn.pane.Markdown("## データ範囲指定"),
        datetime_range_picker,
        pn.pane.Markdown("## ログ"),
        logbox.widget,
    ),
    pn.Column(
        pn.panel(scatter),
        pn.pane.Markdown("## ログ"),
        log_manager.log_pane,
    ),
)

