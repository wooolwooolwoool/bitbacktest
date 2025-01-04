
def convert_to_standard_types(data):
    import numpy as np
    """辞書内のNumPyのデータ型をPython標準の型に変換"""
    if isinstance(data, dict):
        return {k: convert_to_standard_types(v) for k, v in data.items()}
    elif isinstance(data, (np.integer, np.floating)):
        return data.item()  # numpyの数値をPythonの数値に変換
    elif isinstance(data, list):
        return [convert_to_standard_types(item) for item in data]
    return data

def save_result_summary(data_path, data_range, data_interval, params, portfolio_result):
    import datetime, yaml
    now = datetime.datetime.now()
    yml = {
            "data_path": data_path, 
            "data_range": str(data_range), 
            "data_interval": str(data_interval), 
            "params": convert_to_standard_types(params), 
            "portfolio_result": portfolio_result
        }
    now_str = now.strftime("%Y%m%d_%H%M%S")
    with open(f"result_{now_str}.yaml", "w") as f:
        yaml.dump(yml, f, default_flow_style=False, allow_unicode=True)