# server.py
from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import json
import os
from strategies import AVAILABLE_STRATEGIES  # Импортируем динамически загруженные стратегии
from concurrent.futures import ProcessPoolExecutor, Future
from runner import run_strategy
from year_graph import generate_year_graph  # Новый модуль для построения графика
import logging
import threading
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
import importlib
import sys
import shutil
import traceback
from strategies import Strategy

# Настройка CORS
origins = [
    "http://localhost.tiangolo.com",
    "https://localhost.tiangolo.com",
    "http://localhost",
    "http://localhost:8080",
    "http://localhost:5173",
]

app = FastAPI(
    title="Trading Strategies Server",
    description="API для управления и запуска торговых стратегий.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/server.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Создаём пул процессов с максимальным количеством рабочих процессов равным количеству CPU-ядер
executor = ProcessPoolExecutor(max_workers=os.cpu_count())

# Глобальные переменные для отслеживания текущих задач
current_task = {
    'strategy': {'strategy_name': None, 'future': None},
    'year_graph': {'strategy_name': None, 'future': None}
}
task_lock = threading.Lock()

# Определение BASE_DIR и путей
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
results_dir = os.path.join(BASE_DIR, 'results')
plots_dir = os.path.join(BASE_DIR, 'plots')
last_run_result_path = os.path.join(results_dir, 'last_run_result.json')
year_graph_result_path = os.path.join(results_dir, 'year_graph_result.json')  # Путь для сохранения статуса

class StrategyRequest(BaseModel):
    strategy: str = Field(..., description="Название стратегии для запуска", example="MyStrategy")

class YearGraphRequest(BaseModel):
    strategy: str = Field(..., description="Название стратегии для построения графика", example="MyStrategy")

class RunStrategyResponse(BaseModel):
    message: str = Field(..., description="Сообщение о статусе запуска стратегии")

class YearGraphResponse(BaseModel):
    message: str = Field(..., description="Сообщение о статусе построения графика")

def task_done_callback(task_type: str, future: Future):
    """
    Callback-функция, вызываемая при завершении задачи.
    Сбрасывает текущую задачу и логирует результат.
    """
    with task_lock:
        strategy_name = current_task[task_type]['strategy_name']
        current_task[task_type]['strategy_name'] = None
        current_task[task_type]['future'] = None

    if future.exception() is not None:
        logger.error(f"Задача '{task_type}' для стратегии '{strategy_name}' завершилась с ошибкой: {future.exception()}")
        if task_type == 'year_graph':
            # Сохраняем статус ошибки в year_graph_result.json
            error_result = {
                "strategy": strategy_name,
                "status": "failed",
                "error": str(future.exception())
            }
            os.makedirs(results_dir, exist_ok=True)
            try:
                with open(year_graph_result_path, 'w', encoding='utf-8') as f:
                    json.dump(error_result, f, ensure_ascii=False, indent=4)
            except Exception as e:
                logger.error(f"Не удалось сохранить статус ошибки для 'year_graph': {e}")
        elif task_type == 'strategy':
            # Сохраняем статус ошибки в last_run_result.json
            error_result = {
                "strategy": strategy_name,
                "status": "failed",
                "error": str(future.exception())
            }
            os.makedirs(results_dir, exist_ok=True)
            try:
                with open(last_run_result_path, 'w', encoding='utf-8') as f:
                    json.dump(error_result, f, ensure_ascii=False, indent=4)
            except Exception as e:
                logger.error(f"Не удалось сохранить статус ошибки для 'strategy': {e}")
    else:
        logger.info(f"Задача '{task_type}' для стратегии '{strategy_name}' завершилась успешно.")
        if task_type == 'year_graph':
            # Сохраняем успешный статус
            success_result = {
                "strategy": strategy_name,
                "status": "completed",
                "result": f"График для стратегии '{strategy_name}' успешно создан."
            }
            os.makedirs(results_dir, exist_ok=True)
            try:
                with open(year_graph_result_path, 'w', encoding='utf-8') as f:
                    json.dump(success_result, f, ensure_ascii=False, indent=4)
            except Exception as e:
                logger.error(f"Не удалось сохранить статус успеха для 'year_graph': {e}")
        elif task_type == 'strategy':
            # Результаты уже сохранены в runner.py, ничего не делаем
            pass

@app.get("/strategies", tags=["Strategies"])
def get_strategies() -> Dict[str, list]:
    """
    Возвращает список доступных стратегий.

    **Возвращает**:

    - **available_strategies**: Список доступных стратегий.
    """
    return {"available_strategies": list(AVAILABLE_STRATEGIES.keys())}

@app.post("/run_strategy", response_model=RunStrategyResponse, tags=["Strategies"])
def run_strategy_endpoint(request: StrategyRequest):
    """
    Запускает подбор параметров для выбранной стратегии, если никакая другая стратегия не выполняется в данный момент.

    **Параметры**:

    - **strategy**: Название стратегии для запуска.

    **Возвращает**:

    - **message**: Сообщение о статусе запуска стратегии.
    """
    strategy_name = request.strategy

    # Проверка, существует ли стратегия
    if strategy_name not in AVAILABLE_STRATEGIES:
        raise HTTPException(status_code=400, detail=f"Стратегия '{strategy_name}' не найдена.")

    with task_lock:
        # Проверка, выполняется ли уже стратегия
        if current_task['strategy']['future'] is not None and not current_task['strategy']['future'].done():
            raise HTTPException(status_code=400, detail=f"Стратегия '{current_task['strategy']['strategy_name']}' уже выполняется.")

        # Запуск новой стратегии
        future = executor.submit(run_strategy, strategy_name)
        current_task['strategy']['strategy_name'] = strategy_name
        current_task['strategy']['future'] = future
        # Добавление callback для сброса текущей задачи при завершении
        future.add_done_callback(lambda fut: task_done_callback('strategy', fut))

    logger.info(f"Стратегия '{strategy_name}' запущена.")
    return {"message": f"Стратегия '{strategy_name}' запущена."}

@app.post("/year-graph", response_model=YearGraphResponse, tags=["Graphs"])
def year_graph_endpoint(request: YearGraphRequest):
    """
    Создаёт годовой график распределения профита для выбранной стратегии для каждого отрезка в 30 дней.

    **Параметры**:

    - **strategy**: Название стратегии для построения графика.

    **Возвращает**:

    - **message**: Сообщение о статусе построения графика.
    """
    strategy_name = request.strategy
    logger.info(f"Запрос на создание графика для стратегии: {strategy_name}")

    # Проверка, существует ли стратегия
    if strategy_name not in AVAILABLE_STRATEGIES:
        logger.error(f"Стратегия '{strategy_name}' не найдена.")
        raise HTTPException(status_code=400, detail=f"Стратегия '{strategy_name}' не найдена.")

    try:
        generate_year_graph(strategy_name)
        logger.info(f"График для стратегии '{strategy_name}' успешно создан.")
        return {"message": f"График для стратегии '{strategy_name}' успешно создан."}
    except Exception as e:
        logger.error(f"Ошибка при создании графика для стратегии '{strategy_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при создании графика: {e}")

@app.get("/status", tags=["Status"])
def get_status() -> Dict[str, Any]:
    """
    Возвращает статус текущей выполняемой стратегии и графика.

    **Возвращает**:

    - **strategy**: Статус стратегии.
    - **year_graph**: Статус годового графика.
    """
    status_response = {}

    with task_lock:
        # Статус стратегии
        strategy_name = current_task['strategy']['strategy_name']
        strategy_future = current_task['strategy']['future']
        if strategy_name is not None and strategy_future is not None:
            if strategy_future.running():
                status = "running"
                status_response["strategy"] = {"strategy": strategy_name, "status": status}
            elif strategy_future.done():
                if strategy_future.exception() is not None:
                    status = "failed"
                    status_response["strategy"] = {"strategy": strategy_name, "status": status, "error": str(strategy_future.exception())}
                else:
                    status = "completed"
                    # Получаем детали из last_run_result.json
                    if os.path.exists(last_run_result_path):
                        try:
                            with open(last_run_result_path, 'r', encoding='utf-8') as f:
                                last_result = json.load(f)
                        except json.JSONDecodeError:
                            logger.error(f"Ошибка при чтении '{last_run_result_path}'")
                            status_response["strategy"] = {"strategy": strategy_name, "status": status, "error": "Ошибка чтения результатов"}
                            return status_response

                        # Добавляем поле "body" с деталями
                        body = {
                            "best_parameters": last_result.get("best_parameters"),
                            "walk_forward_stats": last_result.get("walk_forward_stats"),
                            "plot": last_result.get("plot"),
                            "backtest_summary": last_result.get("backtest_summary")
                        }
                        status_response["strategy"] = {"strategy": strategy_name, "status": status, "body": body}
                    else:
                        logger.error(f"Файл '{last_run_result_path}' не найден.")
                        status_response["strategy"] = {"strategy": strategy_name, "status": status, "error": "Результаты не найдены"}
            else:
                status = "unknown"
                status_response["strategy"] = {"strategy": strategy_name, "status": status}
        else:
            status_response["strategy"] = {"strategy": None, "status": "idle"}

        # Статус годового графика
        graph_strategy_name = current_task['year_graph']['strategy_name']
        graph_future = current_task['year_graph']['future']
        if graph_strategy_name is not None and graph_future is not None:
            if graph_future.running():
                status = "running"
                status_response["year_graph"] = {"strategy": graph_strategy_name, "status": status}
            elif graph_future.done():
                if graph_future.exception() is not None:
                    status = "failed"
                    status_response["year_graph"] = {"strategy": graph_strategy_name, "status": status, "error": str(graph_future.exception())}
                else:
                    status = "completed"
                    # Результаты уже сохранены в year_graph_result.json
                    status_response["year_graph"] = {"strategy": graph_strategy_name, "status": status, "message": "График готов."}
            else:
                status = "unknown"
                status_response["year_graph"] = {"strategy": graph_strategy_name, "status": status}
        else:
            status_response["year_graph"] = {"strategy": None, "status": "idle"}

    return status_response

@app.get("/run_strategy/result", tags=["Results"])
def run_strategy_result():
    """
    Возвращает результат последнего выполнения стратегии (JSON-файл).
    """
    if os.path.exists(last_run_result_path):
        return FileResponse(last_run_result_path, media_type='application/json', filename='last_run_result.json')
    else:
        raise HTTPException(status_code=404, detail="Результаты последнего запуска стратегии не найдены.")

@app.get("/year-graph/result", tags=["Results"])
def year_graph_result():
    """
    Возвращает HTML-файл с результатами годового графика для выбранной стратегии.
    """
    with task_lock:
        graph_strategy_name = current_task['year_graph']['strategy_name']

    if graph_strategy_name is None:
        # Попытка найти последний успешно завершённый график
        if os.path.exists(year_graph_result_path):
            try:
                with open(year_graph_result_path, 'r', encoding='utf-8') as f:
                    result = json.load(f)
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="Ошибка при чтении результатов графика.")

            if result.get("status") == "completed":
                strategy_name = result.get("strategy")
                plot_path = os.path.join(plots_dir, 'year_graph', f"{strategy_name}_year_graph.html")
                if os.path.exists(plot_path):
                    return FileResponse(plot_path, media_type='text/html', filename=f"{strategy_name}_year_graph.html")
                else:
                    raise HTTPException(status_code=404, detail=f"HTML-плот для стратегии '{strategy_name}' не найден.")
            elif result.get("status") == "failed":
                raise HTTPException(status_code=500, detail=result.get("error", "Неизвестная ошибка."))
            else:
                raise HTTPException(status_code=400, detail="График ещё не готов.")
        else:
            raise HTTPException(status_code=404, detail="Результаты графика не найдены.")
    else:
        # Если график ещё в процессе выполнения или только завершился
        if os.path.exists(year_graph_result_path):
            try:
                with open(year_graph_result_path, 'r', encoding='utf-8') as f:
                    result = json.load(f)
            except json.JSONDecodeError:
                raise HTTPException(status_code=500, detail="Ошибка при чтении результатов графика.")

            if result.get("status") == "completed":
                strategy_name = result.get("strategy")
                plot_path = os.path.join(plots_dir, 'year_graph', f"{strategy_name}_year_graph.html")
                if os.path.exists(plot_path):
                    return FileResponse(plot_path, media_type='text/html', filename=f"{strategy_name}_year_graph.html")
                else:
                    raise HTTPException(status_code=404, detail=f"HTML-плот для стратегии '{strategy_name}' не найден.")
            elif result.get("status") == "failed":
                raise HTTPException(status_code=500, detail=result.get("error", "Неизвестная ошибка."))
            else:
                raise HTTPException(status_code=400, detail="График ещё не готов.")
        else:
            raise HTTPException(status_code=404, detail="Результаты графика не найдены.")

