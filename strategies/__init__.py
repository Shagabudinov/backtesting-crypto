# strategies/__init__.py
import os
import importlib
import glob
from typing import Dict, Any
from backtesting import Strategy

AVAILABLE_STRATEGIES: Dict[str, Dict[str, Any]] = {}

# Путь к директории со стратегиями
strategies_dir = os.path.dirname(__file__)
strategy_files = glob.glob(os.path.join(strategies_dir, "*.py"))

for file in strategy_files:
    if os.path.basename(file).startswith("__"):
        continue
    module_name = os.path.splitext(os.path.basename(file))[0]
    try:
        module = importlib.import_module(f".{module_name}", package="strategies")
    except Exception as e:
        print(f"Не удалось импортировать модуль '{module_name}': {e}")
        continue
    for attr in dir(module):
        obj = getattr(module, attr)
        if isinstance(obj, type) and issubclass(obj, Strategy) and obj is not Strategy:
            strategy_class = obj
            strategy_name = strategy_class.__name__
            # Получаем param_grid из AVAILABLE_Strategies, если он установлен через API
            param_grid = AVAILABLE_STRATEGIES.get(strategy_name, {}).get('param_grid', getattr(strategy_class, 'param_grid', {}))
            if not isinstance(param_grid, dict):
                param_grid = {}
            AVAILABLE_STRATEGIES[strategy_name] = {
                'class': strategy_name,
                'param_grid': param_grid
            }
            # Печатаем param_grid для отладки
            print(f"Стратегия: {strategy_name}, param_grid: {param_grid}")
