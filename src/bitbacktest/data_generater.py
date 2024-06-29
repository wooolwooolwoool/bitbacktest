import random
import numpy as np

def random_data(start_price, price_range, length, seed=None):
    if seed is not None:
        random.seed(seed)
    price = start_price
    price_data = []

    for p in range(length):
        price *= 1 + random.uniform(-price_range, price_range)
        price_data.append(price)
    price_data = np.array(price_data)
    return price_data