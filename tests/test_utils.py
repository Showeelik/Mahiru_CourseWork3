from io import StringIO
import logging
import unittest
from unittest.mock import mock_open, patch

from config import AREAS_DIR, EMPLOYERS_DIR
from src.utils import (AreaFileWorker, CustomFormatter, EmployerFileWorker, filter_jobs_by_salary_range, find_city,
                       format_date, get_integer_input, setup_logger, display_paginated_list)


class TestCustomFormatter(unittest.TestCase):
    def setUp(self):
        self.formatter = CustomFormatter()

    def test_format(self):
        record = logging.LogRecord(
            name="test", level=logging.DEBUG, pathname="", lineno=0, msg="Test message", args=(), exc_info=None
        )
        formatted = self.formatter.format(record)
        self.assertIn("Test message", formatted)


class TestSetupLogger(unittest.TestCase):
    @patch("src.utils.makedirs")
    @patch("src.utils.RotatingFileHandler")
    def test_setup_logger(self, mock_file_handler, mock_makedirs):
        mock_logger = setup_logger("test_module")

        # Debug prints
        print(f"RotatingFileHandler called: {mock_file_handler.called}")
        print(f"makedirs called: {mock_makedirs.called}")

        # Check if logger is set up correctly
        self.assertEqual(mock_logger.name, "test_module")
        self.assertEqual(mock_logger.level, logging.INFO)
        self.assertTrue(mock_file_handler.called)


class TestFormatDate(unittest.TestCase):
    def test_format_date_valid(self):
        date_str = "2023-08-25T15:30:00+0300"
        expected = "2023-08-25 15:30:00"
        self.assertEqual(format_date(date_str), expected)

    def test_format_date_invalid(self):
        date_str = "Invalid date"
        self.assertEqual(format_date(date_str), date_str)


class TestFindCity(unittest.TestCase):
    def test_find_city(self):
        data = [
            {"name": "Moscow", "id": 1, "areas": []},
            {"name": "Saint Petersburg", "id": 2, "areas": []},
        ]
        self.assertEqual(find_city(data, "Moscow"), 1)
        self.assertEqual(find_city(data, "Saint Petersburg"), 2)
        self.assertIsNone(find_city(data, "New York"))


class TestGetIntegerInput(unittest.TestCase):
    @patch("builtins.input", side_effect=["5", "notanumber", "10"])
    def test_get_integer_input(self, mock_input):
        self.assertEqual(get_integer_input("Enter a number: "), 5)
        self.assertEqual(get_integer_input("Enter a number: "), 0)
        self.assertEqual(get_integer_input("Enter a number: "), 10)


class TestFilterJobsBySalaryRange(unittest.TestCase):
    def setUp(self):
        self.jobs = [
            {"salary": {"from": 50000, "to": 70000}},
            {"salary": {"from": 80000, "to": 90000}},
            {"salary": {"from": 20000, "to": 40000}},
        ]

    def test_filter_jobs_by_salary_range_valid_range(self):
        result = filter_jobs_by_salary_range(self.jobs, "50000 - 80000")
        self.assertEqual(len(result), 1)

    def test_filter_jobs_by_salary_range_single_value(self):
        result = filter_jobs_by_salary_range(self.jobs, "60000")
        self.assertEqual(len(result), 1)

    def test_filter_jobs_by_salary_range_invalid_format(self):
        result = filter_jobs_by_salary_range(self.jobs, "invalid")
        self.assertIsNone(result)


class TestAreaFileWorker(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open, read_data='[{"id": 1, "name": "Moscow"}]')
    def test_load_data(self, mock_file):
        worker = AreaFileWorker()
        data = worker.load_data()
        self.assertEqual(data, [{"id": 1, "name": "Moscow"}])
        mock_file.assert_called_with(AREAS_DIR, "r", encoding="utf-8")


class TestEmployerFileWorker(unittest.TestCase):
    @patch("builtins.open", new_callable=mock_open, read_data='[{"id": 1, "name": "Company A"}]')
    def test_load_data(self, mock_file):
        worker = EmployerFileWorker()
        data = worker.load_data()
        self.assertEqual(data, [{"id": 1, "name": "Company A"}])
        mock_file.assert_called_with(EMPLOYERS_DIR, "r", encoding="utf-8")

class TestDisplayPaginatedList(unittest.TestCase):

    @patch('sys.stdout', new_callable=StringIO)
    @patch('builtins.input', side_effect=['q'])  # Мокируем input для завершения цикла
    def test_display_paginated_list_empty(self, mock_input, mock_stdout):
        items = []
        display_paginated_list(items)
        self.assertEqual(mock_stdout.getvalue(), "\nСписок пуст.\n")

    @patch('sys.stdout', new_callable=StringIO)
    @patch('builtins.input', side_effect=['q']) 
    def test_display_paginated_list_one_page(self, mock_input, mock_stdout):
        items = [1, 2, 3]
        display_paginated_list(items, items_per_page=5)
        output = mock_stdout.getvalue()
        self.assertIn(" Страница \x1b[96m№1/1\x1b[0m ", output)
        self.assertIn("1", output)
        self.assertIn("2", output)
        self.assertIn("3", output)

    @patch('sys.stdout', new_callable=StringIO)
    @patch('builtins.input', side_effect=['n', 'p', '3', 'q'])  # Мокируем ввод для навигации
    def test_display_paginated_list_multiple_pages(self, mock_input, mock_stdout):
        items = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        display_paginated_list(items, items_per_page=3)
        output = mock_stdout.getvalue()
        # Проверяем вывод на разных страницах и навигацию
        self.assertIn(" Страница \x1b[96m№1/4\x1b[0m ", output)
        self.assertIn(" Страница \x1b[96m№2/4\x1b[0m ", output)
        self.assertIn(" Страница \x1b[96m№3/4\x1b[0m ", output)



if __name__ == "__main__":
    unittest.main()
