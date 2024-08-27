import datetime
import json
import logging
import logging.handlers
import os
from abc import ABC, abstractmethod
from logging.handlers import RotatingFileHandler
from os import makedirs
from typing import Any, Dict, List, Optional

from config import AREAS_DIR, EMPLOYERS_DIR, LOGS_DIR


class CustomFormatter(logging.Formatter):
    """
    ## Кастомный формат логгера
    """

    LEVEL_COLORS = [
        (logging.DEBUG, "\x1b[32;1m"),
        (logging.INFO, "\x1b[34;1m"),
        (logging.WARNING, "\x1b[33;1m"),
        (logging.ERROR, "\x1b[31;1m"),
        (logging.CRITICAL, "\x1b[41m"),
    ]
    FORMATS = {
        level: logging.Formatter(
            f"\x1b[30;1m%(asctime)s\x1b[0m {color}%(levelname)-10s\x1b[0m \x1b[35m%(name)s\x1b[0m -> %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )
        for level, color in LEVEL_COLORS
    }

    def format(self, record: logging.LogRecord) -> str:
        formatter = self.FORMATS.get(record.levelno)
        if formatter is None:
            formatter = self.FORMATS[logging.DEBUG]

        # Переопределите функцию обратной трассировки, чтобы она всегда печаталась красным цветом
        if record.exc_info:
            text = formatter.formatException(record.exc_info)
            record.exc_text = f"\x1b[31m{text}\x1b[0m"

        output = formatter.format(record)

        # Удаление слоя кэша
        record.exc_text = None
        return output


def setup_logger(module_name: str) -> logging.Logger:
    """
    ### Настройка логгера

    :param str module_name: Имя модуля
    :return logging.Logger: Объект логгера
    """
    # Cоздание логгера
    library, _, _ = module_name.partition(".py")
    logger = logging.getLogger(library)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        if not os.path.exists(LOGS_DIR):
            makedirs(LOGS_DIR)

        # Укажите название к журналу в папке logs
        log_name = f'{datetime.datetime.now().strftime("%Y-%m-%d")}.log'
        log_path = os.path.join(LOGS_DIR, log_name)
        # Создайте обработчик файлов с обычным форматером (без ANSI)
        log_handler = RotatingFileHandler(
            filename=log_path,
            encoding="utf-8",
            maxBytes=32 * 1024 * 1024,  # 32 MiB
            backupCount=2,
        )
        log_handler.setFormatter(
            logging.Formatter(  # Используйте форматер по умолчанию
                "%(asctime)s %(levelname)-8s %(name)s -> %(message)s", "%Y-%m-%d %H:%M:%S"
            )
        )

        # Добавляем обработчики в логгер
        logger.addHandler(log_handler)

    return logger


def format_date(date_str: str) -> str:
    """
    ### Преобразует дату в формате "XXXX-XX-XXTXX:XX:XX+XXXX" в "XX-XX-XXXX XX:XX:XX" (YYYY-MM-DD HH:MM:SS).

    :param str date_str: Дата в формате "XXXX-XX-XXTXX:XX:XX+XXXX"
    :return str: Дата в формате "YYYY-MM-DD HH:MM:SS"
    """
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z").strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return date_str


def find_city(data: List[Dict], city_name: str) -> Any:
    """
    Функция для поиска города по названию

    :param List[Dict] data: Список городов
    :param str city_name: Название города
    :return Any: ID города или None, если город не найден
    """
    for item in data:
        if item["name"].lower() == city_name.lower():
            return item["id"]
        if item["areas"]:
            result = find_city(item["areas"], city_name)
            if result is not None:
                return result
    return None


def get_integer_input(prompt: str) -> int:
    """
    ### Возвращает целое число, введенное пользователем

    :param str prompt: Сообщение для пользователя
    :return int: Целое число
    """
    while True:
        try:
            value = int(input(prompt))
            return value
        except ValueError:
            return 0


def filter_jobs_by_salary_range(jobs: List[Dict], salary_input: str) -> Optional[List[Dict]]:
    """
    ### Фильтрует вакансии по заданному диапазону зарплат или по одному значению.

    :param List[Dict] jobs: Список вакансий
    :param str salary_input: Ввод пользователя
    :return List[Dict]: Список вакансий, отфильтрованный по заданному диапазону зарплат или по одному значению
    :return None: Если диапазон зарплат некорректен
    """
    try:
        # Удаляем пробелы и разделяем по дефису
        salary_parts = list(map(int, salary_input.replace(" ", "").split("-")))

        # Если введено одно значение, устанавливаем его как максимальную зарплату, минимальная = 0
        if len(salary_parts) == 1:
            min_salary = 0
            max_salary = salary_parts[0]
        elif len(salary_parts) == 2:
            min_salary, max_salary = salary_parts
        else:
            raise ValueError("Некорректный ввод диапазона зарплат")
    except ValueError:
        print("Некорректный формат диапазона зарплат. Пожалуйста, используйте формат 'мин - макс' или одно значение.")
        return None

    filtered_jobs = []
    for job in jobs:
        salary_target = job["salary"]["to"] or job["salary"]["from"]
        if min_salary <= salary_target <= max_salary:
            filtered_jobs.append(job)

    return filtered_jobs

def display_paginated_list(items: list, items_per_page: int = 20):
    """
    Функция для вывода списка с пагинацией.

    :param list items: Список элементов для вывода.
    :param int items_per_page: Количество элементов на странице.
    """
    total_items = len(items)
    if total_items == 0:
        print("\nСписок пуст.")
        return

    total_pages = (total_items + items_per_page - 1) // items_per_page
    if total_pages == 0:
        total_pages = 1
    current_page = 1

    while True:
        # Вычисляем индексы начала и конца для текущей страницы
        start_index = (current_page - 1) * items_per_page
        end_index = min(start_index + items_per_page, total_items)

        # Очищаем экран перед выводом новой страницы (например, для терминала)
        os.system('cls' if os.name == 'nt' else 'clear')

        # Выводим информацию о текущей странице и общее количество страниц
        print(f"{f' Страница \033[96m№{current_page}/{total_pages}\033[0m ':=^109}\n")

        # Выводим элементы для текущей страницы
        for i in range(start_index, end_index):
            print(items[i])

        # Выводим информацию о текущей странице и общее количество страниц
        print(f"{f' Страница \033[96m№{current_page}/{total_pages}\033[0m ':=^109}\n")

        # Навигация
        print("Навигация:\n'n' - следующая страница\n'p' - предыдущая страница\n'q' - выход\nИли введите номер страницы для переход на заданную страницу")
        user_input = input("Введите команду: ").strip().lower()

        if user_input == 'n':
            if current_page < total_pages:
                current_page += 1
            else:
                input("Вы на последней странице.")

        elif user_input == 'p':
            if current_page > 1:
                current_page -= 1
            else:
                input("Вы на первой странице.")
        elif user_input == 'q':
            break
        elif user_input.isdigit():
            page_number = int(user_input)
            if 1 <= page_number <= total_pages:
                current_page = page_number
            else:
                input(f"Неверный номер страницы. Введите число от 1 до {total_pages}.")
        else:
            input("Неверная команда. Пожалуйста, повторите ввод.")

class FileWorker(ABC):
    @abstractmethod
    def load_data(self) -> Any:
        pass


class AreaFileWorker(FileWorker):
    def __init__(self) -> None:
        self.file_path = AREAS_DIR

    def load_data(self) -> Any:
        """
        ## Загружает данные город из HH JSON-файла

        :return Any: Список городов
        """
        with open(self.file_path, "r", encoding="utf-8") as file:
            return json.load(file)


class EmployerFileWorker(FileWorker):
    def __init__(self) -> None:
        self.file_path = EMPLOYERS_DIR

    def load_data(self) -> Any:
        """
        ## Загружает данные работодателя из HH JSON-файла

        :return Any: Список работодателей
        """
        with open(self.file_path, "r", encoding="utf-8") as file:
            return json.load(file)
