from backtesting import Strategy
from backtesting.lib import crossover
import talib

class MovingAverageCrossover(Strategy):
    param_names = ['short_window', 'long_window']
    short_window = 10
    long_window = 30

    def init(self):
        self.short_ma = self.I(talib.SMA, self.data.Close, self.short_window)
        self.long_ma = self.I(talib.SMA, self.data.Close, self.long_window)

    def next(self):
        if crossover(self.short_ma, self.long_ma):
            self.position.close()
            self.buy()
        elif crossover(self.long_ma, self.short_ma):
            self.position.close()
            self.sell()