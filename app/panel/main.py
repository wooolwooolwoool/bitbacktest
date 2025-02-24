import sys
import os
import datetime
import panel as pn

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from pages import optimize, bitflyer, datacheck, backtest, other, make_CF_yaml

js_files = {'jquery': 'https://code.jquery.com/jquery-1.11.1.min.js',
            'goldenlayout': 'https://golden-layout.com/files/latest/js/goldenlayout.min.js'}
css_files = ['https://golden-layout.com/files/latest/css/goldenlayout-base.css',
             'https://golden-layout.com/files/latest/css/goldenlayout-light-theme.css']

# Initialize Panel extension
pn.extension('vtk', js_files=js_files, css_files=css_files, design='material', theme='default', sizing_mode="stretch_width")

# Layout the Panel app
layout = pn.Tabs(
    ('Data Check', datacheck.page),
    ('Optimize', optimize.page),
    ('Backtest', backtest.page),
    ('Bitflyer', bitflyer.page),
    ('Make_CF_yaml', make_CF_yaml.page),
    ('Other', other.page),
)

# Serve the app
layout.servable()