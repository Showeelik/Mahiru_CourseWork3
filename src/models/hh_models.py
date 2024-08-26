from typing import Any, Dict, List, Optional, Tuple

# from src.utils import format_date


class Employer:
    __employer_count = 0  # Атрибут класса для подсчета компаний

    def __init__(
        self, id: int, name: str, url: str, vacancies_url: str, open_vacancies: int, vacancies_in_database: int = 0
    ) -> None:
        """
        ## Инициализирует экземпляр компании

        :param id: ID компании
        :param name: Название компании
        :param url: URL компании
        :param vacancies_url: URL вакансий компании
        :param open_vacancies: Количество открытых вакансий компании
        """

        Employer.__employer_count += 1
        self.employer_count = Employer.__employer_count

        self.id = id
        self.name = name
        self.url = url
        self.vacancies_url = vacancies_url
        self.open_vacancies: int = open_vacancies
        self.vacancies_in_database = vacancies_in_database

    def __str__(self) -> str:
        return (
            f"{f" Работодатель \033[96m№{self.employer_count}\033[0m ":=^109}\n"
            f"Название: {self.name}\n"
            f"URL: {self.url}\n"
            f"URL вакансий: {self.vacancies_url}\n"
            f"Открытые вакансии в API HH: {self.open_vacancies}\n"
            f"Вакансий сохранено в базе: {self.vacancies_in_database}\n"
            f"{" Конец ":=^100}\n"
        )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "url": self.url,
            "vacancies_url": self.vacancies_url,
            "open_vacancies": self.open_vacancies,
        }

    def __lt__(self, other: Any) -> bool:
        if isinstance(other, Employer):
            return self.open_vacancies < other.open_vacancies
        return NotImplemented

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Employer):
            return self.open_vacancies == other.open_vacancies
        return NotImplemented

    def __gt__(self, other: Any) -> bool:
        if isinstance(other, Employer):
            return self.open_vacancies > other.open_vacancies
        return NotImplemented

    def __ne__(self, other: Any) -> bool:
        if isinstance(other, Employer):
            return self.open_vacancies != other.open_vacancies
        return NotImplemented

    def __ge__(self, other: Any) -> bool:
        if isinstance(other, Employer):
            return self.open_vacancies >= other.open_vacancies
        return NotImplemented

    def __le__(self, other: Any) -> bool:
        if isinstance(other, Employer):
            return self.open_vacancies <= other.open_vacancies
        return NotImplemented

    @classmethod
    def create_instances_from_hh_api_data(cls, hh_data: List[Dict]) -> List["Employer"]:
        instances = []
        for item in hh_data:
            instance = cls(
                id=item["id"],
                name=item["name"],
                url=item["alternate_url"],
                vacancies_url=item["vacancies_url"],
                open_vacancies=item["open_vacancies"],
            )
            instances.append(instance)
        return instances

    @classmethod
    def reset_employer_count(cls) -> None:
        cls.__employer_count = 0

    @classmethod
    def from_tuple_to_list(cls, data: List[Tuple[int, str, str, str, int, int]]) -> List["Employer"]:
        """
        Преобразует список кортежей в список объектов класса Employer.

        :param List[Tuple[int, str, str, str, int]] data: Список кортежей
        :return List['Employer']: Список объектов класса Employer
        """
        instances = []
        for item in data:
            instance = cls(
                id=item[0],
                name=item[1],
                url=item[2],
                vacancies_url=item[3],
                vacancies_in_database=item[4],
                open_vacancies=item[5],
            )
            instances.append(instance)
        return instances


