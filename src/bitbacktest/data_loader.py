import pandas as pd
import numpy as np
import os
import hashlib
import json

def compute_checksum(file_path: str) -> str:
    """Excelファイルのチェックサム（SHA-256）を計算する"""
    hash_sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_sha256.update(chunk)
    return hash_sha256.hexdigest()

def read_prices_from_sheets(file_path: str, sheet_names: list, step: int = 1, use_cache: bool = False) -> list:
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
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            all_data[sheet_name] = df.iloc[:, 1].tolist()  # 2列目が価格データ

        # キャッシュとして保存
        np.save(cache_file, all_data)
        with open(checksum_file, 'w') as f:
            json.dump({"checksum": current_checksum}, f)
        print(f"Data cached to: {cache_file}")

    # 指定したシートのデータのみ取得
    all_prices = []
    for sheet_name in sheet_names:
        if sheet_name in all_data:
            all_prices.extend(all_data[sheet_name][::step])

    return all_prices

