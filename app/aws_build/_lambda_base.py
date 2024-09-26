import os
import boto3
import base64
import math
import numpy as np
import json
import requests
import time
import traceback
import hashlib
import hmac
from datetime import datetime
import traceback

{Strategy src}

def convert_numpy_array_to_dynamodb(np_array, chunk_size_kb=400):
    # Numpy配列をバイト列に変換
    array_bytes = np_array.tobytes()

    # バイト列をBase64エンコード
    array_base64 = base64.b64encode(array_bytes).decode('utf-8')

    # 分割サイズをバイト単位に変換
    chunk_size = chunk_size_kb * 1024
    num_chunks = math.ceil(len(array_base64) / chunk_size)

    # 分割して保存
    data = {}
    for i in range(num_chunks):
        chunk = array_base64[i * chunk_size:(i + 1) * chunk_size]
        data[str(i)] = chunk
    return data, np_array.dtype

def revert_numpy_array_from_dynamodb(data, dtype):
    # パートを結合
    combined_base64 = b''.join([data[str(i)].encode('utf-8') for i in range(len(data))])

    # Base64デコード
    array_bytes = base64.b64decode(combined_base64)

    # バイト列からNumpy配列に変換
    np_array = np.frombuffer(array_bytes, dtype=dtype)

    return np_array

# データ変換関数
def convert_for_dynamodb(data):
    if data is None:
        return {'NULL': True}
    elif isinstance(data, bool):
        return {'BOOL': data}
    elif isinstance(data, int):
        return {'N': str(data)}
    elif isinstance(data, float):
        return {'F': str(data)}
    elif isinstance(data, str):
        return {'S': data}
    elif isinstance(data, list) or isinstance(data, np.ndarray):
        re_data, dtype = convert_numpy_array_to_dynamodb(np.array(data))
        if "int" in str(dtype):
            k = "LI"
        elif "float" in str(dtype):
            k = "LF"
        else:
            return {'L': [convert_for_dynamodb(item) for item in data]}
        return {k: re_data}
    elif isinstance(data, dict):
        return {'M': {k: convert_for_dynamodb(v) for k, v in data.items()}}
    else:
        raise TypeError(f"Type {type(data)} is not supported")

def revert_from_dynamodb(data):
    if 'NULL' in data:
        return None
    elif 'BOOL' in data:
        return data['BOOL']
    elif 'N' in data:
        return int(data['N'])
    elif 'F' in data:
        return float(data['F'])
    elif 'S' in data:
        return data['S']
    elif 'LI' in data:
        return revert_numpy_array_from_dynamodb(data["LI"], np.int64)
    elif 'LF' in data:
        return revert_numpy_array_from_dynamodb(data["LF"], np.float64)
    elif "L" in data:
        return [revert_from_dynamodb(item) for item in data['L']]
    elif 'M' in data:
        return {k: revert_from_dynamodb(v) for k, v in data['M'].items()}
    else:
        raise TypeError(f"Type {data.keys()} is not supported")

def save_to_dynamodb(table: object, item: dict, partition_key: str):
    """save to dynamoDB

    Args:
        table (object): DynamoDB table
        item (dict): save data
        partition_key (str): partition key of yuor table
    """
    item_converted = {k: convert_for_dynamodb(v) for k, v in item.items()}
    item_converted["id"] = partition_key
    item = json.loads(json.dumps(item_converted))
    
    table.put_item(Item=item)

def read_from_dynamodb(table: object, key_value, partition_key: str) -> dict:
    """read from dynamoDB

    Args:
        table (object): DynamoDB table
        key_value : partition key value of your data
        partition_key (str): partition key of yuor table

    Returns:
        dict: data
    """
    key = {partition_key: key_value}
    response = table.get_item(Key=key)
    item = response.get('Item')
    if item:
        return {k: v if k == partition_key else revert_from_dynamodb(v) for k, v in item.items()}
    else:
        return None

def lambda_handler(event, context):
    try:
        # ビットフライヤーのAPIキーとシークレット
        API_KEY = os.environ["API_KEY"]
        API_SECRET = os.environ["API_SECRET"]
        dynamodb = boto3.resource('dynamodb')
        table = dynamodb.Table(os.environ["TABLE_NAME"])
        
        market = {Market class}()
        market.set_apikey(API_KEY, API_SECRET)        
        strategy = {Strategy class}(market)
        # 環境変数読み込み
        env_variables = {}
        for key, value in os.environ.items():
            try:
                # float に変換
                env_variables[key] = float(value)
            except ValueError:
                # 変換できない場合はそのまま文字列で保持
                env_variables[key] = value
        strategy.reset_param(env_variables)
        try:
            val = read_from_dynamodb(table, os.environ["PARAMS_KEY"], "id")
            if val is not None:
                strategy.dynamic = val
        except:
            pass
        current_price = market.get_current_price()
        signals = strategy.generate_signals(current_price)

        if strategy.trade_limiter():
            strategy.execute_trade(current_price, signals)
        save_to_dynamodb(table, strategy.dynamic, os.environ["PARAMS_KEY"])

    except:
        traceback.print_exc()
    return {
        'statusCode': 200,
        'body': json.dumps('')
    }
