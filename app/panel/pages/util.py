import panel as pn
import datetime
import json
import numpy as np
import pandas as pd
import threading
from multiprocessing import Queue

class LogBox():
    def __init__(self, width=800, height=200):
        self.log_messages = []
        self.log_widget = pn.pane.HTML(
            "ここにログが表示されます",
            styles={
                "font-family": "Consolas, monospace",
                "border": "1px solid gray",
                "padding": "3px",
                "width": f"{width}px",
                "height": f"{height}px",
                "overflow-y": "scroll",  # 縦方向のスクロールバーを表示
            },
        )
        self.widget = pn.Column(self.log_widget)

    def update_log(self, message):
        self.log_messages.append(f"{datetime.datetime.now()}: {message}")
        self.log_widget.object = "<br>".join(self.log_messages)
        print(message)


class LogQueue():
    """Class to send logs to a queue."""
    def __init__(self):
        self.queue = Queue()

    def put(self, msg):
        """Put a message in the queue."""
        self.queue.put(msg)

    def get(self):
        """Get a message from the queue."""
        return self.queue.get()

    def add_log(self, new_row):
        """Add a new log entry."""
        try:
            self.queue.put(json.dumps(new_row))
        except:
            d = {k: int(v) if isinstance(v, np.int64) else v for k, v in new_row.items()}
            self.queue.put(json.dumps(d))

class DataFrameLogManager:
    """Class to manage logs and display them in a Panel."""
    def __init__(self):
        self.log_data = pd.DataFrame(columns=[])
        self.log_pane = pn.pane.DataFrame(self.log_data, height=200, width=800)
        self.log_queue = LogQueue()

    def get_log_queue(self):
        """Get the log queue."""
        return self.log_queue

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

    def start_thread(self):
        """Start the log processing thread."""
        log_thread = threading.Thread(target=self.thread, daemon=True)
        log_thread.start()
        return log_thread

    def stop_thread(self):
        """Stop the log processing thread."""
        self.log_queue.put(None)

class ParameterManager:
    """Class to manage parameter settings."""
    def __init__(self, params, only_constant=False):
        self.params = params
        self.widgets = {}
        self.only_constant = only_constant
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
            if self.only_constant:
                param_type.disabled = True
                lower.disabled = True
                upper.disabled = True
                param_type.value = "Constant"

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

datetime_range_picker = pn.widgets.DatetimeRangePicker(
    name='Datetime Range Picker',
    value=(datetime.datetime(2024, 11, 20, 12, 00), datetime.datetime(2025, 2, 28, 12, 00)),
)