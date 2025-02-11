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