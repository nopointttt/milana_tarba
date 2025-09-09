"""src/services/openai_service.py
Сервис для работы с OpenAI API.
"""
from __future__ import annotations

import asyncio
from typing import Dict, Any, Optional

from openai import AsyncOpenAI

from .openai_prompts import create_analysis_prompt


class OpenAIService:
    """Сервис для работы с OpenAI API."""
    
    def __init__(self, api_key: str, assistant_id: Optional[str] = None):
        """Инициализировать сервис OpenAI.
        
        :param api_key: API ключ OpenAI
        :param assistant_id: ID ассистента OpenAI (опционально)
        """
        self.client = AsyncOpenAI(api_key=api_key)
        self.assistant_id = assistant_id
    
    async def analyze_with_assistant(
        self,
        birth_date: str,
        full_name: str | None,
        analysis_data: Dict[str, Any]
    ) -> str:
        """Проанализировать данные через OpenAI Assistant.
        
        :param birth_date: Дата рождения
        :param full_name: Полное имя (может быть None)
        :param analysis_data: Данные анализа от программной части
        :return: Персонализированный анализ от цифрового психолога
        """
        if not self.assistant_id:
            raise ValueError("Assistant ID не задан")
        
        # Создаём промпт на основе данных
        calculations = analysis_data.get('calculations', {})
        
        prompt = create_analysis_prompt(
            birth_date=birth_date,
            full_name=full_name,
            consciousness_number=calculations.get('consciousness_number'),
            action_number=calculations.get('action_number'),
            name_number=calculations.get('name_number'),
            matrix_data=analysis_data.get('matrix', {}),
            interpretations=analysis_data.get('interpretations', {}),
            exceptions=analysis_data.get('exceptions', {})
        )
        
        try:
            # Создаём thread
            thread = await self.client.beta.threads.create()
            
            # Добавляем сообщение
            await self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=prompt
            )
            
            # Запускаем ассистента
            run = await self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            
            # Ждём завершения с timeout
            timeout_seconds = 60
            start_time = asyncio.get_event_loop().time()
            
            while run.status in ['queued', 'in_progress', 'requires_action']:
                if asyncio.get_event_loop().time() - start_time > timeout_seconds:
                    return "❌ Превышено время ожидания ответа от ассистента"
                
                await asyncio.sleep(1)
                run = await self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
            
            if run.status == 'completed':
                # Получаем ответ
                messages = await self.client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                
                # Ищем последнее сообщение от ассистента
                for message in messages.data:
                    if message.role == 'assistant':
                        return message.content[0].text.value
                
                return "❌ Не удалось получить ответ от ассистента"
            else:
                # Если Assistant API не сработал, используем Chat Completion
                print(f"⚠️ Assistant API не сработал ({run.status}), переключаемся на Chat Completion")
                return await self.analyze_with_chat_completion(
                    birth_date, full_name, analysis_data
                )
                
        except Exception as e:
            return f"❌ Ошибка при работе с OpenAI: {str(e)}"
    
    async def analyze_with_chat_completion(
        self,
        birth_date: str,
        full_name: str | None,
        analysis_data: Dict[str, Any]
    ) -> str:
        """Проанализировать данные через Chat Completion API.
        
        :param birth_date: Дата рождения
        :param full_name: Полное имя (может быть None)
        :param analysis_data: Данные анализа от программной части
        :return: Персонализированный анализ от цифрового психолога
        """
        # Создаём промпт на основе данных
        calculations = analysis_data.get('calculations', {})
        
        prompt = create_analysis_prompt(
            birth_date=birth_date,
            full_name=full_name,
            consciousness_number=calculations.get('consciousness_number'),
            action_number=calculations.get('action_number'),
            name_number=calculations.get('name_number'),
            matrix_data=analysis_data.get('matrix', {}),
            interpretations=analysis_data.get('interpretations', {}),
            exceptions=analysis_data.get('exceptions', {})
        )
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,  # Уменьшаем для Telegram
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"❌ Ошибка при работе с OpenAI: {str(e)}"
    
    async def analyze_person(
        self,
        birth_date: str,
        full_name: str | None,
        analysis_data: Dict[str, Any]
    ) -> str:
        """Проанализировать данные (автоматически выбирает метод).
        
        :param birth_date: Дата рождения
        :param full_name: Полное имя (может быть None)
        :param analysis_data: Данные анализа от программной части
        :return: Персонализированный анализ от цифрового психолога
        """
        if self.assistant_id:
            return await self.analyze_with_assistant(
                birth_date, full_name, analysis_data
            )
        else:
            return await self.analyze_with_chat_completion(
                birth_date, full_name, analysis_data
            )
    
    async def search_practices(self, user_query: str) -> str:
        """Поиск практик по запросу пользователя.
        
        :param user_query: Запрос пользователя для поиска практик
        :return: Список подходящих практик
        """
        if not self.assistant_id:
            raise ValueError("Assistant ID не задан")
        
        # Создаём промпт для поиска практик
        from .openai_prompts import create_practices_prompt
        prompt = create_practices_prompt(user_query)
        
        try:
            # Создаём thread
            thread = await self.client.beta.threads.create()
            
            # Добавляем сообщение
            await self.client.beta.threads.messages.create(
                thread_id=thread.id,
                role="user",
                content=prompt
            )
            
            # Запускаем ассистента
            run = await self.client.beta.threads.runs.create(
                thread_id=thread.id,
                assistant_id=self.assistant_id
            )
            
            # Ждём завершения
            while run.status in ['queued', 'in_progress', 'requires_action']:
                await asyncio.sleep(1)
                run = await self.client.beta.threads.runs.retrieve(
                    thread_id=thread.id,
                    run_id=run.id
                )
            
            if run.status == 'completed':
                # Получаем ответ
                messages = await self.client.beta.threads.messages.list(
                    thread_id=thread.id
                )
                
                if messages.data:
                    return messages.data[0].content[0].text.value
                else:
                    return "❌ Не удалось получить ответ от ассистента"
            else:
                return f"❌ Ошибка выполнения: {run.status}"
                
        except Exception as e:
            # Fallback на Chat Completion API
            return await self.search_practices_with_chat_completion(user_query)
    
    async def search_practices_with_chat_completion(self, user_query: str) -> str:
        """Поиск практик через Chat Completion API.
        
        :param user_query: Запрос пользователя для поиска практик
        :return: Список подходящих практик
        """
        # Создаём промпт для поиска практик
        from .openai_prompts import create_practices_prompt
        prompt = create_practices_prompt(user_query)
        
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1500,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"❌ Ошибка при работе с OpenAI: {str(e)}"
