import sys
import os
import threading
import numpy as np
import pandas as pd
import panel as pn
import holoviews as hv
hv.extension("bokeh")
from holoviews.streams import Buffer
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
from util import LogBox, DataFrameLogManager, datetime_range_picker, ParameterManager, save_result_summary, datetime_interval

logbox = LogBox()

custom_classes = {'SignalGenerator': {}, 'TradeExecutor': {}}

# Constants
DATA_PATH = "my_data/BitCoinPrice_interp.xlsx"
DATA_INTERVAL = 10

# Data stream for real-time plotting
buffer = Buffer(pd.DataFrame({'Times': [], 'Total Value(JPY)': []}), length=200, index=False)
scatter = hv.DynamicMap(hv.Scatter, streams=[buffer])
scatter.opts(title="Backtest Result", xlabel="Time", ylabel="Value", width=1000, height=400, size=8, color="blue")

hline = hv.HLine(0).opts(color="red", line_width=1, line_dash="dashed")
overlay = scatter * hline
scatter_panel = pn.pane.HoloViews(overlay)

# Create and configure the button
button = pn.widgets.Button(name="Start Optimize", button_type="primary")

# Flag to manage update state
is_running = [False]

# Initialize log manager
log_manager = DataFrameLogManager()
df_log_queue = log_manager.get_log_queue()
log_thread = log_manager.start_thread()

# General settings grid
general_grid = pn.GridSpec(width=600, height=20 * (3 + 1))
general_grid[0, 0] = pn.pane.Str("n_calls")
general_grid[0, 1] = n_calls_w = pn.widgets.IntInput(value=10, disabled=False)
general_grid[1, 0] = pn.pane.Str("start_cash")
general_grid[1, 1] = start_cash_w = pn.widgets.IntInput(value=int(2e5), disabled=False)
general_grid[2, 0] = pn.pane.Str("start_coin")
general_grid[2, 1] = start_coin_w = pn.widgets.FloatInput(value=0, disabled=False)

param_manager = None
param_manager_panel = None
price_data = None

def exec_optimize():
    try:
        """Update data and run backtest."""
        button.name = "Running"
        log_manager.log_pane.clear()
        global price_data, scatter_panel, scatter
        logbox.update_log("Start optimize")
        logbox.update_log("Data loading...")
        datetime_range = datetime_range_picker.value
        dates, price_data = read_prices_from_sheets(DATA_PATH, datetime_range,
                                         datetime_interval.value, use_cache=True, with_date=True)
        os.environ["ORDER_NUM_MAX"] = "10"
        target_params = param_manager.get_params()

        market = BacktestMarket(price_data, fee_rate=0, is_fx=True)
        signal_gene = custom_classes['SignalGenerator'][signal_generator_select.value]()
        trade_exec = custom_classes['TradeExecutor'][trade_executor_select.value]()

        logbox.update_log("Strategy parameters:")
        logbox.update_log(f"{target_params}")

        strategy = BacktestStrategy(market, signal_gene, trade_exec)
        backtester = BayesianBacktester(strategy)

        hline = hv.HLine(start_cash_w.value).opts(color="red", line_width=1, line_dash="dashed")
        overlay = scatter * hline
        scatter_panel.object = overlay

        best_value, best_param = backtester.backtest(
            target_params,
            start_cash=start_cash_w.value,
            start_coin=start_coin_w.value,
            n_calls=n_calls_w.value,
            graph_buffer=buffer,
            df_log_queue=df_log_queue
        )
        logbox.update_log(f"Best value: {best_value}")
        save_path = save_result_summary(DATA_PATH, datetime_range, datetime_interval.value, best_param,
                            backtester.best["portfolio"], signal_generator_select.value, trade_executor_select.value)
        logbox.update_log(f"Result saved to {save_path}")

    except Exception as e:
        logbox.update_log(f"Error: {e}")
        logbox.update_log(traceback.format_exc())
    button.name = "Start Optimize"
    is_running[0] = False

backtest_thread = None

def start_optimize(event):
    """Start or stop the update process."""
    global backtest_thread
    if not is_running[0]:
        if backtest_thread is not None:
            backtest_thread.join()
        backtest_thread = threading.Thread(target=exec_optimize, daemon=True)
        backtest_thread.start()
        is_running[0] = True
    else:
        logbox.update_log(f"Cannot start. Running now.")

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

def reload_sg_te(event):
    """Reload the SignalGenerator and TradeExecutor classes."""
    global custom_classes, signal_generator_select, trade_executor_select
    custom_classes = get_custom_classes()
    signal_generator_select.options = list(custom_classes['SignalGenerator'].keys())
    trade_executor_select.options = list(custom_classes['TradeExecutor'].keys())
    logbox.update_log("Reloaded SignalGenerator and TradeExecutor classes")

reload_button = pn.widgets.Button(name="Reload SG and TE", button_type="default")
reload_button.on_click(reload_sg_te)

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
    logbox.update_log(f"Updated parameters: {signal_generator_select.value}, {trade_executor_select.value}")
    return param_manager.param_pane

# Add file upload and dropdowns to the layout
page = pn.Row(
    pn.layout.WidgetBox(
        pn.pane.Markdown("## Select custom classes"),
        pn.layout.Divider(margin=(-20, 0, 0, 0)),
        reload_button,
        pn.Row(
            signal_generator_select,
            trade_executor_select,
        ),
        pn.pane.Markdown("## Optimeze settings"),
        pn.layout.Divider(margin=(-20, 0, 0, 0)),
        general_grid,
        pn.pane.Markdown("## Date range"),
        pn.layout.Divider(margin=(-20, 0, 0, 0)),
        datetime_range_picker,
        pn.pane.Markdown("## Parameter settings"),
        pn.layout.Divider(margin=(-20, 0, 0, 0)),
        update_params,
        button,
        pn.pane.Markdown("## Log"),
        pn.layout.Divider(margin=(-20, 0, 0, 0)),
        logbox.widget,
    ),
    pn.Column(
        scatter_panel,
        log_manager.log_pane,
    )
)
