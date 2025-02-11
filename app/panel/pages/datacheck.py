import panel as pn
import datetime
import os
import sys

import holoviews as hv
hv.extension("bokeh")
from holoviews.streams import Buffer
sys.path.append(".")
from src.bitbacktest.market import BitflyerMarket
from src.bitbacktest.data_loader import read_prices_from_sheets

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from util import LogBox
import backtest
import pandas as pd
import json
import numpy as np
from bokeh.models import DatetimeTickFormatter

logbox = LogBox(height=100)

my_datetime_fmt = DatetimeTickFormatter(seconds="%H:%M:%S",
                        minutes="%H:%M:%S",
                        hours="%H:%M:%S",
                        days="%Y/%m/%d",
                        months="%Y/%m",
                        years="%Y")

DATA_PATH = "my_data/BitCoinPrice_interp.xlsx"
DATA_RANGE = ["202408", "202409", "202410", "202411", "202412"]
DATA_INTERVAL = 10

scatter = hv.Curve(([], [])).opts(title="Profit history", xlabel="Datetime",
                    ylabel="Price(JPY)", width=1600, height=400, color="blue")
scatter_panel = pn.pane.HoloViews(scatter)

datetime_range_picker = pn.widgets.DatetimeRangePicker(
    name='Datetime Range Picker', value=(datetime.datetime(2024, 8, 2, 12, 10), datetime.datetime(2024, 12, 2, 12, 22))
)

# Function to load execution history from JSON
def load_and_plot(event):
    # global scatter_panel
    logbox.update_log("Data loading...")
    datetime_range = datetime_range_picker.value
    dates, price_data = read_prices_from_sheets(DATA_PATH, datetime_range,
                                        DATA_INTERVAL, use_cache=True, with_date=True)
    new_data = pd.DataFrame({'Datetime': dates, 'Price(JPY)': price_data})
    logbox.update_log("Data loaded.")
    backtest.datetime_range_picker.object = datetime_range_picker.value

    scatter = hv.Curve(new_data, 'Datetime', 'Price(JPY)').opts(title="Profit history", width=1600, height=600, color="blue",
                        xformatter=my_datetime_fmt)
    scatter_panel.object = scatter
    logbox.update_log("Plot updated.")

# Buttons
load_button = pn.widgets.Button(name="Load Data")

# Event handlers
load_button.on_click(load_and_plot)

# Layout
page = pn.Column(
    pn.pane.Markdown("## 範囲を指定して価格データを表示"),
    datetime_range_picker, load_button,
    scatter_panel,
    logbox.widget,
)
