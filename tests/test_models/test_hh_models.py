import json
import unittest

from src.models.hh_models import Employer, Vacancy


class TestEmployer(unittest.TestCase):
    def setUp(self):
        Employer.reset_employer_count()

    def test_employer_creation(self):
        employer = Employer(1, "Test Company", "https://test.com", "https://test.com/vacancies", 10)
        self.assertEqual(employer.id, 1)
        self.assertEqual(employer.name, "Test Company")
        self.assertEqual(employer.url, "https://test.com")
        self.assertEqual(employer.vacancies_url, "https://test.com/vacancies")
        self.assertEqual(employer.open_vacancies, 10)
        self.assertEqual(employer.vacancies_in_database, 0)
        self.assertEqual(employer.employer_count, 1)

    def test_employer_count(self):
        e1 = Employer(1, "Company A", "url_a", "vacancies_url_a", 5)
        e2 = Employer(2, "Company B", "url_b", "vacancies_url_b", 3)
        self.assertEqual(e1.employer_count, 1)
        self.assertEqual(e2.employer_count, 2)

    def test_employer_str(self):
        employer = Employer(1, "Test Company", "https://test.com", "https://test.com/vacancies", 10)
        expected_str = (
            f"{' Работодатель \033[96m№1\033[0m ':=^109}\n"
            f"Название: Test Company\n"
            f"URL: https://test.com\n"
            f"URL вакансий: https://test.com/vacancies\n"
            f"Открытые вакансии в API HH: 10\n"
            f"Вакансий сохранено в базе: 0\n"
            f"{' Конец ':=^100}\n"
        )
        self.assertEqual(str(employer), expected_str)

    def test_employer_comparison(self):
        e1 = Employer(1, "Company A", "url_a", "vacancies_url_a", 5)
        e2 = Employer(2, "Company B", "url_b", "vacancies_url_b", 10)
        self.assertLess(e1, e2)
        self.assertGreater(e2, e1)
        self.assertNotEqual(e1, e2)

    def test_employer_to_dict(self):
        employer = Employer(1, "Test Company", "https://test.com", "https://test.com/vacancies", 10)
        expected_dict = {
            "id": 1,
            "name": "Test Company",
            "url": "https://test.com",
            "vacancies_url": "https://test.com/vacancies",
            "open_vacancies": 10,
        }
        self.assertEqual(employer.to_dict(), expected_dict)

    def test_create_instances_from_hh_api_data(self):
        hh_data = [
            {
                "id": 1,
                "name": "Company A",
                "alternate_url": "url_a",
                "vacancies_url": "vacancies_url_a",
                "open_vacancies": 5,
            },
            {
                "id": 2,
                "name": "Company B",
                "alternate_url": "url_b",
                "vacancies_url": "vacancies_url_b",
                "open_vacancies": 10,
            },
        ]
        instances = Employer.create_instances_from_hh_api_data(hh_data)
        self.assertEqual(len(instances), 2)
        self.assertEqual(instances[0].id, 1)
        self.assertEqual(instances[1].name, "Company B")

    def test_employer_reset_count(self):
        Employer.reset_employer_count()
        e1 = Employer(1, "Company A", "url_a", "vacancies_url_a", 5)
        self.assertEqual(e1.employer_count, 1)


