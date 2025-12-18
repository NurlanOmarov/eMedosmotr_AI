"""
API endpoints для работы со справочниками
МКБ-10, категории годности, графы, специальности
"""

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from typing import List, Optional
from pydantic import BaseModel
from pathlib import Path
import pandas as pd
import json

from app.utils.database import get_db
from app.models.reference import (
    ICD10Code, CategoryDictionary, CategoryGraph, ChapterSpecialtyMapping,
    PointDiagnosis, PointCriterion
)
from app.services.rag_service import rag_service

router = APIRouter()


# Pydantic модели
class ICD10Response(BaseModel):
    id: int
    code: str
    name_ru: str
    name_kz: Optional[str]
    level: Optional[int]
    parent_code: Optional[str]

    class Config:
        from_attributes = True


class CategoryResponse(BaseModel):
    id: int
    code_name: str
    display_code: str
    name_ru: str
    description_ru: Optional[str]
    hierarchy_level: Optional[int]

    class Config:
        from_attributes = True


class GraphResponse(BaseModel):
    id: int
    graph: int
    name_ru: str
    description_ru: Optional[str]

    class Config:
        from_attributes = True


# МКБ-10 endpoints
@router.get("/icd10/search", response_model=List[dict])
async def search_icd10(
    query: str = Query(..., description="Текст для поиска"),
    top_k: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    """
    Векторный поиск кодов МКБ-10 по названию болезни
    """
    try:
        results = await rag_service.find_similar_icd10(
            db=db,
            query_text=query,
            top_k=top_k
        )
        return results

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка поиска: {str(e)}")


@router.get("/icd10/code/{code}", response_model=ICD10Response)
async def get_icd10_by_code(
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить информацию о коде МКБ-10
    """
    try:
        query = select(ICD10Code).where(ICD10Code.code == code)
        result = await db.execute(query)
        icd10 = result.scalar_one_or_none()

        if not icd10:
            raise HTTPException(
                status_code=404,
                detail=f"Код МКБ-10 '{code}' не найден"
            )

        return icd10

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.get("/icd10/list", response_model=List[ICD10Response])
async def list_icd10(
    level: Optional[int] = Query(None, description="Уровень иерархии"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """
    Список кодов МКБ-10 с пагинацией
    """
    try:
        query = select(ICD10Code)

        if level is not None:
            query = query.where(ICD10Code.level == level)

        query = query.limit(limit).offset(offset)

        result = await db.execute(query)
        codes = result.scalars().all()

        return codes

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


# Категории годности
@router.get("/categories", response_model=List[CategoryResponse])
async def get_categories(db: AsyncSession = Depends(get_db)):
    """
    Получить все категории годности
    """
    try:
        query = select(CategoryDictionary).order_by(CategoryDictionary.hierarchy_level)
        result = await db.execute(query)
        categories = result.scalars().all()

        return categories

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.get("/categories/{code}", response_model=CategoryResponse)
async def get_category_by_code(
    code: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить категорию по коду (А, Б, В, Г, Д, НГ)
    """
    try:
        query = select(CategoryDictionary).where(CategoryDictionary.display_code == code)
        result = await db.execute(query)
        category = result.scalar_one_or_none()

        if not category:
            raise HTTPException(
                status_code=404,
                detail=f"Категория '{code}' не найдена"
            )

        return category

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


# Графы
@router.get("/graphs", response_model=List[GraphResponse])
async def get_graphs(db: AsyncSession = Depends(get_db)):
    """
    Получить все графы призывников
    """
    try:
        query = select(CategoryGraph).order_by(CategoryGraph.graph)
        result = await db.execute(query)
        graphs = result.scalars().all()

        return graphs

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.get("/graphs/{graph_number}", response_model=GraphResponse)
async def get_graph(
    graph_number: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить информацию о графе
    """
    try:
        query = select(CategoryGraph).where(CategoryGraph.graph == graph_number)
        result = await db.execute(query)
        graph = result.scalar_one_or_none()

        if not graph:
            raise HTTPException(
                status_code=404,
                detail=f"График {graph_number} не найден"
            )

        return graph

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


# Специальности
@router.get("/specialties")
async def get_specialties(db: AsyncSession = Depends(get_db)):
    """
    Получить список всех специальностей врачей
    """
    try:
        query = select(ChapterSpecialtyMapping.specialty).distinct()
        result = await db.execute(query)
        specialties = result.scalars().all()

        return {"specialties": specialties}

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


@router.get("/specialties/{specialty}")
async def get_chapters_for_specialty(
    specialty: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить главы приказа для специальности
    """
    try:
        query = select(ChapterSpecialtyMapping).where(
            ChapterSpecialtyMapping.specialty == specialty
        )
        result = await db.execute(query)
        mappings = result.scalars().all()

        if not mappings:
            raise HTTPException(
                status_code=404,
                detail=f"Специальность '{specialty}' не найдена"
            )

        return {
            "specialty": specialty,
            "chapters": [
                {
                    "chapter": m.chapter,
                    "specialty_ru": m.specialty_ru
                }
                for m in mappings
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


# Статистика
@router.get("/stats")
async def get_references_stats(db: AsyncSession = Depends(get_db)):
    """
    Статистика по справочникам
    """
    try:
        # Подсчет МКБ-10
        query_icd10 = select(func.count()).select_from(ICD10Code)
        result = await db.execute(query_icd10)
        icd10_count = result.scalar()

        # Подсчет категорий
        query_cat = select(func.count()).select_from(CategoryDictionary)
        result = await db.execute(query_cat)
        categories_count = result.scalar()

        # Подсчет граф
        query_graph = select(func.count()).select_from(CategoryGraph)
        result = await db.execute(query_graph)
        graphs_count = result.scalar()

        # Подсчет специальностей
        query_spec = select(func.count(ChapterSpecialtyMapping.specialty.distinct()))
        result = await db.execute(query_spec)
        specialties_count = result.scalar()

        return {
            "icd10_codes": icd10_count,
            "categories": categories_count,
            "graphs": graphs_count,
            "specialties": specialties_count
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка: {str(e)}")


# Загрузка справочников из CSV
@router.post("/load-references")
async def load_references(db: AsyncSession = Depends(get_db)):
    """
    Загрузить все справочники из CSV файлов
    МКБ-10, Приложение 1, Приложение 2, категории
    """
    try:
        # Пути к файлам в Docker контейнере
        references_dir = Path("/app/references")

        stats = {
            "icd10": 0,
            "points_diagnoses": 0,
            "point_criteria": 0,
            "categories": 0,
            "graphs": 0,
            "specialties": 0
        }

        # Очистка всех таблиц справочников
        await db.execute(delete(ChapterSpecialtyMapping))
        await db.execute(delete(PointCriterion))
        await db.execute(delete(PointDiagnosis))
        await db.execute(delete(CategoryDictionary))
        await db.execute(delete(CategoryGraph))
        await db.execute(delete(ICD10Code))
        await db.commit()

        # 1. Загрузка МКБ-10 из mkb10_full.csv
        icd10_path = references_dir / "mkb10_full.csv"
        if icd10_path.exists():
            df = pd.read_csv(icd10_path, sep=';', encoding='utf-8')

            records = []
            for _, row in df.iterrows():
                # Пропускаем заголовок если есть
                if row['MKB_CODE'] == 'MKB_CODE':
                    continue

                record = ICD10Code(
                    code=str(row['MKB_CODE']).strip(),
                    name_ru=str(row['MKB_NAME']).strip() if pd.notna(row['MKB_NAME']) else '',
                    name_kz=None,
                    level=1,
                    parent_code=None
                )
                records.append(record)

            # Bulk insert
            db.add_all(records)
            await db.commit()
            stats['icd10'] = len(records)

        # 2. Загрузка Приложения 1
        points_path = references_dir / "points_diagnoses_rows.csv"
        if points_path.exists():
            df = pd.read_csv(points_path, encoding='utf-8')

            records = []
            for _, row in df.iterrows():
                # Собираем полное название подпункта
                point_name = f"{row.get('diagnoses_decoding', '')} - {row.get('subpoint', '')}"

                record = PointDiagnosis(
                    article=int(row['point']),
                    point_name=point_name,
                    description=str(row.get('diagnoses_codes', '')),
                    icd10_chapter=str(row.get('chapter', ''))
                )
                records.append(record)

            db.add_all(records)
            await db.commit()
            stats['points_diagnoses'] = len(records)

        # 3. Загрузка Приложения 2
        criteria_path = references_dir / "point_criteria_full.csv"
        if criteria_path.exists():
            df = pd.read_csv(criteria_path, encoding='utf-8')

            records = []
            for _, row in df.iterrows():
                record = PointCriterion(
                    article=int(row['article']),
                    subpoint=str(row['subpoint']),
                    description=str(row['criteria_text']),
                    graph_1=None,  # Данные нет в CSV
                    graph_2=None,
                    graph_3=None,
                    graph_4=None
                )
                records.append(record)

            db.add_all(records)
            await db.commit()
            stats['point_criteria'] = len(records)

        # 4. Загрузка категорий
        categories_path = references_dir / "category_dictionary_rows.csv"
        if categories_path.exists():
            df = pd.read_csv(categories_path, encoding='utf-8')

            records = []
            for _, row in df.iterrows():
                record = CategoryDictionary(
                    code_name=str(row['code_name']),
                    display_code=str(row['display_code']),
                    name_ru=str(row['name_ru']),
                    description_ru=str(row.get('description_ru', '')) if pd.notna(row.get('description_ru')) else None,
                    hierarchy_level=int(row['hierarchy_level']) if pd.notna(row.get('hierarchy_level')) else None
                )
                records.append(record)

            db.add_all(records)
            await db.commit()
            stats['categories'] = len(records)

        # 5. Загрузка граф
        graphs = [
            CategoryGraph(
                graph=1,
                name_ru="гражданам при призыве на срочную воинскую службу",
                description_ru="Обычные призывники"
            ),
            CategoryGraph(
                graph=2,
                name_ru="курсантам военно-учебных заведений",
                description_ru="Будущие офицеры"
            ),
            CategoryGraph(
                graph=3,
                name_ru="военнослужащим, проходящим военную службу по контракту",
                description_ru="Действующие офицеры"
            ),
            CategoryGraph(
                graph=4,
                name_ru="при отборе в специальные подразделения",
                description_ru="Спецназ, ДШВ, ВМС"
            )
        ]
        db.add_all(graphs)
        await db.commit()
        stats['graphs'] = len(graphs)

        # 6. Загрузка маппинга специальностей
        mapping_path = references_dir / "chapter_to_specialty_mapping.json"
        if mapping_path.exists():
            with open(mapping_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            records = []
            for item in data:
                record = ChapterSpecialtyMapping(
                    chapter=str(item['chapter']),
                    specialty=str(item['specialty']),
                    specialty_ru=str(item.get('specialty_ru', ''))
                )
                records.append(record)

            db.add_all(records)
            await db.commit()
            stats['specialties'] = len(records)

        return {
            "status": "success",
            "message": "Справочники успешно загружены",
            "stats": stats
        }

    except Exception as e:
        await db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка загрузки справочников: {str(e)}"
        )
