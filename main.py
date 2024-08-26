from src.models.interaction import VacancyInteraction, EmployeeInteraction, DataBaseInteraction
from src.db.db import DBManager

from typing import List


def main() -> None:
    db = DBManager()
    data = None

    while True:
        print("\nВыберите действие:")
        print("\n1. Работа с работодателями")
        print("2. Работа с вакансиями")
        print("3. Работа с базой данных")
        print("4. Выход")

        choice = input("\nВаш выбор: ")

        if choice == "1":
            data = EmployeeInteraction().interact()

        elif choice == "2":
            data = VacancyInteraction().interact()

        elif choice == "3":
            DataBaseInteraction(db, data).interact()

        elif choice == "4":
            print("До свидания.")
            exit(0)

        else:
            print("Неверный выбор. Попробуйте снова.")


if __name__ == "__main__":

    db = DBManager()
    if not db.check_if_db_exists():
        if db.create_db():
            print("База данных успешно создана.")
        else:
            print("Не удалось создать базу данных.")
            exit(1)

    main()
