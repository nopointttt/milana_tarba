"""src/services/openai_functions.py
Функции для работы с OpenAI API в контекстном режиме.
"""
from __future__ import annotations

import json
from typing import Dict, List, Any, Optional
from datetime import date

from src.services.analytics.analytics_service import AnalyticsService
from src.services.analytics_storage import AnalyticsStorageService
from src.services.user_service import UserService


class OpenAIFunctions:
    """Класс для работы с функциями OpenAI."""
    
    def __init__(self, db_session):
        self.db_session = db_session
        self.analytics_service = AnalyticsService()
        self.storage_service = AnalyticsStorageService(db_session)
        self.user_service = UserService(db_session)
    
    def get_functions_schema(self) -> List[Dict[str, Any]]:
        """Возвращает схему функций для OpenAI."""
        return [
            {
                "name": "get_user_analytics",
                "description": "Получить сохраненные анализы пользователя из базы данных",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "ID пользователя в Telegram"
                        }
                    },
                    "required": ["user_id"]
                }
            },
            {
                "name": "calculate_analytics",
                "description": "Рассчитать новые анализы по дате рождения и имени",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "birth_date": {
                            "type": "string",
                            "description": "Дата рождения в формате dd.mm.yyyy"
                        },
                        "name": {
                            "type": "string",
                            "description": "Полное имя пользователя (может быть на кириллице или латинице)"
                        },
                        "request_type": {
                            "type": "string",
                            "description": "Тип запроса: анализ, прогноз, совместимость, реализация",
                            "enum": ["анализ", "прогноз", "совместимость", "реализация"]
                        }
                    },
                    "required": ["birth_date"]
                }
            },
            {
                "name": "save_analytics",
                "description": "Сохранить результаты анализа в базу данных",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "user_id": {
                            "type": "integer",
                            "description": "ID пользователя в Telegram"
                        },
                        "birth_date": {
                            "type": "string",
                            "description": "Дата рождения в формате dd.mm.yyyy"
                        },
                        "name": {
                            "type": "string",
                            "description": "Полное имя пользователя"
                        },
                        "analysis_result": {
                            "type": "object",
                            "description": "Результат анализа"
                        }
                    },
                    "required": ["user_id", "birth_date", "analysis_result"]
                }
            }
        ]
    
    async def execute_function(self, function_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Выполняет указанную функцию."""
        try:
            if function_name == "get_user_analytics":
                return await self._get_user_analytics(arguments)
            elif function_name == "calculate_analytics":
                return await self._calculate_analytics(arguments)
            elif function_name == "save_analytics":
                return await self._save_analytics(arguments)
            else:
                return {"error": f"Неизвестная функция: {function_name}"}
        except Exception as e:
            return {"error": f"Ошибка выполнения функции {function_name}: {str(e)}"}
    
    async def _get_user_analytics(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Получить сохраненные анализы пользователя."""
        user_id = args.get("user_id")
        
        # Получаем пользователя
        user = await self.user_service.get_user_by_telegram_id(str(user_id))
        if not user:
            return {"error": "Пользователь не найден"}
        
        # Получаем анализы
        analytics = await self.storage_service.get_analytics_by_user_id(user.id)
        
        return {
            "success": True,
            "analytics": analytics,
            "user_name": user.full_name,
            "count": len(analytics)
        }
    
    async def _calculate_analytics(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Рассчитать новые анализы."""
        birth_date = args.get("birth_date")
        name = args.get("name")
        
        if not birth_date:
            return {"error": "Дата рождения обязательна"}
        
        # Валидация и нормализация даты
        if not self.analytics_service.validate_birth_date(birth_date):
            return {"error": "Неверный формат даты. Используйте dd.mm.yyyy, dd/mm/yyyy, dd-mm-yyyy или dd mm yyyy"}
        
        # Нормализуем дату к стандартному формату
        try:
            birth_date = self.analytics_service.normalize_date(birth_date)
        except ValueError as e:
            return {"error": str(e)}
        
        # Валидация имени (если указано)
        if name and not self.analytics_service.validate_name(name):
            return {"error": "Имя должно быть только на английском языке. Например: Ivan"}
        
        try:
            # Выполняем анализ
            if name:
                analysis = self.analytics_service.analyze_person(birth_date, name)
            else:
                analysis = self.analytics_service.analyze_person_date_only(birth_date)
            
            return {
                "success": True,
                "analysis": analysis,
                "birth_date": birth_date,
                "name": name
            }
        except Exception as e:
            return {"error": f"Ошибка расчета: {str(e)}"}
    
    async def _get_practices_by_theme(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Получить практики по теме."""
        theme = args.get("theme", "").lower()
        planet = args.get("planet")
        
        # Словарь синонимов для поиска практик
        synonyms = {
            "уверенность": ["уверенность", "уверенность в себе", "самооценка", "лидерство", "смелость", "решительность"],
            "отношения": ["отношения", "любовь", "семья", "партнерство", "совместимость", "брак"],
            "деньги": ["деньги", "финансы", "богатство", "доход", "карьера", "бизнес"],
            "здоровье": ["здоровье", "энергия", "сила", "выносливость", "физическое состояние"],
            "творчество": ["творчество", "искусство", "вдохновение", "креативность", "талант"],
            "духовность": ["духовность", "медитация", "просветление", "душа", "смысл жизни"],
            "общение": ["общение", "коммуникация", "дружба", "социальные связи", "влияние"],
            "развитие": ["развитие", "рост", "обучение", "самосовершенствование", "потенциал"]
        }
        
        # Расширяем поисковые термины
        search_terms = [theme]
        for key, values in synonyms.items():
            if any(term in theme for term in values):
                search_terms.extend(values)
        
        # Загружаем практики
        practices = []
        
        # Список файлов с практиками
        practice_files = [
            "sun_practices.json",
            "moon_practices.json", 
            "mars_practices.json",
            "venus_practices.json",
            "ketu_practices.json"
        ]
        
        for filename in practice_files:
            # Проверяем фильтр по планете
            if planet and planet not in filename:
                continue
                
            try:
                import os
                file_path = os.path.join(
                    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                    "..", "..", "practices-data", filename
                )
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    planet_practices = data.get("practices", [])
                    
                    # Фильтруем по расширенным терминам
                    for practice in planet_practices:
                        practice_text = (
                            practice.get("name", "") + " " +
                            practice.get("description", "") + " " +
                            practice.get("query", "") + " " +
                            " ".join(practice.get("keywords", []))
                        ).lower()
                        
                        # Проверяем совпадение с любым из поисковых терминов
                        if any(term in practice_text for term in search_terms):
                            practices.append(practice)
                            
            except Exception as e:
                print(f"Ошибка загрузки {filename}: {e}")
                continue
        
        # Если не найдено по теме, ищем общие практики
        if not practices:
            for filename in practice_files:
                try:
                    import os
                    file_path = os.path.join(
                        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                        "..", "..", "practices-data", filename
                    )
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        planet_practices = data.get("practices", [])
                        
                        # Берем первые 3 практики из каждого файла
                        practices.extend(planet_practices[:3])
                        
                except Exception as e:
                    print(f"Ошибка загрузки {filename}: {e}")
                    continue
        
        return {
            "success": True,
            "practices": practices[:10],  # Ограничиваем до 10 практик
            "count": len(practices),
            "theme": theme,
            "planet": planet,
            "search_terms": search_terms
        }
    
    async def _save_analytics(self, args: Dict[str, Any]) -> Dict[str, Any]:
        """Сохранить результаты анализа."""
        user_id = args.get("user_id")
        birth_date = args.get("birth_date")
        name = args.get("name", "Не указано")
        analysis_result = args.get("analysis_result")
        
        if not all([user_id, birth_date, analysis_result]):
            return {"error": "Недостаточно данных для сохранения"}
        
        try:
            # Получаем или создаем пользователя
            user = await self.user_service.get_or_create_user(
                telegram_user_id=str(user_id),
                username=None,
                full_name=name
            )
            
            # Парсим дату
            day, month, year = map(int, birth_date.split('.'))
            birth_date_obj = date(year, month, day)
            
            # Сохраняем анализ
            from src.db.models import ReportStatus
            await self.storage_service.save_analysis_result(
                user_id=user.id,
                full_name=name,
                birth_date=birth_date_obj,
                analysis_result=analysis_result,
                status=ReportStatus.DONE
            )
            
            return {
                "success": True,
                "message": "Анализ сохранен успешно"
            }
            
        except Exception as e:
            return {"error": f"Ошибка сохранения: {str(e)}"}
