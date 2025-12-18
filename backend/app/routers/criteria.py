"""
API endpoints для работы с критериями
Поиск и получение критериев из Приложения 2
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from pydantic import BaseModel

from app.utils.database import get_db
from app.models.reference import PointCriterion, PointDiagnosis
from app.services.rag_service import rag_service

router = APIRouter()


# Pydantic модели для запросов/ответов
class CriteriaSearchRequest(BaseModel):
    query: str
    article: Optional[int] = None
    top_k: int = 5


class CriteriaSearchResult(BaseModel):
    id: int
    article: int
    subpoint: str
    description: str
    similarity: float


class PointDiagnosisResponse(BaseModel):
    id: int
    chapter: str
    article: int
    subpoint: str
    diagnoses_codes: Optional[str]
    diagnoses_decoding: Optional[str]
    graph_1: Optional[str]
    graph_2: Optional[str]
    graph_3: Optional[str]
    graph_4: Optional[str]

    class Config:
        from_attributes = True


@router.get("/search", response_model=List[CriteriaSearchResult])
async def search_criteria(
    query: str = Query(..., description="Текст для поиска критериев"),
    article: Optional[int] = Query(None, description="Фильтр по статье"),
    top_k: int = Query(5, ge=1, le=20, description="Количество результатов"),
    db: AsyncSession = Depends(get_db)
):
    """
    Векторный поиск критериев по тексту запроса

    Использует RAG для поиска наиболее релевантных критериев
    из Приложения 2 на основе семантической близости.
    """
    try:
        results = await rag_service.find_similar_criteria(
            db=db,
            query_text=query,
            top_k=top_k,
            article=article
        )

        return [CriteriaSearchResult(**item) for item in results]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка при поиске критериев: {str(e)}")


@router.get("/article/{article}", response_model=List[dict])
async def get_criteria_by_article(
    article: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить все критерии для конкретной статьи
    """
    try:
        query = select(PointCriterion).where(PointCriterion.article == article)
        result = await db.execute(query)
        criteria = result.scalars().all()

        return [
            {
                "id": c.id,
                "article": c.article,
                "subpoint": c.subpoint,
                "description": c.description
            }
            for c in criteria
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.get("/article/{article}/subpoint/{subpoint}")
async def get_criteria_by_article_subpoint(
    article: int,
    subpoint: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить критерии для конкретной статьи и подпункта
    """
    try:
        query = select(PointCriterion).where(
            PointCriterion.article == article,
            PointCriterion.subpoint == subpoint
        )
        result = await db.execute(query)
        criteria = result.scalars().all()

        if not criteria:
            raise HTTPException(
                status_code=404,
                detail=f"Критерии не найдены для статьи {article}, подпункт {subpoint}"
            )

        return [
            {
                "id": c.id,
                "article": c.article,
                "subpoint": c.subpoint,
                "description": c.description
            }
            for c in criteria
        ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.get("/categories/article/{article}/subpoint/{subpoint}", response_model=PointDiagnosisResponse)
async def get_category_for_subpoint(
    article: int,
    subpoint: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить категории годности для статьи и подпункта
    """
    try:
        query = select(PointDiagnosis).where(
            PointDiagnosis.article == article,
            PointDiagnosis.subpoint == subpoint
        )
        result = await db.execute(query)
        point_diagnosis = result.scalar_one_or_none()

        if not point_diagnosis:
            raise HTTPException(
                status_code=404,
                detail=f"Категории не найдены для статьи {article}, подпункт {subpoint}"
            )

        return point_diagnosis

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.get("/stats")
async def get_criteria_stats(db: AsyncSession = Depends(get_db)):
    """
    Статистика по критериям
    """
    try:
        # Количество критериев
        query_criteria = select(PointCriterion)
        result = await db.execute(query_criteria)
        total_criteria = len(result.scalars().all())

        # Количество статей (уникальных)
        query_articles = select(PointCriterion.article).distinct()
        result = await db.execute(query_articles)
        unique_articles = len(result.scalars().all())

        return {
            "total_criteria": total_criteria,
            "unique_articles": unique_articles,
            "average_criteria_per_article": round(total_criteria / unique_articles, 2) if unique_articles > 0 else 0
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")
