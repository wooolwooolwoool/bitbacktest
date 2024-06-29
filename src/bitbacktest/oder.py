from typing import Literal

class OrderExecution:
    def __init__(self, market):
        self.portfolio = {}
        self.hist = {}
        self.order = {'Buy': [], 'Sell': []}
        self.market = market

    def set_market(self, market):
        self.market = market

    def reset_portfolio(self, start_cash: float):
        self.portfolio = {"trade_count": 0, 'cash': start_cash, 'position': 0, 'total_value': start_cash}
        self.hist = {"signals": {"Buy": [], "Sell": []},
                     "execute_signals": {"Buy": [], "Sell": []},
                     "total_value_hist": [],
                     "total_pos_hist": []}

    def _execute_buy_order(self, quantity: float, price: float):
        if self.portfolio['cash'] >= quantity * price:
            self.portfolio['cash'] -= quantity * price
            self.portfolio['position'] += quantity
            self.portfolio["trade_count"] += 1
            return True  # Buy order executed successfully
        else:
            return False  # Insufficient funds

    def _execute_sell_order(self, quantity, price):
        if self.portfolio['position'] >= quantity:
            self.portfolio['cash'] += quantity * price
            self.portfolio['position'] -= quantity
            self.portfolio["trade_count"] += 1
            return True  # Sell order executed successfully
        else:
            return False  # Insufficient funds

    def execute_order(self, kind: Literal['Buy', 'Sell'], quantity: float):
        price = self.market.get_current_price()
        if kind == 'Buy':
            return self._execute_buy_order(quantity, price)
        elif kind == 'Sell':
            return self._execute_sell_order(quantity, price)
        else:
            return False

    def add_order(self: Literal['Buy', 'Sell'], kind, quantity: float, price: float):
        if kind == 'Buy' or kind == 'Sell':
            self.order[kind].append({"quantity": quantity, "price": price})
            return True
        else:
            return False

    def check_order(self):
        price = self.market.get_current_price()
        for order in self.order["Sell"]:
            if price >= order["price"]:
                self.execute_order("Sell", order["quantity"])
                self.order["Sell"].remove(order)
        for order in self.order["Buy"]:
            if price <= order["price"]:
                self.execute_order("Buy", order["quantity"])
                self.order["Buy"].remove(order)

    def save_history(self, price: float):
        self.portfolio['total_value'] = self.portfolio['cash'] + self.portfolio['position'] * price
        self.hist["total_value_hist"].append(self.portfolio['total_value'])
        self.hist["total_pos_hist"].append(self.portfolio['position'])

