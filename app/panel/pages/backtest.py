import sys
import os
import json
import threading
from multiprocessing import Queue
import numpy as np
import pandas as pd
import panel as pn
import holoviews as hv
hv.extension("bokeh")
from holoviews.streams import Buffer
from skopt.space import Integer, Real, Categorical
import yaml
import datetime
import traceback

# Add local module path
sys.path.append(".")
from src.bitbacktest.market import BacktestMarket
from src.bitbacktest.data_loader import read_prices_from_sheets
from src.bitbacktest.strategy import BacktestStrategy

from src.bitbacktest.signal_generator import SignalGenerator
from src.bitbacktest.trade_executor import TradeExecutor

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from util import LogBox, DataFrameLogManager, datetime_range_picker, ParameterManager

scatter_panel = pn.pane.HoloViews()

param_manager = None
param_manager_panel = None
price_data = None


logbox = LogBox()

custom_classes = {'SignalGenerator': {}, 'TradeExecutor': {}}

# Constants
DATA_PATH = "my_data/BitCoinPrice_interp.xlsx"
DATA_INTERVAL = 10

# General settings grid
general_grid = pn.GridSpec(width=600, height=20 * (3 + 1))
general_grid[0, 0] = pn.pane.Str("start_cash")
general_grid[0, 1] = start_cash_w = pn.widgets.IntInput(value=int(2e5), disabled=False)
general_grid[1, 0] = pn.pane.Str("start_coin")
general_grid[1, 1] = start_coin_w = pn.widgets.FloatInput(value=0, disabled=False)

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
                                    logbox.update_log(f"Imported SignalGenerator: {name}")
                                elif issubclass(obj, TradeExecutor) and obj != TradeExecutor:
                                    custom_classes['TradeExecutor'][name] = obj
                                    logbox.update_log(f"Imported TradeExecutor: {name}")
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

    param_manager = ParameterManager(strategy.default_param, only_constant=True)
    logbox.update_log(f"Updated parameters: {signal_generator_select.value}, {trade_executor_select.value}")
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

def exec_backtest(event):
    try:
        global price_data, scatter_panel, scatter
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
        strategy.reset_all(target_params, start_cash_w.value, start_coin_w.value)

        portfolio_result = strategy.backtest(hold_params=[])
        logbox.update_log(portfolio_result)
        logbox.update_log(f"Profit rate: {portfolio_result['total_value'] / start_cash_w.value}")

        # Plot graph
        graph = strategy.create_backtest_graph(backend="holoviews")
        scatter_panel.object = graph
    except Exception as e:
        logbox.update_log(f"Error: {e}")
        logbox.update_log(traceback.format_exc())


# Create and configure the button
button = pn.widgets.Button(name="Start Backtest", button_type="primary")
button.on_click(exec_backtest)

page = pn.Column(
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
    pn.pane.Markdown("## データ範囲指定"),
    datetime_range_picker,
    button,
    scatter_panel,
    pn.pane.Markdown("## ログ"),
    logbox.widget,
)