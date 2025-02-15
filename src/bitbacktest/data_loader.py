import pandas as pd
import numpy as np
import os
import hashlib
import json
import datetime
import functools

def compute_checksum(file_path: str) -> str:
    """Excelファイルのチェックサム（SHA-256）を計算する"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

@functools.cache
def read_prices_from_chash(file_path, use_cache=True):
    # キャッシュファイルとチェックサムファイルのパス
    cache_file = file_path.replace('.xlsx', '_cache.npy')
    checksum_file = file_path.replace('.xlsx', '_checksum.json')

    # チェックサムの読み込みとExcelファイルの更新確認
    current_checksum = compute_checksum(file_path)
    is_cache_valid = False

    if os.path.exists(checksum_file):
        with open(checksum_file, 'r') as f:
            cached_data = json.load(f)
            if cached_data.get("checksum") == current_checksum:
                is_cache_valid = True

    # キャッシュを使用する場合で、有効なキャッシュが存在する場合
    if use_cache and is_cache_valid and os.path.exists(cache_file):
        print(f"Loading data from cache: {cache_file}")
        all_data = np.load(cache_file, allow_pickle=True).item()
    else:
        print(f"Reading data from Excel: {file_path}")
        all_data = {}

        # Excelファイルから各シートの価格データを取得
        for sheet_name in pd.ExcelFile(file_path).sheet_names:
            print(f"Loading : {sheet_name}")
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            all_data[sheet_name] = {}
            all_data[sheet_name]["date"] = df.iloc[:, 0].tolist()  # 2列目が価格データ
            all_data[sheet_name]["price"] = df.iloc[:, 1].tolist()  # 2列目が価格データ

        # キャッシュとして保存
        np.save(cache_file, all_data)
        with open(checksum_file, 'w') as f:
            json.dump({"checksum": current_checksum}, f)
        print(f"Data cached to: {cache_file}")
    return all_data

def read_prices_from_sheets(file_path: str, datetime_range: list, step: int = 1,
                            use_cache: bool = False, with_date: bool = False) -> list:
    all_data = read_prices_from_chash(file_path, use_cache)
    # 指定したシートのデータのみ取得
    all_prices = []
    all_dates = []
    start_sheet = datetime_range[0].strftime("%Y%m")
    end_sheet = datetime_range[1].strftime("%Y%m")
    tmp = start_sheet if start_sheet in all_data else sorted(all_data.keys())[0]
    sheet_names = []
    while True:
        sheet_names.append(tmp)
        if tmp == end_sheet or tmp == sorted(all_data.keys())[-1]:
            break
        tmp = (datetime.datetime.strptime(tmp, "%Y%m") + pd.DateOffset(months=1)).strftime("%Y%m")
    datetime_format = "%Y%m%d%H%M%S"
    for i, sheet_name in enumerate(sheet_names):
        if sheet_name in all_data:
            start_idx = 0
            end_idx = len(all_data[sheet_name]["date"])
            if i==0:
                for idx, date in enumerate(all_data[sheet_name]["date"]):
                    if date >= datetime_range[0]:
                        start_idx = idx
                        break
            elif i==len(sheet_names)-1:
                for idx, date in enumerate(all_data[sheet_name]["date"]):
                    if date >= datetime_range[1]:
                        end_idx = idx
                        break
            all_prices.extend(all_data[sheet_name]["price"][start_idx:end_idx:step])
            if with_date:
                all_dates.extend(all_data[sheet_name]["date"][start_idx:end_idx:step])
    if with_date:
        return all_dates, all_prices
    return all_prices

