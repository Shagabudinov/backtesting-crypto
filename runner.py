# runner.py
import importlib
import os
import json
import logging
from backtesting import Backtest, Strategy
from config import METRIC_KWARGS, DATA_CONFIG, MULTIPERIOD_TEST_CONFIG
from data_fetcher import get_data
from optimizer import optimize
from metrics import combined_metric
import pickle
import traceback
import pandas as pd
import numpy as np
import datetime
from strategies import AVAILABLE_STRATEGIES

def serialize(obj):
    if isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    elif isinstance(obj, pd.Timedelta):
        return str(obj)
    elif isinstance(obj, datetime.datetime):
        return obj.isoformat()
    elif isinstance(obj, datetime.timedelta):
        return str(obj)
    elif isinstance(obj, (np.integer, int)):
        return int(obj)
    elif isinstance(obj, (np.floating, float)):
        return float(obj)
    elif isinstance(obj, (np.bool_, bool)):
        return bool(obj)
    elif isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [serialize(v) for v in obj]
    else:
        return str(obj)  # Fallback to string

def convert_types(params_dict):
    """
    Преобразует значения в стандартные типы Python для сериализации в JSON.
    """
    converted = {}
    for key, value in params_dict.items():
        if isinstance(value, np.integer):
            converted[key] = int(value)
        elif isinstance(value, np.floating):
            converted[key] = float(value)
        else:
            converted[key] = value
    return converted

def walk_forward(strategy: Strategy, data_full: pd.DataFrame, warmup_bars: int, lookback_bars: int = 28*24, validation_bars: int = 7*24, cash: float = 10_000_000, commission: float = 0.002):
    """
    Реализует процесс walk-forward тестирования.
    """
    logger = logging.getLogger(__name__)
    stats_master = []

    for i in range(lookback_bars, len(data_full)-validation_bars, validation_bars):
        logger.info(f"Текущее положение: {i} из {len(data_full)}")

        # Обучающая выборка
        train_start = i - lookback_bars
        train_end = i
        sample_data = data_full.iloc[train_start:train_end]

        # Оптимизация параметров на обучающей выборке
        logger.info(f"Оптимизация параметров на обучающей выборке: {train_start} - {train_end}")
        bt_training = Backtest(sample_data, strategy, cash=cash, commission=commission)
        try:
            stats_training = bt_training.optimize(
                **strategy.param_grid,
                maximize='Equity Final [$]'
            )
        except Exception as e:
            logger.error(f"Ошибка оптимизации на обучающей выборке: {e}")
            logger.error(traceback.format_exc())
            continue

        # Извлечение оптимизированных параметров
        optimized_params = {param: getattr(stats_training._strategy, param) for param in strategy.param_grid.keys()}

        logger.info(f"Оптимизированные параметры: {optimized_params}")

        # Валидационная выборка
        validation_start = i - warmup_bars
        validation_end = i + validation_bars
        validation_data = data_full.iloc[validation_start:validation_end]

        # Тестирование на валидационной выборке с оптимизированными параметрами
        logger.info(f"Тестирование на валидационной выборке: {validation_start} - {validation_end}")
        # Применяем оптимизированные параметры к стратегии
        for param, value in optimized_params.items():
            setattr(strategy, param, value)

        bt_validation = Backtest(
            validation_data, 
            strategy,
            cash=cash, 
            commission=commission
        )
        try:
            stats_validation = bt_validation.run()
        except Exception as e:
            logger.error(f"Ошибка тестирования на валидационной выборке: {e}")
            logger.error(traceback.format_exc())
            continue

        stats_master.append(stats_validation)
        logger.info(f"Результаты теста: Return [%] = {stats_validation['Return [%]']}")

    return stats_master

def plot_walk_forward_results(stats_master, strategy_name):
    """
    Визуализирует результаты walk-forward тестирования.
    """
    import matplotlib.pyplot as plt
    import plotly.express as px
    logger = logging.getLogger(__name__)

    returns = [stat["Return [%]"] for stat in stats_master if stat["# Trades"] > 0]

    if not returns:
        logger.warning("Нет сделок для анализа в walk-forward тестировании.")
        # Создаём пустой график с уведомлением
        fig = px.box(
            [0],
            points="all",
            title=f"Walk-Forward тестирование: Распределение доходности (%) для {strategy_name}\nНет сделок для отображения."
        )
        fig.update_layout(
            xaxis_title="Стратегия",
            yaxis_title="Доходность (%)",
        )
    else:
        # Визуализация распределения доходности
        fig = px.box(
            returns,
            points="all",
            title=f"Walk-Forward тестирование: Распределение доходности (%) для {strategy_name}"
        )
        fig.update_layout(
            xaxis_title="Стратегия",
            yaxis_title="Доходность (%)",
        )

    # Сохранение графика как HTML
    plots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plots', 'walk_forward')
    os.makedirs(plots_dir, exist_ok=True)
    plot_filename = f"{strategy_name}_walk_forward_results.html"
    plot_path = os.path.join(plots_dir, plot_filename)

    try:
        fig.write_html(plot_path)
        logger.info(f"График walk-forward тестирования сохранён в '{plot_path}'")
    except Exception as e:
        logger.error(f"Не удалось сохранить график walk-forward тестирования: {e}")
        logger.error(traceback.format_exc())

    # Визуализация equity curve для каждого окна
    plt.figure(figsize=(10, 6))
    for idx, stat in enumerate(stats_master):
        equity = stat._equity_curve
        plt.plot(equity.index, equity['Equity'], label=f'Окно {idx+1}')

    plt.title(f"Walk-Forward тестирование: Equity Curve для {strategy_name}")
    plt.xlabel("Дата")
    plt.ylabel("Equity [$]")
    plt.legend()
    plt.tight_layout()
    equity_plot_path = os.path.join(plots_dir, f"{strategy_name}_equity_curve.png")
    try:
        plt.savefig(equity_plot_path)
        plt.close()
        logger.info(f"Equity curve сохранён в '{equity_plot_path}'")
    except Exception as e:
        logger.error(f"Не удалось сохранить Equity curve: {e}")
        logger.error(traceback.format_exc())

