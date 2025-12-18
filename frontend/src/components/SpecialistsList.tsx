import { useState, useMemo, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { useData } from '../contexts/DataContext'
import './SpecialistsList.css'

// Типы данных
interface SpecialistExamination {
  conscriptId: string
  conscriptName: string
  conscriptIIN: string
  examinationDate: string
  diagnosis: string
  category: string
  status: 'completed' | 'in_progress' | 'pending'
}

interface Specialist {
  id: string
  name: string
  specialty: string
  avatar?: string
  totalExaminations: number
  completed: number
  inProgress: number
  pending: number
  examinations: SpecialistExamination[]
}

// Список специалистов
const specialistProfiles = [
  { id: '1', name: 'Смирнова А.В.', specialty: 'Терапевт', avatar: '/smirnova-doctor.png' },
  { id: '2', name: 'Казаков И.П.', specialty: 'Хирург', avatar: '/kazakov-doctor.png' },
  { id: '3', name: 'Назарбаева К.М.', specialty: 'Офтальмолог', avatar: '/nazarbayeva-doctor.png' },
  { id: '4', name: 'Абишева Р.К.', specialty: 'Невролог', avatar: '/abisheva-doctor.png' },
  { id: '5', name: 'Жумагулов Б.С.', specialty: 'Отоларинголог', avatar: '/zhumagulov-doctor.png' },
  { id: '6', name: 'Сарсенова М.А.', specialty: 'Дерматолог', avatar: '/sarsenova-doctor.png' },
  { id: '7', name: 'Тулегенова Г.К.', specialty: 'Психиатр', avatar: '/tulegenova-doctor.png' },
  { id: '8', name: 'Ахметова С.Н.', specialty: 'Стоматолог', avatar: '/akhmetova-doctor.png' },
  { id: '9', name: 'Досымбеков К.А.', specialty: 'Фтизиатр', avatar: '/dosymbekov-doctor.png' },
]

export default function SpecialistsList() {
  const { getConscriptsBySpecialist, getSpecialistStats } = useData()
  const [selectedSpecialist, setSelectedSpecialist] = useState<Specialist | null>(null)
  const [searchQuery, setSearchQuery] = useState('')

  // Состояние для статистики специалистов
  const [specialistsStats, setSpecialistsStats] = useState<Record<string, any>>({})

  // Загружаем статистику специалистов асинхронно
  useEffect(() => {
    const loadStats = async () => {
      const statsPromises = specialistProfiles.map(async (profile) => {
        const stats = await getSpecialistStats(profile.specialty)
        return { specialty: profile.specialty, stats }
      })

      const results = await Promise.all(statsPromises)
      const statsMap: Record<string, any> = {}
      results.forEach(({ specialty, stats }) => {
        statsMap[specialty] = stats
      })
      setSpecialistsStats(statsMap)
    }

    loadStats()
  }, [getSpecialistStats])

  // Генерируем список специалистов с динамическими данными из Context
  const specialists = useMemo(() => {
    return specialistProfiles.map(profile => {
      const examinations = getConscriptsBySpecialist(profile.specialty)
      const stats = specialistsStats[profile.specialty] || {
        totalExaminations: 0,
        completed: 0,
        inProgress: 0,
        pending: 0,
      }

      return {
        id: profile.id,
        name: profile.name,
        specialty: profile.specialty,
        avatar: profile.avatar,
        totalExaminations: stats.totalExaminations,
        completed: stats.completed,
        inProgress: stats.inProgress,
        pending: stats.pending,
        examinations,
      }
    })
  }, [getConscriptsBySpecialist, specialistsStats])

  // Фильтрация по поиску
  const filteredSpecialists = specialists.filter(specialist =>
    specialist.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    specialist.specialty.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return '#10b981'
      case 'in_progress': return '#3b82f6'
      case 'pending': return '#f97316'
      default: return '#64748b'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'completed': return 'Завершено'
      case 'in_progress': return 'В процессе'
      case 'pending': return 'Ожидает'
      default: return 'Неизвестно'
    }
  }

  return (
    <>
      <div className="specialists-list">
        {/* Заголовок */}
        <div className="specialists-header">
          <div className="specialists-title-section">
            <h1 className="specialists-title font-code">ВРАЧИ-СПЕЦИАЛИСТЫ</h1>
            <p className="specialists-subtitle">Просмотр работы и результатов освидетельствования</p>
          </div>

          {/* Поиск */}
          <div className="specialists-search">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="search-icon">
              <path
                d="M9 17A8 8 0 1 0 9 1a8 8 0 0 0 0 16zM19 19l-4.35-4.35"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
            <input
              type="text"
              placeholder="Поиск по имени или специальности..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="search-input"
            />
          </div>
        </div>

        {/* Сетка специалистов */}
        <div className="specialists-grid">
          {filteredSpecialists.map((specialist, index) => {
            const progressPercentage = (specialist.completed / specialist.totalExaminations) * 100

            return (
              <motion.div
                key={specialist.id}
                className="specialist-card"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, delay: index * 0.05 }}
                onClick={() => setSelectedSpecialist(specialist)}
              >
                <div className="specialist-card-header">
                  <div className="specialist-avatar">
                    {specialist.avatar ? (
                      <img src={specialist.avatar} alt={specialist.name} />
                    ) : (
                      <div className="specialist-avatar-placeholder">
                        {specialist.name.split(' ').map(n => n[0]).join('')}
                      </div>
                    )}
                  </div>
                  <div className="specialist-info">
                    <h3 className="specialist-name">{specialist.name}</h3>
                    <p className="specialist-specialty">{specialist.specialty}</p>
                  </div>
                </div>

                <div className="specialist-stats">
                  <div className="stat-row">
                    <span className="stat-label">Всего осмотров:</span>
                    <span className="stat-value">{specialist.totalExaminations}</span>
                  </div>
                  <div className="stat-row">
                    <span className="stat-label">Завершено:</span>
                    <span className="stat-value stat-completed">{specialist.completed}</span>
                  </div>
                  <div className="stat-row">
                    <span className="stat-label">В работе:</span>
                    <span className="stat-value stat-in-progress">{specialist.inProgress}</span>
                  </div>
                  <div className="stat-row">
                    <span className="stat-label">Ожидает:</span>
                    <span className="stat-value stat-pending">{specialist.pending}</span>
                  </div>
                </div>

                {/* Категории годности */}
                {specialist.examinations.length > 0 && (
                  <div className="specialist-categories" style={{
                    marginBottom: '1rem',
                    padding: '1rem',
                    background: 'rgba(30, 41, 59, 0.3)',
                    borderRadius: '10px',
                    border: '1px solid rgba(59, 130, 246, 0.1)',
                  }}>
                    <div style={{ marginBottom: '0.5rem', fontSize: '0.85rem', color: '#94a3b8', fontWeight: 500 }}>
                      Категории годности:
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                      {Array.from(new Set(specialist.examinations.map(e => e.category).filter(Boolean))).map((category, idx) => (
                        <span key={idx} className="category-badge">
                          {category}
                        </span>
                      ))}
                      {Array.from(new Set(specialist.examinations.map(e => e.category).filter(Boolean))).length === 0 && (
                        <span style={{ color: '#64748b', fontSize: '0.85rem' }}>Нет данных</span>
                      )}
                    </div>
                  </div>
                )}

                <div className="specialist-progress">
                  <div className="progress-info">
                    <span className="progress-label">Прогресс</span>
                    <span className="progress-percentage">{Math.round(progressPercentage)}%</span>
                  </div>
                  <div className="progress-bar">
                    <motion.div
                      className="progress-fill"
                      initial={{ width: 0 }}
                      animate={{ width: `${progressPercentage}%` }}
                      transition={{ duration: 0.5, delay: 0.2 + index * 0.05 }}
                    />
                  </div>
                </div>

                <button className="view-details-btn">
                  <span>Просмотр результатов</span>
                  <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                    <path
                      d="M6 12L10 8L6 4"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                </button>
              </motion.div>
            )
          })}
        </div>
      </div>

      {/* Модальное окно */}
      <AnimatePresence>
        {selectedSpecialist && (
          <>
            {/* Backdrop */}
            <motion.div
              className="specialist-modal-backdrop"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setSelectedSpecialist(null)}
            />

            {/* Modal Container */}
            <motion.div
              className="specialist-modal-container"
              initial={{ opacity: 0, scale: 0.95, y: 20 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              exit={{ opacity: 0, scale: 0.95, y: 20 }}
              transition={{ type: 'spring', damping: 25, stiffness: 300 }}
            >
              <div className="specialist-modal">
                <div className="modal-header">
                  <div className="modal-header-left">
                    <div className="modal-specialist-avatar">
                      {selectedSpecialist.avatar ? (
                        <img src={selectedSpecialist.avatar} alt={selectedSpecialist.name} />
                      ) : (
                        <div className="specialist-avatar-placeholder">
                          {selectedSpecialist.name.split(' ').map(n => n[0]).join('')}
                        </div>
                      )}
                    </div>
                    <div className="modal-title-section">
                      <h2 className="modal-title">Результаты освидетельствования</h2>
                      <p className="modal-subtitle">
                        {selectedSpecialist.name} • {selectedSpecialist.specialty}
                      </p>
                    </div>
                  </div>
                  <button className="modal-close" onClick={() => setSelectedSpecialist(null)}>
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                      <path
                        d="M18 6L6 18M6 6l12 12"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                      />
                    </svg>
                  </button>
                </div>

                <div className="modal-content">
                  <div className="examinations-table">
                    <table>
                      <thead>
                        <tr>
                          <th>Призывник</th>
                          <th>ИИН</th>
                          <th>Дата осмотра</th>
                          <th>Диагноз</th>
                          <th>Категория</th>
                          <th>Статус</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedSpecialist.examinations.map((exam, index) => (
                          <motion.tr
                            key={index}
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.05 }}
                          >
                            <td className="exam-conscript-name">{exam.conscriptName}</td>
                            <td className="exam-iin">{exam.conscriptIIN}</td>
                            <td className="exam-date">
                              {new Date(exam.examinationDate).toLocaleString('ru-RU', {
                                day: '2-digit',
                                month: '2-digit',
                                year: 'numeric',
                                hour: '2-digit',
                                minute: '2-digit',
                              })}
                            </td>
                            <td className="exam-diagnosis">{exam.diagnosis}</td>
                            <td className="exam-category">
                              <span className="category-badge">{exam.category}</span>
                            </td>
                            <td className="exam-status">
                              <span
                                className="status-badge"
                                style={{ backgroundColor: getStatusColor(exam.status) }}
                              >
                                {getStatusLabel(exam.status)}
                              </span>
                            </td>
                          </motion.tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  )
}
