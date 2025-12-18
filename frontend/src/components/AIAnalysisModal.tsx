import { motion, AnimatePresence } from 'framer-motion'
import { useEffect, useState } from 'react'
import type { ConscriptAnalysis } from '../types'
import { apiClient } from '../services/api'
import './AIAnalysisModal.css'

interface AIAnalysisModalProps {
  isOpen: boolean
  onClose: () => void
  analysis: ConscriptAnalysis | null
  isLoading?: boolean
  onRerunAnalysis?: () => void // Callback для повторного анализа
}

export default function AIAnalysisModal({
  isOpen,
  onClose,
  analysis,
  isLoading = false,
  onRerunAnalysis,
}: AIAnalysisModalProps) {
  const [isExporting, setIsExporting] = useState(false)
  const [savedResults, setSavedResults] = useState<any>(null)
  const [isLoadingSaved, setIsLoadingSaved] = useState(false)
  const [showSavedResults, setShowSavedResults] = useState(false)

  const riskColors = {
    LOW: 'var(--color-primary)',
    MEDIUM: 'var(--color-warning)',
    HIGH: 'var(--color-danger)',
  }

  const riskLabels = {
    LOW: 'НИЗКИЙ РИСК',
    MEDIUM: 'СРЕДНИЙ РИСК',
    HIGH: 'ВЫСОКИЙ РИСК',
  }

  const handleLoadSavedResults = async () => {
    if (!analysis?.conscriptId) return

    setIsLoadingSaved(true)
    try {
      const response = await apiClient.getSavedAnalysisResults(analysis.conscriptId)
      setSavedResults(response)
      setShowSavedResults(true)
      console.log('✅ Сохраненные результаты загружены:', response)
    } catch (error) {
      console.error('❌ Ошибка загрузки сохраненных результатов:', error)
      alert('Не удалось загрузить сохраненные результаты.')
    } finally {
      setIsLoadingSaved(false)
    }
  }

  const handleExportPDF = async () => {
    if (!analysis) return

    setIsExporting(true)
    try {
      const blob = await apiClient.exportAnalysisReport({
        conscript_id: analysis.conscriptId,
        analysis_data: analysis
      })

      // Создаем ссылку для скачивания
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `AI_Analysis_Report_${analysis.conscriptId.substring(0, 8)}_${new Date().toISOString().split('T')[0]}.pdf`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

      console.log('✅ PDF отчет успешно экспортирован')
    } catch (error) {
      console.error('❌ Ошибка экспорта PDF:', error)
      alert('Не удалось экспортировать отчет. Попробуйте еще раз.')
    } finally {
      setIsExporting(false)
    }
  }

  // Блокировка прокрутки body при открытии модального окна
  useEffect(() => {
    if (isOpen) {
      // Сохраняем текущую позицию прокрутки
      const scrollY = window.scrollY
      // Блокируем прокрутку
      document.body.style.overflow = 'hidden'
      document.body.style.position = 'fixed'
      document.body.style.top = `-${scrollY}px`
      document.body.style.width = '100%'

      return () => {
        // Восстанавливаем прокрутку
        document.body.style.overflow = ''
        document.body.style.position = ''
        document.body.style.top = ''
        document.body.style.width = ''
        window.scrollTo(0, scrollY)
      }
    }
  }, [isOpen])

  // Закрытие модального окна по нажатию Escape
  useEffect(() => {
    if (!isOpen) return

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault() // Предотвращаем стандартное поведение
        event.stopPropagation() // Предотвращаем всплытие события
        onClose()
      }
    }

    // Используем capture: true для перехвата события раньше других обработчиков
    document.addEventListener('keydown', handleKeyDown, true)
    return () => document.removeEventListener('keydown', handleKeyDown, true)
  }, [isOpen, onClose])

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="ai-modal-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            className="ai-modal-container"
            initial={{ opacity: 0, scale: 0.95, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          >
            <div className="ai-modal">
              {/* Header */}
              <div className="ai-modal-header">
                <div className="ai-modal-header-left">
                  <div className="ai-modal-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                      <path
                        d="M12 2L2 7L12 12L22 7L12 2Z"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="square"
                      />
                      <path
                        d="M2 17L12 22L22 17M2 12L12 17L22 12"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="square"
                      />
                    </svg>
                  </div>
                  <div className="ai-modal-title-block">
                    <div className="ai-modal-title font-code">
                      {showSavedResults ? 'СОХРАНЕННЫЕ РЕЗУЛЬТАТЫ' : 'ИИ АНАЛИЗ'}
                    </div>
                    <div className="ai-modal-subtitle">
                      {showSavedResults
                        ? 'История AI анализов из базы данных'
                        : 'Автоматическая проверка заключений специалистов'
                      }
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
                  {!isLoading && analysis && (
                    <button
                      className="ai-modal-btn ai-modal-btn-secondary"
                      onClick={() => {
                        if (showSavedResults) {
                          setShowSavedResults(false)
                        } else {
                          handleLoadSavedResults()
                        }
                      }}
                      disabled={isLoadingSaved}
                      style={{
                        padding: '8px 12px',
                        fontSize: '13px',
                        minWidth: '140px'
                      }}
                    >
                      {isLoadingSaved ? (
                        'Загрузка...'
                      ) : showSavedResults ? (
                        '← Текущий анализ'
                      ) : (
                        <>
                          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" style={{ marginRight: '4px' }}>
                            <path
                              d="M7 1V7M7 7L10 4M7 7L4 4M13 7V11.6667C13 12.0203 12.8595 12.3594 12.6095 12.6095C12.3594 12.8595 12.0203 13 11.6667 13H2.33333C1.97971 13 1.64057 12.8595 1.39052 12.6095C1.14048 12.3594 1 12.0203 1 11.6667V7"
                              stroke="currentColor"
                              strokeWidth="1.5"
                              strokeLinecap="square"
                            />
                          </svg>
                          История анализов
                        </>
                      )}
                    </button>
                  )}
                  <button className="ai-modal-close" onClick={onClose}>
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                      <path
                        d="M15 5L5 15M5 5L15 15"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="square"
                      />
                    </svg>
                  </button>
                </div>
              </div>

              {/* Content and Footer */}
              {isLoading ? (
                <div className="ai-modal-content">
                  <div className="ai-modal-loading">
                    <div className="loading-spinner"></div>
                    <div className="loading-text">Выполняется AI анализ...</div>
                  </div>
                </div>
              ) : !analysis ? (
                <div className="ai-modal-content">
                  <div className="ai-modal-empty">
                    <div className="empty-text">Нет данных для анализа</div>
                  </div>
                </div>
              ) : showSavedResults ? (
                <>
                  <div className="ai-modal-content">
                    {savedResults && savedResults.total_count > 0 ? (
                      <div className="ai-modal-section">
                        <div className="ai-modal-section-header">
                          <div className="ai-modal-section-title font-code">
                            СОХРАНЕННЫЕ РЕЗУЛЬТАТЫ ({savedResults.total_count})
                          </div>
                          <div className="ai-modal-subtitle" style={{ marginTop: '4px', fontSize: '13px', opacity: 0.7 }}>
                            Результаты AI анализа из базы данных
                          </div>
                        </div>

                        <div className="ai-analyses-list" style={{ marginTop: '16px' }}>
                          {savedResults.results.map((result: any, index: number) => (
                            <motion.div
                              key={result.id}
                              className={`ai-analysis-item ai-analysis-${result.risk_level?.toLowerCase() || 'low'}`}
                              initial={{ opacity: 0, x: -20 }}
                              animate={{ opacity: 1, x: 0 }}
                              transition={{ delay: index * 0.05 }}
                            >
                              <div className="ai-analysis-header">
                                <div className="ai-analysis-specialty">
                                  {result.specialty}
                                </div>
                                <div className="ai-analysis-article font-code">
                                  {result.article ? `п. ${result.article}` : '—'}
                                  {result.subpoint ? ` пп.${result.subpoint}` : ''}
                                </div>
                              </div>

                              <div className="ai-analysis-categories">
                                <div className="category-item">
                                  <span className="category-label">Врач:</span>
                                  <motion.span
                                    className={`category-value font-code ${
                                      result.status === 'MISMATCH'
                                        ? 'category-value-mismatch'
                                        : ''
                                    }`}
                                  >
                                    {result.doctor_category}
                                  </motion.span>
                                </div>
                                <div className="category-arrow">→</div>
                                <div className="category-item">
                                  <span className="category-label">ИИ:</span>
                                  <motion.span
                                    className={`category-value font-code ${
                                      result.status === 'MISMATCH'
                                        ? 'category-value-mismatch'
                                        : ''
                                    }`}
                                  >
                                    {result.ai_recommended_category}
                                  </motion.span>
                                </div>
                              </div>

                              <div className="ai-analysis-reasoning">
                                <div className="reasoning-label">Обоснование:</div>
                                <div className="reasoning-text">{result.reasoning}</div>
                              </div>

                              <div className="ai-analysis-footer">
                                <div
                                  className={`analysis-status analysis-status-${result.status.toLowerCase()}`}
                                >
                                  {result.status === 'MATCH' && '✓ Соответствует'}
                                  {result.status === 'MISMATCH' && '⚠ Несоответствие'}
                                  {result.status === 'PARTIAL_MISMATCH' && '⚠ Возможно несоответствие'}
                                  {result.status === 'REVIEW_REQUIRED' && '⚠ Требуется проверка'}
                                </div>
                                <div className="analysis-confidence" style={{ fontSize: '12px', opacity: 0.7 }}>
                                  {new Date(result.created_at).toLocaleString('ru-RU', {
                                    year: 'numeric',
                                    month: '2-digit',
                                    day: '2-digit',
                                    hour: '2-digit',
                                    minute: '2-digit'
                                  })}
                                </div>
                              </div>
                            </motion.div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <div className="ai-modal-empty">
                        <div className="empty-text">
                          Нет сохраненных результатов для этого призывника
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Footer for saved results */}
                  <div className="ai-modal-footer">
                    <div className="ai-modal-footer-disclaimer">
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                        <path
                          d="M7 4.66667V7M7 9.33333H7.00667M13 7C13 10.3137 10.3137 13 7 13C3.68629 13 1 10.3137 1 7C1 3.68629 3.68629 1 7 1C10.3137 1 13 3.68629 13 7Z"
                          stroke="currentColor"
                          strokeWidth="1.5"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                      <span>
                        Отображаются результаты из базы данных. Для нового анализа вернитесь к текущему анализу.
                      </span>
                    </div>
                    <div className="ai-modal-footer-actions">
                      <button className="ai-modal-btn ai-modal-btn-secondary" onClick={onClose}>
                        Закрыть
                      </button>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <div className="ai-modal-content">
                    {/* Баннер для сохраненных результатов */}
                    {analysis?.isSaved && (
                      <div className="ai-disclaimer-banner" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', border: 'none' }}>
                        <div className="disclaimer-icon">
                          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                            <path
                              d="M10 2V10M10 10L13 7M10 10L7 7M18 10V16.6667C18 17.0203 17.8595 17.3594 17.6095 17.6095C17.3594 17.8595 17.0203 18 16.6667 18H3.33333C2.97971 18 2.64057 17.8595 2.39052 17.6095C2.14048 17.3594 2 17.0203 2 16.6667V10"
                              stroke="currentColor"
                              strokeWidth="2"
                              strokeLinecap="square"
                            />
                          </svg>
                        </div>
                        <div className="disclaimer-content">
                          <div className="disclaimer-title">💾 Сохраненные результаты</div>
                          <div className="disclaimer-text">
                            Отображаются результаты предыдущего AI анализа из базы данных.
                            Для выполнения нового анализа с актуальными данными нажмите кнопку <strong>"Повторить анализ"</strong> ниже.
                          </div>
                        </div>
                      </div>
                    )}

                    {/* AI Disclaimer Banner */}
                    <div className="ai-disclaimer-banner">
                      <div className="disclaimer-icon">
                        <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                          <path
                            d="M10 6V10M10 14H10.01M19 10C19 14.9706 14.9706 19 10 19C5.02944 19 1 14.9706 1 10C1 5.02944 5.02944 1 10 1C14.9706 1 19 5.02944 19 10Z"
                            stroke="currentColor"
                            strokeWidth="2"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                          />
                        </svg>
                      </div>
                      <div className="disclaimer-content">
                        <div className="disclaimer-title">⚠️ Важное предупреждение</div>
                        <div className="disclaimer-text">
                          Данный анализ выполнен с использованием искусственного интеллекта и носит <strong>рекомендательный характер</strong>.
                          Результаты ИИ могут содержать неточности и <strong>требуют обязательной проверки</strong> квалифицированным медицинским специалистом.
                          Окончательное решение о категории годности принимает председатель военно-врачебной комиссии.
                        </div>
                      </div>
                    </div>

                    {/* Risk Level */}
                    <div
                      className="ai-modal-risk-banner"
                      style={{
                        '--risk-color': riskColors[analysis.overallRiskLevel || 'LOW'],
                      } as React.CSSProperties}
                    >
                  <div className="risk-banner-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                      <path
                        d="M12 9V13M12 17H12.01M21 12C21 16.9706 16.9706 21 12 21C7.02944 21 3 16.9706 3 12C3 7.02944 7.02944 3 12 3C16.9706 3 21 7.02944 21 12Z"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                      />
                    </svg>
                  </div>
                  <div className="risk-banner-content">
                    <div className="risk-banner-label-with-info">
                      <span className="risk-banner-label">Общий уровень риска</span>
                      <div className="info-tooltip-wrapper">
                        <div className="info-icon">i</div>
                        <div className="info-tooltip">
                          Интегральная оценка риска на основе всех выявленных несоответствий. Низкий - нет проблем, Средний - требуется внимание, Высокий - критические расхождения.
                        </div>
                      </div>
                    </div>
                    <div className="risk-banner-value font-code">
                      {riskLabels[analysis.overallRiskLevel || 'LOW']}
                    </div>
                  </div>
                </div>

                {/* Stats Grid */}
                <div className="ai-modal-stats-grid">
                  <div className="ai-modal-stat-card">
                    <div className="stat-card-icon">
                      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                        <path
                          d="M16.6667 2.5H3.33333C2.8731 2.5 2.5 2.8731 2.5 3.33333V16.6667C2.5 17.1269 2.8731 17.5 3.33333 17.5H16.6667C17.1269 17.5 17.5 17.1269 17.5 16.6667V3.33333C17.5 2.8731 17.1269 2.5 16.6667 2.5Z"
                          stroke="currentColor"
                          strokeWidth="1.5"
                        />
                        <path
                          d="M6.66667 10H13.3333M6.66667 6.66667H13.3333M6.66667 13.3333H10"
                          stroke="currentColor"
                          strokeWidth="1.5"
                        />
                      </svg>
                    </div>
                    <div className="stat-card-content">
                      <div className="stat-card-label">Всего заключений</div>
                      <div className="stat-card-value font-code">
                        {analysis.examinations?.length || 0}
                      </div>
                    </div>
                  </div>

                  <div className="ai-modal-stat-card stat-warning">
                    <div className="stat-card-icon">
                      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                        <path
                          d="M10 6.66667V10M10 13.3333H10.0083M18.3333 10C18.3333 14.6024 14.6024 18.3333 10 18.3333C5.39763 18.3333 1.66667 14.6024 1.66667 10C1.66667 5.39763 5.39763 1.66667 10 1.66667C14.6024 1.66667 18.3333 5.39763 18.3333 10Z"
                          stroke="currentColor"
                          strokeWidth="1.5"
                          strokeLinecap="square"
                        />
                      </svg>
                    </div>
                    <div className="stat-card-content">
                      <div className="stat-card-label-with-info">
                        <span className="stat-card-label">Несоответствий</span>
                        <div className="info-tooltip-wrapper">
                          <div className="info-icon">i</div>
                          <div className="info-tooltip">
                            Количество заключений, где категория годности, поставленная врачом, не совпадает с рекомендацией ИИ.
                          </div>
                        </div>
                      </div>
                      <div className="stat-card-value font-code">
                        {analysis.aiAnalyses?.filter((a) => a.status === 'MISMATCH' || a.status === 'PARTIAL_MISMATCH')
                          .length || 0}
                      </div>
                    </div>
                  </div>

                  <div className="ai-modal-stat-card">
                    <div className="stat-card-icon">
                      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                        <path
                          d="M2.5 10L7.5 15L17.5 5"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="square"
                        />
                      </svg>
                    </div>
                    <div className="stat-card-content">
                      <div className="stat-card-label-with-info">
                        <span className="stat-card-label">Средняя уверенность</span>
                        <div className="info-tooltip-wrapper">
                          <div className="info-icon">i</div>
                          <div className="info-tooltip">
                            Средний уровень уверенности ИИ во всех проанализированных заключениях специалистов. Значение от 0% до 100%.
                          </div>
                        </div>
                      </div>
                      <div className="stat-card-value font-code">
                        {analysis.aiAnalyses && analysis.aiAnalyses.length > 0
                          ? Math.round(
                              (analysis.aiAnalyses.reduce(
                                (acc: number, a: any) => acc + (a.confidence || 0),
                                0
                              ) /
                                analysis.aiAnalyses.length) *
                                100
                            )
                          : 0}
                        %
                      </div>
                    </div>
                  </div>
                </div>

                {/* Analyses List */}
                {analysis.aiAnalyses && analysis.aiAnalyses.length > 0 && (
                  <div className="ai-modal-section">
                    <div className="ai-modal-section-header">
                      <div className="ai-modal-section-title font-code">
                        РЕЗУЛЬТАТЫ АНАЛИЗА
                      </div>
                    </div>

                    <div className="ai-analyses-list">
                      {analysis.aiAnalyses.map((aiAnalysis, index) => (
                        <motion.div
                          key={index}
                          className={`ai-analysis-item ai-analysis-${aiAnalysis.riskLevel?.toLowerCase() || 'low'}`}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.05 }}
                        >
                          <div className="ai-analysis-header">
                            <div className="ai-analysis-specialty">
                              {aiAnalysis.specialty}
                            </div>
                            <div className="ai-analysis-article font-code">
                              п. {aiAnalysis.point} пп.{aiAnalysis.subpoint}
                            </div>
                          </div>

                          <div className="ai-analysis-categories">
                            <div className="category-item">
                              <span className="category-label">Врач:</span>
                              <motion.span
                                className={`category-value font-code ${
                                  aiAnalysis.status === 'MISMATCH'
                                    ? 'category-value-mismatch'
                                    : ''
                                }`}
                                animate={
                                  aiAnalysis.status === 'MISMATCH'
                                    ? {
                                        opacity: [1, 0.4, 1],
                                        scale: [1, 1.05, 1],
                                      }
                                    : {}
                                }
                                transition={{
                                  duration: 1.5,
                                  repeat: Infinity,
                                  ease: 'easeInOut',
                                }}
                              >
                                {aiAnalysis.doctorCategory}
                              </motion.span>
                            </div>
                            <div className="category-arrow">→</div>
                            <div className="category-item">
                              <span className="category-label">ИИ:</span>
                              <motion.span
                                className={`category-value font-code ${
                                  aiAnalysis.status === 'MISMATCH'
                                    ? 'category-value-mismatch'
                                    : ''
                                }`}
                                animate={
                                  aiAnalysis.status === 'MISMATCH'
                                    ? {
                                        opacity: [1, 0.4, 1],
                                        scale: [1, 1.05, 1],
                                      }
                                    : {}
                                }
                                transition={{
                                  duration: 1.5,
                                  repeat: Infinity,
                                  ease: 'easeInOut',
                                }}
                              >
                                {aiAnalysis.aiRecommendedCategory}
                              </motion.span>
                            </div>
                          </div>

                          <div className="ai-analysis-reasoning">
                            <div className="reasoning-label">Обоснование:</div>
                            <div className="reasoning-text">{aiAnalysis.reasoning}</div>
                          </div>

                          <div className="ai-analysis-footer">
                            <div
                              className={`analysis-status analysis-status-${aiAnalysis.status.toLowerCase()}`}
                            >
                              {aiAnalysis.status === 'MATCH' && '✓ Соответствует'}
                              {aiAnalysis.status === 'MISMATCH' && '⚠ Несоответствие'}
                              {aiAnalysis.status === 'PARTIAL_MISMATCH' && '⚠ Возможно несоответствие'}
                              {aiAnalysis.status === 'REVIEW_REQUIRED' &&
                                '⚠ Требуется проверка'}
                            </div>
                            <div className="analysis-confidence">
                              Уверенность:{' '}
                              <span className="font-code">
                                {Math.round(aiAnalysis.confidence * 100)}%
                              </span>
                            </div>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                  </div>
                )}
                  </div>

                  {/* Footer */}
                  <div className="ai-modal-footer">
                    <div className="ai-modal-footer-disclaimer">
                      <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
                        <path
                          d="M7 4.66667V7M7 9.33333H7.00667M13 7C13 10.3137 10.3137 13 7 13C3.68629 13 1 10.3137 1 7C1 3.68629 3.68629 1 7 1C10.3137 1 13 3.68629 13 7Z"
                          stroke="currentColor"
                          strokeWidth="1.5"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                        />
                      </svg>
                      <span>
                        Результаты ИИ-анализа носят рекомендательный характер и требуют проверки специалистом
                      </span>
                    </div>
                    <div className="ai-modal-footer-actions">
                      <button className="ai-modal-btn ai-modal-btn-secondary" onClick={onClose}>
                        Закрыть
                      </button>
                      {analysis?.isSaved && onRerunAnalysis && (
                        <button
                          className="ai-modal-btn ai-modal-btn-primary"
                          onClick={() => {
                            onRerunAnalysis()
                            // onClose() // Можно закрыть модал, новый откроется с новым анализом
                          }}
                          style={{
                            background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                            border: 'none'
                          }}
                        >
                          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                            <path
                              d="M13.65 2.35C12.2 0.9 10.21 0 8 0C3.58 0 0 3.58 0 8C0 12.42 3.58 16 8 16C11.73 16 14.84 13.45 15.73 10H13.65C12.83 12.33 10.61 14 8 14C4.69 14 2 11.31 2 8C2 4.69 4.69 2 8 2C9.66 2 11.14 2.69 12.22 3.78L9 7H16V0L13.65 2.35Z"
                              fill="currentColor"
                            />
                          </svg>
                          <span>Повторить анализ</span>
                        </button>
                      )}
                      <button
                        className="ai-modal-btn ai-modal-btn-primary"
                        onClick={handleExportPDF}
                        disabled={isExporting}
                      >
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                          <path
                            d="M14 10V12.6667C14 13.0203 13.8595 13.3594 13.6095 13.6095C13.3594 13.8595 13.0203 14 12.6667 14H3.33333C2.97971 14 2.64057 13.8595 2.39052 13.6095C2.14048 13.3594 2 13.0203 2 12.6667V10M4.66667 6.66667L8 10M8 10L11.3333 6.66667M8 10V2"
                            stroke="currentColor"
                            strokeWidth="1.5"
                            strokeLinecap="square"
                          />
                        </svg>
                        <span>{isExporting ? 'Экспорт...' : 'Экспорт отчёта'}</span>
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
