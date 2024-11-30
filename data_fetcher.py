# data_fetcher.py
import yfinance as yf
import pandas as pd
import logging

logger = logging.getLogger(__name__)

def get_data(symbol: str, period: str = '1y', interval: str = '1h') -> pd.DataFrame:
    """
    Загружает данные с Yahoo Finance.

    :param symbol: Тикер для загрузки данных.
    :param period: Период данных (например, '1y' для одного года).
    :param interval: Интервал данных (например, '1h' для часового интервала).
    :return: DataFrame с загруженными данными.
    """
    try:
        # Ваш код по загрузке данных
        logger.info(f"Данные для символа {symbol} успешно загружены.")
        data = yf.download(tickers=symbol, period=period, interval=interval)
        data.columns = [col[0] if isinstance(col, tuple) else col for col in data.columns]
        return data
    except Exception as e:
        logger.error(f"Ошибка при загрузке данных для символа {symbol}: {e}")
        raise e

