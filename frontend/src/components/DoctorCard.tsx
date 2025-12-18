import { motion } from 'framer-motion'
import './DoctorCard.css'

export interface Doctor {
  id: string
  fullName: string
  specialty: string
  category: string
  experience: number
  education: string
  licenseNumber: string
  photoUrl?: string
  conclusionsCount: number
  accuracyRate: number
  status: 'active' | 'break' | 'offline'
}

interface DoctorCardProps {
  doctor: Doctor
  onClick?: () => void
  compact?: boolean
}

export default function DoctorCard({ doctor, onClick, compact = false }: DoctorCardProps) {
  const statusLabels = {
    active: 'НА СМЕНЕ',
    break: 'ПЕРЕРЫВ',
    offline: 'НЕ В СЕТИ',
  }

  const statusIcons = {
    active: '●',
    break: '◐',
    offline: '○',
  }

  return (
    <motion.div
      className={`doctor-card ${compact ? 'doctor-card-compact' : ''} ${onClick ? 'doctor-card-clickable' : ''}`}
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      onClick={onClick}
    >
      {/* Header */}
      <div className="doctor-card-header">
        <div className="doctor-card-title font-code">КАРТА ВРАЧА</div>
        <div className={`doctor-status-badge doctor-status-${doctor.status}`}>
          <span className="doctor-status-icon">{statusIcons[doctor.status]}</span>
          <span className="doctor-status-text font-code">{statusLabels[doctor.status]}</span>
        </div>
      </div>

      {/* Main content */}
      <div className="doctor-card-content">
        {/* Photo */}
        <div className="doctor-photo-block">
          <div className="doctor-photo">
            {doctor.photoUrl ? (
              <img src={doctor.photoUrl} alt={doctor.fullName} />
            ) : (
              <div className="doctor-photo-placeholder">
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
                  <circle
                    cx="38"
                    cy="10"
                    r="6"
                    fill="var(--color-primary)"
                    stroke="currentColor"
                    strokeWidth="1.5"
                  />
                </svg>
              </div>
            )}
          </div>

          <div className="doctor-photo-label font-mono">ФОТО ВРАЧА</div>

          {/* License badge */}
          <div className="doctor-license-badge">
            <div className="doctor-license-label">№ ЛИЦЕНЗИИ</div>
            <div className="doctor-license-number font-code">{doctor.licenseNumber}</div>
          </div>
        </div>

        {/* Info */}
        <div className="doctor-info-block">
          {/* Full name */}
          <div className="doctor-info-section">
            <div className="doctor-info-label">ФАМИЛИЯ ИМЯ ОТЧЕСТВО</div>
            <div className="doctor-info-value doctor-name font-mono">{doctor.fullName}</div>
          </div>

          {/* Specialty & Category */}
          <div className="doctor-data-grid">
            <div className="doctor-data-item">
              <div className="doctor-data-label">СПЕЦИАЛЬНОСТЬ</div>
              <div className="doctor-data-value">{doctor.specialty}</div>
            </div>

            <div className="doctor-data-item">
              <div className="doctor-data-label">КАТЕГОРИЯ</div>
              <div className="doctor-data-value">
                <span className="doctor-category-badge font-code">{doctor.category}</span>
              </div>
            </div>
          </div>

          {/* Experience & Education */}
          {!compact && (
            <>
              <div className="doctor-data-grid">
                <div className="doctor-data-item">
                  <div className="doctor-data-label">СТАЖ РАБОТЫ</div>
                  <div className="doctor-data-value font-code">
                    {doctor.experience} {doctor.experience === 1 ? 'год' : doctor.experience < 5 ? 'года' : 'лет'}
                  </div>
                </div>

                <div className="doctor-data-item">
                  <div className="doctor-data-label">ОСМОТРОВ СЕГОДНЯ</div>
                  <div className="doctor-data-value font-code">{doctor.conclusionsCount}</div>
                </div>
              </div>

              {/* Education */}
              <div className="doctor-education-box">
                <div className="doctor-education-label">ОБРАЗОВАНИЕ</div>
                <div className="doctor-education-value">{doctor.education}</div>
              </div>

              {/* Stats */}
              <div className="doctor-stats-box">
                <div className="doctor-stat-item">
                  <div className="doctor-stat-label">Точность AI-проверки</div>
                  <div className="doctor-stat-bar">
                    <motion.div
                      className="doctor-stat-fill"
                      initial={{ width: 0 }}
                      animate={{ width: `${doctor.accuracyRate * 100}%` }}
                      transition={{ duration: 1, ease: 'easeOut' }}
                      style={{
                        background:
                          doctor.accuracyRate >= 0.95
                            ? 'var(--color-primary)'
                            : doctor.accuracyRate >= 0.85
                            ? 'var(--color-warning)'
                            : 'var(--color-danger)',
                      }}
                    />
                  </div>
                  <div className="doctor-stat-value font-code">
                    {Math.round(doctor.accuracyRate * 100)}%
                  </div>
                </div>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Footer (only for non-compact) */}
      {!compact && (
        <div className="doctor-card-footer">
          <button className="doctor-card-btn">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path
                d="M2 5.33333H14M5.33333 2V5.33333M10.6667 2V5.33333M2 8V13.3333C2 13.687 2.14048 14.0261 2.39052 14.2761C2.64057 14.5262 2.97971 14.6667 3.33333 14.6667H12.6667C13.0203 14.6667 13.3594 14.5262 13.6095 14.2761C13.8595 14.0261 14 13.687 14 13.3333V8H2Z"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="square"
              />
            </svg>
            <span>История заключений</span>
          </button>

          <button className="doctor-card-btn">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path
                d="M8 14C11.3137 14 14 11.3137 14 8C14 4.68629 11.3137 2 8 2C4.68629 2 2 4.68629 2 8C2 11.3137 4.68629 14 8 14Z"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="square"
              />
              <path
                d="M8 5.33333V8H10.6667"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="square"
              />
            </svg>
            <span>График работы</span>
          </button>
        </div>
      )}
    </motion.div>
  )
}
