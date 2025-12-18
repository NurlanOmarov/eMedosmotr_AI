import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import ConscriptTable from './components/ConscriptTable'
import AIAnalysisPanel from './components/AIAnalysisPanel'
import Header from './components/Header'
import Sidebar from './components/Sidebar'
import DetailedAnalysisModal from './components/DetailedAnalysisModal'
import ConscriptDetailCard from './components/ConscriptDetailCard'
import AIAnalysisModal from './components/AIAnalysisModal'
import ChairmanDashboard from './components/ChairmanDashboard'
import SpecialistsList from './components/SpecialistsList'
import { useData } from './contexts/DataContext'
import { apiClient } from './services/api'
import type {
  Conscript,
  ConscriptAnalysis,
  AIAnalysis,
  RiskLevel,
  CheckDoctorConclusionResponse,
  Severity
} from './types'
import './App.css'

// Типы ролей пользователя
export type UserRole = 'doctor' | 'chairman'

export interface User {
  id: string
  name: string
  role: UserRole
  specialty?: string
  photo?: string
}

// Тестовые пользователи для демо (без авторизации)
export const DEMO_USERS: User[] = [
  { id: '1', name: 'Смирнова А.В.', role: 'doctor', specialty: 'Терапевт', photo: '/smirnova-doctor.png' },
  { id: '2', name: 'Казаков И.П.', role: 'doctor', specialty: 'Хирург', photo: '/kazakov-doctor.png' },
  { id: '3', name: 'Назарбаева К.М.', role: 'doctor', specialty: 'Офтальмолог', photo: '/nazarbayeva-doctor.png' },
  { id: '4', name: 'Абишева Р.К.', role: 'doctor', specialty: 'Невролог', photo: '/abisheva-doctor.png' },
  { id: '5', name: 'Жумагулов Б.С.', role: 'doctor', specialty: 'Отоларинголог', photo: '/zhumagulov-doctor.png' },
  { id: '6', name: 'Сарсенова М.А.', role: 'doctor', specialty: 'Дерматолог', photo: '/sarsenova-doctor.png' },
  { id: '7', name: 'Тулегенова Г.К.', role: 'doctor', specialty: 'Психиатр', photo: '/tulegenova-doctor.png' },
  { id: '8', name: 'Ахметова С.Н.', role: 'doctor', specialty: 'Стоматолог', photo: '/akhmetova-doctor.png' },
  { id: '9', name: 'Досымбеков К.А.', role: 'doctor', specialty: 'Фтизиатр', photo: '/dosymbekov-doctor.png' },
  { id: '10', name: 'Председатель ВВК', role: 'chairman' },
]

