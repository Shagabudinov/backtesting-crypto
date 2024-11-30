# strategies/RsiOscillator.py
from backtesting import Strategy
from backtesting.lib import crossover
import talib

class RsiOscillator(Strategy):
    param_names = ['upper_bound', 'lower_bound', 'rsi_window', 'tp_coef', 'sl_coef']
    upper_bound = 70
    lower_bound = 30
    rsi_window = 14
    tp_coef = 1.15
    sl_coef = 0.95

    def init(self):
        self.rsi = self.I(talib.RSI, self.data.Close, self.rsi_window)

    def next(self):
        price = self.data.Close[-1]
        if crossover(self.rsi, self.upper_bound):
            self.position.close()
        elif crossover(self.lower_bound, self.rsi):
            self.buy(sl=self.sl_coef * price, tp=self.tp_coef * price)
