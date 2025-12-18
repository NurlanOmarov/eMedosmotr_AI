import { motion } from 'framer-motion'
import type { ExaminationCompleteness } from '../types'
import './ExaminationCompletenessStatus.css'

interface ExaminationCompletenessStatusProps {
  completeness: ExaminationCompleteness
}

export default function ExaminationCompletenessStatus({
  completeness,
}: ExaminationCompletenessStatusProps) {
  const {
    is_complete,
    completed_specialists,
    missing_specialists,
    total_required,
    total_completed,
    missing_diagnoses,
    missing_categories,
    can_run_ai_analysis,
  } = completeness

  return (
    <motion.div
      className={`completeness-status ${can_run_ai_analysis ? 'status-ready' : 'status-incomplete'}`}
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Header */}
      <div className="completeness-header">
        <div className="completeness-icon">
          {can_run_ai_analysis ? (
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path
                d="M7 10L9 12L13 8M19 10C19 14.9706 14.9706 19 10 19C5.02944 19 1 14.9706 1 10C1 5.02944 5.02944 1 10 1C14.9706 1 19 5.02944 19 10Z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          ) : (
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path
                d="M10 6V10M10 14H10.01M19 10C19 14.9706 14.9706 19 10 19C5.02944 19 1 14.9706 1 10C1 5.02944 5.02944 1 10 1C14.9706 1 19 5.02944 19 10Z"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          )}
        </div>
        <div className="completeness-title">
          {can_run_ai_analysis
            ? 'Все специалисты провели освидетельствование'
            : 'Освидетельствование не завершено'}
        </div>
        <div className="completeness-badge font-code">
          {total_completed} / {total_required}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="completeness-progress">
        <motion.div
          className="completeness-progress-fill"
          initial={{ width: 0 }}
          animate={{ width: `${(total_completed / total_required) * 100}%` }}
          transition={{ duration: 0.5, delay: 0.2 }}
        />
      </div>

      {/* Details */}
      {!can_run_ai_analysis && (
        <div className="completeness-details">
          {missing_specialists.length > 0 && (
            <div className="completeness-error">
              <div className="error-label">❌ Не провели осмотр:</div>
              <div className="error-list">
                {missing_specialists.map((specialist, idx) => (
                  <span key={idx} className="error-item">
                    {specialist}
                  </span>
                ))}
              </div>
            </div>
          )}

          {missing_diagnoses.length > 0 && (
            <div className="completeness-error">
              <div className="error-label">⚠️ Нет диагноза:</div>
              <div className="error-list">
                {missing_diagnoses.map((specialist, idx) => (
                  <span key={idx} className="error-item">
                    {specialist}
                  </span>
                ))}
              </div>
            </div>
          )}

          {missing_categories.length > 0 && (
            <div className="completeness-error">
              <div className="error-label">⚠️ Нет категории годности:</div>
              <div className="error-list">
                {missing_categories.map((specialist, idx) => (
                  <span key={idx} className="error-item">
                    {specialist}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="completeness-warning">
            <strong>ИИ анализ недоступен.</strong> Дождитесь завершения всех осмотров.
          </div>
        </div>
      )}

      {/* Completed Specialists */}
      {completed_specialists.length > 0 && (
        <div className="completeness-completed">
          <div className="completed-label">✅ Провели осмотр:</div>
          <div className="completed-list">
            {completed_specialists.map((specialist, idx) => (
              <span key={idx} className="completed-item">
                {specialist}
              </span>
            ))}
          </div>
        </div>
      )}
    </motion.div>
  )
}
