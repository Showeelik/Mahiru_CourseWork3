import os
from typing import Any, List

import dotenv
import psycopg2
from psycopg2 import Error

from src.utils import setup_logger

logger = setup_logger(__name__)
dotenv.load_dotenv()


class DBManager:
    def __init__(self) -> None:
        self.__conn = self.__connect()
        self.__cursor = self.__conn.cursor()

    def __connect(self) -> psycopg2.extensions.connection:
        """
        Подключение к базе данных PostgreSQL.

        :return psycopg2.extensions.connection: Объект соединения с базой данных.
        """
        try:

            conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD_USER"),
                port=os.getenv("DB_PORT"),
            )
            logger.info("Подключен к базе данных PostgreSQL")
            return conn
        except Error as error:
            logger.error(f"Ошибка соединения: {error}")
            raise

    def _execute_statement(self, statement: str, params: tuple = ()) -> bool:
        """
        Выполнение SQL-запроса.

        :param str statement: SQL-запрос.
        :param tuple params: Параметры для SQL-запроса.
        :return bool: Успех выполнения запроса.
        """
        try:
            self.__cursor.execute(statement, params)
            self.__conn.commit()
            return True
        except Error as e:
            logger.error(f"Ошибка выполнения SQL-запроса: {e}")
            raise Error(e)

    def create_db(self) -> bool:
        """
        Создание базы данных и необходимых таблиц.

        :return bool: Успех выполнения создания схемы и таблиц.
        """
        statement = """
        CREATE SCHEMA IF NOT EXISTS hh_api;

        DROP TABLE IF EXISTS hh_api.vacancies;
        DROP TABLE IF EXISTS hh_api.employers;

        CREATE TABLE hh_api.employers (
            id SERIAL PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            url TEXT NOT NULL,
            vacancies_url TEXT NOT NULL,
            open_vacancies INTEGER
        );

        CREATE TABLE hh_api.vacancies (
            id SERIAL PRIMARY KEY,
            employer_id INTEGER NOT NULL REFERENCES hh_api.employers(id),
            title VARCHAR(255) NOT NULL,
            url TEXT NOT NULL,
            address VARCHAR(255),
            publication_date TIMESTAMP,
            experience VARCHAR(255),
            schedule VARCHAR(255),
            employment VARCHAR(255),
            salary_from INTEGER,
            salary_to INTEGER,
            salary_currency VARCHAR(255),
            salary_gross BOOLEAN,
            description TEXT,
            requirement TEXT
        );"""
        return self._execute_statement(statement)

    def insert_into_employers(self, data: tuple) -> bool:
        """
        Вставка данных в таблицу employers.

        :param tuple data: Данные для вставки в таблицу employers.
        :return bool: Успех выполнения вставки.
        """
        statement = """
        INSERT INTO hh_api.employers (id, name, url, vacancies_url, open_vacancies)
        VALUES (%s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
        """
        return self._execute_statement(statement, data)

    def insert_into_vacancies(self, data: tuple) -> bool:
        """
        Вставка данных в таблицу vacancies.

        :param tuple data: Данные для вставки в таблицу vacancies.
        :return bool: Успех выполнения вставки.
        """
        statement = """
        INSERT INTO hh_api.vacancies (
            id, employer_id, title, url, address, publication_date, experience, schedule, employment,
            salary_from, salary_to, salary_currency, salary_gross, description, requirement
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO NOTHING;
        """
        return self._execute_statement(statement, data)

    def get_companies_and_vacancies_count(self) -> List[Any]:
        """
        Получение списка компаний и количества вакансий у каждой компании.

        :return list: Список кортежей с названием компании и количеством вакансий.
        """
        statement = """
        SELECT e.id, e.name, e.url, e.vacancies_url, COUNT(v.id), e.open_vacancies AS vacancies_count
        FROM hh_api.employers e
        LEFT JOIN hh_api.vacancies v ON e.id = v.employer_id
        GROUP BY e.id
        ORDER BY vacancies_count DESC;
        """
        if self._execute_statement(statement):
            return self.__cursor.fetchall()
        return []

    def get_all_vacancies(self) -> List[Any]:
        """
        ## Получение всех вакансий из базы данных.

        :return list: Список всех вакансий.
        """
        statement = "SELECT * FROM hh_api.vacancies;"
        if self._execute_statement(statement):
            return self.__cursor.fetchall()
        return []

    def get_avg_salary(self) -> float | None:
        """
        ## Подсчет средней заработной платы.

        :return float: Средняя заработная плата.
        :return None: Если нет данных о зарплате.
        """
        statement = """
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
        """
        if self._execute_statement(statement):
            result = self.__cursor.fetchone()
            return result[0] if result and result[0] is not None else None
        return None

    def get_vacancies_with_higher_salary(self) -> List[tuple[Any, ...]]:
        """
        ## Получение вакансий с зарплатой выше средней.

        :return list: Список вакансий с зарплатой выше средней.
        """
        avg_salary = self.get_avg_salary()
        if avg_salary is None:
            # Если нет данных о зарплате
            print("Нет данных о зарплате.")
            logger.info("Нет данных о зарплате.")
            return []

        statement = """
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
        """
        if self._execute_statement(statement, (avg_salary,)):
            return self.__cursor.fetchall()
        return []

    def get_vacancies_with_keyword(self, keyword: str, company_id: int = 0) -> list:
        """
        ### Вывод вакансий по ключевому слову во всех компаниях
        ### или только в указанной компании

        :param str keyword: Ключевое слово
        :param int company_id: ID компании (опционально)
        :return list: Список вакансий
        """
        # Определяем SQL-запрос и параметры
        if company_id != 0:
            # Если указан ID компании, искать только в этой компании
            statement = """
            SELECT *
            FROM hh_api.vacancies
            WHERE title ILIKE %s AND employer_id = %s;
            """
            params = ("%" + keyword + "%", company_id)  # Кортеж из двух элементов
        else:
            # Искать во всех компаниях
            statement = "SELECT * FROM hh_api.vacancies WHERE title ILIKE %s;"
            params = ("%" + keyword + "%",)  # Кортеж из одного элемента

        # Выполнение SQL-запроса и получение результатов
        if self._execute_statement(statement, params):
            result = self.__cursor.fetchall()
            return result

        return []

    def check_if_db_exists(self) -> bool | None:
        """
        Проверка существования базы данных (схемы и таблиц)

        :return bool: True, если таблицы существуют, иначе False
        """
        statement = """
        SELECT EXISTS (
            SELECT 1
            FROM information_schema.tables
            WHERE table_schema = 'hh_api'
            AND table_name = 'employers'
        );
        """
        if self._execute_statement(statement):
            result = self.__cursor.fetchone()
            return result[0] if result else False

        return False

    def drop_db(self) -> None:
        """
        Удаление таблиц и схемы из базы данных.
        """
        statement = """
        DROP TABLE IF EXISTS hh_api.vacancies;
        DROP TABLE IF EXISTS hh_api.employers;
        """
        self._execute_statement(statement)

    def close(self) -> None:
        """
        Закрытие соединения с базой данных.
        """
        if self.__cursor:
            self.__cursor.close()
        if self.__conn:
            self.__conn.close()
        logger.info("Соединение с базой данных закрыто.")
