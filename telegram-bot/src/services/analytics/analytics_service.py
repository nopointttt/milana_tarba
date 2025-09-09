"""src/services/analytics/analytics_service.py
Основной сервис аналитики, объединяющий все алгоритмы расчётов.

Предоставляет единый интерфейс для расчёта всех показателей:
- Число Сознания (ЧС)
- Число Действия (ЧД) 
- Матрица
- Число Имени
- Транслитерация
"""
from __future__ import annotations

from datetime import date
from typing import Dict, Any, Union

from .chs import calc_chs
from .chd import calc_chd_with_exceptions
from .matrix import Matrix
from .name_number import calc_name_number, get_name_interpretation
from .transliteration import normalize_name_for_calculation, is_cyrillic_text, is_latin_text


class AnalyticsService:
    """Сервис для полного анализа по системе Миланы Тарба."""
    
    def __init__(self):
        """Инициализировать сервис аналитики."""
        pass
    
    def analyze_person(self, birth_date: Union[str, date], full_name: str) -> Dict[str, Any]:
        """Выполнить полный анализ человека.
        
        :param birth_date: Дата рождения в формате "dd.mm.yyyy" или объект date
        :param full_name: Полное имя (кириллица или латиница)
        :return: Словарь с результатами анализа
        :raises ValueError: при неверных входных данных
        """
        # Валидация входных данных
        if not birth_date:
            raise ValueError("Дата рождения не может быть пустой")
        
        if not full_name or not full_name.strip():
            raise ValueError("Имя не может быть пустым")
        
        # 1. Расчёт Числа Сознания (ЧС)
        chs = calc_chs(birth_date)
        
        # 2. Расчёт Числа Действия (ЧД) с учётом исключений
        chd = calc_chd_with_exceptions(birth_date, chs)
        
        # 3. Построение Матрицы
        matrix = Matrix(birth_date)
        matrix_analysis = matrix.analyze_energies()
        
        # 4. Обработка имени
        original_name = full_name.strip()
        is_cyrillic = is_cyrillic_text(original_name)
        
        if is_cyrillic:
            # Транслитерируем для расчёта
            latin_name = normalize_name_for_calculation(original_name)
            name_number = calc_name_number(latin_name)
        else:
            # Уже на латинице
            latin_name = normalize_name_for_calculation(original_name)
            name_number = calc_name_number(latin_name)
        
        # 5. Интерпретация Числа Имени
        name_interpretation = get_name_interpretation(name_number)
        
        # Формируем результат
        result = {
            "input_data": {
                "birth_date": str(birth_date) if isinstance(birth_date, date) else birth_date,
                "original_name": original_name,
                "latin_name": latin_name,
                "is_cyrillic": is_cyrillic
            },
            "calculations": {
                "consciousness_number": chs,
                "action_number": chd,
                "name_number": name_number
            },
            "matrix": {
                "digit_counts": matrix_analysis["digit_counts"],
                "missing_digits": matrix_analysis["missing_digits"],
                "strong_digits": matrix_analysis["strong_digits"],
                "weak_digits": matrix_analysis["weak_digits"],
                "analysis": matrix_analysis["analysis"]
            },
            "interpretations": {
                "name_interpretation": name_interpretation
            },
            "exceptions": {
                "has_chs_chd_conflict": self._check_chs_chd_conflict(chs, chd)
            }
        }
        
        return result
    
    def analyze_person_date_only(self, birth_date: Union[str, date]) -> Dict[str, Any]:
        """Выполнить анализ только по дате рождения (без имени).
        
        :param birth_date: Дата рождения в формате "dd.mm.yyyy" или объект date
        :return: Словарь с результатами анализа (без Числа Имени)
        :raises ValueError: при неверных входных данных
        """
        # Валидация входных данных
        if not birth_date:
            raise ValueError("Дата рождения не может быть пустой")
        
        # 1. Расчёт Числа Сознания (ЧС)
        chs = calc_chs(birth_date)
        
        # 2. Расчёт Числа Действия (ЧД) с учётом исключений
        chd = calc_chd_with_exceptions(birth_date, chs)
        
        # 3. Построение Матрицы
        matrix = Matrix(birth_date)
        matrix_analysis = matrix.analyze_energies()
        
        # Формируем результат (без данных об имени)
        result = {
            "input_data": {
                "birth_date": str(birth_date) if isinstance(birth_date, date) else birth_date,
                "has_name": False
            },
            "calculations": {
                "consciousness_number": chs,
                "action_number": chd,
                "name_number": None  # Нет имени
            },
            "matrix": {
                "digit_counts": matrix_analysis["digit_counts"],
                "missing_digits": matrix_analysis["missing_digits"],
                "strong_digits": matrix_analysis["strong_digits"],
                "weak_digits": matrix_analysis["weak_digits"],
                "analysis": matrix_analysis["analysis"]
            },
            "interpretations": {
                "consciousness_interpretation": self.get_consciousness_interpretation(chs),
                "action_interpretation": self.get_action_interpretation(chd)
            },
            "exceptions": {
                "has_chs_chd_conflict": self._check_chs_chd_conflict(chs, chd)
            }
        }
        
        return result
    
    def _check_chs_chd_conflict(self, chs: int, chd: int) -> bool:
        """Проверить наличие конфликта между ЧС и ЧД.
        
        :param chs: Число Сознания
        :param chd: Число Действия
        :return: True если есть конфликт
        """
        return (chs == 1 and chd == 7) or (chs == 3 and chd == 6)
    
    def get_consciousness_interpretation(self, chs: int) -> str:
        """Получить интерпретацию Числа Сознания.
        
        :param chs: Число Сознания (1-9)
        :return: Интерпретация
        """
        interpretations = {
            1: "Лидерство, независимость, оригинальность",
            2: "Дипломатия, сотрудничество, чувствительность",
            3: "Творчество, самовыражение, оптимизм", 
            4: "Практичность, стабильность, трудолюбие",
            5: "Свобода, приключения, перемены",
            6: "Гармония, ответственность, забота",
            7: "Духовность, анализ, интуиция",
            8: "Материальный успех, власть, организация",
            9: "Завершение, мудрость, служение"
        }
        return interpretations.get(chs, "Неизвестное число")
    
    def get_action_interpretation(self, chd: int) -> str:
        """Получить интерпретацию Числа Действия.
        
        :param chd: Число Действия (1-9)
        :return: Интерпретация
        """
        interpretations = {
            1: "Лидерство, инициатива, независимость",
            2: "Дипломатия, сотрудничество, терпение",
            3: "Творчество, самовыражение, общение",
            4: "Практичность, стабильность, планирование",
            5: "Свобода, приключения, перемены",
            6: "Гармония, ответственность, забота",
            7: "Духовность, анализ, интуиция",
            8: "Материальный успех, власть, контроль",
            9: "Завершение, мудрость, служение"
        }
        return interpretations.get(chd, "Неизвестное число")
    
    def validate_birth_date(self, date_str: str) -> bool:
        """Проверить корректность формата даты рождения.
        
        :param date_str: Дата в формате "dd.mm.yyyy", "dd/mm/yyyy", "dd-mm-yyyy" или "dd mm yyyy"
        :return: True если формат корректен
        """
        try:
            from datetime import datetime
            # Пробуем разные форматы даты
            date_formats = ["%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%d %m %Y"]
            
            for fmt in date_formats:
                try:
                    datetime.strptime(date_str, fmt)
                    return True
                except ValueError:
                    continue
            return False
        except ValueError:
            return False
    
    def validate_name(self, name: str) -> bool:
        """Проверить корректность имени.
        
        :param name: Имя для проверки
        :return: True если имя корректно
        """
        if not name or not name.strip():
            return False
        
        # Проверяем, что содержит только кириллические или латинские буквы
        name = name.strip()
        try:
            if is_cyrillic_text(name):
                # Проверяем, что нет цифр и спецсимволов
                for char in name:
                    if char.isdigit() or char in "!@#$%^&*()_+={}[]|\\:;\"'<>?,./":
                        return False
                return True
            elif is_latin_text(name):
                return True
            else:
                return False
        except Exception:
            return False
    
    def normalize_date(self, date_str: str) -> str:
        """Нормализовать дату к формату dd.mm.yyyy.
        
        :param date_str: Дата в любом поддерживаемом формате
        :return: Дата в формате dd.mm.yyyy
        :raises ValueError: если формат не поддерживается
        """
        from datetime import datetime
        
        date_formats = ["%d.%m.%Y", "%d/%m/%Y", "%d-%m-%Y", "%d %m %Y"]
        
        for fmt in date_formats:
            try:
                d = datetime.strptime(date_str, fmt)
                return d.strftime("%d.%m.%Y")
            except ValueError:
                continue
        
        raise ValueError("Неподдерживаемый формат даты")
