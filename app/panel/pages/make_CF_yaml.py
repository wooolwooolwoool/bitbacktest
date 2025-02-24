import sys
import os
import numpy as np
import panel as pn
import holoviews as hv
hv.extension("bokeh")
import traceback
import datetime

# Add local module path
sys.path.append(".")
from src.bitbacktest.market import BacktestMarket
from src.bitbacktest.data_loader import read_prices_from_sheets
from src.bitbacktest.strategy import BacktestStrategy

from src.bitbacktest.signal_generator import SignalGenerator
from src.bitbacktest.trade_executor import TradeExecutor

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from util import LogBox, datetime_range_picker, ParameterManager, load_result_summary, datetime_interval

scatter_panel = pn.pane.HoloViews()

param_manager = None
param_manager_panel = None
price_data = None


logbox = LogBox()

status_widgit = pn.pane.Markdown("## Ready")

custom_classes = {'SignalGenerator': {}, 'TradeExecutor': {}}

plot_param_select = pn.layout.WidgetBox()
plot_param_select_obj = None

# Constants
DATA_PATH = "my_data/BitCoinPrice_interp.xlsx"

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

def reload_sg_te(event):
    """Reload the SignalGenerator and TradeExecutor classes."""
    global custom_classes, signal_generator_select, trade_executor_select
    custom_classes = get_custom_classes()
    signal_generator_select.options = list(custom_classes['SignalGenerator'].keys())
    trade_executor_select.options = list(custom_classes['TradeExecutor'].keys())
    logbox.update_log("Reloaded SignalGenerator and TradeExecutor classes")

reload_button = pn.widgets.Button(name="Reload SG and TE", button_type="primary")
reload_button.on_click(reload_sg_te)

class PlotParamSelector:
    def __init__(self, params):
        self.widget = pn.GridSpec(width=600)
        self.params = params
        self.w = []
        l = []
        for i, p in enumerate(params):
            self.widget[i, 0] = p
            self.w.append(pn.widgets.ToggleGroup(name='ToggleGroup', options=['None', 'Price', 'Value', "Additional"], behavior="radio"))
            self.widget[i, 1:4] = self.w[-1]

    @property
    def value(self):
        selected_params = []
        axis = []
        for i, p in enumerate(self.params):
            if self.w[i].value != "None":
                selected_params.append(p)
                axis.append(self.w[i].value)
        return selected_params, axis

@pn.depends(signal_generator_select.param.value)
@pn.depends(trade_executor_select.param.value)
def update_params(event):
    """Update the parameter settings."""
    global param_manager, plot_param_select_obj
    market = BacktestMarket([])
    signal_gene = custom_classes['SignalGenerator'][signal_generator_select.value]()
    trade_exec = custom_classes['TradeExecutor'][trade_executor_select.value]()
    strategy = BacktestStrategy(market, signal_gene, trade_exec)

    param_manager = ParameterManager(strategy.default_param, only_constant=True)
    strategy.reset_all({}, 0)
    logbox.update_log(f"Updated parameters: {signal_generator_select.value}, {trade_executor_select.value}")
    pane = pn.Column(
        param_manager.param_pane,
    )
    return pane

# File upload widget
file_input_yaml = pn.widgets.FileInput(name='', accept='.yaml')

def load_yaml_file(event):
    """Save uploaded file to my_data/custom_src directory."""
    global custom_classes, signal_generator_select, trade_executor_select
    signal_generator_name, trade_executor_name, param = load_result_summary(file_input_yaml.value)
    trade_executor_select.value = trade_executor_name
    signal_generator_select.value = signal_generator_name
    param_manager.set_params(param)

file_input_yaml.param.watch(load_yaml_file, 'value')

def exec_build(event):
    try:
        global status_widgit
        status_widgit.value = "## Making..."
        now = datetime.datetime.now()
        yaml_path = f"my_data/CloudFormation_{now.strftime('%Y%m%d_%H%M%S')}_{signal_generator_select.value}_{trade_executor_select.value}.yaml"
        os.system(f"python3 app/aws_build/build_all.py -s {signal_generator_select.value} -t {trade_executor_select.value} -o {yaml_path}")
        logbox.update_log(f"Complete make. save to {yaml_path}")
        status_widgit.value = f"Complete make. save to {yaml_path}"
    except Exception as e:
        logbox.update_log(f"Error: {e}")
        logbox.update_log(traceback.format_exc())

# Create and configure the button
button = pn.widgets.Button(name="Start Make yaml", button_type="primary")
button.on_click(exec_build)

page = pn.Column(
    pn.pane.Markdown("## Load result summary"),
    pn.layout.Divider(margin=(-20, 0, 0, 0)),
    file_input_yaml,
    pn.pane.Markdown("## Select custom classes"),
    pn.layout.Divider(margin=(-20, 0, 0, 0)),
    pn.Row(
        signal_generator_select,
        trade_executor_select,
    ),
    reload_button,
    pn.pane.Markdown("## Parameter settings"),
    pn.layout.Divider(margin=(-20, 0, 0, 0)),
    update_params,
    button,
    status_widgit,
    pn.pane.Markdown("## Log"),
    pn.layout.Divider(margin=(-20, 0, 0, 0)),
    logbox.widget,
)