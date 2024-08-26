import unittest
from unittest.mock import MagicMock, patch

from src.api.hh_api import HHAPI


class TestHHAPI(unittest.TestCase):

    def setUp(self):
        self.api = HHAPI()

    @patch("src.api.hh_api.requests.get")
    def test_load_employers(self, mock_get):
        # Mocking response data
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [{"id": "1", "name": "Employer 1"}, {"id": "2", "name": "Employer 2"}]
        }
        mock_get.return_value = mock_response

        employers = self.api.load_employers(query="IT", total_pages=1, per_page=2)
        self.assertIsInstance(employers, list)
        self.assertEqual(len(employers), 2)
        self.assertEqual(employers[0]["name"], "Employer 1")

    @patch("src.api.hh_api.requests.get")
    def test_load_vacancies(self, mock_get):
        # Mocking response data
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [{"id": "1", "name": "Vacancy 1"}, {"id": "2", "name": "Vacancy 2"}]
        }
        mock_get.return_value = mock_response

        vacancies = self.api.load_vacancies(query="Python", total_pages=1, per_page=2)
        self.assertIsInstance(vacancies, list)
        self.assertEqual(len(vacancies), 2)
        self.assertEqual(vacancies[0]["name"], "Vacancy 1")

    @patch("src.api.hh_api.requests.get")
    def test_load_vacancies_with_employers(self, mock_get):
        # Mocking response data
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "items": [{"id": "1", "name": "Vacancy 1"}, {"id": "2", "name": "Vacancy 2"}]
        }
        mock_get.return_value = mock_response

        vacancies = self.api.load_vacancies(employer_ids=[123, 456], total_pages=1, per_page=2)
        self.assertIsInstance(vacancies, list)
        self.assertEqual(len(vacancies), 4)
        self.assertEqual(vacancies[0]["name"], "Vacancy 1")


if __name__ == "__main__":
    unittest.main()
