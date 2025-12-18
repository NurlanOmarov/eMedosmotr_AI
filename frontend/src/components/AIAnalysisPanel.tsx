import { motion, AnimatePresence } from 'framer-motion'
import { useState, useEffect } from 'react'
import type { Conscript, ConscriptAnalysis, RiskLevel, AIAnalysis } from '../types'
import type { User } from '../App'
import { apiClient } from '../services/api'
import './AIAnalysisPanel.css'

interface AIAnalysisPanelProps {
  conscript: Conscript
  analysis: ConscriptAnalysis | null
  isLoading: boolean
  onRunAnalysis: () => void
  onOpenDetailedAnalysis?: (analysis: AIAnalysis) => void
  currentUser: User
}

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

export default function AIAnalysisPanel({
  conscript,
  analysis,
  isLoading,
  onRunAnalysis,
  onOpenDetailedAnalysis,
  currentUser: _currentUser,
}: AIAnalysisPanelProps) {
  void _currentUser
  const [expanded, setExpanded] = useState(true)
  const [savedResults, setSavedResults] = useState<any>(null)
  const [isLoadingSaved, setIsLoadingSaved] = useState(false)
  const [showSaved, setShowSaved] = useState(false)

  // Автоматическая загрузка сохраненных результатов при открытии панели
  useEffect(() => {
    const loadSavedResults = async () => {
      if (!conscript?.id) return

      setIsLoadingSaved(true)
      try {
        const response = await apiClient.getSavedAnalysisResults(conscript.id)
        setSavedResults(response)
        console.log('✅ Автоматически загружены сохраненные результаты:', response)
      } catch (error) {
        console.error('❌ Ошибка загрузки сохраненных результатов:', error)
      } finally {
        setIsLoadingSaved(false)
      }
    }

    loadSavedResults()
  }, [conscript?.id])

  const mockAnalysis = {
    overallRiskLevel: 'MEDIUM' as RiskLevel,
    examinations: [
      { specialty: 'Терапевт', doctorCategory: 'Б', confidence: 0.92 },
      { specialty: 'Окулист', doctorCategory: 'В', confidence: 0.88 },
      { specialty: 'Хирург', doctorCategory: 'А', confidence: 0.95 },
    ],
    aiAnalyses: [
      {
        specialty: 'Окулист',
        doctorCategory: 'В' as const,
        aiRecommendedCategory: 'Б' as const,
        article: 109,
        point: 34,
        subpoint: '4',
        riskLevel: 'MEDIUM' as RiskLevel,
        status: 'MISMATCH' as const,
        confidence: 0.88,
        reasoning: 'Миопия средней степени соответствует категории Б, а не В.',
      },
    ],
  }

  const displayAnalysis = analysis || mockAnalysis

  return (
    <motion.div
      className={`ai-panel ${expanded ? '' : 'ai-panel-collapsed'}`}
      layout
      transition={{ type: 'spring', stiffness: 300, damping: 30 }}
    >
      {/* Header */}
      <div className="ai-panel-header" onClick={() => setExpanded(!expanded)}>
        <div className="ai-panel-header-left">
          {/* AI Icon */}
          <motion.div
            className="ai-panel-icon"
            animate={{
              boxShadow: [
                '0 0 0 0 rgba(0, 168, 107, 0.4)',
                '0 0 0 12px rgba(0, 168, 107, 0)',
              ],
            }}
            transition={{ repeat: Infinity, duration: 2 }}
          >
            <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path
                d="M12 2L2 7L12 12L22 7L12 2Z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="square"
                strokeLinejoin="miter"
              />
              <path
                d="M2 17L12 22L22 17"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="square"
                strokeLinejoin="miter"
              />
              <path
                d="M2 12L12 17L22 12"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="square"
                strokeLinejoin="miter"
              />
            </svg>
          </motion.div>

          {/* Title */}
          <div className="ai-panel-title-block">
            <div className="ai-panel-title font-code">AI АНАЛИЗ</div>
            <div className="ai-panel-subtitle">
              Автоматическая проверка заключений
            </div>
          </div>
        </div>

        <div className="ai-panel-header-right">
          {/* Risk indicator */}
          {displayAnalysis && displayAnalysis.overallRiskLevel && (
            <div
              className="ai-panel-risk"
              style={
                { '--risk-color': riskColors[displayAnalysis.overallRiskLevel] } as any
              }
            >
              <div className="ai-panel-risk-dot" />
              <span className="ai-panel-risk-text font-code">
                {riskLabels[displayAnalysis.overallRiskLevel]}
              </span>
            </div>
          )}

          {/* Toggle button */}
          <motion.button
            className="ai-panel-toggle"
            animate={{ rotate: expanded ? 0 : 180 }}
            transition={{ duration: 0.3 }}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path
                d="M4 6L8 10L12 6"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="square"
              />
            </svg>
          </motion.button>
        </div>
      </div>

      {/* Content */}
      <AnimatePresence>
        {expanded && (
          <motion.div
            className="ai-panel-content"
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.3 }}
          >
            {/* AI Disclaimer */}
            <div className="ai-panel-disclaimer">
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path
                  d="M8 5.33333V8M8 10.6667H8.00667M15 8C15 11.866 11.866 15 8 15C4.13401 15 1 11.866 1 8C1 4.13401 4.13401 1 8 1C11.866 1 15 4.13401 15 8Z"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              <span>
                <strong>Внимание:</strong> Результаты ИИ-анализа носят рекомендательный характер.
                Окончательное решение принимает председатель ВВК.
              </span>
            </div>

            {/* Stats grid */}
            {displayAnalysis ? (
              <>
                <div className="ai-stats-grid">
                  {/* Examinations completed */}
                  <div className="ai-stat-card">
                    <div className="ai-stat-icon">
                      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                        <path
                          d="M16.6667 2.5H3.33333C2.8731 2.5 2.5 2.8731 2.5 3.33333V16.6667C2.5 17.1269 2.8731 17.5 3.33333 17.5H16.6667C17.1269 17.5 17.5 17.1269 17.5 16.6667V3.33333C17.5 2.8731 17.1269 2.5 16.6667 2.5Z"
                          stroke="currentColor"
                          strokeWidth="1.5"
                        />
                        <path d="M6.66667 10H13.3333M6.66667 6.66667H13.3333M6.66667 13.3333H10" stroke="currentColor" strokeWidth="1.5" />
                      </svg>
                    </div>
                    <div className="ai-stat-content">
                      <div className="ai-stat-label">Заключений</div>
                      <div className="ai-stat-value font-code">
                        {displayAnalysis.examinations?.length || 0}/7
                      </div>
                    </div>
                  </div>

                  {/* Mismatches found */}
                  <div className="ai-stat-card ai-stat-card-warning">
                    <div className="ai-stat-icon">
                      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                        <path
                          d="M10 6.66667V10M10 13.3333H10.0083M18.3333 10C18.3333 14.6024 14.6024 18.3333 10 18.3333C5.39763 18.3333 1.66667 14.6024 1.66667 10C1.66667 5.39763 5.39763 1.66667 10 1.66667C14.6024 1.66667 18.3333 5.39763 18.3333 10Z"
                          stroke="currentColor"
                          strokeWidth="1.5"
                          strokeLinecap="square"
                        />
                      </svg>
                    </div>
                    <div className="ai-stat-content">
                      <div className="ai-stat-label">Несоответствий</div>
                      <div className="ai-stat-value font-code">
                        {displayAnalysis.aiAnalyses?.filter(a => a.status === 'MISMATCH' || a.status === 'PARTIAL_MISMATCH')
                          .length || 0}
                      </div>
                    </div>
                  </div>

                  {/* Average confidence */}
                  <div className="ai-stat-card">
                    <div className="ai-stat-icon">
                      <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                        <path
                          d="M2.5 10L7.5 15L17.5 5"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="square"
                        />
                      </svg>
                    </div>
                    <div className="ai-stat-content">
                      <div className="ai-stat-label-with-info">
                        <span className="ai-stat-label">Уверенность AI</span>
                        <div className="info-tooltip-wrapper">
                          <div className="info-icon">i</div>
                          <div className="info-tooltip">
                            Средний уровень уверенности ИИ во всех проанализированных заключениях специалистов. Значение от 0% до 100%.
                          </div>
                        </div>
                      </div>
                      <div className="ai-stat-value font-code">
                        {displayAnalysis.aiAnalyses && displayAnalysis.aiAnalyses.length > 0
                          ? Math.round(
                              (displayAnalysis.aiAnalyses.reduce(
                                (acc: number, a: any) => acc + (a.confidence || 0),
                                0
                              ) /
                                displayAnalysis.aiAnalyses.length) *
                                100
                            )
                          : 0}
                        %
                      </div>
                    </div>
                  </div>
                </div>

                {/* Detailed findings */}
                <div className="ai-findings">
                  <div className="ai-findings-header">
                    <div className="ai-findings-title font-code">ВЫЯВЛЕННЫЕ ПРОБЛЕМЫ</div>
                    <div className="ai-findings-count">
                      {displayAnalysis.aiAnalyses?.length || 0}
                    </div>
                  </div>

                  <div className="ai-findings-list">
                    {displayAnalysis.aiAnalyses?.map((finding: any, index: number) => (
                      <motion.div
                        key={index}
                        className={`ai-finding ai-finding-${finding.riskLevel.toLowerCase()}`}
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.1 }}
                        onClick={() => onOpenDetailedAnalysis?.(finding)}
                        style={{ cursor: 'pointer' }}
                      >
                        <div className="ai-finding-header">
                          <div className="ai-finding-specialty">{finding.specialty}</div>
                          <div className="ai-finding-article font-code">
                            п. {finding.point} пп.{finding.subpoint}
                          </div>
                        </div>
                        <div className="ai-finding-status">
                          <span className="ai-finding-status-label">
                            {finding.status === 'MISMATCH' ? '⚠ Несоответствие' :
                             finding.status === 'PARTIAL_MISMATCH' ? '⚠ Возможно несоответствие' :
                             '✓ Соответствие'}
                          </span>
                        </div>
                        <div className="ai-finding-action">
                          <span className="ai-finding-action-text">Подробнее →</span>
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>

                {/* Actions */}
                <div className="ai-actions">
                  <button className="ai-action-btn ai-action-btn-primary">
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path
                        d="M14 4.66667V11.3333C14 11.687 13.8595 12.0261 13.6095 12.2761C13.3594 12.5262 13.0203 12.6667 12.6667 12.6667H3.33333C2.97971 12.6667 2.64057 12.5262 2.39052 12.2761C2.14048 12.0261 2 11.687 2 11.3333V4.66667M14 4.66667H2M14 4.66667L10.6667 2H5.33333L2 4.66667"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="square"
                      />
                    </svg>
                    <span>Сформировать заключение</span>
                  </button>

                  <button
                    className="ai-action-btn"
                    onClick={() => {
                      const firstMismatch = displayAnalysis.aiAnalyses?.find((a: any) => a.status === 'MISMATCH' || a.status === 'PARTIAL_MISMATCH')
                      if (firstMismatch) {
                        onOpenDetailedAnalysis?.(firstMismatch)
                      } else if (displayAnalysis.aiAnalyses?.length) {
                        onOpenDetailedAnalysis?.(displayAnalysis.aiAnalyses[0])
                      }
                    }}
                  >
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path
                        d="M8 2V14M2 8H14"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="square"
                      />
                    </svg>
                    <span>Подробный анализ</span>
                  </button>

                  <button className="ai-action-btn" onClick={onRunAnalysis}>
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path
                        d="M13.6 7.2C13.8 8.4 13.6 9.6 13 10.6C12.4 11.6 11.4 12.4 10.2 12.8C9 13.2 7.8 13.2 6.6 12.8C5.4 12.4 4.4 11.6 3.8 10.6M2.4 8.8C2.2 7.6 2.4 6.4 3 5.4C3.6 4.4 4.6 3.6 5.8 3.2C7 2.8 8.2 2.8 9.4 3.2C10.6 3.6 11.6 4.4 12.2 5.4M2 10V13H5M11 3H14V6"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="square"
                      />
                    </svg>
                    <span>Повторить анализ</span>
                  </button>
                </div>
              </>
            ) : (
              /* No analysis yet */
              <div className="ai-empty">
                <div className="ai-empty-icon">
                  <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                    <path
                      d="M24 6L6 14L24 22L42 14L24 6Z"
                      stroke="currentColor"
                      strokeWidth="3"
                      strokeLinecap="square"
                    />
                    <path d="M6 34L24 42L42 34M6 24L24 32L42 24" stroke="currentColor" strokeWidth="3" strokeLinecap="square" />
                  </svg>
                </div>
                <div className="ai-empty-title font-code">
                  {showSaved ? 'СОХРАНЕННЫЕ РЕЗУЛЬТАТЫ' : 'АНАЛИЗ НЕ ВЫПОЛНЕН'}
                </div>
                <div className="ai-empty-text">
                  {showSaved && savedResults?.total_count > 0
                    ? `Найдено ${savedResults.total_count} сохраненных результатов анализа`
                    : showSaved
                    ? 'Нет сохраненных результатов для этого призывника'
                    : 'Нажмите кнопку ниже, чтобы запустить AI анализ заключений специалистов'}
                </div>

                {/* Кнопка переключения на сохраненные результаты */}
                {savedResults && savedResults.total_count > 0 && !showSaved && (
                  <button
                    className="ai-action-btn ai-action-btn-secondary"
                    onClick={() => setShowSaved(true)}
                    disabled={isLoadingSaved}
                    style={{ marginBottom: '12px' }}
                  >
                    <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                      <path
                        d="M4 6L8 10L12 6"
                        stroke="currentColor"
                        strokeWidth="1.5"
                        strokeLinecap="square"
                      />
                    </svg>
                    <span>Показать сохраненные результаты ({savedResults.total_count})</span>
                  </button>
                )}

                {showSaved && savedResults && savedResults.total_count > 0 ? (
                  <>
                    {/* Список сохраненных результатов */}
                    <div className="ai-findings-list" style={{ maxHeight: '400px', overflowY: 'auto', marginBottom: '12px', width: '100%' }}>
                      {savedResults.results.map((result: any, index: number) => (
                        <motion.div
                          key={result.id}
                          className={`ai-finding ai-finding-${result.risk_level?.toLowerCase() || 'low'}`}
                          initial={{ opacity: 0, x: -20 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.05 }}
                          style={{ marginBottom: '8px' }}
                        >
                          <div className="ai-finding-header">
                            <div className="ai-finding-specialty">{result.specialty}</div>
                            <div className="ai-finding-article font-code">
                              {result.article ? `п. ${result.article}` : '—'}
                              {result.subpoint ? ` пп.${result.subpoint}` : ''}
                            </div>
                          </div>
                          <div style={{ display: 'flex', gap: '12px', marginTop: '4px', fontSize: '13px' }}>
                            <div>Врач: <strong>{result.doctor_category}</strong></div>
                            <div>→</div>
                            <div>ИИ: <strong>{result.ai_recommended_category}</strong></div>
                          </div>
                          <div style={{ marginTop: '6px', fontSize: '12px', opacity: 0.8 }}>
                            {result.reasoning}
                          </div>
                          <div className="ai-finding-status" style={{ marginTop: '6px' }}>
                            <span className="ai-finding-status-label">
                              {result.status === 'MATCH' ? '✓ Соответствие' :
                               result.status === 'MISMATCH' ? '⚠ Несоответствие' :
                               result.status === 'PARTIAL_MISMATCH' ? '⚠ Возможно несоответствие' :
                               '⚠ Требуется проверка'}
                            </span>
                            <span style={{ fontSize: '11px', opacity: 0.6, marginLeft: 'auto' }}>
                              {new Date(result.created_at).toLocaleString('ru-RU', {
                                year: 'numeric',
                                month: '2-digit',
                                day: '2-digit',
                                hour: '2-digit',
                                minute: '2-digit'
                              })}
                            </span>
                          </div>
                        </motion.div>
                      ))}
                    </div>
                    <button
                      className="ai-action-btn"
                      onClick={() => setShowSaved(false)}
                      style={{ marginBottom: '12px' }}
                    >
                      ← Вернуться к запуску анализа
                    </button>
                  </>
                ) : null}

                {!showSaved && (
                  <button
                    className="ai-action-btn ai-action-btn-primary"
                    onClick={onRunAnalysis}
                    disabled={isLoading}
                  >
                    {isLoading ? (
                      <>
                        <motion.svg
                          width="16"
                          height="16"
                          viewBox="0 0 16 16"
                          fill="none"
                          animate={{ rotate: 360 }}
                          transition={{ repeat: Infinity, duration: 1, ease: 'linear' }}
                        >
                          <path
                            d="M8 2V4M8 12V14M14 8H12M4 8H2M12.2 12.2L10.8 10.8M5.2 5.2L3.8 3.8M12.2 3.8L10.8 5.2M5.2 10.8L3.8 12.2"
                            stroke="currentColor"
                            strokeWidth="1.5"
                            strokeLinecap="square"
                          />
                        </motion.svg>
                        <span>Анализ...</span>
                      </>
                    ) : (
                      <>
                        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                          <path d="M4 8L7 11L12 5" stroke="currentColor" strokeWidth="2" strokeLinecap="square" />
                        </svg>
                        <span>Запустить AI анализ</span>
                      </>
                    )}
                  </button>
                )}
              </div>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  )
}
