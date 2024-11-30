import os
import sys
import json
import pandas as pd
import plotly.express as px
import logging
import traceback  # Добавлено для подробного логирования исключений
from backtesting import Backtest
from data_fetcher import get_data
from config import AVAILABLE_STRATEGIES, DATA_CONFIG, MULTIPERIOD_TEST_CONFIG
from optimizer import load_best_params, get_strategy_class, apply_params_to_strategy

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/year_graph.log", encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def generate_year_graph(strategy_name: str) -> str:
    try:
        logger.info(f"Начало генерации годового графика для стратегии '{strategy_name}'")
        
        # Загрузите лучшие параметры стратегии
        best_params = load_best_params(strategy_name)
        logger.info(f"Лучшие параметры для стратегии '{strategy_name}': {best_params}")
            
        # Получите класс стратегии из имени
        strategy_class = get_strategy_class(strategy_name)
            
        # Примените лучшие параметры к стратегии
        apply_params_to_strategy(strategy_class, best_params)
            
        # Загрузите данные для тестирования
        data = get_data(
            symbol=DATA_CONFIG['symbol'],
            period=DATA_CONFIG['period'],
            interval=DATA_CONFIG['interval']
        )
            
        logger.info("Данные для тестирования загружены успешно.")
            
        # Настройки мультипериодного теста
        window_size = MULTIPERIOD_TEST_CONFIG['window_size']
        step = MULTIPERIOD_TEST_CONFIG['step']
        cash = MULTIPERIOD_TEST_CONFIG['cash']
        commission = MULTIPERIOD_TEST_CONFIG['commission']
            
        returns = []
            
        for x in range(window_size, len(data) + 1, step):
            logger.info(f"Обработка периода {x - window_size} - {x}")
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
                    logger.info(f"Период {x - window_size} - {x}: Return [%] = {stats['Return [%]']}")
                    returns.append(stats["Return [%]"])
                else:
                    logger.info(f"Период {x - window_size} - {x}: Сделки не были совершены.")
            except Exception as e:
                logger.error(f"Ошибка в периоде {x - window_size} - {x}: {e}")
                logger.error(traceback.format_exc())
                continue
            
        if not returns:
            logger.warning("Нет сделок для анализа в годовом тесте.")
            # Создаём пустой график с уведомлением
            fig = px.box(
                [0],
                points="all",
                title=f"Годовой тест: Распределение доходности (%) для {strategy_name}\nНет сделок для отображения."
            )
            fig.update_layout(
                xaxis_title="Стратегия",
                yaxis_title="Доходность (%)",
            )
        else:
            # Визуализация результатов
            fig = px.box(
                returns,
                points="all",
                title=f"Годовой тест: Распределение доходности (%) для {strategy_name}"
            )
            fig.update_layout(
                xaxis_title="Стратегия",
                yaxis_title="Доходность (%)",
            )
            
        # Сохранение графика как HTML
        plots_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'plots', 'year_graph')
        os.makedirs(plots_dir, exist_ok=True)
        plot_filename = f"{strategy_name}_year_graph.html"
        plot_path = os.path.join(plots_dir, plot_filename)
            
        try:
            fig.write_html(plot_path)
            logger.info(f"График для стратегии '{strategy_name}' сохранён в '{plot_path}'")
        except Exception as e:
            logger.error(f"Не удалось сохранить график для стратегии '{strategy_name}': {e}")
            logger.error(traceback.format_exc())
            raise e
            
        return plot_path
    except Exception as e:
        logger.error(f"Исключение в generate_year_graph: {e}")
        logger.error(traceback.format_exc())
        raise e
