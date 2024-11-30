# main.py
import sys
import io
import os
import json
import numpy as np
import pandas as pd
import pickle
import warnings
import logging
from datetime import datetime
import argparse

from backtesting import Backtest, Strategy
from backtesting.lib import crossover, resample_apply

import matplotlib.pyplot as plt
import plotly.express as px

from data_fetcher import get_data
from optimizer import optimize
from config import AVAILABLE_STRATEGIES, METRIC_KWARGS, DATA_CONFIG, MULTIPERIOD_TEST_CONFIG
from metrics import combined_metric
from runner import walk_forward, plot_walk_forward_results, run_strategy

# Игнорируем FutureWarning от pandas
warnings.simplefilter(action='ignore', category=FutureWarning)

# Устанавливаем кодировку для корректного отображения русских символов
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/main.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger()

def main():
    """
    Главная функция для запуска стратегии.
    """
    import argparse

    parser = argparse.ArgumentParser(description='Запуск стратегии.')
    parser.add_argument('--strategy', type=str, required=True, help='Имя стратегии для запуска')

    args = parser.parse_args()

    run_strategy(args.strategy)

if __name__ == '__main__':
    main()
