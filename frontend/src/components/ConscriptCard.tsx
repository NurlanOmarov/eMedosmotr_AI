import { motion } from 'framer-motion'
import type { Conscript } from '../types'
import './ConscriptCard.css'

interface ConscriptCardProps {
  conscript: Conscript
}

export default function ConscriptCard({ conscript }: ConscriptCardProps) {
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('ru-RU', {
      day: '2-digit',
      month: 'long',
      year: 'numeric',
    })
  }

  const calculateAge = (birthDate: string) => {
    const today = new Date()
    const birth = new Date(birthDate)
    let age = today.getFullYear() - birth.getFullYear()
    const monthDiff = today.getMonth() - birth.getMonth()
    if (monthDiff < 0 || (monthDiff === 0 && today.getDate() < birth.getDate())) {
      age--
    }
    return age
  }

  return (
    <motion.div
      className="conscript-card"
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
    >
      {/* Card header */}
      <div className="conscript-card-header">
        <div className="conscript-card-title font-code">КАРТА ПРИЗЫВНИКА</div>
        <div className="conscript-card-number font-code">{conscript.draftNumber}</div>
      </div>

      {/* Main content */}
      <div className="conscript-card-content">
        {/* Photo */}
        <div className="conscript-photo-block">
          <div className="conscript-photo">
            {conscript.photo ? (
              <img src={conscript.photo} alt={conscript.fullName} />
            ) : (
              <div className="conscript-photo-placeholder">
                <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                  <path
                    d="M24 24C28.4183 24 32 20.4183 32 16C32 11.5817 28.4183 8 24 8C19.5817 8 16 11.5817 16 16C16 20.4183 19.5817 24 24 24Z"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="square"
                  />
                  <path
                    d="M8 40C8 34.6957 10.1071 29.6086 13.8579 25.8579C17.6086 22.1071 22.6957 20 28 20H20C14.6957 20 9.60859 22.1071 5.85786 25.8579C2.10714 29.6086 0 34.6957 0 40"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="square"
                  />
                </svg>
              </div>
            )}
          </div>

          {/* Photo label */}
          <div className="conscript-photo-label font-mono">ФОТО 3×4</div>

          {/* Status badge */}
          <div className={`conscript-status-badge conscript-status-${conscript.status}`}>
            <div className="status-badge-dot" />
            <span className="status-badge-text font-code">
              {conscript.status === 'pending' && 'ОЖИДАНИЕ'}
              {conscript.status === 'in_progress' && 'ОСМОТР'}
              {conscript.status === 'completed' && 'ЗАВЕРШЁН'}
            </span>
          </div>
        </div>

        {/* Info */}
        <div className="conscript-info-block">
          {/* Full name */}
          <div className="conscript-info-section">
            <div className="conscript-info-label">ФАМИЛИЯ ИМЯ ОТЧЕСТВО</div>
            <div className="conscript-info-value conscript-name font-mono">
              {conscript.fullName}
            </div>
          </div>

          {/* Personal data grid */}
          <div className="conscript-data-grid">
            <div className="conscript-data-item">
              <div className="conscript-data-label">ИИН</div>
              <div className="conscript-data-value font-code">{conscript.iin}</div>
            </div>

            <div className="conscript-data-item">
              <div className="conscript-data-label">ДАТА РОЖДЕНИЯ</div>
              <div className="conscript-data-value font-code">
                {formatDate(conscript.birthDate)}
              </div>
            </div>

            <div className="conscript-data-item">
              <div className="conscript-data-label">ВОЗРАСТ</div>
              <div className="conscript-data-value font-code">
                {calculateAge(conscript.birthDate)} лет
              </div>
            </div>
          </div>

          {/* Medical info */}
          <div className="conscript-medical-info">
            <div className="medical-info-row">
              <span className="medical-info-label">Рост:</span>
              <span className="medical-info-value font-code">178 см</span>
            </div>
            <div className="medical-info-row">
              <span className="medical-info-label">Вес:</span>
              <span className="medical-info-value font-code">75 кг</span>
            </div>
            <div className="medical-info-row">
              <span className="medical-info-label">Группа крови:</span>
              <span className="medical-info-value font-code">II (A) Rh+</span>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <div className="conscript-card-footer">
        <button className="conscript-card-btn">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M2 5.33333H14M5.33333 2V5.33333M10.6667 2V5.33333M2 8V13.3333C2 13.687 2.14048 14.0261 2.39052 14.2761C2.64057 14.5262 2.97971 14.6667 3.33333 14.6667H12.6667C13.0203 14.6667 13.3594 14.5262 13.6095 14.2761C13.8595 14.0261 14 13.687 14 13.3333V8H2Z"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="square"
            />
          </svg>
          <span>История осмотров</span>
        </button>

        <button className="conscript-card-btn">
          <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
            <path
              d="M14 10V12.6667C14 13.0203 13.8595 13.3594 13.6095 13.6095C13.3594 13.8595 13.0203 14 12.6667 14H3.33333C2.97971 14 2.64057 13.8595 2.39052 13.6095C2.14048 13.3594 2 13.0203 2 12.6667V10M4.66667 6.66667L8 10M8 10L11.3333 6.66667M8 10V2"
              stroke="currentColor"
              strokeWidth="1.5"
              strokeLinecap="square"
            />
          </svg>
          <span>Скачать карту</span>
        </button>
      </div>
    </motion.div>
  )
}
