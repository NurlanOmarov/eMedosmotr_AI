import { motion, AnimatePresence } from 'framer-motion'
import { useState } from 'react'
import type { AIAnalysis } from '../types'
import { apiClient } from '../services/api'
import './DetailedAnalysisModal.css'

interface DetailedAnalysisModalProps {
  isOpen: boolean
  onClose: () => void
  analysis: AIAnalysis | null
  conscriptId?: string
}

export default function DetailedAnalysisModal({
  isOpen,
  onClose,
  analysis,
  conscriptId,
}: DetailedAnalysisModalProps) {
  const [isExporting, setIsExporting] = useState(false)

  if (!analysis) return null

  const riskColors = {
    LOW: 'var(--color-primary)',
    MEDIUM: 'var(--color-warning)',
    HIGH: 'var(--color-danger)',
  }

  const handleExportPDF = async () => {
    if (!analysis || !conscriptId) {
      alert('Нет данных для экспорта')
      return
    }

    setIsExporting(true)
    try {
      // Формируем данные для одного анализа
      const analysisData = {
        conscriptId: conscriptId,
        examinations: [],
        aiAnalyses: [analysis],
        overallRiskLevel: analysis.riskLevel
      }

      const blob = await apiClient.exportAnalysisReport({
        conscript_id: conscriptId,
        analysis_data: analysisData
      })

      // Создаем ссылку для скачивания
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `Detailed_Analysis_${analysis.specialty}_${new Date().toISOString().split('T')[0]}.pdf`
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

  return (
    <AnimatePresence>
      {isOpen && (
        <>
          {/* Backdrop */}
          <motion.div
            className="modal-backdrop"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
          />

          {/* Modal */}
          <motion.div
            className="modal-container"
            initial={{ opacity: 0, scale: 0.9, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.9, y: 20 }}
            transition={{ type: 'spring', damping: 25, stiffness: 300 }}
          >
            <div className="modal">
              {/* Header */}
              <div className="modal-header">
                <div className="modal-header-left">
                  <div className="modal-icon">
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
                  <div className="modal-title-block">
                    <div className="modal-title font-code">ПОДРОБНЫЙ АНАЛИЗ</div>
                    <div className="modal-subtitle">{analysis.specialty}</div>
                  </div>
                </div>

                <button className="modal-close" onClick={onClose}>
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

              {/* Content */}
              <div className="modal-content">
                {/* Summary Section */}
                <section className="modal-section">
                  <div className="modal-section-header">
                    <div className="modal-section-title font-code">СВОДКА</div>
                  </div>

                  <div className="summary-grid">
                    <div className="summary-card">
                      <div className="summary-card-label">Пункт приказа</div>
                      <div className="summary-card-value font-code">
                        п. {analysis.point} пп.{analysis.subpoint}
                      </div>
                    </div>

                    <div className="summary-card">
                      <div className="summary-card-label">Категория врача</div>
                      <div className="summary-card-value font-code">
                        {analysis.doctorCategory}
                      </div>
                    </div>

                    <div className="summary-card">
                      <div className="summary-card-label">Рекомендация AI</div>
                      <div className="summary-card-value font-code">
                        {analysis.aiRecommendedCategory}
                      </div>
                    </div>

                    <div className="summary-card">
                      <div className="summary-card-label">Уверенность</div>
                      <div className="summary-card-value font-code">
                        {Math.round(analysis.confidence * 100)}%
                      </div>
                    </div>
                  </div>

                  {/* Status indicator */}
                  <div
                    className={`status-indicator status-indicator-${analysis.status.toLowerCase()}`}
                  >
                    <div className="status-indicator-icon">
                      {analysis.status === 'MATCH' && '✓'}
                      {analysis.status === 'MISMATCH' && '✕'}
                      {analysis.status === 'PARTIAL_MISMATCH' && '⚠'}
                      {analysis.status === 'REVIEW_REQUIRED' && '⚠'}
                    </div>
                    <div className="status-indicator-text">
                      {analysis.status === 'MATCH' && 'ЗАКЛЮЧЕНИЕ СООТВЕТСТВУЕТ'}
                      {analysis.status === 'MISMATCH' && 'ОБНАРУЖЕНО НЕСООТВЕТСТВИЕ'}
                      {analysis.status === 'PARTIAL_MISMATCH' && 'ВОЗМОЖНО НЕСООТВЕТСТВИЕ'}
                      {analysis.status === 'REVIEW_REQUIRED' && 'ТРЕБУЕТСЯ ПРОВЕРКА'}
                    </div>
                  </div>
                </section>

                {/* Reasoning Section */}
                <section className="modal-section">
                  <div className="modal-section-header">
                    <div className="modal-section-title font-code">ОБОСНОВАНИЕ</div>
                    <div
                      className="risk-badge"
                      style={{ '--risk-color': analysis.riskLevel ? riskColors[analysis.riskLevel] : riskColors.LOW } as any}
                    >
                      <div className="risk-badge-dot" />
                      <span className="risk-badge-text font-code">
                        {analysis.riskLevel} RISK
                      </span>
                    </div>
                  </div>

                  <div className="reasoning-box">
                    <p className="reasoning-text">{analysis.reasoning}</p>
                  </div>
                </section>

                {/* Subpoint Details */}
                {analysis.subpointDetails && (
                  <section className="modal-section">
                    <div className="modal-section-header">
                      <div className="modal-section-title font-code">
                        ДЕТАЛИ ПОДПУНКТА
                      </div>
                    </div>

                    <div className="details-box">
                      <div className="details-item">
                        <div className="details-label">Текст критерия:</div>
                        <div className="details-value">
                          {analysis.subpointDetails.criteriaText}
                        </div>
                      </div>

                      {analysis.subpointDetails.matchedCriteria && (
                        <div className="details-item">
                          <div className="details-label">Совпавшие критерии:</div>
                          <div className="details-value">
                            {analysis.subpointDetails.matchedCriteria}
                          </div>
                        </div>
                      )}

                      {analysis.subpointDetails.parametersMatched && (
                        <div className="details-item">
                          <div className="details-label">Совпавшие параметры:</div>
                          <div className="parameters-grid">
                            {Object.entries(
                              analysis.subpointDetails.parametersMatched
                            ).map(([key, value]) => (
                              <div key={key} className="parameter-chip">
                                <span className="parameter-key font-mono">{key}:</span>
                                <span className="parameter-value font-code">
                                  {String(value)}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  </section>
                )}

                {/* Category Details */}
                {analysis.categoryDetails && analysis.categoryDetails.alternativeCategories && analysis.categoryDetails.alternativeCategories.length > 0 && (
                  <section className="modal-section">
                    <div className="modal-section-header">
                      <div className="modal-section-title font-code">
                        ДЕТАЛИ КАТЕГОРИИ
                      </div>
                    </div>

                    <div className="details-box">
                      <div className="details-item">
                        <div className="details-label">
                          Альтернативные категории:
                        </div>
                        <div className="alternatives-list">
                          {analysis.categoryDetails.alternativeCategories.map(
                            (cat, idx) => (
                              <span key={idx} className="alternative-chip font-code">
                                {cat}
                              </span>
                            )
                          )}
                        </div>
                      </div>
                    </div>
                  </section>
                )}

                {/* Confidence Meter */}
                <section className="modal-section">
                  <div className="modal-section-header">
                    <div className="modal-section-title font-code">
                      УРОВЕНЬ УВЕРЕННОСТИ
                    </div>
                  </div>

                  <div className="confidence-meter">
                    <div className="confidence-bar">
                      <motion.div
                        className="confidence-fill"
                        initial={{ width: 0 }}
                        animate={{ width: `${analysis.confidence * 100}%` }}
                        transition={{ duration: 1, ease: 'easeOut' }}
                        style={{
                          background:
                            analysis.confidence >= 0.8
                              ? 'var(--color-primary)'
                              : analysis.confidence >= 0.6
                              ? 'var(--color-warning)'
                              : 'var(--color-danger)',
                        }}
                      />
                    </div>
                    <div className="confidence-labels">
                      <span className="confidence-label font-mono">0%</span>
                      <span className="confidence-value font-code">
                        {Math.round(analysis.confidence * 100)}%
                      </span>
                      <span className="confidence-label font-mono">100%</span>
                    </div>
                  </div>
                </section>
              </div>

              {/* Footer */}
              <div className="modal-footer">
                <button className="modal-btn modal-btn-secondary" onClick={onClose}>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path
                      d="M12 4L4 12M4 4L12 12"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="square"
                    />
                  </svg>
                  <span>Закрыть</span>
                </button>

                <button
                  className="modal-btn modal-btn-primary"
                  onClick={handleExportPDF}
                  disabled={isExporting || !conscriptId}
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
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}
