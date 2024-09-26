import numpy as np
import os

def read_prices_from_sheets(file_path: str, sheet_names: list, step: int = 1, use_cache: bool = True) -> list:
    # キャッシュファイルのパス（Excelファイルと同じディレクトリに保存）
    cache_file = file_path.replace('.xlsx', '_cache.npy')
    
    # キャッシュを使用する場合
    if use_cache and os.path.exists(cache_file):
        print(f"Loading data from cache: {cache_file}")
        all_prices = np.load(cache_file).tolist()
        return all_prices[::step]  # stepを考慮してデータを返す

    all_prices = []  # 価格データを格納する配列
    import pandas as pd

    # キャッシュが存在しないか、使用しない場合はExcelファイルからデータを読み込む
    print(f"Reading data from Excel: {file_path}")
    for sheet_name in sheet_names:
        df = pd.read_excel(file_path, sheet_name=sheet_name)
        all_prices.extend(df.iloc[:, 1].tolist())  # 2列目が価格データ

    # 読み込んだデータをキャッシュとして保存
    np.save(cache_file, np.array(all_prices))
    print(f"Data cached to: {cache_file}")

    return all_prices[::step]  # stepを考慮してデータを返す