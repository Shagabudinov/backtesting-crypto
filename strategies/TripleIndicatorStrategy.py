from backtesting import Strategy
from backtesting.lib import resample_apply
import talib

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