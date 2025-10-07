"""src/services/video_practices_service.py
Практики и техники, извлеченные из транскрибированных видео Миланы Тарба.
"""
from typing import Dict, List, Any


class VideoPracticesService:
    """Сервис для работы с практиками из видеоматериалов."""
    
    def __init__(self):
        """Инициализация сервиса."""
        self.video_practices = self._load_video_practices()
    
    def _load_video_practices(self) -> Dict[str, Any]:
        """Загрузить практики из видеоматериалов."""
        return {
            "emotional_peace": {
                "name": "Практики эмоционального покоя",
                "target": "Люди с двумя девятками в матрице, эмоциональный раздрай",
                "description": "Обязательные практики для выхода из эгоизма и эмоционального состояния",
                "steps": [
                    "Физический уровень: ходьба, баня, питание, вода, сон",
                    "Духовный уровень: медитации, молитва, благодарность, нейропрактики", 
                    "Социальный уровень: общение с приятными людьми, польза людям",
                    "Интеллектуальный уровень: позиция ученика, получение знаний"
                ],
                "source": "Видео: Прогностика, совместимость, лайфхаки"
            },
            "find_pluses_in_minuses": {
                "name": "Найти плюсы в минусах партнера",
                "target": "Конфликты в отношениях, раздражение партнером",
                "description": "Техника трансформации восприятия недостатков партнера",
                "steps": [
                    "1. В своих плюсах найти антиподы (теневые стороны)",
                    "2. В этих антиподах найти плюсы",
                    "3. В минусах партнера найти по 3 плюса на каждый минус",
                    "4. Записать все плюсы на листе",
                    "5. Фокусироваться только на хорошем в партнере"
                ],
                "example": "Вранье партнера → Плюс: умеет защитить от переживаний, может структурировать информацию под ситуацию",
                "source": "Видео: Прогностика, совместимость, лайфхаки"
            },
            "gratitude_with_entry_point": {
                "name": "Практика благодарности с точкой входа", 
                "target": "Улучшение отношений, фокус на хорошем",
                "description": "Усиленная версия практики благодарности для отношений",
                "steps": [
                    "1. Каждый день писать минимум 7 благодарностей",
                    "2. К каждой благодарности указывать 'точку входа' - через кого это стало возможно",
                    "3. Пример: 'Благодарю за возможность учиться. Точка входа: муж (сидел с детьми)'",
                    "4. Делать 21 день подряд",
                    "5. Обязательно включать мужа/партнера в точки входа"
                ],
                "effect": "Начинаете помнить о людях только хорошее вместо плохого",
                "source": "Видео: Прогностика, совместимость, лайфхаки"
            },
            "communication_with_freedom": {
                "name": "Общение через свободу выбора",
                "target": "Общение с мужчинами, особенно ЧС 5",
                "description": "Техника управления через создание ощущения свободы",
                "steps": [
                    "1. НЕ говорить: 'Ты должен делать так'",
                    "2. Предлагать варианты: 'Можно так, а можно так'",
                    "3. Передавать ответственность: 'Как ты считаешь?'",
                    "4. Заканчивать: 'Как сделаем?'",
                    "5. Говорить через их ценности и пользу",
                    "6. Быть готовой к любому ответу (готовность к отказу)"
                ],
                "principle": "Мужчина голова, женщина шея - поворачивать мягко",
                "source": "Видео: Прогностика, совместимость, лайфхаки"
            },
            "make_kings_with_eyes": {
                "name": "Делаем королей своими глазами",
                "target": "Улучшение отношений, поднятие самооценки партнера",
                "description": "Техника видения партнера с его лучшей стороны",
                "steps": [
                    "1. Смотреть на партнера с точки B (лучшей версии)",
                    "2. Находить и подчеркивать его достоинства",
                    "3. Видеть в нем потенциал и возможности",
                    "4. Говорить ему о его сильных сторонах",
                    "5. Фокусироваться на том, что он делает хорошо",
                    "6. Игнорировать недостатки (не акцентировать)"
                ],
                "effect": "Партнер чувствует себя мужчиной, которого хотят и уважают",
                "source": "Видео: Прогностика, совместимость, лайфхаки"
            },
            "path_of_hero": {
                "name": "Путь героя", 
                "target": "Низкая самооценка, синдром отличницы",
                "description": "Восстановление чувства собственной ценности",
                "steps": [
                    "1. Составить список минимум 50 достижений за всю жизнь",
                    "2. Начинать с сегодняшнего дня и идти назад в детство",
                    "3. Включать как крупные, так и мелкие достижения",
                    "4. Записывать всё подряд: 'научилась ездить на велосипеде'",
                    "5. Читать список когда нужно поднять самооценку"
                ],
                "effect": "Возвращение чувства 'я охеренная молодец'",
                "source": "Видео: Описание энергий планет, ЧС"
            },
            "true_request_technique": {
                "name": "Техника определения истинного запроса",
                "target": "Диагностика клиентов, понимание себя",
                "description": "5 вопросов для углубления запроса",
                "steps": [
                    "1. Чего вы хотите?",
                    "2. В чем конкретно это заключается?",
                    "3. Что вам это даст?",
                    "4. Что вы будете чувствовать, когда это получите?",
                    "5. Через что еще можно прийти к этим ощущениям?"
                ],
                "purpose": "Выявить истинную потребность за поверхностным запросом",
                "source": "Видео: Описание энергий планет, ЧС"
            }
        }
    
    def get_practice_by_name(self, practice_name: str) -> Dict[str, Any]:
        """Получить практику по названию."""
        for practice_id, practice_data in self.video_practices.items():
            if practice_data["name"].lower() in practice_name.lower():
                return practice_data
        return {}
    
    def get_practices_for_consciousness(self, chs: int) -> List[Dict[str, Any]]:
        """Получить рекомендуемые практики для конкретного ЧС."""
        recommendations = {
            2: ["gratitude_with_entry_point", "emotional_peace"],
            3: ["path_of_hero", "find_pluses_in_minuses"], 
            4: ["emotional_peace", "path_of_hero"],
            5: ["communication_with_freedom", "emotional_peace"],
            9: ["emotional_peace", "gratitude_with_entry_point", "find_pluses_in_minuses"]
        }
        
        practice_ids = recommendations.get(chs, ["emotional_peace"])
        return [self.video_practices[pid] for pid in practice_ids if pid in self.video_practices]
    
    def get_practices_for_relationships(self) -> List[Dict[str, Any]]:
        """Получить все практики для отношений."""
        relationship_practices = [
            "find_pluses_in_minuses",
            "gratitude_with_entry_point", 
            "communication_with_freedom",
            "make_kings_with_eyes"
        ]
        return [self.video_practices[pid] for pid in relationship_practices]
    
    def get_diagnostic_practices(self) -> List[Dict[str, Any]]:
        """Получить диагностические практики."""
        return [self.video_practices["true_request_technique"]]
    
    def search_video_practices(self, query: str) -> List[Dict[str, Any]]:
        """Поиск практик по запросу."""
        query_lower = query.lower()
        results = []
        
        for practice_id, practice_data in self.video_practices.items():
            # Поиск в названии, описании и целевой аудитории
            searchable_text = (
                practice_data["name"] + " " + 
                practice_data["description"] + " " + 
                practice_data["target"]
            ).lower()
            
            if any(word in searchable_text for word in query_lower.split()):
                results.append(practice_data)
        
        return results
