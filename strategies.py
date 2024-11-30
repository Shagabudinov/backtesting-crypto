# strategies.py
from backtesting import Strategy
from backtesting.lib import crossover, resample_apply
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

class TripleIndicatorStrategy(Strategy):
    param_names = [
        'rsi_upper', 'rsi_lower', 'rsi_window',
        'macd_fast', 'macd_slow', 'macd_signal',
        'sma_window', 'tp_coef', 'sl_coef'
    ]
    rsi_upper = 70
    rsi_lower = 30
    rsi_window = 14
    macd_fast = 12
    macd_slow = 26
    macd_signal = 9
    sma_window = 50  # Дневная SMA

    tp_coef = 1.15  # Тейк-профит
    sl_coef = 0.95  # Стоп-лосс

    def init(self):
        # Инициализация индикаторов
        self.rsi = self.I(talib.RSI, self.data.Close, self.rsi_window)

        macd, macd_signal_line, macd_hist = talib.MACD(
            self.data.Close,
            fastperiod=self.macd_fast,
            slowperiod=self.macd_slow,
            signalperiod=self.macd_signal
        )
        self.macd = self.I(lambda x: macd, self.data.Close)
        self.macd_signal_line = self.I(lambda x: macd_signal_line, self.data.Close)

        self.daily_sma = resample_apply(
            'D', talib.SMA, self.data.Close, self.sma_window, plot=False
        )

    def next(self):
        price = self.data.Close[-1]

        # Лонг
        if (
            self.rsi[-1] < self.rsi_lower and
            self.macd[-1] > self.macd_signal_line[-1] and
            self.data.Close[-1] > self.daily_sma[-1]
        ):
            tp = self.tp_coef * price
            sl = self.sl_coef * price
            self.buy(sl=sl, tp=tp)

        elif (
            self.rsi[-1] > self.rsi_upper or
            self.macd[-1] < self.macd_signal_line[-1] or
            self.data.Close[-1] < self.daily_sma[-1]
        ):
            self.position.close()

        # Шорт
        if (
            self.rsi[-1] > self.rsi_upper and
            self.macd[-1] < self.macd_signal_line[-1] and
            self.data.Close[-1] < self.daily_sma[-1]
        ):
            tp = price / self.tp_coef  # Для шорта TP ниже цены
            sl = price / self.sl_coef  # Для шорта SL выше цены
            self.sell(sl=sl, tp=tp)

        elif (
            self.rsi[-1] < self.rsi_lower or
            self.macd[-1] > self.macd_signal_line[-1] or
            self.data.Close[-1] > self.daily_sma[-1]
        ):
            self.position.close()

