from abc import ABC, abstractmethod
import numpy as np

class Market(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def get_current_price(self):
        pass

class DammyMarket(ABC):
    def __init__(self):
        pass

    def get_current_price(self):
        pass

class BacktestMarket(Market):
    def __init__(self, data: np.ndarray):
        self.data = data
        self.index = 0

    def set_current_index(self, index: int):
        self.index = index

    def get_current_price(self):
        return self.data[self.index]

    def get_data(self):
        return self.data[:self.index]
    
    def __len__(self):
        return len(self.data)
