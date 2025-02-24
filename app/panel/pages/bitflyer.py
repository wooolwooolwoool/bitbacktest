import panel as pn
import datetime
import os
import sys
import traceback

import holoviews as hv
hv.extension("bokeh")
from holoviews.streams import Buffer
sys.path.append(".")
from src.bitbacktest.market import BitflyerMarket

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from util import LogBox
import pandas as pd
import json
import numpy as np
from bokeh.models import DatetimeTickFormatter


execution_history_file = "my_data/execution_history.json"

my_datetime_fmt = DatetimeTickFormatter(seconds="%H:%M:%S",
                        minutes="%H:%M:%S",
                        hours="%H:%M:%S",
                        days="%Y/%m/%d",
                        months="%Y/%m",
                        years="%Y")

logbox = LogBox()
bitflyermarket = BitflyerMarket()

try:
    bitflyermarket.set_apikey(os.environ["API_KEY"], os.environ["API_SECRET"])
except:
    pass

log_data = pd.DataFrame(columns=[])
log_pane = pn.pane.DataFrame(log_data, height=200)

scatter = hv.Curve(([], []))
scatter_panel = pn.panel(scatter)

# Function to fetch and save execution history
def fetch_and_save_execution_history(event):
    execution_history = bitflyermarket.get_executions_all()
    with open(execution_history_file, "w") as f:
        json.dump(execution_history, f)
    log_pane.object = pd.DataFrame(execution_history)
    logbox.update_log("Execution history fetched and saved.")

# Function to load execution history from JSON
def load_execution_history(event):
    try:
        with open(execution_history_file, "r") as f:
            execution_history = json.load(f)
        log_pane.object = pd.DataFrame(execution_history)
        logbox.update_log("Execution history loaded from JSON.")

        with open(execution_history_file, "r") as f:
            execution_history = json.load(f)
        dates, profits = bitflyermarket.calc_profits(execution_history)
        total_profits = []
        old_profit = 0
        for profit in profits:
            total_profits.append(profit + old_profit)
            old_profit += profit

        new_data = pd.DataFrame({'Datetime': dates, 'Total Profit(JPY)': total_profits})
        scatter_panel.object = hv.Curve(new_data, 'Datetime', 'Total Profit(JPY)').opts(title="Profit history",
                            width=1600, height=600, color="blue",
                            xformatter=my_datetime_fmt)
    except Exception as e:
        logbox.update_log(f"Error: {e}")
        logbox.update_log(traceback.format_exc())
        logbox.update_log("Failed to load execution history from JSON.")
# Buttons
fetch_button = pn.widgets.Button(name="Fetch and Save Execution History")
load_button = pn.widgets.Button(name="Load Execution History")

# Event handlers
fetch_button.on_click(fetch_and_save_execution_history)
load_button.on_click(load_execution_history)
load_execution_history(None)

# Layout
page = pn.Column(
    pn.pane.Markdown("## Execution History"),
    pn.layout.Divider(margin=(-20, 0, 0, 0)),
    pn.Row(
        fetch_button,
        load_button,
    ),
    log_pane,
    scatter_panel,
    pn.pane.Markdown("## Log"),
    pn.layout.Divider(margin=(-20, 0, 0, 0)),
    logbox.widget,
)

