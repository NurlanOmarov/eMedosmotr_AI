// ============================================
// EMEDOSMOTR AI — DATA CONTEXT
// Централизованное управление данными призывников и врачей
// ОБНОВЛЕНО: Использует реальные данные из API
// ============================================

import { createContext, useContext, useState, ReactNode, useEffect } from 'react'
import type { Conscript, DoctorExamination } from '../types'
import { apiClient } from '../services/api'

// Типы для Context
interface DataContextType {
  conscripts: Conscript[]
  loading: boolean
  error: string | null
  refreshConscripts: () => Promise<void>
  updateConscriptExamination: (
    conscriptId: string,
    specialty: string,
    examination: Partial<DoctorExamination>
  ) => void
  addConscriptExamination: (
    conscriptId: string,
    examination: DoctorExamination
  ) => void
  getConscript: (id: string) => Conscript | undefined
  getConscriptsBySpecialist: (specialty: string) => {
    conscriptId: string
    conscriptName: string
    conscriptIIN: string
    examinationDate: string
    diagnosis: string
    category: string
    status: 'completed' | 'in_progress' | 'pending'
  }[]
  getSpecialistStats: (specialty: string) => Promise<{
    totalExaminations: number
    completed: number
    inProgress: number
    pending: number
  }>
}

const DataContext = createContext<DataContextType | undefined>(undefined)

