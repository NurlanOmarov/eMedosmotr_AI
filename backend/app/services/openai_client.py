"""
OpenAI клиент для работы с GPT-4o-mini API
Обработка запросов к AI модели
"""

from typing import Optional, List, Dict, Any
import asyncio
from openai import AsyncOpenAI
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class OpenAIService:
    """
    Сервис для работы с OpenAI API
    Использует GPT-4o-mini для анализа
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.AI_MODEL
        self.temperature = settings.AI_TEMPERATURE
        self.max_tokens = settings.AI_MAX_TOKENS

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Базовый метод для chat completion

        Args:
            messages: Список сообщений для модели
            temperature: Температура генерации (опционально)
            max_tokens: Максимальное количество токенов (опционально)
            response_format: Формат ответа (например, {"type": "json_object"})

        Returns:
            Словарь с результатами
        """
        try:
            params = {
                "model": self.model,
                "messages": messages,
                "temperature": temperature or self.temperature,
                "max_tokens": max_tokens or self.max_tokens,
            }

            if response_format:
                params["response_format"] = response_format

            response = await self.client.chat.completions.create(**params)

            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "tokens": {
                    "prompt": response.usage.prompt_tokens,
                    "completion": response.usage.completion_tokens,
                    "total": response.usage.total_tokens
                },
                "finish_reason": response.choices[0].finish_reason
            }

        except Exception as e:
            logger.error(f"Ошибка при вызове OpenAI API: {e}")
            raise

    async def analyze_with_prompt(
        self,
        system_prompt: str,
        user_content: str,
        temperature: Optional[float] = None,
        json_mode: bool = False
    ) -> Dict[str, Any]:
        """
        Анализ с использованием системного промпта

        Args:
            system_prompt: Системный промпт
            user_content: Контент пользователя
            temperature: Температура (опционально)
            json_mode: Использовать JSON mode

        Returns:
            Результат анализа
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ]

        response_format = {"type": "json_object"} if json_mode else None

        return await self.chat_completion(
            messages=messages,
            temperature=temperature,
            response_format=response_format
        )

    async def create_embedding(self, text: str) -> List[float]:
        """
        Создание embedding вектора для текста

        Args:
            text: Текст для векторизации

        Returns:
            Вектор embeddings
        """
        try:
            response = await self.client.embeddings.create(
                model=settings.EMBEDDING_MODEL,
                input=text,
                dimensions=settings.EMBEDDING_DIMENSIONS
            )
            return response.data[0].embedding

        except Exception as e:
            logger.error(f"Ошибка при создании embedding: {e}")
            raise

    async def create_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 100
    ) -> List[List[float]]:
        """
        Создание embeddings для списка текстов (батчами)

        Args:
            texts: Список текстов
            batch_size: Размер батча

        Returns:
            Список векторов
        """
        embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            try:
                response = await self.client.embeddings.create(
                    model=settings.EMBEDDING_MODEL,
                    input=batch,
                    dimensions=settings.EMBEDDING_DIMENSIONS
                )

                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)

            except Exception as e:
                logger.error(f"Ошибка при создании batch embeddings: {e}")
                raise

        return embeddings


# Глобальный экземпляр сервиса
openai_service = OpenAIService()
