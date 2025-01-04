class TradeExecutor():
    def execute_trade(self, price, signal):
        pass
    
class NormalExecutor(TradeExecutor):
    def execute_trade(self, price, signal):
        if signal in ['Buy', "Sell"]:
            self.market.place_market_order(signal,
                                           self.static["one_order_quantity"])
        
class SpreadOrderExecutor(TradeExecutor):
    def execute_trade(self, price, signal):
        if signal in ['Buy', "Sell"]:
            if signal == 'Buy':
                trade_price = price * self.static["trade_rate_buy"]
            else:
                trade_price = price * self.static["trade_rate_sell"]
            self.market.place_limit_order(signal,
                                           self.static["one_order_quantity"],
                                           trade_price)