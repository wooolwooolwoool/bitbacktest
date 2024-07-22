import sys, os

sys.path.append(".")
from src.bitbacktest.market import BitflyerMarket
import unittest


class TestGetOrder(unittest.TestCase):

    def test_get_open_orders(self):
        API_KEY = os.environ["API_KEY"]
        API_SECRET = os.environ["API_SECRET"]

        bitflyer = BitflyerMarket()
        bitflyer.set_apikey(API_KEY, API_SECRET)

        orders = bitflyer.get_open_orders()
        self.assertIsNotNone(orders)
        self.assertGreater(len(orders), 0)