export function DataProvider({ children }: { children: ReactNode }) {
  const [conscripts, setConscripts] = useState<Conscript[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Функция для загрузки призывников из API
  const loadConscripts = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await apiClient.getAllConscripts({ limit: 100 })

      console.log('[DataContext] Получен ответ от API:', response)
      console.log('[DataContext] Количество призывников:', response.conscripts?.length || 0)

      // Преобразуем данные из бэкенда в формат фронтенда
      const transformedConscripts: Conscript[] = response.conscripts.map((c: any) => {
        console.log(`[DataContext] Обработка призывника ${c.full_name}:`, c)
        console.log(`[DataContext] Заключения (${c.examinations?.length || 0}):`, c.examinations)

        const examinations = c.examinations.map((exam: any) => {
          const transformed = {
            id: exam.id,
            specialty: exam.specialty,
            specialtyRu: exam.med_commission_member || exam.specialty,
            doctorName: exam.doctor_name || '',
            conclusion: exam.conclusion || exam.diagnosis_text,
            icd10Codes: exam.diagnosis_accompany_id ? [exam.diagnosis_accompany_id] : [],
            doctorCategory: exam.valid_category || exam.category,
            isSaved: exam.is_saved,
            savedAt: exam.examination_date || new Date().toISOString(),
            // Детальные поля осмотра
            complaints: exam.complain || '',
            anamnesis: exam.anamnesis || '',
            objectiveData: exam.objective_data || '',
            specialResearchResults: exam.special_research_results || '',
            // Специфичные поля для офтальмолога
            od_vision_without_correction: exam.od_vision_without_correction || null,
            os_vision_without_correction: exam.os_vision_without_correction || null,
            // Специфичное поле для стоматолога
            dentist_json: exam.dentist_json || null,
          }
          console.log(`[DataContext]   - ${exam.med_commission_member || exam.specialty}: категория=${exam.valid_category}, код МКБ=${exam.diagnosis_accompany_id}, врач=${exam.doctor_name}`, transformed)
          return transformed
        })

        return {
          id: c.id,
          iin: c.iin,
          fullName: c.full_name,
          birthDate: c.birth_date,
          draftNumber: c.draft_number || '',
          status: mapStatus(c.status, c.examination_complete),
          photo: `/avatars/${c.iin}.png`,
          medicalCommissionDate: c.medical_commission_date || c.draft_date || '',
          draftDistrict: c.address || '',
          categoryGraphId: c.category_graph_id || 1, // ID подгруппы (1-19) для UI селекта
          graph: c.graph || 1, // Номер основного графа (1-4) для API валидации
          examinations
        }
      })

      console.log('[DataContext] Трансформированные данные:', transformedConscripts)
      console.log('[DataContext] Всего призывников после трансформации:', transformedConscripts.length)

      setConscripts(transformedConscripts)
    } catch (err: any) {
      console.error('[DataContext] Ошибка загрузки данных:', err)
      setError(err.message || 'Ошибка загрузки данных')
    } finally {
      setLoading(false)
    }
  }

  // Маппинг статусов из бэкенда в статусы фронтенда
  const mapStatus = (backendStatus: string, isComplete: boolean): 'completed' | 'pending' | 'in_progress' => {
    // Если статус уже 'completed' в бэкенде, используем его
    if (backendStatus === 'completed') {
      return 'completed'
    }
    // Если освидетельствование завершено (все 9 врачей), но статус еще in_progress
    if (isComplete && backendStatus === 'in_progress') {
      return 'completed'
    }
    // Если статус in_progress
    if (backendStatus === 'in_progress') {
      return 'in_progress'
    }
    // Во всех остальных случаях - pending
    return 'pending'
  }

  // Загрузка данных при монтировании компонента
  useEffect(() => {
    loadConscripts()
  }, [])

  // Функция для обновления заключения врача
  const updateConscriptExamination = (
    conscriptId: string,
    specialty: string,
    examination: Partial<DoctorExamination>
  ) => {
    setConscripts((prev) =>
      prev.map((conscript) => {
        if (conscript.id !== conscriptId) return conscript

        const examinations = conscript.examinations || []
        const examIndex = examinations.findIndex((e) => e.specialty === specialty)

        if (examIndex >= 0) {
          // Обновляем существующее заключение
          const updatedExaminations = [...examinations]
          updatedExaminations[examIndex] = {
            ...updatedExaminations[examIndex],
            ...examination,
          }
          return { ...conscript, examinations: updatedExaminations }
        }

        return conscript
      })
    )
  }

  // Функция для добавления нового заключения
  const addConscriptExamination = (
    conscriptId: string,
    examination: DoctorExamination
  ) => {
    setConscripts((prev) =>
      prev.map((conscript) => {
        if (conscript.id !== conscriptId) return conscript

        const examinations = conscript.examinations || []
        return {
          ...conscript,
          examinations: [...examinations, examination],
        }
      })
    )
  }

  // Получить конкретного призывника по ID
  const getConscript = (id: string): Conscript | undefined => {
    return conscripts.find((c) => c.id === id)
  }

  // Получить список призывников для конкретного специалиста
  const getConscriptsBySpecialist = (specialty: string) => {
    const results: {
      conscriptId: string
      conscriptName: string
      conscriptIIN: string
      examinationDate: string
      diagnosis: string
      category: string
      status: 'completed' | 'in_progress' | 'pending'
    }[] = []

    conscripts.forEach((conscript) => {
      const examination = conscript.examinations?.find((exam) => exam.specialty === specialty)

      if (examination) {
        results.push({
          conscriptId: conscript.id,
          conscriptName: conscript.fullName,
          conscriptIIN: conscript.iin,
          examinationDate: examination.savedAt || '-',
          diagnosis: examination.conclusion || 'Ожидает осмотра',
          category: examination.doctorCategory || '-',
          status: examination.isSaved ? 'completed' : 'pending',
        })
      } else {
        // Если заключения нет, все равно показываем призывника
        results.push({
          conscriptId: conscript.id,
          conscriptName: conscript.fullName,
          conscriptIIN: conscript.iin,
          examinationDate: '-',
          diagnosis: 'Ожидает осмотра',
          category: '-',
          status: 'pending',
        })
      }
    })

    return results
  }

  // Получить статистику по специалисту
  const getSpecialistStats = async (specialty: string) => {
    try {
      const stats = await apiClient.getSpecialistStats(specialty)
      return {
        totalExaminations: stats.total_examinations,
        completed: stats.completed,
        inProgress: stats.in_progress,
        pending: stats.pending,
      }
    } catch (err) {
      console.error(`[DataContext] Ошибка получения статистики для ${specialty}:`, err)

      // Fallback: считаем статистику локально
      const examinationsList = getConscriptsBySpecialist(specialty)
      const completed = examinationsList.filter((exam) => exam.status === 'completed').length
      const pending = examinationsList.filter((exam) => exam.status === 'pending').length
      const inProgress = examinationsList.filter((exam) => exam.status === 'in_progress').length

      return {
        totalExaminations: examinationsList.length,
        completed,
        inProgress,
        pending,
      }
    }
  }

  const value: DataContextType = {
    conscripts,
    loading,
    error,
    refreshConscripts: loadConscripts,
    updateConscriptExamination,
    addConscriptExamination,
    getConscript,
    getConscriptsBySpecialist,
    getSpecialistStats,
  }

  return <DataContext.Provider value={value}>{children}</DataContext.Provider>
}

export function useData() {
  const context = useContext(DataContext)
  if (context === undefined) {
    throw new Error('useData must be used within a DataProvider')
  }
  return context
}
