from abc import ABC, abstractmethod
from typing import Any, List, Literal, Optional

from src.api.hh_api import HHAPI
from src.db.db import DBManager
from src.models.hh_models import Employer, Vacancy
from src.utils import AreaFileWorker, EmployerFileWorker, find_city, setup_logger

logger = setup_logger(__name__)


class Interaction(ABC):

    @abstractmethod
    def interact(self) -> Any:
        pass

    @staticmethod
    def _sorted_jobs(jobs: List[Vacancy], reverse: bool = False) -> List[Vacancy]:
        """
        ## Сортировка вакансий по зарплате

        :param List[Vacancy] jobs: Список вакансий
        :param reverse: Сортировать по убыванию (по умолчанию True)
        :type reverse: bool = True
        :return List[Vacancy]: Список вакансий, отсортированный по зарплате
        """

        return sorted(jobs, reverse=reverse)


class SearchInteraction(Interaction):
    def __init__(self, api: HHAPI, search_type: Literal["vacancy", "employer"]) -> None:
        """
        ## Интерактивный поиск вакансий или работодателей

        :param API api: API
        :param search_type: Тип поиска
        :type search_type: Literal["vacancy", "employer"]
        """
        self.api = api
        self.search_type = search_type

    def interact(self) -> Any:
        """
        ## Поиск вакансий или работодателей

        :return List[dict]: Список вакансий или работодателей
        """
        # TODO : добавить поиск вакансий и взаимодействие с базой данных
        # if self.search_type == "vacancy":
        #     area = input("\nВыберите регион (По умолчанию Все): ")
        #     logger.info(f"Выбран регион поиска: {area if area else 'Все'}")
        #     city_id = find_city(AreaFileWorker().load_data(), area)

        #     query = input("Введите поисковый запрос: ")
        #     logger.info(f"Поиск по ключевому слову: {query}")

        #     salary_range = (
        #         input(
        # "Введите диапазон зарплаты. Формат: мин - макс (через пробел) или макс (необязательно): ") or None
        #     )

        #     print("\nИщем вакансии...")

        #     jobs_data = self.api.load_vacancies(query=query, area=city_id, per_page=20)

        #     if salary_range:
        #         filter_jobs = filter_jobs_by_salary_range(jobs_data, salary_range)
        #         if filter_jobs is None:
        #             logger.info("Вакансий не найдено.")
        #             print("\nВакансий не найдено.")
        #             return []
        #         logger.info(f"Найдено {len(filter_jobs)} вакансий.")
        #         return filter_jobs

        #     logger.info(f"Найдено {len(jobs_data)} вакансий.")

        #     return jobs_data
        if self.search_type == "employer":  # elif self.search_type == "employer":
            query = input("Введите поисковый запрос (По умолчанию любые): ")
            area = input("Выберите регион (По умолчанию всe): ")
            city_id = find_city(AreaFileWorker().load_data(), area)
            sort_employers = (
                input(
                    "Сортировать работодателя по количеству вакансий? (По умолчанию сортировка по название) (y/n) "
                ).lower()
                == "y"
            )

            print("\nИщем работодателей...")
            employers = self.api.load_employers(query, area=city_id, sort_by=sort_employers)
            if len(employers) == 0:
                logger.info("Работодатели не найдены.")
                print("\nРаботодатели не найдены.")
                return []

            logger.info(f"Найдено {len(employers)} работодателей.")

            return employers


class VacancyInteraction(Interaction):
    def __init__(self) -> None:
        self.search_vacancies = SearchInteraction(HHAPI(), search_type="vacancy")
        self.db = DBManager()
        self.api = HHAPI()

    def interact(self) -> List[Vacancy]:
        """
        # Вывод вакансий
        """
        while True:
            print("\n1. Загрузить вакансии из списка работадателей в базе данных")
            print("2. Загрузить вакансии из API HH.ru (Недоступно, в разработке.)")
            print("3. Назад")

            choice = input("\nВыберите опцию: ")

            if choice == "1":
                self.employers = self.db.get_companies_and_vacancies_count()
                if len(self.employers) == 0:
                    logger.info("Работодатели не найдены в базе данных.")
                    print("\nРаботодатели не найдены в базе данных.")
                    continue

                self.employers_ids = [employer[0] for employer in self.employers]
                self.storage = self.api.load_vacancies(per_page=100, employer_ids=self.employers_ids)
                vacances = Vacancy.create_instances_from_hh_api_data(self.storage)

                if input(f"\nВывести {len(vacances)} вакансии? (Да/Нет) ").lower() == "да":
                    for vac in self._sorted_jobs(vacances):
                        print(vac)

                return vacances

            elif choice == "2":
                print("\nНедоступно, в разработке.")
                # self.storage = self.search_vacancies.interact()
                # vacances = Vacancy.create_instances_from_hh_api_data(self.storage)

                # if input(f"\nВывести {len(vacances)} вакансии? (Да/Нет) ").lower() == "да":
                #     for vac in self._sorted_jobs(vacances):
                #         print(vac)
                # return vacances
                return []

            elif choice == "3":
                logger.info("Назад.")
                break

            else:
                print("\nНеверная опция.")


