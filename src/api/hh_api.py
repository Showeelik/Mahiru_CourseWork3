from abc import ABC, abstractmethod
from typing import Any, Dict, Union, overload

import requests

from src.utils import setup_logger

logger = setup_logger(__name__)


class API(ABC):

    @abstractmethod
    def load_employers(
        self, query: str = None, page: int = 0, per_page: int = 10, sort_by: bool = False, area: int = None
    ) -> list[dict[Any, Any]]:
        pass

    @abstractmethod
    def load_vacancies(
        self, query: str = None, page: int = 0, per_page: int = 10, area: int = None, employer_ids: list[int] = None
    ) -> list[dict[Any, Any]]:
        pass


class HHAPI(API):
    def __init__(self) -> None:
        self.__url_employers = "https://api.hh.ru/employers"
        self.__url_vacancies = "https://api.hh.ru/vacancies"
        self.__headers = {"User-Agent": "HH-User-Agent"}
        self.__params_emp: Dict[str, Union[str, int]] = {}
        self.__params_var: Dict[str, Union[str, int]] = {}
        self.vacancies: list[dict[Any, Any]] = []

    def load_vacancies(
        self, query: str = None, page: int = None, per_page: int = 10, area: int = None, employer_ids: list[int] = None
    ) -> list[dict[Any, Any]]:
        """
        Загружает вакансии по ключевому слову из API hh.ru.

        :param query: Ключевое слово
        :param page: Максимальное количество страниц, если None - то без ограничения
        :param per_page: Количество вакансий на странице
        :param employer_ids: ID работодателя
        :param area: ID региона
        :type query: str = None
        :type page: int = None
        :type per_page: int = 10
        :type employer_ids: list[int] = None
        :type area: int = None

        :return list[dict[Any, Any]]: Список вакансий
        """
        if query:
            logger.info(f"Поиск вакансий по ключевому слову: {query}")

        # Параметры запроса
        self.__params_var = {
            "text": query or None,
            "page": page or 0,
            "per_page": per_page or 10,
            "area": area or None,
        }

        # Если employer_ids не указаны, ищем вакансии без фильтра по работодателям
        if employer_ids is None:
            while int(self.__params_var["page"]) < 20:
                response = requests.get(self.__url_vacancies, headers=self.__headers, params=self.__params_var)
                response.raise_for_status()
                vacancies = response.json().get("items", [])
                self.vacancies.extend(vacancies)
                print(f"\rЗагрузка {len(self.vacancies)} вакансий.", end="")
                self.__params_var["page"] += 1

        else:
            # Поиск по каждому работодателю
            for employer_id in employer_ids:
                self.__params_var["employer_id"] = employer_id
                while int(self.__params_var["page"]) < 20:
                    response = requests.get(self.__url_vacancies, headers=self.__headers, params=self.__params_var)
                    try:
                        response.raise_for_status()
                    except requests.exceptions.HTTPError as e:
                        raise requests.exceptions.HTTPError(e)
                    vacancies = response.json().get("items", [])
                    self.vacancies.extend(vacancies)
                    print(f"\rЗагружено {len(self.vacancies)} вакансий.", end="")
                    self.__params_var["page"] += 1

        logger.info(f"Загружено {len(self.vacancies)} вакансий.")

        return self.vacancies

    def load_employers(
        self,
        query: str = None,
        page: int = 0,
        total_page: int = 10,
        per_page: int = 10,
        sort_by: bool = False,
        area: int = None,
    ) -> list[dict[Any, Any]]:
        """
        Загружает список работодателей из API hh.ru

        :param int page: Номер страницы
        :param int per_page: Количество работодателей на странице
        :param bool sort_by: Сортировать по количеству открытых вакансий
        :return list[dict[Any, Any]]: Список работодателей
        """

        self.employers = []

        self.__params_emp = {
            "text": query if query is not None else "",
            "page": page,
            "per_page": per_page,
            "only_with_vacancies": "true",
            "sort_by": "by_vacancies_open" if sort_by else "by_name",
        }

        if area is not None:
            self.__params_emp["area"] = area

        # Извлекать новые данные из API
        while int(self.__params_emp["page"]) < total_page:
            response = requests.get(self.__url_employers, headers=self.__headers, params=self.__params_emp)
            response.raise_for_status()
            employers = response.json().get("items", [])
            self.employers.extend(employers)
            self.__params_emp["page"] = int(self.__params_emp["page"]) + 1

        logger.info(f"Загружено {len(self.employers)} работодателей из API HH.ru")

        return self.employers