def run_strategy(strategy_name: str):
    """
    Функция для запуска выбранной стратегии.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Запуск стратегии: {strategy_name}")

    # Определяем базовую директорию
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(BASE_DIR, 'results')
    plots_dir = os.path.join(BASE_DIR, 'plots')
    os.makedirs(results_dir, exist_ok=True)
    os.makedirs(plots_dir, exist_ok=True)
    last_run_result_path = os.path.join(results_dir, 'last_run_result.json')
    strategy_run_result_path = os.path.join(results_dir, f'{strategy_name}_run_result.json')

    if strategy_name not in AVAILABLE_STRATEGIES:
        logger.error(f"Стратегия '{strategy_name}' не найдена.")
        return

    strategy_info = AVAILABLE_STRATEGIES[strategy_name]
    strategy_class_name = strategy_info['class']

    # Импортируем класс стратегии из strategies/<strategy_name>.py
    try:
        strategies_module = importlib.import_module(f".{strategy_name}", package="strategies")
        strategy_class = getattr(strategies_module, strategy_class_name)
    except Exception as e:
        logger.error(f"Не удалось импортировать стратегию '{strategy_name}': {e}")
        logger.error(traceback.format_exc())
        return

    # Создаем экземпляр стратегии
    strategy = strategy_class

    # Получаем данные
    try:
        data = get_data(
            symbol=DATA_CONFIG['symbol'],
            period=DATA_CONFIG['period'],
            interval=DATA_CONFIG['interval']
        )
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных: {e}")
        logger.error(traceback.format_exc())
        return

    logger.info("Данные загружены успешно.")

    # Разделение данных на обучающую и тестовую выборки
    test_period = '30d'
    test_end = data.index.max()
    test_start = test_end - pd.Timedelta(test_period)
    train_data = data[data.index < test_start]
    test_data = data[data.index >= test_start]

    logger.info(f"Обучающая выборка: {train_data.index.min()} - {train_data.index.max()}")
    logger.info(f"Тестовая выборка: {test_data.index.min()} - {test_data.index.max()}")

    # Оптимизация параметров стратегии на обучающих данных
    logger.info("Начинается оптимизация параметров стратегии на обучающих данных.")
    try:
        results_df = optimize(
            strategy_class=strategy,
            data=train_data,
            param_grid=strategy_info['param_grid'],
            metric_func=combined_metric,  # Импортированная функция
            metric_kwargs=METRIC_KWARGS
        )
    except Exception as e:
        logger.error(f"Ошибка оптимизации стратегии: {e}")
        logger.error(traceback.format_exc())
        return

    # Сохраняем результаты оптимизации в CSV
    optimization_results_path = os.path.join(results_dir, 'optimization_results.csv')
    try:
        results_df.to_csv(optimization_results_path, index=False)
        logger.info(f"Результаты оптимизации сохранены в '{optimization_results_path}'")
    except Exception as e:
        logger.error(f"Ошибка при сохранении результатов оптимизации: {e}")
        logger.error(traceback.format_exc())

    # Выбираем лучшую комбинацию параметров
    if results_df.empty:
        logger.warning("Нет результатов оптимизации для сохранения.")
        return

    best = results_df.iloc[0]
    logger.info("Лучшая комбинация параметров:")
    logger.info(best)

    # Создаём папку 'best_stats', если она не существует
    best_stats_dir = os.path.join(BASE_DIR, 'best_stats')
    os.makedirs(best_stats_dir, exist_ok=True)

    # Формируем имя файла на основе имени стратегии
    best_stats_filename = f"{strategy_name}_best_stats.json"
    best_stats_path = os.path.join(best_stats_dir, best_stats_filename)

    # Извлекаем только параметры стратегии
    best_params = {param: best[param] for param in strategy_info['param_grid'].keys()}

    # Преобразуем типы параметров
    best_params_converted = convert_types(best_params)

    # Сохраняем лучшие параметры в JSON файл
    try:
        with open(best_stats_path, 'w', encoding='utf-8') as f:
            json.dump(best_params_converted, f, ensure_ascii=False, indent=4)
        logger.info(f"Лучшие параметры сохранены в '{best_stats_path}'")
    except Exception as e:
        logger.error(f"Ошибка при сохранении лучших параметров: {e}")
        logger.error(traceback.format_exc())

    # Проведение walk-forward тестирования на тестовых данных
    logger.info("Начало walk-forward тестирования на тестовых данных.")
    lookback_bars = MULTIPERIOD_TEST_CONFIG.get('window_size', 30 * 24)     # 30 дней * 24 часа = 720 часов
    validation_bars = MULTIPERIOD_TEST_CONFIG.get('step', 24)             # Шаг в часах (например, ежедневно)
    warmup_bars = MULTIPERIOD_TEST_CONFIG.get('warmup_bars', 14 * 24)    # 14 дней * 24 часа = 336 часов

    try:
        stats_master = walk_forward(
            strategy=strategy,
            data_full=test_data,
            warmup_bars=warmup_bars,
            lookback_bars=lookback_bars,
            validation_bars=validation_bars,
            cash=MULTIPERIOD_TEST_CONFIG.get('cash', 10_000_000),
            commission=MULTIPERIOD_TEST_CONFIG.get('commission', 0.002)
        )
    except Exception as e:
        logger.error(f"Ошибка walk-forward тестирования: {e}")
        logger.error(traceback.format_exc())
        return

    # Сохранение результатов walk-forward тестирования
    walk_forward_stats_path = os.path.join(results_dir, 'walk_forward_stats.pickle')
    try:
        with open(walk_forward_stats_path, "wb") as f:
            pickle.dump(stats_master, f)
        logger.info(f"Результаты walk-forward тестирования сохранены в '{walk_forward_stats_path}'")
    except Exception as e:
        logger.error(f"Ошибка при сохранении результатов walk-forward тестирования: {e}")
        logger.error(traceback.format_exc())

    # Создание Backtest для тестовых данных с оптимизированными параметрами
    logger.info("Создание Backtest для тестовых данных с оптимизированными параметрами.")
    try:
        # Применить лучшие параметры к стратегии
        for param, value in best_params_converted.items():
            setattr(strategy, param, value)

        # Создать Backtest для тестовых данных с оптимизированными параметрами
        bt_final = Backtest(test_data, strategy, cash=MULTIPERIOD_TEST_CONFIG.get('cash', 10_000_000), commission=MULTIPERIOD_TEST_CONFIG.get('commission', 0.002))
        stats_final = bt_final.run()

        # Создать папку для HTML-плотов выбранной стратегии
        strategy_plots_dir = os.path.join(plots_dir, strategy_name)
        os.makedirs(strategy_plots_dir, exist_ok=True)

        # Определяем путь для сохранения HTML-плота
        plot_filename = 'latest.html'
        plot_path = os.path.join(strategy_plots_dir, plot_filename)

        # Генерация HTML-плота
        bt_final.plot(
            filename=plot_path,
            plot_width=800,
            plot_equity=True,
            plot_return=True,
            plot_pl=True,
            plot_volume=True,
            plot_drawdown=True,
            smooth_equity=False,
            relative_equity=True,
            superimpose=True,
            resample=True,
            reverse_indicators=False,
            show_legend=True,
            open_browser=False
        )
        logger.info(f"HTML-плот сохранён в '{plot_path}'")

        # Добавление пути к HTML-плоту и лучшим параметрам в last_run_result.json
        last_run_result = {
            "strategy": strategy_name,
            "status": "completed",
            "walk_forward_stats": walk_forward_stats_path,
            "plot": plot_path,
            "best_parameters": best_params_converted,
            "backtest_summary": serialize(stats_final.to_dict())
        }
        try:
            with open(last_run_result_path, 'w', encoding='utf-8') as f:
                json.dump(last_run_result, f, ensure_ascii=False, indent=4)
            with open(strategy_run_result_path, 'w', encoding='utf-8') as f:
                json.dump(last_run_result, f, ensure_ascii=False, indent=4)
            logger.info(f"Путь к HTML-плоту и лучшие параметры добавлены в '{last_run_result_path}'")
        except Exception as e:
            logger.error(f"Ошибка при сохранении last_run_result.json: {e}")
            logger.error(traceback.format_exc())

    except Exception as e:
        logger.error(f"Ошибка при генерации HTML-плота: {e}")
        logger.error(traceback.format_exc())
        # В случае ошибки при генерации плота обновим статус в last_run_result.json
        last_run_result = {
            "strategy": strategy_name,
            "status": "failed",
            "error": f"Ошибка при генерации HTML-плота: {e}"
        }
        try:
            with open(last_run_result_path, 'w', encoding='utf-8') as f:
                json.dump(last_run_result, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logger.error(f"Не удалось сохранить статус ошибки для last_run_result.json: {e}")

    # Визуализация результатов walk-forward тестирования
    try:
        plot_walk_forward_results(stats_master, strategy_name)
    except Exception as e:
        logger.error(f"Ошибка при визуализации результатов walk-forward тестирования: {e}")
        logger.error(traceback.format_exc())
