import os
from typing import Any, List

import dotenv
import psycopg2
from psycopg2 import Error, connect

from src.utils import setup_logger

logger = setup_logger(__name__)
dotenv.load_dotenv()




class ExecuteStatement:
    def __init__(self, conn: psycopg2.extensions.connection, statement: str, params: tuple = ()) -> None:
        self.__statement = statement
        self.__params = params
        self.__conn = conn
        self.__cursor = None

    def __enter__(self) -> 'ExecuteStatement':
        # Устанавливаем курсор
        self.__cursor = self.__conn.cursor()
        return self

    def execute(self) -> psycopg2.extensions.cursor:
        try:
            # Выполняем SQL-запрос
            self.__cursor.execute(self.__statement, self.__params)
        except Error as e:
            logger.error(e)
        return self.__cursor

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if exc_type is not None:
            # В случае исключения откатываем транзакцию
            logger.error(f"Ошибка транзакции: {exc_val}")
            self.__conn.rollback()
        else:
            # В случае успеха фиксируем изменения
            self.__conn.commit()

        # Закрываем курсор
        if self.__cursor is not None:
            logger.info("Закрытие курсора")
            self.__cursor.close()
        # Закрываем соединение
        if self.__conn is not None:
            logger.info("Закрытие соединения с базой данных")
            self.__conn.close()

class DBManager:
    
    def __connect(self) -> psycopg2.extensions.connection:
        """
        Подключение к базе данных PostgreSQL.

        :return psycopg2.extensions.connection: Объект соединения с базой данных.
        """
        try:
            conn = connect(
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

    def _execute_statement(self, statement: str, params: tuple = ()) -> ExecuteStatement:
        # Возвращаем экземпляр ExecuteStatement, который можно использовать как контекстный менеджер
        return ExecuteStatement(self.__connect(), statement, params)
        
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

        with self._execute_statement(statement) as cursor:
            cursor.execute()
        return True


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
        with self._execute_statement(statement, data) as cursor:
            cursor.execute()
            logger.info("Вставка данных в таблицу employers")
        return True


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
        with self._execute_statement(statement, data) as cursor:
            cursor.execute()
            logger.info("Вставка данных в таблицу vacancies")
        return True

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
        with self._execute_statement(statement) as cursor:
            cursor = cursor.execute()
            logger.info("Получение списка компаний и количества вакансий у каждой компании")
            return cursor.fetchall()
    
    def get_companies_with_keyword(self, keyword: str) -> List[Any]:
        """
        ## Поиск компаний по ключевому слову.
        """
        statement = """
        SELECT *
        FROM hh_api.employers
        WHERE name ILIKE %s;
        """
        with self._execute_statement(statement, (f"%{keyword}%",)) as cursor:
            cursor = cursor.execute()
            logger.info("Поиск компаний по ключевому слову")
            return cursor.fetchall()



    def get_all_vacancies(self) -> List[Any]:
        """
        ## Получение всех вакансий из базы данных.

        :return list: Список всех вакансий.
        """
        statement = "SELECT * FROM hh_api.vacancies;"
        with self._execute_statement(statement) as cursor:
            cursor = cursor.execute()
            logger.info("Получение всех вакансий из базы данных")
            return cursor.fetchall() 


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
        with self._execute_statement(statement) as cursor:
            cursor = cursor.execute()
            result = cursor.fetchone()
            logger.info("Подсчет средней заработной платы")
            return result[0] if result else None


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
        with self._execute_statement(statement, (avg_salary,)) as cursor:
            cursor = cursor.execute()
            logger.info("Получение вакансий с зарплатой выше средней")
            return cursor.fetchall()


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
        with self._execute_statement(statement, params) as cursor:
            cursor = cursor.execute()
            logger.info("Вывод вакансий по ключевому слову во всех компаниях или только в указанной компании")
            return cursor.fetchall()

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
        with self._execute_statement(statement) as cursor:
            cursor = cursor.execute()
            result = cursor.fetchone()
            logger.info("Проверка существования базы данных (схемы и таблиц)")
            return result[0] if result else False

    def drop_db(self) -> None:
        """
        Удаление таблиц и схемы из базы данных.
        """
        statement = """
        DROP TABLE IF EXISTS hh_api.vacancies;
        DROP TABLE IF EXISTS hh_api.employers;
        """
        with self._execute_statement(statement) as cursor:
            
            cursor.execute()
