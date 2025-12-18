// ============================================
// EMEDOSMOTR AI — API CLIENT
// ============================================

import axios, { AxiosInstance } from 'axios'
import type {
  AIAnalysis,
  Criterion,
  ICD10Code,
  CheckDoctorConclusionRequest,
  CheckDoctorConclusionResponse
} from '../types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class APIClient {
  private client: AxiosInstance

  constructor() {
    this.client = axios.create({
      baseURL: API_BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 30000,
    })

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`)
        return config
      },
      (error) => Promise.reject(error)
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        console.log(`[API] Response:`, response.status)
        return response
      },
      (error) => {
        console.error('[API] Error:', error.response?.data || error.message)
        return Promise.reject(error)
      }
    )
  }

  // ========== HEALTH CHECKS ==========

  async healthCheck(): Promise<{ status: string }> {
    const response = await this.client.get('/health')
    return response.data
  }

  async healthCheckDB(): Promise<{ status: string }> {
    const response = await this.client.get('/health/db')
    return response.data
  }

  async healthCheckAI(): Promise<{ status: string }> {
    const response = await this.client.get('/health/ai')
    return response.data
  }

  // ========== AI ANALYSIS ==========

  async analyzeExamination(data: {
    doctor_conclusion: string
    specialty: string
    doctor_category: string
    icd10_codes?: string[]
    graph?: number
    conscript_draft_id?: string
    examination_id?: string
    anamnesis?: string
    complaints?: string
    special_research_results?: string
    additional_context?: string
  }): Promise<AIAnalysis> {
    const response = await this.client.post('/api/v1/ai/analyze-examination', data)

    // Трансформируем snake_case ключи с бэкенда в camelCase для фронтенда
    const backendData = response.data
    return {
      specialty: backendData.specialty,
      doctorCategory: backendData.doctor_category,
      aiRecommendedCategory: backendData.ai_recommended_category,
      status: backendData.status,
      riskLevel: backendData.risk_level,
      article: backendData.article,
      point: backendData.article, // point и article - одно и то же
      subpoint: backendData.subpoint,
      confidence: backendData.confidence,
      reasoning: backendData.reasoning,
      subpointDetails: backendData.subpoint_details ? {
        criteriaText: backendData.subpoint_details.criteria_text || backendData.subpoint_details.reasoning || '',
        matchedCriteria: backendData.subpoint_details.matched_criteria || '',
        parametersMatched: backendData.subpoint_details.parameters_matched || {}
      } : undefined,
      categoryDetails: backendData.category_details ? {
        alternativeCategories: backendData.category_details.alternative_categories || []
      } : undefined
    }
  }

  async determineSubpoint(data: {
    doctor_conclusion: string
    specialty: string
    icd10_codes?: string[]
    additional_context?: string
  }): Promise<any> {
    const response = await this.client.post('/api/v1/ai/determine-subpoint', data)
    return response.data
  }

  async determineCategory(data: {
    article: number
    subpoint: string
    graph: number
  }): Promise<any> {
    const response = await this.client.post('/api/v1/ai/determine-category', data)
    return response.data
  }

  async testAnalysis(): Promise<AIAnalysis> {
    const response = await this.client.post('/api/v1/ai/test-analysis')
    return response.data
  }

  // ========== EXAMINATION COMPLETENESS ==========

  async checkExaminationCompleteness(conscriptDraftId: string): Promise<{
    is_complete: boolean
    completed_specialists: string[]
    missing_specialists: string[]
    total_required: number
    total_completed: number
    missing_diagnoses: string[]
    missing_categories: string[]
    can_run_ai_analysis: boolean
  }> {
    const response = await this.client.get(
      `/api/v1/ai/check-completeness/${conscriptDraftId}`
    )
    return response.data
  }

  async validateForAIAnalysis(conscriptDraftId: string): Promise<{
    validation: {
      can_proceed: boolean
      is_ready_for_ai: boolean
      errors: Array<{
        type: string
        message: string
        missing: string[]
      }>
    }
    completeness: {
      is_complete: boolean
      completed_specialists: string[]
      missing_specialists: string[]
      total_required: number
      total_completed: number
      missing_diagnoses: string[]
      missing_categories: string[]
      can_run_ai_analysis: boolean
    }
  }> {
    const response = await this.client.post(
      `/api/v1/ai/validate-for-ai-analysis/${conscriptDraftId}`
    )
    return response.data
  }

  async getRequiredSpecialists(): Promise<{
    required_specialists: string[]
    total_count: number
  }> {
    const response = await this.client.get('/api/v1/ai/required-specialists')
    return response.data
  }

  // ========== CRITERIA SEARCH ==========

  async searchCriteria(params: {
    query: string
    top_k?: number
  }): Promise<Criterion[]> {
    const response = await this.client.get('/api/v1/criteria/search', { params })
    return response.data
  }

  async getCriteriaByArticle(article: number): Promise<Criterion[]> {
    const response = await this.client.get(`/api/v1/criteria/article/${article}`)
    return response.data
  }

  async getCriteriaBySubpoint(
    article: number,
    subpoint: string
  ): Promise<Criterion> {
    const response = await this.client.get(
      `/api/v1/criteria/article/${article}/subpoint/${subpoint}`
    )
    return response.data
  }

  async getCriteriaStats(): Promise<any> {
    const response = await this.client.get('/api/v1/criteria/stats')
    return response.data
  }

  // ========== REFERENCES ==========

  async searchICD10(params: {
    query: string
    top_k?: number
  }): Promise<ICD10Code[]> {
    const response = await this.client.get('/api/v1/references/icd10/search', { params })
    return response.data
  }

  async getICD10ByCode(code: string): Promise<ICD10Code> {
    const response = await this.client.get(`/api/v1/references/icd10/code/${code}`)
    return response.data
  }

  async listICD10(params: {
    skip?: number
    limit?: number
  } = {}): Promise<ICD10Code[]> {
    const response = await this.client.get('/api/v1/references/icd10/list', { params })
    return response.data
  }

  async getCategories(): Promise<any[]> {
    const response = await this.client.get('/api/v1/references/categories')
    return response.data
  }

  async getCategoryByCode(code: string): Promise<any> {
    const response = await this.client.get(`/api/v1/references/categories/${code}`)
    return response.data
  }

  async getGraphs(): Promise<any[]> {
    const response = await this.client.get('/api/v1/references/graphs')
    return response.data
  }

  async getGraphByNumber(graphNumber: number): Promise<any> {
    const response = await this.client.get(`/api/v1/references/graphs/${graphNumber}`)
    return response.data
  }

  async getSpecialties(): Promise<string[]> {
    const response = await this.client.get('/api/v1/references/specialties')
    return response.data
  }

  async getChaptersBySpecialty(specialty: string): Promise<number[]> {
    const response = await this.client.get(
      `/api/v1/references/specialties/${specialty}`
    )
    return response.data
  }

  async getReferencesStats(): Promise<any> {
    const response = await this.client.get('/api/v1/references/stats')
    return response.data
  }

  // ========== CONSCRIPTS ==========

  async getAllConscripts(params: {
    skip?: number
    limit?: number
    status?: string
  } = {}): Promise<{
    total: number
    conscripts: any[]
  }> {
    const response = await this.client.get('/api/v1/conscripts', { params })
    return response.data
  }

  async getConscriptById(conscriptId: string): Promise<any> {
    const response = await this.client.get(`/api/v1/conscripts/${conscriptId}`)
    return response.data
  }

  async getSpecialistStats(specialty: string): Promise<{
    specialty: string
    total_examinations: number
    completed: number
    in_progress: number
    pending: number
  }> {
    const response = await this.client.get(`/api/v1/conscripts/specialists/${specialty}/stats`)
    return response.data
  }

  async getExaminationsBySpecialist(specialty: string): Promise<any[]> {
    const response = await this.client.get(`/api/v1/conscripts/specialists/${specialty}/examinations`)
    return response.data
  }

  // ========== VALIDATION (Приказ 722) ==========

  /**
   * Полная трёхэтапная валидация заключения врача
   * Этап 0: Проверка противоречий
   * Этап 1: Клиническая валидация (AI + RAG + Приложение 2)
   * Этап 2: Административная проверка (SQL + Приложение 1)
   */
  async checkDoctorConclusion(
    data: CheckDoctorConclusionRequest
  ): Promise<CheckDoctorConclusionResponse> {
    const response = await this.client.post('/api/v1/validation/check-doctor-conclusion', data)
    return response.data
  }

  /**
   * Проверка только противоречий (Этап 0)
   * Быстрая проверка без AI анализа
   */
  async checkContradictionsOnly(data: CheckDoctorConclusionRequest): Promise<{
    total_contradictions: number
    has_critical: boolean
    contradictions: Array<{
      type: string
      severity: string
      description: string
      source_field?: string
      target_field?: string
      recommendation?: string
    }>
  }> {
    const response = await this.client.post('/api/v1/validation/check-contradictions-only', data)
    return response.data
  }

  /**
   * Получить сохраненные результаты AI анализа для призывника
   */
  async getSavedAnalysisResults(conscriptDraftId: string, specialty?: string): Promise<{
    results: Array<{
      id: string
      conscript_draft_id: string
      examination_id?: string
      specialty: string
      doctor_category: string
      ai_recommended_category: string
      status: string
      risk_level: string
      article?: number
      subpoint?: string
      reasoning: string
      confidence?: number
      model_used?: string
      tokens_used?: number
      analysis_duration_seconds?: number
      created_at: string
    }>
    total_count: number
  }> {
    const params = specialty ? `?specialty=${encodeURIComponent(specialty)}` : ''
    const response = await this.client.get(`/api/v1/validation/saved-analysis/${conscriptDraftId}${params}`)
    return response.data
  }

  /**
   * RAG поиск заболеваний в тексте
   */
  async searchDiseasesInText(
    text: string,
    topK: number = 5,
    similarityThreshold: number = 0.65
  ): Promise<{
    query_text: string
    total_found: number
    threshold: number
    diseases: Array<{
      article: number
      subpoint: string
      description: string
      similarity: number
    }>
  }> {
    const response = await this.client.post('/api/v1/validation/search-diseases-in-text', null, {
      params: { text, top_k: topK, similarity_threshold: similarityThreshold }
    })
    return response.data
  }

  // ========== PDF EXPORT ==========

  /**
   * Экспорт отчета анализа ИИ в PDF
   */
  async exportAnalysisReport(data: {
    conscript_id: string
    analysis_data: any
  }): Promise<Blob> {
    const response = await this.client.post('/api/v1/ai/export-analysis-report', data, {
      responseType: 'blob'
    })
    return response.data
  }
}

export const apiClient = new APIClient()
export default apiClient
