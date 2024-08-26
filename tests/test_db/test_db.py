import unittest
from unittest.mock import MagicMock, patch

from src.db.db import DBManager


class TestDBManager(unittest.TestCase):

    def setUp(self):
        # Мокируем соединение с базой данных и курсор
        self.db_manager = DBManager()
        self.db_manager._DBManager__conn = MagicMock()
        self.db_manager._DBManager__cursor = MagicMock()

    @patch("src.db.db.psycopg2.connect")
    def test_connect(self, mock_connect):
        # Проверяем, что соединение было установлено
        self.db_manager._DBManager__connect()
        mock_connect.assert_called_once()

    def test_create_db(self):
        # Проверяем, что SQL-запрос на создание схемы и таблиц выполняется
        self.db_manager.create_db()
        self.db_manager._DBManager__cursor.execute.assert_called()

    def test_insert_into_employers(self):
        data = (1, "Test Company", "http://example.com", "http://example.com/vacancies", 10)
        self.db_manager.insert_into_employers(data)
        self.db_manager._DBManager__cursor.execute.assert_called_with(
            """
        INSERT INTO hh_api.employers (id, name, url, vacancies_url, open_vacancies)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
        """,
            data,
        )

    def test_insert_into_vacancies(self):
        data = (
            1,
            1,
            "Test Vacancy",
            "http://example.com",
            "Test Address",
            "2024-08-25 12:00:00",
            "3 years",
            "Full-time",
            "Permanent",
            1000,
            2000,
            "USD",
            True,
            "Test Description",
            "Test Requirements",
        )
        self.db_manager.insert_into_vacancies(data)
        self.db_manager._DBManager__cursor.execute.assert_called_with(
            """
        INSERT INTO hh_api.vacancies (
            id, employer_id, title, url, address, publication_date, experience, schedule, employment,
            salary_from, salary_to, salary_currency, salary_gross, description, requirement
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
        """,
            data,
        )

    def test_get_companies_and_vacancies_count(self):
        self.db_manager.get_companies_and_vacancies_count()
        self.db_manager._DBManager__cursor.execute.assert_called_with(
            """
        SELECT e.id, e.name, e.url, e.vacancies_url, COUNT(v.id), e.open_vacancies AS vacancies_count
        FROM hh_api.employers e
        LEFT JOIN hh_api.vacancies v ON e.id = v.employer_id
        GROUP BY e.id
        ORDER BY vacancies_count DESC;
        """,
            (),
        )

    def test_get_all_vacancies(self):
        self.db_manager.get_all_vacancies()
        self.db_manager._DBManager__cursor.execute.assert_called_with("SELECT * FROM hh_api.vacancies;", ())

    def test_get_avg_salary(self):
        self.db_manager.get_avg_salary()
        self.db_manager._DBManager__cursor.execute.assert_called_with(
            """
        SELECT AVG(
                    CASE
                        WHEN salary_to IS NOT NULL AND salary_from IS NOT NULL
                        THEN (salary_to + salary_from) / 2.0
                        WHEN salary_to IS NOT NULL
                        THEN salary_to
                        ELSE salary_from
                    END
                ) AS avg_salary
        FROM hh_api.vacancies
        WHERE salary_from IS NOT NULL OR salary_to IS NOT NULL;
        """,
            (),
        )

    def test_get_vacancies_with_higher_salary(self):
        self.db_manager.get_avg_salary = MagicMock(return_value=1500)
        self.db_manager.get_vacancies_with_higher_salary()
        self.db_manager._DBManager__cursor.execute.assert_called_with(
            """
        SELECT *
        FROM hh_api.vacancies
        WHERE
        CASE
            WHEN salary_to IS NOT NULL AND salary_from IS NOT NULL
            THEN (salary_to + salary_from) / 2.0
            WHEN salary_to IS NOT NULL
            THEN salary_to
            ELSE salary_from
        END > %s;
        """,
            (1500,),
        )

    def test_get_vacancies_with_keyword(self):
        keyword = "Python"
        company_id = 123
        self.db_manager.get_vacancies_with_keyword(keyword, company_id)
        self.db_manager._DBManager__cursor.execute.assert_called_with(
            """
            SELECT *
            FROM hh_api.vacancies
            WHERE title ILIKE %s AND employer_id = %s;
            """,
            ("%Python%", company_id),
        )

    def test_check_if_db_exists(self):
        self.db_manager.check_if_db_exists()
        self.db_manager._DBManager__cursor.execute.assert_called_with(
            """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'hh_api'
            AND table_name = 'employers'
        );
        """,
            (),
        )

    def test_drop_db(self):
        self.db_manager.drop_db()
        self.db_manager._DBManager__cursor.execute.assert_called_with(
            """
        DROP TABLE IF EXISTS hh_api.vacancies;
        DROP TABLE IF EXISTS hh_api.employers;
        """,
            (),
        )

    def test_close(self):
        self.db_manager.close()
        self.db_manager._DBManager__cursor.close.assert_called()
        self.db_manager._DBManager__conn.close.assert_called()


if __name__ == "__main__":
    unittest.main()
