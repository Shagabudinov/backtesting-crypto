# test_year_graph.py
from year_graph import generate_year_graph

if __name__ == "__main__":
    try:
        plot_path = generate_year_graph("MovingAverageCrossover")
        print(f"График успешно сохранён по пути: {plot_path}")
    except Exception as e:
        print(f"Ошибка при генерации графика: {e}")