class TestVacancy(unittest.TestCase):
    def test_vacancy_creation(self):
        vacancy = Vacancy(
            1,
            1,
            "Test Vacancy",
            "https://test.com/vacancy",
            "2023-08-26",
            {"from": 50000, "to": 70000, "currency": "RUB", "gross": True},
            {"requirement": "Some requirement", "responsibility": "Some responsibility"},
            address="Some address",
            employment="Full-time",
            schedule="Flexible",
            experience="3 years",
        )
        self.assertEqual(vacancy.id, 1)
        self.assertEqual(vacancy.id_employer, 1)
        self.assertEqual(vacancy.title, "Test Vacancy")
        self.assertEqual(vacancy.salary_from, 50000)
        self.assertEqual(vacancy.salary_to, 70000)
        self.assertEqual(vacancy.salary_currency, "RUB")
        self.assertTrue(vacancy.salary_gross)
        self.assertEqual(vacancy.requirement, "Some requirement")

    def test_vacancy_str(self):
        vacancy = Vacancy(
            1,
            1,
            "Test Vacancy",
            "https://test.com/vacancy",
            "2023-08-26",
            {"from": 50000, "to": 70000, "currency": "RUB", "gross": True},
            {"requirement": "Some requirement", "responsibility": "Some responsibility"},
            address="Some address",
            employment="Full-time",
            schedule="Flexible",
            experience="3 years",
        )
        expected_str = (
            f"{' Вакансия ':=^100}\n"
            f"Вакансия: Test Vacancy\n"
            f"URL: https://test.com/vacancy\n"
            f"URL Работодателя: https://hh.ru/employer/1\n"
            f"Адрес: Some address\n"
            f"Дата публикации: 2023-08-26\n"
            f"Опыт работы: 3 years\n"
            f"График работы: Flexible\n"
            f"Тип занятости: Full-time\n"
            f"Зарплата: от 50000 - до 70000 (RUB) до вычета налогов\n"
            f"Требования: Some requirement\n"
            f"Описание: Some responsibility\n"
            f"{' Конец ':=^100}\n"
        )
        self.assertEqual(str(vacancy), expected_str)

    def test_vacancy_comparison(self):
        v1 = Vacancy(
            1,
            1,
            "Test Vacancy 1",
            "https://test.com/vacancy1",
            "2023-08-26",
            {"from": 50000, "to": 70000, "currency": "RUB", "gross": True},
            {"requirement": "Requirement 1", "responsibility": "Responsibility 1"},
        )
        v2 = Vacancy(
            2,
            2,
            "Test Vacancy 2",
            "https://test.com/vacancy2",
            "2023-08-26",
            {"from": 60000, "to": 80000, "currency": "RUB", "gross": True},
            {"requirement": "Requirement 2", "responsibility": "Responsibility 2"},
        )
        self.assertLess(v1, v2)
        self.assertGreater(v2, v1)
        self.assertNotEqual(v1, v2)

    def test_vacancy_to_dict(self):
        vacancy = Vacancy(
            1,
            1,
            "Test Vacancy",
            "https://test.com/vacancy",
            "2023-08-26",
            {"from": 50000, "to": 70000, "currency": "RUB", "gross": True},
            {"requirement": "Some requirement", "responsibility": "Some responsibility"},
            address="Some address",
            employment="Full-time",
            schedule="Flexible",
            experience="3 years",
        )
        expected_dict = {
            "id": 1,
            "id_employer": 1,
            "name": "Test Vacancy",
            "alternate_url": "https://test.com/vacancy",
            "address": "Some address",
            "published_at": "2023-08-26",
            "experience": "3 years",
            "schedule": "Flexible",
            "employment": "Full-time",
            "salary_to": 70000,
            "salary_from": 50000,
            "salary_currency": "RUB",
            "salary_gross": True,
            "requirement": "Some requirement",
            "description": "Some responsibility",
        }
        self.assertEqual(vacancy.to_dict(), expected_dict)

    def test_vacancy_to_json(self):
        vacancy = Vacancy(
            1,
            1,
            "Test Vacancy",
            "https://test.com/vacancy",
            "2023-08-26",
            {"from": 50000, "to": 70000, "currency": "RUB", "gross": True},
            {"requirement": "Some requirement", "responsibility": "Some responsibility"},
            address="Some address",
            employment="Full-time",
            schedule="Flexible",
            experience="3 years",
        )
        expected_json = {
            "id": 1,
            "name": "Test Vacancy",
            "alternate_url": "https://test.com/vacancy",
            "address": "Some address",
            "published_at": "2023-08-26",
            "experience": "3 years",
            "schedule": "Flexible",
            "employment": "Full-time",
            "employer": {"id": 1, "url": "https://hh.ru/employer/1"},
            "salary": {
                "to": 70000,
                "from": 50000,
                "currency": "RUB",
                "gross": True,
            },
            "snippet": {"requirement": "Some requirement", "responsibility": "Some responsibility"},
        }
        self.assertEqual(vacancy.to_json(), expected_json)


if __name__ == "__main__":
    unittest.main()
