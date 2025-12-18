"""
SQLAlchemy модели для eMedosmotr AI
Экспорт всех моделей для удобного импорта
"""

from app.models.conscript import (
    Conscript,
    AnthropometricData
)

from app.models.medical import (
    SpecialistExamination,
    ErdbDiagnosisHistory,
    BureauHospitalization,
    ErsbHistory,
    InstrumentalExamResult,
    ErdbSpecialStatus
)

from app.models.reference import (
    ICD10Code,
    PointDiagnosis,
    PointCriterion,
    CategoryDictionary,
    CategoryGraph,
    ChapterSpecialtyMapping
)

from app.models.ai import (
    AIAnalysisResult,
    AIFinalVerdict,
    AIAnalysisFeedback,
    KnowledgeBaseDocument,
    KnowledgeBaseChunk,
    SimilarCasesCache,
    AIPrompt
)

from app.models.system import (
    AIRequestLog,
    SystemSetting
)

__all__ = [
    # Conscripts
    "Conscript",
    "AnthropometricData",

    # Medical
    "SpecialistExamination",
    "ErdbDiagnosisHistory",
    "BureauHospitalization",
    "ErsbHistory",
    "InstrumentalExamResult",
    "ErdbSpecialStatus",

    # Reference
    "ICD10Code",
    "PointDiagnosis",
    "PointCriterion",
    "CategoryDictionary",
    "CategoryGraph",
    "ChapterSpecialtyMapping",

    # AI
    "AIAnalysisResult",
    "AIFinalVerdict",
    "AIAnalysisFeedback",
    "KnowledgeBaseDocument",
    "KnowledgeBaseChunk",
    "SimilarCasesCache",
    "AIPrompt",

    # System
    "AIRequestLog",
    "SystemSetting",
]
