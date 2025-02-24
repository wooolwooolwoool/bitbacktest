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
from util import LogBox, datetime_range_picker, datetime_interval, my_datetime_fmt
import pandas as pd
import json
import numpy as np
from bokeh.models import DatetimeTickFormatter

logbox = LogBox(height=100)

DATA_PATH = "my_data/BitCoinPrice_interp.xlsx"
DATA_INTERVAL = 10

scatter = hv.Curve(([], [])).opts(title="Price history", xlabel="Datetime",
                    ylabel="Price(JPY)", width=1600, height=400, color="blue")
scatter_panel = pn.pane.HoloViews(scatter)


# Function to load execution history from JSON
def load_and_plot(event):
    # global scatter_panel
    logbox.update_log("Data loading...")
    datetime_range = datetime_range_picker.value
    dates, price_data = read_prices_from_sheets(DATA_PATH, datetime_range,
                                        DATA_INTERVAL, use_cache=True, with_date=True)
    new_data = pd.DataFrame({'Datetime': dates, 'Price(JPY)': price_data})
    logbox.update_log("Data loaded.")

    scatter = hv.Curve(new_data, 'Datetime', 'Price(JPY)').opts(title="Price history", width=1600, height=600, color="blue",
                        xformatter=my_datetime_fmt)
    scatter_panel.object = scatter
    logbox.update_log("Plot updated.")

# Buttons
load_button = pn.widgets.Button(name="Load Data", button_type="primary")

# Event handlers
load_button.on_click(load_and_plot)

# Layout
page = pn.Column(
    pn.pane.Markdown("## Show Price History"),
    pn.layout.Divider(margin=(-20, 0, 0, 0)),
    pn.Row(
        datetime_range_picker, datetime_interval, load_button
    ),
    scatter_panel,
    logbox.widget,
)
