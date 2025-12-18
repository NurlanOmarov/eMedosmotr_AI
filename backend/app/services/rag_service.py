"""
RAG (Retrieval-Augmented Generation) сервис
Векторный поиск критериев и документов
"""

from typing import List, Dict, Any, Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
import logging

from app.models.reference import PointCriterion, ICD10Code
from app.models.ai import KnowledgeBaseChunk, KnowledgeBaseDocument
from app.services.openai_client import openai_service
from app.config import settings

logger = logging.getLogger(__name__)


class RAGService:
    """
    Сервис для векторного поиска и RAG
    """

    @staticmethod
    async def find_similar_criteria(
        db: AsyncSession,
        query_text: str,
        top_k: int = None,
        article: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Поиск похожих критериев по тексту запроса

        Args:
            db: Сессия базы данных
            query_text: Текст запроса
            top_k: Количество результатов
            article: Фильтр по статье (опционально)

        Returns:
            Список похожих критериев с оценкой similarity
        """
        if top_k is None:
            top_k = settings.RAG_TOP_K

        try:
            # Создаем embedding для запроса
            query_embedding = await openai_service.create_embedding(query_text)

            # Строим запрос с векторным поиском
            query = select(
                PointCriterion,
                (PointCriterion.criteria_embedding.cosine_distance(query_embedding)).label("distance")
            ).where(
                PointCriterion.criteria_embedding.is_not(None)  # Только записи с embeddings
            )

            if article:
                query = query.where(PointCriterion.article == article)

            query = query.order_by("distance").limit(top_k)

            result = await db.execute(query)
            rows = result.all()

            # Форматируем результаты
            results = []
            for criterion, distance in rows:
                similarity = 1 - distance  # Конвертируем distance в similarity

                results.append({
                    "id": criterion.id,
                    "article": criterion.article,
                    "subpoint": criterion.subpoint,
                    "description": criterion.description,
                    "similarity": round(similarity, 4)
                })

            return results

        except Exception as e:
            logger.error(f"Ошибка при поиске похожих критериев: {e}")
            raise

    @staticmethod
    async def find_similar_icd10(
        db: AsyncSession,
        query_text: str,
        top_k: int = None
    ) -> List[Dict[str, Any]]:
        """
        Поиск похожих кодов МКБ-10 по тексту

        Args:
            db: Сессия базы данных
            query_text: Текст запроса (название болезни)
            top_k: Количество результатов

        Returns:
            Список похожих кодов МКБ-10
        """
        if top_k is None:
            top_k = settings.RAG_TOP_K

        try:
            # Создаем embedding для запроса
            query_embedding = await openai_service.create_embedding(query_text)

            # Строим запрос
            query = select(
                ICD10Code,
                (ICD10Code.name_embedding.cosine_distance(query_embedding)).label("distance")
            ).order_by("distance").limit(top_k)

            result = await db.execute(query)
            rows = result.all()

            # Форматируем результаты
            results = []
            for icd_code, distance in rows:
                similarity = 1 - distance

                results.append({
                    "id": icd_code.id,
                    "code": icd_code.code,
                    "name_ru": icd_code.name_ru,
                    "name_kz": icd_code.name_kz,
                    "level": icd_code.level,
                    "similarity": round(similarity, 4)
                })

            return results

        except Exception as e:
            logger.error(f"Ошибка при поиске МКБ-10: {e}")
            raise

    @staticmethod
    async def find_relevant_knowledge(
        db: AsyncSession,
        query_text: str,
        top_k: int = None,
        document_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Поиск релевантных фрагментов в базе знаний

        Args:
            db: Сессия базы данных
            query_text: Текст запроса
            top_k: Количество результатов
            document_type: Тип документа (опционально)

        Returns:
            Список релевантных фрагментов
        """
        if top_k is None:
            top_k = settings.RAG_TOP_K

        try:
            # Создаем embedding для запроса
            query_embedding = await openai_service.create_embedding(query_text)

            # Строим запрос с JOIN к документам
            query = select(
                KnowledgeBaseChunk,
                KnowledgeBaseDocument.title,
                KnowledgeBaseDocument.document_type,
                (KnowledgeBaseChunk.chunk_embedding.cosine_distance(query_embedding)).label("distance")
            ).join(
                KnowledgeBaseDocument,
                KnowledgeBaseChunk.document_id == KnowledgeBaseDocument.id
            )

            if document_type:
                query = query.where(KnowledgeBaseDocument.document_type == document_type)

            query = query.order_by("distance").limit(top_k)

            result = await db.execute(query)
            rows = result.all()

            # Форматируем результаты
            results = []
            for chunk, doc_title, doc_type, distance in rows:
                similarity = 1 - distance

                results.append({
                    "chunk_id": str(chunk.id),
                    "document_title": doc_title,
                    "document_type": doc_type,
                    "chunk_text": chunk.chunk_text,
                    "chunk_order": chunk.chunk_order,
                    "metadata": chunk.chunk_metadata,
                    "similarity": round(similarity, 4)
                })

            return results

        except Exception as e:
            logger.error(f"Ошибка при поиске в базе знаний: {e}")
            raise

    @staticmethod
    async def build_rag_context(
        db: AsyncSession,
        query_text: str,
        article: Optional[int] = None,
        include_knowledge: bool = False  # ✅ ИСПРАВЛЕНО: база знаний пока пуста
    ) -> str:
        """
        Построение контекста для RAG промпта

        Args:
            db: Сессия базы данных
            query_text: Текст запроса
            article: Статья для фильтрации
            include_knowledge: Включить базу знаний

        Returns:
            Форматированный контекст для промпта
        """
        context_parts = []

        # Ищем релевантные критерии
        criteria = await RAGService.find_similar_criteria(
            db, query_text, top_k=3, article=article
        )

        if criteria:
            context_parts.append("# Релевантные критерии из Приложения 2:\n")
            for i, crit in enumerate(criteria, 1):
                context_parts.append(
                    f"{i}. Статья {crit['article']}, подпункт {crit['subpoint']}\n"
                    f"   Описание: {crit['description']}\n"
                )

        # Ищем в базе знаний
        if include_knowledge:
            knowledge = await RAGService.find_relevant_knowledge(
                db, query_text, top_k=2
            )

            if knowledge:
                context_parts.append("\n# Релевантная информация из базы знаний:\n")
                for i, item in enumerate(knowledge, 1):
                    context_parts.append(
                        f"{i}. {item['document_title']}\n"
                        f"   {item['chunk_text']}\n"
                    )

        return "\n".join(context_parts) if context_parts else "Контекст не найден"

    @staticmethod
    async def search_diseases_in_text(
        db: AsyncSession,
        text: str,
        top_k: int = 5,
        similarity_threshold: float = 0.65
    ) -> List[Dict[str, Any]]:
        """
        Поиск упоминаний заболеваний в произвольном тексте через RAG

        Используется для проверки противоречий (Этап 0) в системе валидации.
        Анализирует текст и находит наиболее похожие критерии заболеваний
        из таблицы point_criteria.

        Args:
            db: Сессия базы данных
            text: Текст для анализа (анамнез, жалобы, примечания и т.д.)
            top_k: Максимальное количество результатов
            similarity_threshold: Минимальный порог похожести (0-1)

        Returns:
            Список найденных заболеваний с категориями годности
            [
                {
                    "article": 43,
                    "subpoint": "3",
                    "description": "...",
                    "similarity": 0.85,
                    "categories": {1: "Д", 2: "Д", 3: "В-ИНД", 4: "НГ"}
                }
            ]
        """
        # Проверка минимальной длины текста
        if not text or len(text.strip()) < 10:
            return []

        try:
            # Создаем embedding для текста
            query_embedding = await openai_service.create_embedding(text)

            # Ищем похожие критерии (заболевания) в point_criteria
            query = select(
                PointCriterion,
                (PointCriterion.criteria_embedding.cosine_distance(query_embedding)).label("distance")
            ).where(
                PointCriterion.criteria_embedding.is_not(None)
            ).order_by("distance").limit(top_k)

            result = await db.execute(query)
            rows = result.all()

            # Фильтруем по threshold и форматируем результаты
            diseases = []
            for criterion, distance in rows:
                similarity = 1 - distance

                # Пропускаем результаты ниже порога
                if similarity < similarity_threshold:
                    continue

                diseases.append({
                    "article": criterion.article,
                    "subpoint": criterion.subpoint,
                    "description": criterion.description,
                    "similarity": round(similarity, 4),
                    "categories": {
                        1: criterion.graph_1,
                        2: criterion.graph_2,
                        3: criterion.graph_3,
                        4: criterion.graph_4
                    }
                })

            logger.debug(
                f"search_diseases_in_text: найдено {len(diseases)} заболеваний "
                f"(threshold={similarity_threshold})"
            )

            return diseases

        except Exception as e:
            logger.error(f"Ошибка при поиске заболеваний в тексте: {e}")
            return []

    @staticmethod
    async def search_diseases_in_multiple_fields(
        db: AsyncSession,
        fields: Dict[str, Optional[str]],
        top_k: int = 3,
        similarity_threshold: float = 0.65
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Поиск заболеваний в нескольких текстовых полях

        Args:
            db: Сессия базы данных
            fields: Словарь {название_поля: значение}
            top_k: Количество результатов на поле
            similarity_threshold: Минимальный порог похожести

        Returns:
            Словарь {название_поля: [найденные_заболевания]}
        """
        results = {}

        for field_name, field_value in fields.items():
            if field_value and len(field_value.strip()) >= 10:
                diseases = await RAGService.search_diseases_in_text(
                    db=db,
                    text=field_value,
                    top_k=top_k,
                    similarity_threshold=similarity_threshold
                )
                if diseases:
                    results[field_name] = diseases

        return results


# Глобальный экземпляр сервиса
rag_service = RAGService()