@app.get("/get_plot", tags=["Plots"])
def get_plot(strategy: str):
    """
    Возвращает HTML-код с результатами бэктеста для выбранной стратегии.

    **Параметры**:

    - **strategy**: Название стратегии для получения графика.

    **Возвращает**:

    - HTML-код с графиком.
    """
    if strategy not in AVAILABLE_STRATEGIES:
        raise HTTPException(status_code=400, detail=f"Стратегия '{strategy}' не найдена.")

    plot_path = os.path.join(plots_dir, strategy, 'latest.html')

    if not os.path.exists(plot_path):
        raise HTTPException(status_code=404, detail=f"HTML-плот для стратегии '{strategy}' не найден.")

    logger.info(f"Отправка HTML-кода для стратегии '{strategy}' из '{plot_path}'")

    # Чтение содержимого HTML-файла
    with open(plot_path, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Возвращаем содержимое HTML-файла как строку
    return HTMLResponse(content=html_content)

@app.get("/debug", tags=["Debug"])
def debug_executor_status() -> Dict[str, Any]:
    """
    Отладочный маршрут для проверки состояния задач.

    **Возвращает**:

    - **current_tasks**: Текущие задачи и их состояние.
    """
    status = {
        "current_tasks": {
            task: {
                "strategy": current_task[task]['strategy_name'],
                "running": current_task[task]['future'].running() if current_task[task]['future'] else None,
                "done": current_task[task]['future'].done() if current_task[task]['future'] else None,
                "exception": str(current_task[task]['future'].exception()) if current_task[task]['future'] and current_task[task]['future'].done() else None
            } for task in current_task
        }
    }
    return status

@app.get("/run_strategy/result_for_strategy", tags=["Results"])
def run_strategy_result_for_strategy(strategy: str):
    """
    Возвращает результат выполнения стратегии (JSON-файл) для указанной стратегии.

    **Параметры**:

    - **strategy**: Название стратегии для получения результата.

    **Возвращает**:

    - JSON-файл с результатами выполнения стратегии.
    """
    if strategy not in AVAILABLE_STRATEGIES:
        raise HTTPException(status_code=400, detail=f"Стратегия '{strategy}' не найдена.")

    strategy_run_result_path = os.path.join(results_dir, f'{strategy}_run_result.json')

    if os.path.exists(strategy_run_result_path):
        return FileResponse(strategy_run_result_path, media_type='application/json', filename=f'{strategy}_run_result.json')
    else:
        raise HTTPException(status_code=404, detail=f"Результаты для стратегии '{strategy}' не найдены.")

@app.get("/year-graph/result_for_strategy", tags=["Results"])
def year_graph_result_for_strategy(strategy: str):
    """
    Возвращает HTML-код с годовым графиком для указанной стратегии.

    **Параметры**:

    - **strategy**: Название стратегии для получения графика.

    **Возвращает**:

    - HTML-код с графиком.
    """
    if strategy not in AVAILABLE_STRATEGIES:
        logger.error(f"Стратегия '{strategy}' не найдена.")
        raise HTTPException(status_code=400, detail=f"Стратегия '{strategy}' не найдена.")

    # Формируем путь к файлу графика
    plot_path = os.path.join(plots_dir, 'year_graph', f"{strategy}_year_graph.html")

    if os.path.exists(plot_path):
        logger.info(f"Отправка годового графика для стратегии '{strategy}' из '{plot_path}'")
        # Читаем содержимое HTML-файла и возвращаем его
        with open(plot_path, 'r', encoding='utf-8') as html_file:
            html_content = html_file.read()
        return HTMLResponse(content=html_content, media_type='text/html')
    else:
        logger.error(f"Годовой график для стратегии '{strategy}' не найден в '{plot_path}'")
        raise HTTPException(status_code=404, detail=f"График для стратегии '{strategy}' не найден.")

# @app.post("/add_strategy", tags=["Strategies"])
# def add_strategy(
#     strategy_name: str = Form(..., description="Название новой стратегии"),
#     param_grid: str = Form(..., description="Параметры стратегии в формате JSON"),
#     strategy_code: UploadFile = File(...)
# ):
#     """
#     Добавляет новую стратегию путем загрузки Python-кода и метаданных.
    
#     **Параметры**:
    
#     - **strategy_name**: Название новой стратегии.
#     - **param_grid**: Параметры стратегии в формате JSON.
#     - **strategy_code**: Файл с кодом стратегии (Python скрипт).
    
#     **Возвращает**:
    
#     - **message**: Сообщение о статусе добавления стратегии.
#     """
#     logger.info(f"Попытка добавления стратегии: {strategy_name}")

#     # Проверка, существует ли уже стратегия с таким именем
#     if strategy_name in AVAILABLE_STRATEGIES:
#         logger.error(f"Стратегия '{strategy_name}' уже существует.")
#         raise HTTPException(status_code=400, detail=f"Стратегия '{strategy_name}' уже существует.")

#     # Проверка расширения файла
#     if not strategy_code.filename.endswith(".py"):
#         logger.error(f"Неверное расширение файла: {strategy_code.filename}")
#         raise HTTPException(status_code=400, detail="Файл должен иметь расширение .py")

#     # Путь для сохранения файла
#     strategies_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'strategies')
#     os.makedirs(strategies_dir, exist_ok=True)
#     file_path = os.path.join(strategies_dir, f"{strategy_name}.py")

#     # Сохранение файла
#     try:
#         with open(file_path, "wb") as buffer:
#             shutil.copyfileobj(strategy_code.file, buffer)
#         logger.info(f"Файл стратегии сохранён по пути: {file_path}")
#     except Exception as e:
#         logger.error(f"Ошибка при сохранении файла стратегии: {e}")
#         raise HTTPException(status_code=500, detail=f"Ошибка при сохранении файла стратегии: {e}")

#     # Парсинг param_grid
#     try:
#         param_grid_dict = json.loads(param_grid)
#         logger.debug(f"Полученный param_grid: {param_grid_dict}")
#     except json.JSONDecodeError as e:
#         # Удаление файла при ошибке
#         os.remove(file_path)
#         logger.error(f"Ошибка парсинга param_grid: {e}")
#         raise HTTPException(status_code=400, detail=f"Параметры стратегии должны быть в формате JSON: {e}")

#     # Добавление в AVAILABLE_STRategies
#     AVAILABLE_STRATEGIES[strategy_name] = {
#         'class': strategy_name,
#         'param_grid': param_grid_dict
#     }
#     logger.info(f"Стратегия '{strategy_name}' добавлена в AVAILABLE_Strategies с param_grid: {param_grid_dict}")

#     # Импортирование новой стратегии
#     try:
#         # Добавление директории strategies в sys.path для импорта
#         if strategies_dir not in sys.path:
#             sys.path.insert(0, strategies_dir)
#             logger.debug(f"Добавлена директория '{strategies_dir}' в sys.path")

#         # Импортировать модуль стратегии
#         module = importlib.import_module(strategy_name)
#         strategy_class = getattr(module, strategy_name)
#         logger.info(f"Импортирован класс стратегии: {strategy_class}")

#         # Проверка наличия 'param_grid' в классе стратегии
#         if not hasattr(strategy_class, 'param_grid') or strategy_class.param_grid != param_grid_dict:
#             logger.warning(f"Класс стратегии '{strategy_name}' не содержит 'param_grid' или он отличается от переданного.")
#             # Устанавливаем 'param_grid' как атрибут класса
#             setattr(strategy_class, 'param_grid', param_grid_dict)
#             logger.info(f"'param_grid' установлен для класса стратегии '{strategy_name}': {param_grid_dict}")
#     except Exception as e:
#         # Удаление файла и из AVAILABLE_Strategies при ошибке
#         os.remove(file_path)
#         del AVAILABLE_STRATEGIES[strategy_name]
#         logger.error(f"Ошибка при загрузке новой стратегии: {e}")
#         logger.error(traceback.format_exc())
#         raise HTTPException(status_code=400, detail=f"Ошибка при загрузке новой стратегии: {e}")

#     # Перезагрузка модуля 'strategies' для обновления AVAILABLE_Strategies
#     try:
#         if 'strategies' in sys.modules:
#             strategies_module = sys.modules['strategies']
#             importlib.reload(strategies_module)
#             logger.info("Модуль 'strategies' перезагружен.")
#         else:
#             strategies_module = importlib.import_module('strategies')
#             logger.info("Модуль 'strategies' импортирован.")
#     except Exception as e:
#         logger.error(f"Ошибка при перезагрузке модуля 'strategies': {e}")
#         raise HTTPException(status_code=500, detail=f"Ошибка при перезагрузке модуля 'strategies': {e}")

#     logger.info(f"Стратегия '{strategy_name}' успешно добавлена.")
#     return {"message": f"Стратегия '{strategy_name}' успешно добавлена."}


# Модель запроса для добавления стратегии
class AddStrategyRequest(BaseModel):
    strategy_name: str = Field(..., description="Название новой стратегии", example="NewStrategy")

@app.post("/add_strategy", tags=["Strategies"])
async def add_strategy(
    strategy_name: str = Form(..., description="Название новой стратегии"),
    strategy_code: UploadFile = File(...)
):
    """
    Добавляет новую стратегию путем загрузки Python-кода.
    
    **Параметры**:
    
    - **strategy_name**: Название новой стратегии.
    - **strategy_code**: Файл с кодом стратегии (Python скрипт).
    
    **Возвращает**:
    
    - **message**: Сообщение о статусе добавления стратегии.
    """
    logger = logging.getLogger("server")
    logger.info(f"Попытка добавления стратегии: {strategy_name}")

    # Проверка, существует ли уже стратегия с таким именем
    if strategy_name in AVAILABLE_STRATEGIES:
        logger.error(f"Стратегия '{strategy_name}' уже существует.")
        raise HTTPException(status_code=400, detail=f"Стратегия '{strategy_name}' уже существует.")

    # Проверка расширения файла
    if not strategy_code.filename.endswith(".py"):
        logger.error(f"Неверное расширение файла: {strategy_code.filename}")
        raise HTTPException(status_code=400, detail="Файл должен иметь расширение .py")

    # Путь для сохранения файла
    strategies_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'strategies')
    os.makedirs(strategies_dir, exist_ok=True)
    file_path = os.path.join(strategies_dir, f"{strategy_name}.py")

    # Сохранение файла
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(strategy_code.file, buffer)
        logger.info(f"Файл стратегии сохранён по пути: {file_path}")
    except Exception as e:
        logger.error(f"Ошибка при сохранении файла стратегии: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при сохранении файла стратегии: {e}")

    # Импортирование новой стратегии
    try:
        # Добавление директории strategies в sys.path для импорта
        if strategies_dir not in sys.path:
            sys.path.insert(0, strategies_dir)
            logger.debug(f"Добавлена директория '{strategies_dir}' в sys.path")

        # Импортировать модуль стратегии
        module = importlib.import_module(strategy_name)
        strategy_class = getattr(module, strategy_name)
        logger.info(f"Импортирован класс стратегии: {strategy_class}")

        # Проверка наличия 'param_grid' в классе стратегии
        if not hasattr(strategy_class, 'param_grid') or not isinstance(strategy_class.param_grid, dict):
            logger.error(f"Класс стратегии '{strategy_name}' не содержит атрибута 'param_grid' или он некорректен.")
            # Удаление файла стратегии при ошибке
            os.remove(file_path)
            raise HTTPException(status_code=400, detail="Класс стратегии должен содержать атрибут 'param_grid' как словарь.")
        
        param_grid = strategy_class.param_grid
        logger.debug(f"Полученный param_grid для стратегии '{strategy_name}': {param_grid}")

    except Exception as e:
        # Удаление файла и из AVAILABLE_STRategies при ошибке
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Файл стратегии '{strategy_name}' удалён из-за ошибки импорта.")
        logger.error(f"Ошибка при загрузке новой стратегии: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=400, detail=f"Ошибка при загрузке новой стратегии: {e}")

    # Добавление в AVAILABLE_Strategies
    AVAILABLE_STRATEGIES[strategy_name] = {
        'class': strategy_name,
        'param_grid': param_grid
    }
    logger.info(f"Стратегия '{strategy_name}' добавлена в AVAILABLE_Strategies с param_grid: {param_grid}")

    # Перезагрузка модуля 'strategies' для обновления AVAILABLE_Strategies
    try:
        if 'strategies' in sys.modules:
            strategies_module = sys.modules['strategies']
            importlib.reload(strategies_module)
            logger.info("Модуль 'strategies' перезагружен.")
        else:
            strategies_module = importlib.import_module('strategies')
            logger.info("Модуль 'strategies' импортирован.")
    except Exception as e:
        logger.error(f"Ошибка при перезагрузке модуля 'strategies': {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка при перезагрузке модуля 'strategies': {e}")

    logger.info(f"Стратегия '{strategy_name}' успешно добавлена.")
    return {"message": f"Стратегия '{strategy_name}' успешно добавлена."}


@app.delete("/delete_strategy", tags=["Strategies"])
def delete_strategy(request: StrategyRequest):
    """
    Удаляет указанную стратегию и все связанные с ней графики и результаты.
    
    **Параметры**:
    
    - **strategy_name**: Название стратегии для удаления.
    
    **Возвращает**:
    
    - **message**: Сообщение о статусе удаления стратегии.
    """
    strategy_name = request.strategy_name

    logger.info(f"Запрос на удаление стратегии: {strategy_name}")

    # Проверка существования стратегии
    if strategy_name not in AVAILABLE_STRATEGIES:
        logger.error(f"Стратегия '{strategy_name}' не найдена.")
        #raise HTTPException(status_code=404, detail=f"Стратегия '{strategy_name}' не найдена.")

    # Определение путей к файлам и директориям
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    strategies_dir = os.path.join(BASE_DIR, 'strategies')
    results_dir = os.path.join(BASE_DIR, 'results')
    plots_dir = os.path.join(BASE_DIR, 'plots')
    best_stats_dir = os.path.join(BASE_DIR, 'best_stats')

    strategy_file_path = os.path.join(strategies_dir, f"{strategy_name}.py")
    strategy_run_result_path = os.path.join(results_dir, f"{strategy_name}_run_result.json")
    strategy_best_stats_path = os.path.join(best_stats_dir, f"{strategy_name}_best_stats.json")
    optimization_results_path = os.path.join(results_dir, 'optimization_results.csv')  # Общий файл оптимизации
    walk_forward_stats_path = os.path.join(results_dir, 'walk_forward_stats.pickle')  # Общий файл walk-forward
    year_graph_result_path = os.path.join(results_dir, 'year_graph_result.json')

    # Путь к графикам стратегии
    strategy_plot_dir = os.path.join(plots_dir, strategy_name)
    strategy_walk_forward_plot = os.path.join(plots_dir, 'walk_forward', f"{strategy_name}_walk_forward_results.html")
    strategy_equity_curve_plot = os.path.join(plots_dir, 'walk_forward', f"{strategy_name}_equity_curve.png")
    strategy_latest_plot = os.path.join(plots_dir, strategy_name, 'latest.html')

    errors = []

    # Функция для удаления файла с проверкой
    def remove_file(path):
        try:
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"Удалён файл: {path}")
        except Exception as e:
            logger.error(f"Не удалось удалить файл '{path}': {e}")
            errors.append(f"Не удалось удалить файл '{path}': {e}")

    # Функция для удаления директории с проверкой
    def remove_dir(path):
        try:
            if os.path.exists(path):
                shutil.rmtree(path)
                logger.info(f"Удалена директория: {path}")
        except Exception as e:
            logger.error(f"Не удалось удалить директорию '{path}': {e}")
            errors.append(f"Не удалось удалить директорию '{path}': {e}")

    # 1. Удаление файла стратегии
    remove_file(strategy_file_path)

    # 2. Удаление результатов выполнения стратегии
    remove_file(strategy_run_result_path)

    # 3. Удаление графиков стратегии
    remove_dir(strategy_plot_dir)

    # 4. Удаление walk-forward графиков, если они специфичны для стратегии
    remove_file(strategy_walk_forward_plot)
    remove_file(strategy_equity_curve_plot)

    # 4.1 Удаление весов
    remove_file(strategy_best_stats_path)

    # 5. Удаление общего файла walk-forward, если он не используется другими стратегиями
    # (Опционально: требуется дополнительная логика для проверки)
    # remove_file(walk_forward_stats_path)

    # 6. Удаление статуса графика
    remove_file(year_graph_result_path)

    # 7. Удаление стратегии из AVAILABLE_STRATEGIES
    del AVAILABLE_STRATEGIES[strategy_name]
    logger.info(f"Стратегия '{strategy_name}' удалена из AVAILABLE_STRATEGIES.")

    # 8. Перезагрузка модуля 'strategies' для обновления AVAILABLE_STRATEGIES
    try:
        if 'strategies' in sys.modules:
            strategies_module = sys.modules['strategies']
            importlib.reload(strategies_module)
            logger.info(f"Модуль 'strategies' перезагружен.")
        else:
            strategies_module = importlib.import_module('strategies')
            logger.info(f"Модуль 'strategies' импортирован.")
    except Exception as e:
        logger.error(f"Ошибка при перезагрузке модуля 'strategies': {e}")
        errors.append(f"Ошибка при перезагрузке модуля 'strategies': {e}")

    if errors:
        raise HTTPException(status_code=500, detail={"message": "Стратегия удалена с ошибками.", "errors": errors})

    return {"message": f"Стратегия '{strategy_name}' и все связанные с ней данные успешно удалены."}    
