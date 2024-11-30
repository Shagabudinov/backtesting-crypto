# # config.py
from typing import Dict, Any

# AVAILABLE_STRATEGIES: Dict[str, Dict[str, Any]] = {
#     'RsiOscillator': {
#         'class': 'RsiOscillator',
#         'param_grid': {
#             'upper_bound': range(70, 75, 5),
#             'lower_bound': range(30, 35, 5),
#             'rsi_window': range(10, 30, 2),
#             'tp_coef': [round(x, 2) for x in __import__('numpy').arange(1.05, 1.5, 0.01)],
#             'sl_coef': [round(x, 2) for x in __import__('numpy').arange(0.75, 0.99, 0.01)]
#         }
#     },
#     'MovingAverageCrossover': {
#         'class': 'MovingAverageCrossover',
#         'param_grid': {
#             'short_window': range(5, 20, 5),
#             'long_window': range(20, 50, 5)
#         }
#     },
#     'TripleIndicatorStrategy': {
#         'class': 'TripleIndicatorStrategy',
#         'param_grid': {
#             'rsi_upper': range(70, 80, 10),
#             'rsi_lower': range(20, 40, 10),
#             'rsi_window': range(10, 20, 5),
#             'macd_fast': range(10, 14, 4),
#             'macd_slow': range(20, 30, 5),
#             'macd_signal': range(5, 20, 5),
#             'sma_window': range(30, 110, 20),
#             'tp_coef': [round(x, 2) for x in __import__('numpy').arange(1.05, 1.45, 0.2)],
#             'sl_coef': [round(x, 2) for x in __import__('numpy').arange(0.8, 0.98, 0.06)],
#         },
#     }
# }

# # Настройки метрики
# METRIC_KWARGS: Dict[str, Any] = {
#     'trades_weight': 0.4,
#     'winrate_weight': 0.6
# }

# # Настройки данных
# DATA_CONFIG: Dict[str, str] = {
#     'symbol': 'BTC-USD',
#     'period': '1y',
#     'interval': '1h'
# }

# # Параметры мультипериодного теста
# MULTIPERIOD_TEST_CONFIG: Dict[str, Any] = {
#     'window_size': 30 * 24,    # 30 дней * 24 часа = 720 часов
#     'step': 24,                 # Шаг в часах (например, ежедневно)
#     'cash': 10_000_000,         # Начальный капитал
#     'commission': 0.002         # Комиссия
# }

# # Настройки данных для тестирования
# TEST_DATA_CONFIG = {
#     'symbol': 'BTC-USD',       # Символ для тестирования
#     'period': '1y',            # Период данных
#     'interval': '1h'           # Интервал данных
# }

# config.py
from typing import Dict, Any
from strategies import AVAILABLE_STRATEGIES  # Импортируем динамически загруженные стратегии

# Настройки метрики
METRIC_KWARGS: Dict[str, Any] = {
    'trades_weight': 0.4,
    'winrate_weight': 0.6
}

# Настройки данных
DATA_CONFIG: Dict[str, str] = {
    'symbol': 'BTC-USD',
    'period': '1y',
    'interval': '1h'
}

# Параметры мультипериодного теста
MULTIPERIOD_TEST_CONFIG: Dict[str, Any] = {
    'window_size': 30 * 24,    # 30 дней * 24 часа = 720 часов
    'step': 24,                 # Шаг в часах (например, ежедневно)
    'cash': 10_000_000,         # Начальный капитал
    'commission': 0.002         # Комиссия
}

# Настройки данных для тестирования
TEST_DATA_CONFIG = {
    'symbol': 'BTC-USD',       # Символ для тестирования
    'period': '1y',            # Период данных
    'interval': '1h'           # Интервал данных
}

