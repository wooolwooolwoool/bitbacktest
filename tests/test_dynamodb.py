import os
from bitbacktest.utils.dynamodb import *

# テスト用データ
sample_data = {
    'id': '12345',  # パーティションキー
    'name': 'John Doe',
    'age': 30,
    'height': 5.75,
    'married': True,
    'children': None,
    'hobbies': ['reading', 'travelling'],
    'address': {
        'street': '123 Main St',
        'city': 'Anytown',
        'zipcode': None
    }
}

aws_access_key_id = os.environ["aws_access_key_id"]
aws_secret_access_key = os.environ["aws_secret_access_key"]

table_name = os.environ["table_name"]
region_name = os.environ["region_name"]

table = get_dynamodb_table(table_name, aws_access_key_id, aws_secret_access_key, region_name)

# データの保存
partition_key = 'id'  # パーティションキーのフィールド名
save_to_dynamodb(table, sample_data, partition_key)
print(f"Data saved to DynamoDB: {sample_data}")

# データの読み取り
retrieved_data = read_from_dynamodb(table, sample_data[partition_key], partition_key)
print(f"Data retrieved from DynamoDB: {retrieved_data}")