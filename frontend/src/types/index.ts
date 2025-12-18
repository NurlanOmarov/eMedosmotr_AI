// ============================================
// EMEDOSMOTR AI — TYPE DEFINITIONS
// ============================================

export interface Conscript {
  id: string
  iin: string
  fullName: string
  birthDate: string
  draftNumber: string
  status: 'pending' | 'in_progress' | 'completed'
  photo?: string
  medicalCommissionDate?: string
  draftDistrict?: string
  categoryGraphId?: number // ID графа (1-19) из справочника - DEPRECATED
  graph?: number // Номер графа (1-4) - ИСПОЛЬЗУЙТЕ ЭТО ПОЛЕ
  examinations?: DoctorExamination[] // Заключения специалистов
}

export interface DoctorExamination {
  id: string
  specialty: string
  specialtyRu?: string
  doctorName: string
  conclusion: string
  icd10Codes: string[]
  doctorCategory: FitnessCategory
  isSaved: boolean
  savedAt?: string
  confidence?: number
  // Детальные поля осмотра
  complaints?: string
  anamnesis?: string
  objectiveData?: string
  specialResearchResults?: string
  // Специфичные поля для офтальмолога
  od_vision_without_correction?: string | null
  os_vision_without_correction?: string | null
  // Специфичное поле для стоматолога
  dentist_json?: Record<string, string> | null
}

// Категории годности по Приказу 722: А, Б, В, Г, Д, Е, НГ, ИНД, В-ИНД
export type FitnessCategory = 'А' | 'A' | 'Б' | 'Б-3' | 'Б-4' | 'В' | 'Г' | 'Д' | 'Е' | 'НГ' | 'ИНД' | 'В-ИНД'

export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH'

export type AnalysisStatus = 'MATCH' | 'MISMATCH' | 'PARTIAL_MISMATCH' | 'REVIEW_REQUIRED'

export interface AIAnalysis {
  specialty: string
  doctorCategory: FitnessCategory | null
  aiRecommendedCategory: FitnessCategory | null
  status: AnalysisStatus
  riskLevel: RiskLevel | null
  article: number // ID строки в базе данных (не используется в UI)
  point: number // Номер пункта из приказа (например, 34)
  subpoint: string // Вариант пункта (например, "4")
  confidence: number
  reasoning: string
  subpointDetails?: {
    criteriaText: string
    matchedCriteria: string
    parametersMatched: Record<string, any>
  }
  categoryDetails?: {
    alternativeCategories: FitnessCategory[]
  }
}

export interface ConscriptAnalysis {
  conscriptId: string
  examinations: DoctorExamination[]
  aiAnalyses: AIAnalysis[]
  finalCategory?: FitnessCategory
  overallRiskLevel: RiskLevel | null
  completedAt?: string
  timestamp?: string
  isSaved?: boolean // Флаг, что это сохраненные результаты из БД
}

export interface Criterion {
  id: number
  article: number
  subpoint: string
  criteriaText: string
  detailsText?: string
  similarity?: number
}

export interface ICD10Code {
  code: string
  name: string
  description?: string
}

export interface APIError {
  detail: string
  status: number
}

export interface ExaminationCompleteness {
  is_complete: boolean
  completed_specialists: string[]
  missing_specialists: string[]
  total_required: number
  total_completed: number
  missing_diagnoses: string[]
  missing_categories: string[]
  can_run_ai_analysis: boolean
}

export interface ValidationError {
  type: 'MISSING_SPECIALISTS' | 'MISSING_DIAGNOSES' | 'MISSING_CATEGORIES'
  message: string
  missing: string[]
}

export interface AIAnalysisValidation {
  validation: {
    can_proceed: boolean
    is_ready_for_ai: boolean
    errors: ValidationError[]
  }
  completeness: ExaminationCompleteness
}

// ============================================
// НОВЫЕ ТИПЫ ДЛЯ /api/v1/validation ЭНДПОИНТОВ
// ============================================

export type ContradictionType =
  | 'TYPE_A_HEALTHY_VS_DISEASE'
  | 'TYPE_B_DISEASE_VS_HEALTHY'
  | 'TYPE_C_DISEASE_A_VS_DISEASE_B'
  | 'TYPE_D_CATEGORY_MISMATCH'
  | 'TYPE_E_LOGICAL_ERROR'
  | 'TYPE_F_OBVIOUS_CATEGORY_MISMATCH'

export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

export type OverallStatus = 'VALID' | 'WARNING' | 'INVALID'

export type CategoryMatchStatus = 'MATCH' | 'MISMATCH' | 'REVIEW_REQUIRED'

export interface RAGMatch {
  article: number
  subpoint: string
  description: string
  similarity: number
  categories: Record<number, string | null>
}

export interface ContradictionDetail {
  type: ContradictionType
  severity: Severity
  description: string
  source_field?: string
  target_field?: string
  source_value?: string
  target_value?: string
  rag_matches: RAGMatch[]
  recommendation?: string
}

export interface ValidationStageResult {
  stage_name: string
  stage_number: number
  passed: boolean
  status: string
  details: Record<string, any>
  duration_seconds?: number
  error_message?: string
}

export interface CheckDoctorConclusionRequest {
  diagnosis_text: string
  doctor_category: string
  specialty: string
  anamnesis?: string
  complaints?: string
  objective_data?: string
  special_research_results?: string
  conclusion_text?: string
  doctor_notes?: string
  icd10_codes?: string[]
  article_hint?: number
  subpoint_hint?: string
  graph?: number
  conscript_draft_id?: string
  examination_id?: string
  save_to_db?: boolean
}

export interface CheckDoctorConclusionResponse {
  overall_status: OverallStatus
  risk_level: Severity
  stage_0_contradictions: ContradictionDetail[]
  stage_1_clinical: ValidationStageResult
  stage_2_administrative: ValidationStageResult
  ai_recommended_article?: number
  ai_recommended_subpoint?: string
  ai_recommended_category?: string
  ai_confidence: number
  ai_reasoning: string
  doctor_article?: number
  doctor_subpoint?: string
  doctor_category: string
  category_match_status: CategoryMatchStatus
  should_review: boolean
  review_reasons: string[]
  recommendations: string[]
  is_healthy: boolean
  metadata: Record<string, any>
}
