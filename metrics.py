# metrics.py

def combined_metric(stats, trades_weight=0.4, winrate_weight=0.6):
    """
    Вычисляет комбинированную метрику на основе количества сделок и процентной ставки выигрыша.

    :param stats: Статистика бэктеста.
    :param trades_weight: Вес для количества сделок.
    :param winrate_weight: Вес для процентной ставки выигрыша.
    :return: Значение комбинированной метрики.
    """
    num_trades = stats.get('# Trades', 0)
    winrate = stats.get('Win Rate [%]', 0)
    return trades_weight * num_trades + winrate_weight * winrate
