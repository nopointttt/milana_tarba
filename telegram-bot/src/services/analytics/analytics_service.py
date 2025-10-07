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

from datetime import date, datetime
from typing import Dict, Any, Union, List

from .chs import calc_chs
from .chd import calc_chd_with_exceptions
from .matrix import Matrix
from .name_number import calc_name_number, get_name_interpretation
from .transliteration import normalize_name_for_calculation, is_cyrillic_text, is_latin_text
from .personal_dates import calc_all_personal_dates


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
        
        # 6. Расчёт личных дат
        personal_dates = calc_all_personal_dates(birth_date)
        
        # 7. Расчёт Числа Дхармы (Кармы)
        dharma_number = self.calc_dharma_number(birth_date)
        dharma_interpretation = self.get_dharma_interpretation(dharma_number)
        
        # 8. Расчёт трансформации сознания
        transformation = self.calc_consciousness_transformation(chs)
        transformation_interpretation = self.get_transformation_interpretation(chs, transformation)
        
        # 9. Получение дополнительных данных
        energy_sources = self.get_energy_sources_by_consciousness(chs)
        relationship_lifehacks = self.get_relationship_lifehacks_by_consciousness(chs)
        consciousness_triggers = self.get_consciousness_triggers(chs)
        
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
                "name_number": name_number,
                "personal_year": personal_dates["personal_year"],
                "personal_month": personal_dates["personal_month"],
                "personal_day": personal_dates["personal_day"]
            },
            "matrix": {
                "digit_counts": matrix_analysis["digit_counts"],
                "missing_digits": matrix_analysis["missing_digits"],
                "strong_digits": matrix_analysis["strong_digits"],
                "weak_digits": matrix_analysis["weak_digits"],
                "analysis": matrix_analysis["analysis"]
            },
            "interpretations": {
                "name_interpretation": name_interpretation,
                "dharma_interpretation": dharma_interpretation,
                "transformation_interpretation": transformation_interpretation
            },
            "dharma": {
                "dharma_number": dharma_number,
                "interpretation": dharma_interpretation
            },
            "transformation": {
                "steps": transformation,
                "interpretation": transformation_interpretation
            },
            "psychology": {
                "energy_sources": energy_sources,
                "relationship_lifehacks": relationship_lifehacks,
                "consciousness_triggers": consciousness_triggers
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
    
    def get_energy_sources_by_consciousness(self, chs: int) -> Dict[str, List[str]]:
        """Получить источники наполнения энергией по Числу Сознания.
        
        :param chs: Число Сознания (1-9)
        :return: Источники энергии по уровням
        """
        energy_sources = {
            1: {
                "physical": ["Активные виды спорта", "Силовые тренировки", "Боевые искусства", "Индивидуальные достижения"],
                "spiritual": ["Медитации на силу", "Аффирмации лидерства", "Визуализация побед", "Практики уверенности"],
                "social": ["Руководящие роли", "Менторство", "Публичные выступления", "Признание заслуг"],
                "intellectual": ["Изучение стратегий", "Лидерские курсы", "Книги о достижениях", "Планирование целей"]
            },
            2: {
                "physical": ["Парные танцы", "Йога", "Массаж", "Спа-процедуры", "Объятия"],
                "spiritual": ["Медитации на гармонию", "Практики сострадания", "Работа с эмоциями", "Дыхательные техники"],
                "social": ["Глубокие беседы", "Эмоциональная поддержка", "Совместная деятельность", "Забота о других"],
                "intellectual": ["Психология отношений", "Эмоциональный интеллект", "Искусство", "Культура"]
            },
            3: {
                "physical": ["Творческие движения", "Танцы", "Театр", "Рисование", "Пение"],
                "spiritual": ["Медитации на творчество", "Визуализация идей", "Практики вдохновения", "Работа с музой"],
                "social": ["Творческие коллективы", "Выступления", "Обмен идеями", "Вдохновляющее общение"],
                "intellectual": ["Изучение искусств", "Креативные техники", "Философия творчества", "Новые знания"]
            },
            4: {
                "physical": ["Структурированные тренировки", "Строительство", "Садоводство", "Рукоделье"],
                "spiritual": ["Медитации на стабильность", "Заземляющие практики", "Ритуалы порядка", "Работа с основами"],
                "social": ["Семейные традиции", "Стабильные отношения", "Помощь в организации", "Наставничество"],
                "intellectual": ["Фундаментальные знания", "Системное мышление", "Планирование", "Структурирование"]
            },
            5: {
                "physical": ["Путешествия", "Разнообразный спорт", "Новые маршруты", "Активный отдых"],
                "spiritual": ["Медитации на свободу", "Практики освобождения", "Работа с ограничениями", "Расширение сознания"],
                "social": ["Новые знакомства", "Разнообразное общение", "Коммуникативные игры", "Обмен опытом"],
                "intellectual": ["Изучение языков", "Новые области знаний", "Курсы коммуникации", "Культурный обмен"]
            },
            6: {
                "physical": ["SPA и красота", "Массаж", "Уход за телом", "Эстетические процедуры"],
                "spiritual": ["Медитации на любовь", "Практики благодарности", "Работа с сердечной чакрой", "Прощение"],
                "social": ["Забота о близких", "Романтические отношения", "Семейное время", "Помощь нуждающимся"],
                "intellectual": ["Психология любви", "Искусство отношений", "Семейная психология", "Эстетика"]
            },
            7: {
                "physical": ["Йога", "Медитативные практики", "Дыхательные техники", "Духовные ретриты"],
                "spiritual": ["Глубокие медитации", "Духовные практики", "Работа с интуицией", "Исследование сознания"],
                "social": ["Духовное общение", "Мудрые наставники", "Философские беседы", "Уединение"],
                "intellectual": ["Эзотерические знания", "Философия", "Духовные учения", "Самопознание"]
            },
            8: {
                "physical": ["Дисциплинированные тренировки", "Выносливость", "Материальное творчество", "Рукоделие"],
                "spiritual": ["Медитации на терпение", "Практики выносливости", "Работа с дисциплиной", "Преодоление трудностей"],
                "social": ["Профессиональное общение", "Наставничество", "Передача опыта", "Материальная помощь"],
                "intellectual": ["Профессиональное развитие", "Мастерство", "Детальное изучение", "Экспертиза"]
            },
            9: {
                "physical": ["Интенсивные тренировки", "Соревновательный спорт", "Активная деятельность", "Физические вызовы"],
                "spiritual": ["Медитации на служение", "Практики отдачи", "Работа с завершением", "Трансформация"],
                "social": ["Помощь людям", "Социальная деятельность", "Завершение проектов", "Эмоциональная поддержка"],
                "intellectual": ["Обобщение знаний", "Мудрость", "Завершение циклов", "Передача опыта"]
            }
        }
        return energy_sources.get(chs, {
            "physical": ["Физическая активность"],
            "spiritual": ["Медитации"],
            "social": ["Общение"],
            "intellectual": ["Обучение"]
        })
    
    def get_relationship_lifehacks_by_consciousness(self, chs: int) -> List[str]:
        """Получить лайфхаки в отношениях по Числу Сознания.
        
        :param chs: Число Сознания (1-9)
        :return: Список лайфхаков для отношений
        """
        lifehacks = {
            1: [
                "Признавайте их авторитет и лидерские качества",
                "Не критикуйте напрямую - предлагайте альтернативы", 
                "Давайте им возможность принимать решения",
                "Хвалите их достижения и успехи",
                "Не спорьте - лучше аргументированно объясняйте",
                "Поддерживайте их инициативы"
            ],
            2: [
                "Уделяйте больше внимания и проявляйте заботу",
                "Обнимайте чаще - им нужен физический контакт",
                "Давайте обратную связь - им важно знать ваши чувства",
                "Делитесь своим настроением и состоянием",
                "Избегайте долгих объяснений - будьте чуткими",
                "Используйте смайлики в сообщениях"
            ],
            3: [
                "Поддерживайте их творческие идеи и проекты",
                "Давайте им пространство для самовыражения",
                "Будьте благодарными слушателями их историй",
                "Поощряйте их оптимизм и энтузиазм",
                "Участвуйте в их творческих начинаниях",
                "Цените их юмор и легкость общения"
            ],
            4: [
                "Уважайте их потребность в стабильности",
                "Планируйте вместе - им нужна предсказуемость",
                "Ценитие их практичность и надежность",
                "Не торопите с принятием решений",
                "Поддерживайте семейные традиции",
                "Будьте последовательными в словах и действиях"
            ],
            5: [
                "Давайте им свободу и не ограничивайте",
                "Поддерживайте их тягу к приключениям", 
                "Не давите - они сделают назло если заставлять",
                "Разговаривайте через пользу - что для них ценно",
                "Давайте свободу выбора: 'Можно так, а можно так. Как считаешь?'",
                "Передавайте мяч ответственности через вопросы",
                "Заканчивайте фразы: 'А ты как считаешь?', 'Как сделаем?'",
                "Они ценят имидж - важно как они выглядят в обществе",
                "Будьте готовы к переменам и хаотичности в минусе"
            ],
            6: [
                "Проявляйте романтику и нежность",
                "Создавайте красивую атмосферу в отношениях",
                "Ценитие их заботу и ответственность",
                "Уделяйте внимание эстетике и красоте",
                "Поддерживайте их стремление к гармонии",
                "Благодарите за проявления любви"
            ],
            7: [
                "Уважайте их потребность в уединении",
                "Поддерживайте их духовные поиски",
                "Ведите глубокие философские беседы",
                "Давайте им время на размышления",
                "Цените их мудрость и интуицию",
                "Не торопите с эмоциональной близостью"
            ],
            8: [
                "Уважайте их амбиции и цели",
                "Поддерживайте их стремление к успеху",
                "Ценитие их трудолюбие и упорство",
                "Помогайте в достижении материальных целей",
                "Будьте надежным партнером в делах",
                "Признавайте их компетентность"
            ],
            9: [
                "КРИТИЧНО: Практики эмоционального покоя - их основа!",
                "Не подходите к ним в эмоциональном раздрае", 
                "Помните - они помнят ВСЕ ваши недостатки наизусть",
                "На контроле 'справедливость' - 'я больше вкладываюсь'",
                "Склонны к паранойе в минусе - 'почему он меня не ценит'",
                "Смотрите на них 'глазами королей' - с точки B",
                "Подчеркивайте их достоинства и достижения",
                "Практика благодарности с точкой входа обязательна",
                "В конфликте - сначала успокоиться, потом говорить"
            ]
        }
        return lifehacks.get(chs, [
            "Будьте внимательными к их потребностям",
            "Проявляйте уважение к их особенностям",
            "Поддерживайте их сильные стороны"
        ])
    
    def get_consciousness_triggers(self, chs: int) -> List[str]:
        """Получить триггеры (раздражители) по Числу Сознания.
        
        :param chs: Число Сознания (1-9)
        :return: Список триггеров
        """
        triggers = {
            1: [
                "Когда люди не делают так, как они хотят",
                "Несогласие и несогласованность",
                "Когда не реагируют на просьбы",
                "Когда критикуют и шутят в их сторону",
                "Когда люди не берут ответственность",
                "Нытики, слабые, медлительные люди",
                "Когда их не слушают в разговоре",
                "Когда не признают их авторитет",
                "Когда ограничивают личное пространство",
                "Когда им не служат или не нуждаются в них"
            ],
            2: [
                "Когда их не понимают",
                "Когда им уделяют мало внимания, не обнимают",
                "Когда не дают обратной связи",
                "Когда не делятся настроением и состоянием",
                "Когда долго приходится объяснять",
                "Отсутствие эмоциональной близости",
                "Равнодушие к их чувствам",
                "Игнорирование их потребностей"
            ],
            3: [
                "Когда их не ценят за творчество",
                "Ограничение самовыражения",
                "Критика их идей и проектов",
                "Принуждение к рутинной работе",
                "Игнорирование их энтузиазма",
                "Отсутствие признания талантов"
            ],
            4: [
                "Хаос и неопределенность",
                "Постоянные изменения планов",
                "Отсутствие четких целей",
                "Непредсказуемость партнера",
                "Нарушение договоренностей",
                "Импульсивные решения окружающих"
            ],
            5: [
                "Ограничения свободы",
                "Принуждение к рутине",
                "Запреты на путешествия и новизну",
                "Монотонная деятельность",
                "Попытки их контролировать",
                "Отсутствие разнообразия в жизни"
            ],
            6: [
                "Отсутствие красоты и гармонии",
                "Конфликты и агрессия вокруг",
                "Игнорирование их заботы",
                "Неблагодарность за их усилия",
                "Грубость и невоспитанность",
                "Разрушение семейных ценностей"
            ],
            7: [
                "Поверхностное общение",
                "Отсутствие времени на размышления",
                "Принуждение к быстрым решениям",
                "Игнорирование их интуиции",
                "Материализм окружающих",
                "Отсутствие духовного понимания"
            ],
            8: [
                "Некомпетентность окружающих",
                "Безответственность других",
                "Отсутствие дисциплины",
                "Легкомысленное отношение к делу",
                "Неуважение к их экспертизе",
                "Попытки обойти установленные правила"
            ],
            9: [
                "Несправедливость и неравенство",
                "Эгоизм окружающих",
                "Отсутствие возможности помочь",
                "Незавершенные дела и проекты",
                "Равнодушие к страданиям других",
                "Препятствия в служении людям"
            ]
        }
        return triggers.get(chs, [
            "Непонимание их особенностей",
            "Неуважение к их потребностям"
        ])
    
    def calc_dharma_number(self, birth_date: Union[str, date]) -> int:
        """Рассчитать Число Дхармы (Карма человека).
        
        Формула из базы знаний: день + месяц рождения (без года)
        Пример: 05.09.1992 → 5+9 = 14 = 1+4 = 5
        
        :param birth_date: Дата рождения
        :return: Число Дхармы (1-9)
        """
        # Парсим дату
        if isinstance(birth_date, str):
            try:
                birth_dt = datetime.strptime(birth_date, "%d.%m.%Y")
            except ValueError:
                raise ValueError(f"Неверный формат даты: {birth_date}")
        else:
            birth_dt = birth_date
        
        # Рассчитываем по формуле день + месяц
        day = birth_dt.day
        month = birth_dt.month
        dharma_sum = day + month
        
        # Сворачиваем до однозначного числа
        while dharma_sum > 9:
            dharma_sum = sum(int(digit) for digit in str(dharma_sum))
        
        return dharma_sum
    
    def get_dharma_interpretation(self, dharma: int) -> str:
        """Получить интерпретацию Числа Дхармы.
        
        :param dharma: Число Дхармы (1-9)
        :return: Интерпретация кармических задач
        """
        interpretations = {
            1: "Кармическая задача: развивать лидерство и независимость. Научиться принимать решения и брать ответственность за свою жизнь.",
            2: "Кармическая задача: развивать понимание и дипломатию. Научиться сотрудничать и создавать гармонию в отношениях.",
            3: "Кармическая задача: развивать творчество и самовыражение. Научиться делиться своими талантами с миром.",
            4: "Кармическая задача: развивать целеустремленность и структурность. Научиться ставить цели и достигать их систематично.",
            5: "Кармическая задача: развивать коммуникацию и свободу. Научиться общаться и расширять границы сознания.",
            6: "Кармическая задача: развивать любовь и заботу. Научиться создавать гармонию и красоту в жизни.",
            7: "Кармическая задача: развивать духовность и мудрость. Научиться глубокому анализу и интуитивному пониманию.",
            8: "Кармическая задача: развивать мастерство и дисциплину. Научиться упорству и профессиональному совершенству.",
            9: "Кармическая задача: развивать служение и мудрость. Научиться помогать людям и завершать важные циклы."
        }
        return interpretations.get(dharma, "Неизвестная кармическая задача")
    
    def calc_consciousness_transformation(self, chs: int) -> Dict[str, Any]:
        """Рассчитать шаги трансформации сознания.
        
        Алгоритм из базы знаний: от ЧС сделать шаг назад, потом шаг вперед
        
        :param chs: Число Сознания (1-9)
        :return: Шаги трансформации
        """
        transformations = {
            1: {"prev": 9, "next": 2, "path": "9 → 1 → 2"},
            2: {"prev": 1, "next": 3, "path": "1 → 2 → 3"},
            3: {"prev": 2, "next": 4, "path": "2 → 3 → 4"},
            4: {"prev": 3, "next": 5, "path": "3 → 4 → 5"},
            5: {"prev": 4, "next": 6, "path": "4 → 5 → 6"},
            6: {"prev": 5, "next": 7, "path": "5 → 6 → 7"},
            7: {"prev": 6, "next": 8, "path": "6 → 7 → 8"},
            8: {"prev": 7, "next": 9, "path": "7 → 8 → 9"},
            9: {"prev": 8, "next": 1, "path": "8 → 9 → 1"}
        }
        return transformations.get(chs, {"prev": 1, "next": 1, "path": "1 → 1 → 1"})
    
    def get_transformation_interpretation(self, chs: int, transformation: Dict[str, Any]) -> str:
        """Получить интерпретацию трансформации сознания.
        
        :param chs: Число Сознания
        :param transformation: Данные трансформации
        :return: Описание программы развития
        """
        prev_energy = transformation["prev"]
        next_energy = transformation["next"]
        
        energy_names = {
            1: "лидерство", 2: "дипломатия", 3: "творчество", 4: "структурность",
            5: "коммуникация", 6: "гармония", 7: "духовность", 8: "мастерство", 9: "служение"
        }
        
        prev_name = energy_names.get(prev_energy, "энергия")
        next_name = energy_names.get(next_energy, "энергия")
        current_name = energy_names.get(chs, "энергия")
        
        interpretation = f"""Программа трансформации сознания для ЧС {chs}:

**Этап 1:** Освоить энергию {prev_energy} ({prev_name})
Развивать качества предыдущей энергии для укрепления основы

**Этап 2:** Углубить энергию {chs} ({current_name})  
Совершенствовать свою основную энергию сознания

**Этап 3:** Освоить энергию {next_energy} ({next_name})
Расширить сознание через освоение следующей энергии

Путь трансформации: {transformation["path"]}"""

        return interpretation
    
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
