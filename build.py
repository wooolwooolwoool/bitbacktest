class BitflyerMarket(Market):
    def __init__(self):
        super().__init__()
        self.apikey = None
        self.secret = None
        self.API_URL = 'https://api.bitflyer.jp'
        self.product_code = 'BTC_JPY'

    def set_apikey(self, apikey, secret):
        self.apikey = apikey
        self.secret = secret

    def place_market_order(self, side, quantity):
        # 成行注文を出す
        if self.apikey is None or self.secret is None:
            raise ValueError("API key and secret must be set before placing an order.")

        endpoint = '/v1/me/sendchildorder'
        order_url = self.API_URL + endpoint

        order_data = {
            'product_code': self.product_code,
            'child_order_type': 'MARKET',
            'side': side,
            'size': quantity,
        }
        body = json.dumps(order_data)
        headers = self.header('POST', endpoint=endpoint, body=body)

        response = requests.post(order_url, headers=headers, data=body)
        return response.json()

    def place_limit_order(self, side: Literal['Buy', 'Sell'], quantity: float, price: float):
        if self.apikey is None or self.secret is None:
            raise ValueError("API key and secret must be set before placing an order.")

        # 指値注文を出す
        endpoint = '/v1/me/sendchildorder'
        order_url = self.API_URL + endpoint

        order_data = {
            'product_code': self.product_code,
            'child_order_type': 'LIMIT',
            'side': side,
            'price': price,
            'size': quantity,
        }
        body = json.dumps(order_data)
        headers = self.header('POST', endpoint=endpoint, body=body)

        response = requests.post(order_url, headers=headers, data=body)
        if responce.code == "200":
            return True
        else:
            return False


    def cancel_order(self, side: Literal['Buy', 'Sell'], order_id: int):
        return True

    def header(method: str, endpoint: str, body: str) -> dict:
        timestamp = str(time.time())
        if body == '':
            message = timestamp + method + endpoint
        else:
            message = timestamp + method + endpoint + body
        signature = hmac.new(self.secret.encode('utf-8'), message.encode('utf-8'),
                            digestmod=hashlib.sha256).hexdigest()
        headers = {
            'Content-Type': 'application/json',
            'ACCESS-KEY': self.API_KEY,
            'ACCESS-TIMESTAMP': timestamp,
            'ACCESS-SIGN': signature
        }
        return headers

    def get_open_orders():
        # 出ている注文一覧を取得
        endpoint = '/v1/me/getchildorders'
        
        params = {
            'product_code': 'BTC_JPY',
            'child_order_state': 'ACTIVE',  # 出ている注文だけを取得
        }
        endpoint_for_header = endpoint + '?'
        for k, v in params.items():
            endpoint_for_header += k + '=' + v
            endpoint_for_header += '&'
        endpoint_for_header = endpoint_for_header[:-1]
        
        headers = header('GET', endpoint=endpoint_for_header, body="")

        response = requests.get(API_URL + endpoint, headers=headers, params=params)
        orders = response.json()
        return orders

