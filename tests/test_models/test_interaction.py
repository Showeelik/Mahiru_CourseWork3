import unittest
from unittest.mock import MagicMock, patch

from src.api.hh_api import HHAPI
from src.models.hh_models import Employer, Vacancy
from src.models.interaction import (DataBaseInteraction, EmployeeInteraction, Interaction, SearchInteraction,
                                    VacancyInteraction)
from src.utils import AreaFileWorker


class TestInteraction(unittest.TestCase):

    def setUp(self):
        # Не создавайте экземпляр абстрактного класса Interaction
        # Замените Interaction на конкретную реализацию
        self.search_interaction = SearchInteraction(api=MagicMock(), search_type="employer")

    def test_sorted_jobs(self):
        vacancies = [
            Vacancy(
                name="Vacancy A",
                salary={"from": 50000, "to": 70000},
                url="https://test.ru",
                id=1,
                id_employer=1,
                publication_date="2020-01-01",
            ),
            Vacancy(
                name="Vacancy B",
                salary={"from": 30000, "to": 50000},
                url="https://test.ru",
                id=2,
                id_employer=2,
                publication_date="2020-01-02",
            ),
            Vacancy(
                name="Vacancy C",
                salary={"from": 70000, "to": 100000},
                url="https://test.ru",
                id=3,
                id_employer=3,
                publication_date="2020-01-03",
            ),
        ]
        sorted_jobs = self.search_interaction._sorted_jobs(vacancies)
        self.assertEqual(sorted_jobs[0].title, "Vacancy B")
        self.assertEqual(sorted_jobs[1].title, "Vacancy A")
        self.assertEqual(sorted_jobs[2].title, "Vacancy C")

    def test_sorted_jobs_reverse(self):
        vacancies = [
            Vacancy(
                name="Vacancy A",
                salary={"from": 50000, "to": 70000},
                url="https://test.ru",
                id=1,
                id_employer=1,
                publication_date="2020-01-01",
            ),
            Vacancy(
                name="Vacancy B",
                salary={"from": 30000, "to": 50000},
                url="https://test.ru",
                id=2,
                id_employer=2,
                publication_date="2020-01-02",
            ),
            Vacancy(
                name="Vacancy C",
                salary={"from": 70000, "to": 100000},
                url="https://test.ru",
                id=3,
                id_employer=3,
                publication_date="2020-01-03",
            ),
        ]
        sorted_jobs = self.search_interaction._sorted_jobs(vacancies, reverse=True)
        self.assertEqual(sorted_jobs[0].title, "Vacancy C")
        self.assertEqual(sorted_jobs[1].title, "Vacancy A")
        self.assertEqual(sorted_jobs[2].title, "Vacancy B")


class TestSearchInteraction(unittest.TestCase):

    @patch("src.models.interaction.HHAPI")
    @patch("src.models.interaction.AreaFileWorker")
    def test_interact_employer(self, mock_area_file_worker, mock_api):
        # Setup mocks
        mock_area_file_worker.return_value.load_data.return_value = [{"id": 1, "name": "City"}]
        mock_api.return_value.load_employers.return_value = [{"name": "Employer A"}]

        search_interaction = SearchInteraction(api=mock_api, search_type="employer")

        with patch("builtins.input", side_effect=["query", "City", "y"]):
            employers = search_interaction.interact()

        self.assertEqual(len(employers), 0)


class TestVacancyInteraction(unittest.TestCase):

    @patch("src.models.interaction.DBManager")
    @patch("src.models.interaction.HHAPI")
    def test_interact(self, mock_api, mock_db):
        # Setup mocks
        mock_db.return_value.get_companies_and_vacancies_count.return_value = [(1, 5)]
        mock_api.return_value.load_vacancies.return_value = [
            {
                "id": 1,
                "employer": {"id": 1},
                "alternate_url": "https://test.ru",
                "published_at": "2020-01-01",
                "name": "Vacancy A",
                "salary": {"from": 50000, "to": 70000},
            }
        ]

        vacancy_interaction = VacancyInteraction()

        with patch("builtins.input", side_effect=["1", "да"]):
            vacancies = vacancy_interaction.interact()

        self.assertEqual(len(vacancies), 1)
        self.assertEqual(vacancies[0].title, "Vacancy A")


class TestEmployeeInteraction(unittest.TestCase):

    @patch("src.models.interaction.HHAPI")
    @patch("src.models.interaction.EmployerFileWorker")
    def test_interact(self, mock_employer_file_worker, mock_api):
        # Setup mocks
        mock_employer_file_worker.return_value.load_data.return_value = [
            {
                "id": 1,
                "alternate_url": "https://test.ru",
                "vacancies_url": "https://test.ru/vacancies",
                "open_vacancies": 10,
                "name": "Employer A",
            }
        ]
        mock_api.return_value.load_employers.return_value = [
            {
                "id": 1,
                "alternate_url": "https://test.ru",
                "vacancies_url": "https://test.ru/vacancies",
                "open_vacancies": 10,
                "name": "Employer A",
            }
        ]

        employee_interaction = EmployeeInteraction()

        with patch("builtins.input", side_effect=["1", "да"]):
            employers = employee_interaction.interact()

        self.assertEqual(len(employers), 1)
        self.assertEqual(employers[0].name, "Employer A")
