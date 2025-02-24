import sys
import os
import panel as pn
import traceback

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from util import LogBox

logbox = LogBox()

# File upload widget
file_input = pn.widgets.FileInput(name='Upload .py file', accept='.py')

def save_file(event):
    """Save uploaded file to my_data/custom_src directory."""
    os.makedirs('my_data/custom_src', exist_ok=True)
    if file_input.value is not None:
        file_path = os.path.join('my_data/custom_src', file_input.filename)
        with open(file_path, 'wb') as f:
            f.write(file_input.value)
        logbox.update_log(f"File {file_input.filename} saved to {file_path}")

file_input.param.watch(save_file, 'value')

# Add file upload and dropdowns to the layout
page = pn.Column(
    pn.pane.Markdown("## Upload custom classes"),
    pn.layout.Divider(margin=(-20, 0, 0, 0)),
    file_input,
    pn.pane.Markdown("## Log"),
    pn.layout.Divider(margin=(-20, 0, 0, 0)),
    logbox.widget,
)
