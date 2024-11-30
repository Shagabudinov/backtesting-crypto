# optimizer.py
import itertools
from multiprocessing import Pool, cpu_count
import pandas as pd
from backtesting import Backtest
from typing import Any, Dict, Tuple
from metrics import combined_metric
import json
import os
import logging
import importlib

def run_backtest(params: Tuple[Any, ...], strategy_class: Any, data: pd.DataFrame, metric_func, metric_kwargs: Dict = {}) -> Dict:
    """
    Выполняет бэктест для заданной комбинации параметров стратегии.
    """
    print(params)
    # Извлекаем имена параметров стратегии
    param_names = strategy_class.param_names
    
    # Создаем словарь параметров
    params_dict = dict(zip(param_names, params))

    # Создаем экземпляр стратегии, передаем и данные, и параметры
    strategy_instance = strategy_class

    # Создаем бэктест
    bt = Backtest(data, strategy_instance, cash=10_000_000, commission=0.002)

    # Запускаем бэктест
    stats = bt.run()

    # Вычисляем комбинированную метрику
    metric = metric_func(stats, **metric_kwargs)
    stats['metric'] = metric
    for param, value in zip(param_names, params):
        stats[param] = value

    return stats




def worker(args):
    """
    Рабочая функция для multiprocessing.Pool.map.
    Распаковывает аргументы и вызывает run_backtest.
    """
    params, strategy_class_name, data, metric_func, metric_kwargs = args
    # Dynamically import strategy class inside worker
    try:
        strategies_module = importlib.import_module(f"strategies.{strategy_class_name}")
        strategy_class = getattr(strategies_module, strategy_class_name)
    except Exception as e:
        logging.error(f"Ошибка импорта стратегии '{strategy_class_name}': {e}")
        return {}

    return run_backtest(params, strategy_class, data, metric_func, metric_kwargs)


def optimize(strategy_class: Any, data: pd.DataFrame, param_grid: Dict[str, Any], metric_func, metric_kwargs: Dict = {}) -> pd.DataFrame:
    """
    Оптимизирует параметры стратегии с использованием многопроцессорности.
    """
    # Генерируем все возможные комбинации параметров
    param_names = list(param_grid.keys())
    param_values = list(param_grid.values())
    all_params = list(itertools.product(*param_values))

    print(f"Всего комбинаций для оптимизации: {len(all_params)}")

    # Подготовка параметров для передачи в Pool.map
    tasks = [(params, strategy_class.__name__, data, metric_func, metric_kwargs) for params in all_params]

    # Определяем количество доступных процессов
    num_processes = cpu_count()
    print(f"Используется процессов: {num_processes}")

    # Создаём пул процессов и запускаем оптимизацию
    with Pool(processes=num_processes) as pool:
        results = pool.map(worker, tasks)

    # Преобразуем результаты в DataFrame для удобного анализа
    df = pd.DataFrame(results)

    # Сортируем по комбинированной метрике в порядке убывания
    df_sorted = df.sort_values(by='metric', ascending=False).reset_index(drop=True)

    return df_sorted

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
        raise FileNotFoundError(f"Файл с лучшими параметрами для стратегии '{strategy_name}' не найден.")
    
    with open(best_stats_path, 'r', encoding='utf-8') as f:
        best_params = json.load(f)
    
    return best_params

def get_strategy_class(strategy_name: str):
    """
    Получает класс стратегии по её имени из модуля strategies.<strategy_name>.py.
    
    :param strategy_name: Имя стратегии.
    :return: Класс стратегии.
    """
    try:
        strategies_module = importlib.import_module(f"strategies.{strategy_name}")
        strategy_class = getattr(strategies_module, strategy_name)
        return strategy_class
    except (ImportError, AttributeError) as e:
        logging.error(f"Стратегия '{strategy_name}' не найдена в модуле 'strategies.{strategy_name}'. Ошибка: {e}")
        raise e

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