class Vacancy:
    def __init__(
        self,
        id: int,
        id_employer: int,
        name: str,
        url: str,
        publication_date: str,
        salary: Optional[Dict[str, Any]] = None,
        snippet: Optional[Dict[str, str]] = None,
        address: str = "Не указан адрес",
        employment: str = "Не указано занятость",
        schedule: str = "Не указан график",
        experience: str = "Не указан опыт",
    ) -> None:
        """
        Инициализирует экземпляр вакансии

        :param int id: Идентификатор вакансии
        :param int id_employer: Идентификатор компании
        :param str name: Название вакансии
        :param str url: URL вакансии
        :param str address: Адрес вакансии
        :param str publication_date: Дата публикации вакансии
        :param dict salary: Зарплата
        :param dict snippet: Описание вакансии
        :param str employment: Занятость вакансии
        :param str schedule: График работы вакансии
        :param str experience: Опыт работы вакансии
        """

        self.id = id
        self.id_employer = id_employer
        self.title = name
        self.url = url
        self.address = address
        self.publication_date = publication_date
        self.experience = experience
        self.schedule = schedule
        self.employment = employment
        self.salary = salary or {}
        self.salary_to = self.salary.get("to")
        self.salary_from = self.salary.get("from")
        self.salary_gross = self.salary.get("gross", False)
        self.salary_currency = self.salary.get("currency")
        self.snippet = snippet or {}
        self.requirement = self.snippet.get("requirement")
        self.description = self.snippet.get("responsibility")

    @classmethod
    def create_instances_from_hh_api_data(cls, hh_data: List[Dict[str, Any]]) -> List["Vacancy"]:
        instances = []
        for item in hh_data:
            instance = cls(
                id=item["id"],
                id_employer=item["employer"]["id"],
                name=item["name"],
                url=item["alternate_url"],
                address=(item.get("address") or {}).get("raw") or item.get("area", {}).get("name", "Не указан адрес"),
                publication_date=item["published_at"],
                experience=item.get("experience", {}).get("name", "Не указан опыт"),
                schedule=item.get("schedule", {}).get("name", "Не указан график"),
                employment=item.get("employment", {}).get("name", "Не указано занятость"),
                salary=item.get("salary", {}),
                snippet=item.get("snippet", {}),
            )
            instances.append(instance)
        return instances

    @classmethod
    def from_tuple_to_list(cls, data: List[tuple]) -> List["Vacancy"]:
        """
        Преобразует список кортежей в список объектов класса Vacancy.

        :param List[tuple] data:
            Список кортежей, где каждый кортеж содержит данные для создания объекта Vacancy.

        :return: Список объектов Vacancy.
        :rtype: List[Vacancy]
        """
        instances = []
        for item in data:
            instance = cls(
                id=item[0],
                id_employer=item[1],
                name=item[2],
                url=item[3],
                address=item[4],
                publication_date=item[5],
                experience=item[6],
                schedule=item[7],
                employment=item[8],
                salary={"to": item[9], "from": item[10], "currency": item[11], "gross": item[12]},
                snippet={"requirement": item[13], "responsibility": item[14]},
            )
            instances.append(instance)
        return instances

    def __str__(self) -> str:
        salary_str = (
            (f"от {self.salary_from}" if self.salary_from else "")
            + (" - " if self.salary_to and self.salary_from else "")
            + (f"до {self.salary_to}" if self.salary_to else "")
            + (f" ({self.salary_currency})" if self.salary_currency else "Зарплата не указана")
            + (" до вычета налогов" if self.salary_gross else "")
        )
        return (
            f"{' Вакансия ':=^100}\n"
            f"Вакансия: {self.title}\n"
            f"URL: {self.url}\n"
            f"URL Работодателя: https://hh.ru/employer/{self.id_employer}\n"
            f"Адрес: {self.address}\n"
            f"Дата публикации: {self.publication_date}\n"
            f"Опыт работы: {self.experience}\n"
            f"График работы: {self.schedule}\n"
            f"Тип занятости: {self.employment}\n"
            f"Зарплата: {salary_str}\n"
            f"Требования: {self.requirement or 'Не указано требования'}\n"
            f"Описание: {self.description or 'Не указано описание'}\n"
            f"{' Конец ':=^100}\n"
        )

    # Операторы сравнения, опирающиеся на зарплату
    def __lt__(self, other: Any) -> bool:
        if isinstance(other, Vacancy):
            return self.__get_salary() < other.__get_salary()
        return NotImplemented

    def __le__(self, other: Any) -> bool:
        if isinstance(other, Vacancy):
            return self.__get_salary() <= other.__get_salary()
        return NotImplemented

    def __gt__(self, other: Any) -> bool:
        if isinstance(other, Vacancy):
            return self.__get_salary() > other.__get_salary()
        return NotImplemented

    def __ge__(self, other: Any) -> bool:
        if isinstance(other, Vacancy):
            return self.__get_salary() >= other.__get_salary()
        return NotImplemented

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Vacancy):
            return self.__get_salary() == other.__get_salary()
        return NotImplemented

    def __ne__(self, other: Any) -> bool:
        if isinstance(other, Vacancy):
            return self.__get_salary() != other.__get_salary()
        return NotImplemented

    def to_json(self) -> dict:
        """
        Возвращает словарь с данными о вакансии
        """
        return {
            "id": self.id,
            "name": self.title,
            "alternate_url": self.url,
            "address": self.address,
            "published_at": self.publication_date,
            "experience": self.experience,
            "schedule": self.schedule,
            "employment": self.employment,
            "employer": {"id": self.id_employer, "url": "https://hh.ru/employer/" + str(self.id_employer)},
            "salary": {
                "to": self.salary_to,
                "from": self.salary_from,
                "currency": self.salary_currency,
                "gross": self.salary_gross,
            },
            "snippet": {"requirement": self.requirement, "responsibility": self.description},
        }

    def to_dict(self) -> dict:
        """
        Возвращает словарь с данными о вакансии
        """
        return {
            "id": self.id,
            "id_employer": self.id_employer,
            "name": self.title,
            "alternate_url": self.url,
            "address": self.address,
            "published_at": self.publication_date,
            "experience": self.experience,
            "schedule": self.schedule,
            "employment": self.employment,
            "salary_to": self.salary_to,
            "salary_from": self.salary_from,
            "salary_currency": self.salary_currency,
            "salary_gross": self.salary_gross,
            "requirement": self.requirement,
            "description": self.description,
        }

    def __get_salary(self) -> float:
        """
        Приватный метод для получения средней зарплаты
        """
        salary_from = float(self.salary.get("from", 0) or 0)
        salary_to = float(self.salary.get("to", 0) or 0)
        return (salary_from + salary_to) / 2 if salary_from and salary_to else max(salary_from, salary_to)