function App() {
  // Используем Context вместо локального state для данных призывников
  const { conscripts, getConscript } = useData()

  const [selectedConscript, setSelectedConscript] = useState<Conscript | null>(null)
  const [analysis, setAnalysis] = useState<ConscriptAnalysis | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [systemStatus, setSystemStatus] = useState<'healthy' | 'degraded' | 'down'>('healthy')

  // Модальное окно подробного анализа
  const [isDetailedModalOpen, setIsDetailedModalOpen] = useState(false)
  const [selectedAnalysis, setSelectedAnalysis] = useState<AIAnalysis | null>(null)

  // Модальное окно AI анализа
  const [isAIAnalysisModalOpen, setIsAIAnalysisModalOpen] = useState(false)

  // Детальная карточка призывника
  const [isDetailCardOpen, setIsDetailCardOpen] = useState(false)

  // Текущий пользователь (роль)
  const [currentUser, setCurrentUser] = useState<User>(DEMO_USERS[9]) // По умолчанию - председатель

  // Активный раздел для навигации
  const [activeSection, setActiveSection] = useState<string>('dashboard')

  // Check system health on mount
  useEffect(() => {
    checkSystemHealth()
  }, [])

  const checkSystemHealth = async () => {
    try {
      const health = await apiClient.healthCheck()
      if (health.status === 'ok') {
        setSystemStatus('healthy')
      } else {
        setSystemStatus('degraded')
      }
    } catch (error) {
      console.error('System health check failed:', error)
      // Для MVP продолжаем работать с mock данными
      setSystemStatus('degraded')
    }
  }

  const handleConscriptSelect = (conscript: Conscript) => {
    setSelectedConscript(conscript)
    // Reset analysis when selecting new conscript
    setAnalysis(null)
    // Open detail card
    setIsDetailCardOpen(true)
  }

  const handleRunAnalysis = async (graphId?: number) => {
    if (!selectedConscript) return

    // Используем переданный граф или граф призывника
    // ИСПРАВЛЕНО: используем graph (1-4), а не categoryGraphId (1-19)
    const currentGraphId = graphId || selectedConscript.graph || 1

    setIsLoading(true)
    try {
      // ВАЖНО: Проверяем полноту освидетельствования перед запуском ИИ анализа
      // В реальном приложении здесь будет вызов API
      // const validation = await apiClient.validateForAIAnalysis(selectedConscript.draftId)

      // Для MVP используем проверку мок-данных
      // Проверяем, что все обязательные специалисты провели осмотр и сохранили заключения
      const requiredSpecialists = ['Терапевт', 'Хирург', 'Офтальмолог', 'Невролог', 'Отоларинголог', 'Дерматолог', 'Психиатр', 'Стоматолог', 'Фтизиатр']

      // Получаем список завершенных осмотров (isSaved = true)
      const completedExaminations = selectedConscript.examinations?.filter(exam => exam.isSaved) || []
      const completedSpecialists = completedExaminations.map(exam => exam.specialtyRu || exam.specialty)

      // Определяем недостающих специалистов
      const missingSpecialists = requiredSpecialists.filter(spec => !completedSpecialists.includes(spec))

      if (missingSpecialists.length > 0) {
        // Освидетельствование не завершено - блокируем запуск ИИ анализа
        alert(`⚠️ Невозможно запустить ИИ анализ!\n\nНе все специалисты провели освидетельствование.\n\nОтсутствуют завершенные заключения от:\n${missingSpecialists.map(s => `• ${s}`).join('\n')}\n\nДля запуска ИИ анализа необходимо, чтобы все ${requiredSpecialists.length} обязательных специалистов завершили осмотр призывника (заполнили все поля и нажали "Сохранить").`)
        setIsLoading(false)
        return
      }

      // Проверяем наличие диагноза и категории у каждого специалиста
      const missingDiagnoses: string[] = []
      const missingCategories: string[] = []

      completedExaminations.forEach(exam => {
        const specialtyName = exam.specialtyRu || exam.specialty
        // Если категория "А" (годен), код МКБ-10 не требуется
        // В остальных случаях требуется код МКБ-10 и текст заключения
        if (exam.doctorCategory !== 'А' && exam.doctorCategory !== 'A') {
          // Для категорий Б, В, Г, Д требуется код МКБ-10
          if (!exam.icd10Codes || exam.icd10Codes.length === 0 || !exam.conclusion) {
            missingDiagnoses.push(specialtyName)
          }
        } else {
          // Для категории А требуется хотя бы текст заключения
          if (!exam.conclusion) {
            missingDiagnoses.push(specialtyName)
          }
        }

        if (!exam.doctorCategory) {
          missingCategories.push(specialtyName)
        }
      })

      if (missingDiagnoses.length > 0 || missingCategories.length > 0) {
        let errorMessage = '⚠️ Невозможно запустить ИИ анализ!\n\n'

        if (missingDiagnoses.length > 0) {
          errorMessage += `Не указаны диагнозы у специалистов:\n${missingDiagnoses.map(s => `• ${s}`).join('\n')}\n\n`
        }

        if (missingCategories.length > 0) {
          errorMessage += `Не указаны категории годности у специалистов:\n${missingCategories.map(s => `• ${s}`).join('\n')}\n\n`
        }

        errorMessage += 'Для запуска ИИ анализа:\n• Специалисты с категорией А (годен) должны указать заключение\n• Специалисты с категориями Б, В, Г, Д должны указать код МКБ-10 и заключение\n• Все специалисты должны указать категорию годности'

        alert(errorMessage)
        setIsLoading(false)
        return
      }

      // Если проверка пройдена, запускаем анализ
      console.log('Запуск AI анализа для всех осмотров...')

      // Запускаем AI анализ для каждого завершенного осмотра
      // ИСПОЛЬЗУЕМ НОВЫЙ API /api/v1/validation/check-doctor-conclusion
      const aiAnalysesPromises = completedExaminations.map(async (examination) => {
        try {
          console.log(`Анализ осмотра: ${examination.specialty}`)

          // Вызываем НОВЫЙ API валидации (трёхэтапная проверка по Приказу 722)
          const validationResult: CheckDoctorConclusionResponse = await apiClient.checkDoctorConclusion({
            diagnosis_text: examination.conclusion,
            doctor_category: examination.doctorCategory,
            specialty: examination.specialty,
            anamnesis: examination.anamnesis || undefined,
            complaints: examination.complaints || undefined,
            objective_data: examination.objectiveData || undefined,
            special_research_results: examination.specialResearchResults || undefined,
            icd10_codes: examination.icd10Codes,
            graph: currentGraphId,
            conscript_draft_id: selectedConscript.id,
            examination_id: examination.id,
            save_to_db: true
          })

          console.log(`✓ Валидация ${examination.specialty} завершена:`, validationResult)

          // Преобразуем результат валидации в формат AIAnalysis для совместимости с UI
          const mapSeverityToRiskLevel = (severity: Severity): RiskLevel => {
            switch (severity) {
              case 'CRITICAL':
              case 'HIGH':
                return 'HIGH'
              case 'MEDIUM':
                return 'MEDIUM'
              default:
                return 'LOW'
            }
          }

          console.log(`[${examination.specialty}] risk_level from backend:`, validationResult.risk_level)
          console.log(`[${examination.specialty}] category_match_status:`, validationResult.category_match_status)
          console.log(`[${examination.specialty}] ai_category:`, validationResult.ai_recommended_category)
          console.log(`[${examination.specialty}] doctor_category:`, examination.doctorCategory)
          console.log(`[${examination.specialty}] overall_status:`, validationResult.overall_status)
          console.log(`[${examination.specialty}] stage_0_contradictions:`, JSON.stringify(validationResult.stage_0_contradictions, null, 2))

          const aiAnalysis: AIAnalysis = {
            specialty: examination.specialty,
            doctorCategory: examination.doctorCategory,
            aiRecommendedCategory: validationResult.ai_recommended_category as any || null,
            status: validationResult.category_match_status,
            riskLevel: mapSeverityToRiskLevel(validationResult.risk_level),
            article: validationResult.ai_recommended_article || 0,
            point: validationResult.ai_recommended_article || 0,
            subpoint: validationResult.ai_recommended_subpoint || '',
            confidence: validationResult.ai_confidence,
            reasoning: validationResult.ai_reasoning || validationResult.review_reasons.join('; '),
            subpointDetails: validationResult.stage_1_clinical?.details ? {
              criteriaText: validationResult.stage_1_clinical.details.criteria_text || '',
              matchedCriteria: validationResult.stage_1_clinical.details.matched_criteria || '',
              parametersMatched: validationResult.stage_1_clinical.details.parameters_matched || {}
            } : undefined,
            categoryDetails: {
              alternativeCategories: []
            }
          }

          return aiAnalysis
        } catch (error) {
          console.error(`✗ Ошибка анализа ${examination.specialty}:`, error)
          // В случае ошибки возвращаем null, но не прерываем весь процесс
          return null
        }
      })

      // Ждем завершения всех анализов
      const aiAnalysesResults = await Promise.all(aiAnalysesPromises)

      // Фильтруем успешные результаты
      const aiAnalyses = aiAnalysesResults.filter(result => result !== null) as AIAnalysis[]

      if (aiAnalyses.length === 0) {
        alert('❌ Не удалось выполнить AI анализ. Проверьте подключение к серверу.')
        setIsLoading(false)
        return
      }

      // Определяем общий уровень риска
      // ВАЖНО: Если нет несоответствий (все MATCH), то риск LOW независимо от других факторов
      const mismatchCount = aiAnalyses.filter(
        a => a.status === 'MISMATCH' || a.status === 'PARTIAL_MISMATCH'
      ).length

      let overallRiskLevel: RiskLevel

      if (mismatchCount === 0) {
        // Нет несоответствий - всегда LOW риск
        overallRiskLevel = 'LOW'
      } else {
        // Есть несоответствия - определяем по уровням риска
        const riskLevels = aiAnalyses.map(a => a.riskLevel)
        overallRiskLevel =
          riskLevels.includes('HIGH') ? 'HIGH' :
          riskLevels.includes('MEDIUM') ? 'MEDIUM' : 'LOW'
      }

      const analysisResult: ConscriptAnalysis = {
        conscriptId: selectedConscript.id,
        examinations: completedExaminations,
        aiAnalyses: aiAnalyses,
        overallRiskLevel: overallRiskLevel,
        completedAt: new Date().toISOString(),
      }

      setAnalysis(analysisResult)
      const graphName = getGraphName(currentGraphId)
      console.log(`✅ AI анализ завершен успешно! График: ${graphName}, Проанализировано осмотров: ${aiAnalyses.length}/${completedExaminations.length}`)
    } catch (error) {
      console.error('Analysis failed:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getGraphName = (graphId: number): string => {
    const graphNames: Record<number, string> = {
      1: 'Графа I (приписка к призывным участкам)',
      2: 'Графа I (призыв на срочную воинскую службу)',
      3: 'Графа I (отбор для подготовки по военно-техническим специальностям)',
      4: 'Графа I (поступление в военные учебные заведения)',
      5: 'Графа II (поступление в ВУЗ)',
      6: 'Графа II (военные кафедры)',
      7: 'Графа II (служба по контракту)',
      8: 'Графа II (подготовка на возмездной основе)',
      9: 'Графа II (срочная воинская служба)',
      10: 'Графа II (курсанты до заключения контракта)',
      11: 'Графа II (рядовые и сержанты запаса)',
      12: 'Графа III (офицеры запаса)',
      13: 'Графа III (служба по контракту)',
      14: 'Графа III (офицеры по призыву)',
      15: 'Графа III (послевузовское образование)',
      16: 'Графа III (курсанты после заключения контракта)',
      17: 'Графа III (офицеры запаса на воинских сборах)',
      18: 'Графа IV (ДШВ, ВМС, ЧСН)',
      19: 'Графа IV (подводное вождение танков)',
    }
    return graphNames[graphId] || 'Графа I (призыв на срочную воинскую службу)'
  }

  const handleOpenDetailedAnalysis = (aiAnalysis: AIAnalysis) => {
    setSelectedAnalysis(aiAnalysis)
    setIsDetailedModalOpen(true)
  }

  const handleCloseDetailedModal = () => {
    setIsDetailedModalOpen(false)
    setSelectedAnalysis(null)
  }

  const handleUserChange = (user: User) => {
    setCurrentUser(user)
    // Переключаем на дэшборд для председателя, на призывников для врачей
    if (user.role === 'chairman') {
      setActiveSection('dashboard')
    } else {
      setActiveSection('conscripts')
    }
  }

  const handleSectionChange = (sectionId: string) => {
    setActiveSection(sectionId)
  }

  const handleCloseDetailCard = () => {
    setIsDetailCardOpen(false)
  }

  const handleOpenAIAnalysisModal = async (graphId?: number) => {
    // Сначала проверяем наличие сохраненных результатов в БД
    if (selectedConscript) {
      try {
        console.log('🔍 Проверка наличия сохраненных результатов для призывника:', selectedConscript.fullName, selectedConscript.id)

        // Показываем модал с индикатором загрузки
        setIsLoading(true)
        setIsAIAnalysisModalOpen(true)

        const savedResults = await apiClient.getSavedAnalysisResults(selectedConscript.id)
        console.log('📦 Ответ от API getSavedAnalysisResults:', savedResults)

        if (savedResults && savedResults.total_count > 0) {
          console.log(`✅ Найдено ${savedResults.total_count} сохраненных результатов для призывника ${selectedConscript.fullName}`)
          console.log('📋 Результаты:', savedResults.results)
          // Есть сохраненные результаты - показываем их без нового анализа
          // Преобразуем сохраненные результаты в формат ConscriptAnalysis
          const aiAnalyses: AIAnalysis[] = savedResults.results.map(result => ({
            specialty: result.specialty,
            doctorCategory: result.doctor_category as FitnessCategory | null,
            aiRecommendedCategory: result.ai_recommended_category as FitnessCategory | null,
            status: result.status,
            riskLevel: result.risk_level as RiskLevel,
            article: result.article || 0,
            point: result.article || 0,
            subpoint: result.subpoint || '',
            confidence: result.confidence || 0,
            reasoning: result.reasoning,
            categoryDetails: {
              alternativeCategories: []
            }
          }))

          // Вычисляем общий уровень риска
          const hasHighRisk = aiAnalyses.some(a => a.riskLevel === 'HIGH')
          const hasMediumRisk = aiAnalyses.some(a => a.riskLevel === 'MEDIUM')
          const overallRiskLevel: RiskLevel = hasHighRisk ? 'HIGH' : hasMediumRisk ? 'MEDIUM' : 'LOW'

          setAnalysis({
            conscriptId: selectedConscript.id,
            examinations: selectedConscript.examinations || [],
            aiAnalyses: aiAnalyses,
            overallRiskLevel: overallRiskLevel,
            timestamp: savedResults.results[0]?.created_at || new Date().toISOString(),
            isSaved: true // Флаг, что это сохраненные результаты
          })

          setIsLoading(false)

          // Показываем пользователю уведомление о найденных результатах
          console.log(`ℹ️ Отображаются сохраненные результаты (${savedResults.total_count} анализов). Используйте кнопку "Повторить анализ" для нового анализа.`)

          return // Не запускаем новый анализ
        } else {
          console.log('ℹ️ Сохраненных результатов не найдено, запускаем новый анализ')
          // Нет сохраненных результатов - запускаем новый анализ
          await handleRunAnalysis(graphId)
        }
      } catch (error) {
        console.error('❌ Ошибка при проверке сохраненных результатов:', error)
        // В случае ошибки запускаем новый анализ
        await handleRunAnalysis(graphId)
      }
    }
  }

  const handleCloseAIAnalysisModal = () => {
    setIsAIAnalysisModalOpen(false)
  }

  const handleRerunAnalysis = async (graphId?: number) => {
    console.log('🔄 Запуск повторного анализа...')
    setIsLoading(true)
    await handleRunAnalysis(graphId)
  }

  return (
    <div className="app">
      <Header
        conscript={selectedConscript}
        systemStatus={systemStatus}
        currentUser={currentUser}
        availableUsers={DEMO_USERS}
        onUserChange={handleUserChange}
      />

      <div className="app-layout">
        {/* Sidebar навигация (только для председателя) */}
        {currentUser.role === 'chairman' && (
          <Sidebar
            currentUser={currentUser}
            activeSection={activeSection}
            onSectionChange={handleSectionChange}
          />
        )}

        <main className={`app-main ${currentUser.role === 'doctor' ? 'app-main-full' : ''}`}>
          {/* Динамическое отображение контента в зависимости от активного раздела */}
          {activeSection === 'dashboard' && currentUser.role === 'chairman' && (
            <ChairmanDashboard />
          )}

          {activeSection === 'conscripts' && (
            <ConscriptTable
              conscripts={conscripts}
              selectedId={selectedConscript?.id}
              onSelect={handleConscriptSelect}
              isDetailCardOpen={isDetailCardOpen}
            />
          )}

          {activeSection === 'specialists' && currentUser.role === 'chairman' && (
            <SpecialistsList />
          )}

          {activeSection === 'dispensary' && (
            <div className="coming-soon">
              <h2>📋 Диспансер</h2>
              <p>Функционал в разработке</p>
            </div>
          )}

          {activeSection === 'hospital' && (
            <div className="coming-soon">
              <h2>🏥 Госпитализация</h2>
              <p>Функционал в разработке</p>
            </div>
          )}

          {activeSection === 'vaccination' && (
            <div className="coming-soon">
              <h2>💉 Вакцинация</h2>
              <p>Функционал в разработке</p>
            </div>
          )}

          {activeSection === 'reports' && (
            <div className="coming-soon">
              <h2>📈 Отчёты</h2>
              <p>Функционал в разработке</p>
            </div>
          )}

          {activeSection === 'history' && (
            <div className="coming-soon">
              <h2>📜 История</h2>
              <p>Функционал в разработке</p>
            </div>
          )}

          {activeSection === 'analytics' && (
            <div className="coming-soon">
              <h2>🤖 Аналитика AI</h2>
              <p>Функционал в разработке</p>
            </div>
          )}
        </main>
      </div>

      {/* Детальная карточка призывника */}
      <AnimatePresence>
        {isDetailCardOpen && selectedConscript && (
          <ConscriptDetailCard
            conscript={selectedConscript}
            currentUser={currentUser}
            onClose={handleCloseDetailCard}
            onOpenAIAnalysis={handleOpenAIAnalysisModal}
          />
        )}
      </AnimatePresence>

      {/* Модальное окно AI анализа */}
      <AIAnalysisModal
        isOpen={isAIAnalysisModalOpen}
        onClose={handleCloseAIAnalysisModal}
        analysis={analysis}
        isLoading={isLoading}
        onRerunAnalysis={handleRerunAnalysis}
      />

      {/* Модальное окно подробного анализа */}
      <DetailedAnalysisModal
        isOpen={isDetailedModalOpen}
        onClose={handleCloseDetailedModal}
        analysis={selectedAnalysis}
      />
    </div>
  )
}

export default App
