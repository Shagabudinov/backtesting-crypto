# multiperiod_test.py
import os
import sys
import json
import pandas as pd
import matplotlib.pyplot as plt
import plotly.express as px
import logging
import importlib

from backtesting import Backtest

from data_fetcher import get_data
from test_config import STRATEGY_NAME, TEST_DATA_CONFIG, MULTIPERIOD_TEST_CONFIG

def setup_logging():
    """
    Настраивает логирование.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("multiperiod_test.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )

def load_best_params(strategy_name: str) -> dict:
    """
    Загружает лучшие параметры для указанной стратегии из JSON файла.
    
    :param strategy_name: Имя стратегии.
    :return: Словарь с лучшими параметрами.
    """
    script_dir = os.path.dirname(__file__)
    best_stats_dir = os.path.join(script_dir, 'best_stats')
    best_stats_filename = f"{strategy_name}_best_stats.json"
    best_stats_path = os.path.join(best_stats_dir, best_stats_filename)
    
    if not os.path.exists(best_stats_path):
        logging.error(f"Файл с лучшими параметрами для стратегии '{strategy_name}' не найден в папке 'best_stats'.")
        sys.exit(1)
    
    with open(best_stats_path, 'r', encoding='utf-8') as f:
        best_params = json.load(f)
    
    return best_params

def get_strategy_class(strategy_name: str):
    """
    Получает класс стратегии по её имени из модуля strategies.py.
    
    :param strategy_name: Имя стратегии.
    :return: Класс стратегии.
    """
    try:
        strategies_module = importlib.import_module('strategies')
        strategy_class = getattr(strategies_module, strategy_name)
        return strategy_class
    except (ImportError, AttributeError) as e:
        logging.error(f"Стратегия '{strategy_name}' не найдена в модуле 'strategies.py'. Ошибка: {e}")
        sys.exit(1)

def apply_params_to_strategy(strategy_class, params: dict):
    """
    Применяет параметры к классу стратегии.
    
    :param strategy_class: Класс стратегии.
    :param params: Словарь параметров.
    """
    for param, value in params.items():
        if hasattr(strategy_class, param):
            setattr(strategy_class, param, value)
            logging.info(f"Параметр '{param}' установлен в значение {value}.")
        else:
            logging.warning(f"Внимание: стратегия {strategy_class.__name__} не имеет параметра '{param}'.")

def multiperiod_test():
    setup_logging()
    logging.info("Начало мультипериодного тестирования стратегии.")
    
    # Загрузите лучшие параметры стратегии
    best_params = load_best_params(STRATEGY_NAME)
    logging.info(f"Лучшие параметры для стратегии '{STRATEGY_NAME}':")
    logging.info(best_params)
    
    # Получите класс стратегии из имени
    strategy_class = get_strategy_class(STRATEGY_NAME)
    
    # Примените лучшие параметры к стратегии
    apply_params_to_strategy(strategy_class, best_params)
    
    # Загрузите данные для тестирования
    data = get_data(
        symbol=TEST_DATA_CONFIG['symbol'],
        period=TEST_DATA_CONFIG['period'],
        interval=TEST_DATA_CONFIG['interval']
    )
    
    logging.info("Данные для тестирования загружены успешно.")
    
    # Настройки мультипериодного теста
    window_size = MULTIPERIOD_TEST_CONFIG['window_size']
    step = MULTIPERIOD_TEST_CONFIG['step']
    cash = MULTIPERIOD_TEST_CONFIG['cash']
    commission = MULTIPERIOD_TEST_CONFIG['commission']
    
    returns = []
    
    for x in range(window_size, len(data) + 1, step):
        try:
            # Выбираем данные за последние window_size часов
            window_data = data.iloc[x - window_size:x]
            
            bt = Backtest(
                window_data,
                strategy_class,
                cash=cash,
                commission=commission
            )
            
            # Запуск стратегии с лучшими параметрами
            stats = bt.run()
            
            if stats["# Trades"] > 0:
                logging.info(f"Период {x - window_size} - {x}: Return [%] = {stats['Return [%]']}")
                returns.append(stats["Return [%]"])
            else:
                logging.info(f"Период {x - window_size} - {x}: Сделки не были совершены.")
        except Exception as e:
            logging.error(f"Ошибка в периоде {x - window_size} - {x}: {e}")
            continue
    
    if not returns:
        logging.warning("Нет сделок для анализа в мультипериодном тесте.")
        sys.exit(0)
    
    # Визуализация результатов
    fig = px.box(returns, points="all", title=f"Мультипериодный тест: Распределение доходности (%) для {STRATEGY_NAME}")
    fig.update_layout(
        xaxis_title="Стратегия",
        yaxis_title="Доходность (%)",
    )
    fig.show()

if __name__ == '__main__':
    multiperiod_test()