class EmployeeInteraction(Interaction):
    def __init__(self) -> None:
        self.search_employers = SearchInteraction(HHAPI(), search_type="employer")
        self.api = HHAPI()

    def interact(self) -> List[Employer] | None:
        """
        # Вывод работодателей
        """
        while True:
            print("\n1. Выбор работодателя из списка по умолчанию")
            print("2. Загрузить свой список работадателей из API HH.ru")
            print("3. Назад")

            choice = input("\nВыберите опцию: ")

            if choice == "1":

                employes = self.__show_employers()

                return employes

            elif choice == "2":

                employes = self.__show_my_employees()

                return employes

            elif choice == "3":
                logger.info("Назад.")
                return None

            else:
                print("\nНеверная опция.")

    def __show_employers(self) -> List[Employer]:
        """
        ## Вывод работодателей по умолчанию
        """

        employer_names = EmployerFileWorker().load_data()

        data_api = []

        for employer_name in employer_names:
            data_api.extend(self.api.load_employers(employer_name["name"], total_pages=1, per_page=1))
            print(f"\rЗагружено: {len(data_api)} работодателей", end="")

        employes = Employer.create_instances_from_hh_api_data(data_api)

        if input(f"\nВывести {len(employes)} работодателя? (Да/Нет) ").lower() == "да":
            for employer in employes:
                print(employer)

            Employer.reset_employer_count()

        return employes

    def __show_my_employees(self) -> List[Employer]:
        """
        ## Вывод своего списка работодателей
        """

        employes = Employer.create_instances_from_hh_api_data(self.search_employers.interact())

        for employer in employes:
            print(employer)

        Employer.reset_employer_count()

        return employes


class DataBaseInteraction(Interaction):
    def __init__(self, db: DBManager, storage: Optional[List[Vacancy] | List[Employer]] = None) -> None:
        self.db = db
        self.storage = storage

    def interact(self) -> None:
        while True:
            print(
                "\n1. Загрузить даннуе в базу данных" + (" (Недоступно, нет данных)" if self.storage is None else "")
            )
            print("2. Получить данные из базы данных")

            if not self.db.check_if_db_exists():
                print("3. Создать базу данных")
            else:
                print("3. Удалить базу данных")

            print("4. Назад")

            choice = input("\nВыберите опцию: ")

            if choice == "1":
                if self.storage is None:
                    print("\nНедоступно, нет данных.")
                    continue
                print("\nЗагрузка данных в базу данных.")
                if isinstance(self.storage, list):
                    # Проверяем, что все элементы являются экземплярами Vacancy
                    # прежде чем вызывать _load_vacancies_to_db
                    if all(isinstance(item, Vacancy) for item in self.storage):
                        self._load_vacancies_to_db(self.storage)  # self.storage теперь точно List[Vacancy]

                    # Проверяем, что все элементы являются экземплярами Employer
                    # прежде чем вызывать _load_employers_to_db
                    if all(isinstance(item, Employer) for item in self.storage):
                        self._load_employers_to_db(self.storage)  # self.storage теперь точно List[Employer]
                    else:
                        print("\nОшибка: список содержит объекты несоответствующего типа.")
                else:
                    print("\nОшибка: self.storage не является списком.")

            elif choice == "2":

                self._additional_functions()

            elif choice == "3":
                if self.db.check_if_db_exists():
                    self.db.drop_db()
                    print("\nБаза данных удалена.")
                else:
                    if self.db.create_db():
                        print("\nБаза данных создана.")
                    else:
                        print("\nОшибка: не удалось создать базу данных.")

            elif choice == "4":
                logger.info("Назад.")
                break

            else:
                print("\nНеверная опция.")

    def _load_vacancies_to_db(self, data: List[Vacancy]) -> None:
        """
        ## Загрузка вакансий в базуданных

        :param List[Vacancy] data: Список вакансий для загрузки
        """
        for vacancy in data:
            self.db.insert_into_vacancies(tuple(vacancy.to_dict().values()))

        print("\nВакансии загружены в базу данных.")

    def _load_employers_to_db(self, data: List[Employer]) -> None:
        """
        ## Загрузка работодателей в базу данных

        :param List[Employer] data: Список работодателей для загрузки
        """
        for employer in data:
            self.db.insert_into_employers(tuple(employer.to_dict().values()))

        print("\nРаботодатели загружены в базу данных.")

    def _additional_functions(self) -> None:
        """
        ## Дополнительные функции для работы с базой данных
        """
        while True:
            print("\n1. Вывод всех работодателей")
            print("2. Вывод всех вакансий из базе данных")
            print("3. Вывод вакансий по ключевому слову")
            print("4. Вывод вакансий с зарплатой выше средней")
            print("5. Подсчет средней заработной платы у всех вакансий")
            print("6. Назад")

            choice = input("\nВыберите опцию: ")

            if choice == "1":

                employers = Employer.from_tuple_to_list(self.db.get_companies_and_vacancies_count())

                for employer in employers:
                    print(employer)

                Employer.reset_employer_count()

            elif choice == "2":
                vacancies = Vacancy.from_tuple_to_list(self.db.get_all_vacancies())
                for vacancy in self._sorted_jobs(vacancies):
                    print(vacancy)

            elif choice == "3":

                keyword = input("\nВведите ключевое слово: ")
                vacancies = Vacancy.from_tuple_to_list(self.db.get_vacancies_with_keyword(keyword))
                for vacancy in self._sorted_jobs(vacancies):
                    print(vacancy)

            elif choice == "4":
                vacancies = Vacancy.from_tuple_to_list(self.db.get_vacancies_with_higher_salary())
                for vacancy in self._sorted_jobs(vacancies):
                    print(vacancy)

            elif choice == "5":
                average_salary = self.db.get_avg_salary()
                print(f"\nСредняя зарплата: {average_salary:.0f} руб.")

            elif choice == "6":
                logger.info("Назад.")
                break

            else:
                print("\nНеверная опция.")
