"""src/services/analytics/personal_dates.py
Расчет личных дат (личный год, месяц, день) по системе Миланы Тарба.
"""
from datetime import datetime, date
from typing import Dict, Union


def reduce_to_single_digit(number: int) -> int:
    """Сводит число к одной цифре путем суммирования цифр."""
    while number > 9:
        number = sum(int(digit) for digit in str(number))
    return number


def calc_personal_year(birth_date: Union[str, date], current_year: int = None) -> int:
    """Рассчитывает личный год.
    
    Формула: (день + месяц + текущий_год) % 9
    Если результат > 9, то суммировать до одной цифры.
    
    :param birth_date: Дата рождения в формате "dd.mm.yyyy" или объект date
    :param current_year: Текущий год (по умолчанию - текущий год)
    :return: Личный год (1-9)
    """
    if current_year is None:
        current_year = datetime.now().year
    
    # Парсим дату рождения
    if isinstance(birth_date, str):
        try:
            birth_dt = datetime.strptime(birth_date, "%d.%m.%Y")
        except ValueError:
            raise ValueError(f"Неверный формат даты: {birth_date}. Используйте dd.mm.yyyy")
    else:
        birth_dt = birth_date
    
    day = birth_dt.day
    month = birth_dt.month
    
    # Рассчитываем личный год
    personal_year = day + month + current_year
    personal_year = reduce_to_single_digit(personal_year)
    
    return personal_year


def calc_personal_month(personal_year: int, current_month: int = None) -> int:
    """Рассчитывает личный месяц.
    
    Формула: (личный_год + текущий_месяц) % 9
    Если результат > 9, то суммировать до одной цифры.
    
    :param personal_year: Личный год
    :param current_month: Текущий месяц (по умолчанию - текущий месяц)
    :return: Личный месяц (1-9)
    """
    if current_month is None:
        current_month = datetime.now().month
    
    personal_month = personal_year + current_month
    personal_month = reduce_to_single_digit(personal_month)
    
    return personal_month


def calc_personal_day(personal_month: int, current_day: int = None) -> int:
    """Рассчитывает личный день.
    
    Формула: (личный_месяц + текущий_день) % 9
    Если результат > 9, то суммировать до одной цифры.
    
    :param personal_month: Личный месяц
    :param current_day: Текущий день (по умолчанию - текущий день)
    :return: Личный день (1-9)
    """
    if current_day is None:
        current_day = datetime.now().day
    
    personal_day = personal_month + current_day
    personal_day = reduce_to_single_digit(personal_day)
    
    return personal_day


def calc_all_personal_dates(birth_date: Union[str, date], current_date: date = None) -> Dict[str, int]:
    """Рассчитывает все личные даты.
    
    :param birth_date: Дата рождения
    :param current_date: Текущая дата (по умолчанию - сегодня)
    :return: Словарь с личными датами
    """
    if current_date is None:
        current_date = datetime.now().date()
    
    current_year = current_date.year
    current_month = current_date.month
    current_day = current_date.day
    
    personal_year = calc_personal_year(birth_date, current_year)
    personal_month = calc_personal_month(personal_year, current_month)
    personal_day = calc_personal_day(personal_month, current_day)
    
    return {
        'personal_year': personal_year,
        'personal_month': personal_month,
        'personal_day': personal_day,
        'current_date': current_date.strftime("%d.%m.%Y")
    }


def get_personal_date_interpretation(personal_number: int) -> str:
    """Возвращает интерпретацию личной даты.
    
    :param personal_number: Число личной даты (1-9)
    :return: Интерпретация
    """
    interpretations = {
        1: "Энергия новых начинаний, лидерства и инициативы",
        2: "Энергия сотрудничества, дипломатии и партнерства", 
        3: "Энергия творчества, самовыражения и коммуникации",
        4: "Энергия стабильности, работы и практичности",
        5: "Энергия свободы, перемен и приключений",
        6: "Энергия ответственности, заботы и гармонии",
        7: "Энергия духовности, анализа и внутренней работы",
        8: "Энергия материального успеха, власти и достижений",
        9: "Энергия завершения, мудрости и служения"
    }
    
    return interpretations.get(personal_number, "Неизвестная энергия")
