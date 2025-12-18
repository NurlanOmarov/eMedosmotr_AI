import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import './ChairmanDashboard.css'

// Типы данных для дэшборда
interface DashboardStats {
  totalConscripts: number
  inProgress: number
  sentToAdditional: number
  canceled: number
  passedRegional: number
  passedNational: number
  passedMedical: number
}

interface CategoryStats {
  suitable: number
  suitableWithLimitations: number
  limitedSuitable: number
  temporarilyUnsuitable: number
  unsuitable: number
  notSuitable: number
  notSuitableExcluded: number
  sentToExam: number
}

interface SpecialistWorkload {
  name: string
  specialty: string
  completed: number
  inProgress: number
  pending: number
  total: number
}

interface DiagnosisTop {
  category: string
  count: number
  percentage: number
}

interface DispenseryStat {
  name: string
  count: number
}

// МОК ДАННЫЕ
const mockDashboardStats: DashboardStats = {
  totalConscripts: 248,
  inProgress: 42,
  sentToAdditional: 18,
  canceled: 5,
  passedRegional: 89,
  passedNational: 34,
  passedMedical: 183,
}

const mockCategoryStats: CategoryStats = {
  suitable: 98,
  suitableWithLimitations: 45,
  limitedSuitable: 32,
  temporarilyUnsuitable: 28,
  unsuitable: 15,
  notSuitable: 12,
  notSuitableExcluded: 8,
  sentToExam: 10,
}

const mockSpecialistWorkload: SpecialistWorkload[] = [
  {
    name: 'Смирнова А.В.',
    specialty: 'Терапевт',
    completed: 198,
    inProgress: 28,
    pending: 22,
    total: 248,
  },
  {
    name: 'Казаков И.П.',
    specialty: 'Хирург',
    completed: 185,
    inProgress: 35,
    pending: 28,
    total: 248,
  },
  {
    name: 'Назарбаева К.М.',
    specialty: 'Офтальмолог',
    completed: 212,
    inProgress: 18,
    pending: 18,
    total: 248,
  },
  {
    name: 'Абишева Р.К.',
    specialty: 'Невролог',
    completed: 175,
    inProgress: 42,
    pending: 31,
    total: 248,
  },
  {
    name: 'Жумагулов Б.С.',
    specialty: 'Отоларинголог',
    completed: 188,
    inProgress: 32,
    pending: 28,
    total: 248,
  },
  {
    name: 'Сарсенова М.А.',
    specialty: 'Дерматолог',
    completed: 195,
    inProgress: 28,
    pending: 25,
    total: 248,
  },
  {
    name: 'Тулегенова Г.К.',
    specialty: 'Психиатр',
    completed: 220,
    inProgress: 15,
    pending: 13,
    total: 248,
  },
  {
    name: 'Ахметова С.Н.',
    specialty: 'Стоматолог',
    completed: 205,
    inProgress: 22,
    pending: 21,
    total: 248,
  },
  {
    name: 'Досымбеков К.А.',
    specialty: 'Фтизиатр',
    completed: 190,
    inProgress: 30,
    pending: 28,
    total: 248,
  },
]

const mockDiagnosisTop: DiagnosisTop[] = [
  { category: 'Здоров (годен)', count: 98, percentage: 39.5 },
  { category: 'Плоскостопие', count: 32, percentage: 12.9 },
  { category: 'Миопия средней степени', count: 28, percentage: 11.3 },
  { category: 'Хронические заболевания ЖКТ', count: 25, percentage: 10.1 },
  { category: 'Сколиоз I-II степени', count: 22, percentage: 8.9 },
  { category: 'Астигматизм', count: 18, percentage: 7.3 },
  { category: 'Хронический тонзиллит', count: 15, percentage: 6.0 },
  { category: 'Аллергические реакции', count: 10, percentage: 4.0 },
]

const mockDispenseryStat: DispenseryStat[] = [
  { name: 'Наркология', count: 3 },
  { name: 'Психиатрия', count: 8 },
  { name: 'Туберкулёз', count: 2 },
  { name: 'Кожвен', count: 5 },
  { name: 'По общим заболеваниям', count: 47 },
]

// Данные для графика направленных на доп. обследование
const mockSpecialistExaminations: { specialty: string; count: number }[] = [
  { specialty: 'Смирнова А.В. (Терапевт)', count: 3 },
  { specialty: 'Казаков И.П. (Хирург)', count: 5 },
  { specialty: 'Назарбаева К.М. (Офтальмолог)', count: 2 },
  { specialty: 'Петрова Е.С. (Невролог)', count: 4 },
  { specialty: 'Ахметов Б.К. (Психиатр)', count: 1 },
  { specialty: 'Иванов С.П. (ЛОР)', count: 2 },
  { specialty: 'Сергеев М.А. (Стоматолог)', count: 0 },
  { specialty: 'Кузнецова О.И. (Дерматолог)', count: 1 },
]

export default function ChairmanDashboard() {
  const [selectedPeriod, setSelectedPeriod] = useState<'today' | 'week' | 'month'>('today')

  // Вычисления для графиков
  const processCompletionPercentage = useMemo(() => {
    const completed = mockDashboardStats.passedRegional + mockDashboardStats.passedMedical
    return Math.round((completed / mockDashboardStats.totalConscripts) * 100)
  }, [])

  const categoryChartData = useMemo(() => {
    return [
      { label: 'Годен', value: mockCategoryStats.suitable, color: '#4ade80' },
      { label: 'Годен с незнач. огр.', value: mockCategoryStats.suitableWithLimitations, color: '#60a5fa' },
      { label: 'Ограниченно годен', value: mockCategoryStats.limitedSuitable, color: '#facc15' },
      { label: 'Временно не годен', value: mockCategoryStats.temporarilyUnsuitable, color: '#fb923c' },
      { label: 'Не годен', value: mockCategoryStats.unsuitable, color: '#f87171' },
    ].filter(item => item.value > 0)
  }, [])

  const totalCategories = useMemo(() => {
    return categoryChartData.reduce((sum, item) => sum + item.value, 0)
  }, [categoryChartData])

  return (
    <div className="chairman-dashboard">
      {/* Заголовок дэшборда */}
      <motion.div
        className="dashboard-header"
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3 }}
      >
        <div className="dashboard-title-section">
          <h1 className="dashboard-title font-code">ПАНЕЛЬ ПРЕДСЕДАТЕЛЯ ВВК</h1>
          <p className="dashboard-subtitle">Аналитика и мониторинг процесса медосмотра призывников</p>
        </div>

        <div className="dashboard-period-selector">
          <button
            className={`period-btn ${selectedPeriod === 'today' ? 'active' : ''}`}
            onClick={() => setSelectedPeriod('today')}
          >
            Сегодня
          </button>
          <button
            className={`period-btn ${selectedPeriod === 'week' ? 'active' : ''}`}
            onClick={() => setSelectedPeriod('week')}
          >
            Неделя
          </button>
          <button
            className={`period-btn ${selectedPeriod === 'month' ? 'active' : ''}`}
            onClick={() => setSelectedPeriod('month')}
          >
            Месяц
          </button>
        </div>
      </motion.div>

      {/* Основные метрики */}
      <div className="dashboard-grid">
        {/* Процесс прохождения медосмотра */}
        <motion.div
          className="dashboard-card card-primary"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.1 }}
        >
          <div className="card-header">
            <h2 className="card-title">Процесс прохождения медосмотра</h2>
            <div className="card-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <path d="M9 11L12 14L22 4" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M21 12V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V5C3 4.46957 3.21071 3.96086 3.58579 3.58579C3.96086 3.21071 4.46957 3 5 3H16" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
          </div>
          <div className="stats-grid-5">
            <div className="stat-item">
              <div className="stat-value">{mockDashboardStats.totalConscripts}</div>
              <div className="stat-label">Всего призывников</div>
            </div>
            <div className="stat-item accent-blue">
              <div className="stat-value">{mockDashboardStats.inProgress}</div>
              <div className="stat-label">Проходят медосмотр</div>
            </div>
            <div className="stat-item accent-purple">
              <div className="stat-value">{mockDashboardStats.sentToAdditional}</div>
              <div className="stat-label">Направлены на доп. обследование</div>
            </div>
            <div className="stat-item accent-gray">
              <div className="stat-value">{mockDashboardStats.canceled}</div>
              <div className="stat-label">Отменен</div>
            </div>
            <div className="stat-item accent-green">
              <div className="stat-value">{mockDashboardStats.passedRegional}</div>
              <div className="stat-label">Прошли приём врачей (область)</div>
            </div>
            <div className="stat-item accent-orange">
              <div className="stat-value">{mockDashboardStats.passedNational}</div>
              <div className="stat-label">Прошёл приём начмеда</div>
            </div>
            <div className="stat-item accent-teal">
              <div className="stat-value">{mockDashboardStats.passedMedical}</div>
              <div className="stat-label">Прошли медкомиссию (область)</div>
            </div>
          </div>
        </motion.div>

        {/* Категория годности (КМК) */}
        <motion.div
          className="dashboard-card"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.15 }}
        >
          <div className="card-header">
            <h2 className="card-title">Категория годности (КМК)</h2>
            <div className="card-icon">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="2"/>
                <path d="M12 6V12L16 14" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
              </svg>
            </div>
          </div>
          <div className="category-stats">
            <div className="category-chart">
              {totalCategories > 0 ? (
                <div className="pie-chart">
                  <svg viewBox="0 0 200 200" className="pie-svg">
                    {categoryChartData.reduce((acc, item, index) => {
                      const percentage = (item.value / totalCategories) * 100
                      const startAngle = index === 0 ? 0 : acc.endAngle
                      const angle = (percentage / 100) * 360
                      const endAngle = startAngle + angle

                      const x1 = 100 + 80 * Math.cos((Math.PI * startAngle) / 180)
                      const y1 = 100 + 80 * Math.sin((Math.PI * startAngle) / 180)
                      const x2 = 100 + 80 * Math.cos((Math.PI * endAngle) / 180)
                      const y2 = 100 + 80 * Math.sin((Math.PI * endAngle) / 180)
                      const largeArc = angle > 180 ? 1 : 0

                      const path = `M 100 100 L ${x1} ${y1} A 80 80 0 ${largeArc} 1 ${x2} ${y2} Z`

                      acc.paths.push(
                        <path
                          key={item.label}
                          d={path}
                          fill={item.color}
                          className="pie-slice"
                        />
                      )
                      acc.endAngle = endAngle
                      return acc
                    }, { paths: [] as JSX.Element[], endAngle: 0 }).paths}
                    <circle cx="100" cy="100" r="50" fill="#0f172a" />
                    <text x="100" y="95" textAnchor="middle" className="pie-center-text">
                      {totalCategories}
                    </text>
                    <text x="100" y="110" textAnchor="middle" className="pie-center-label">
                      всего
                    </text>
                  </svg>
                </div>
              ) : (
                <div className="no-data">Нет данных</div>
              )}
            </div>
            <div className="category-legend">
              {categoryChartData.map(item => (
                <div key={item.label} className="legend-item">
                  <div className="legend-color" style={{ backgroundColor: item.color }}></div>
                  <div className="legend-label">{item.label}</div>
                  <div className="legend-value">{item.value}</div>
                </div>
              ))}
            </div>
          </div>
        </motion.div>

        {/* Число направленных на доп. обследование по каждому члену медкомиссии */}
        <motion.div
          className="dashboard-card card-wide"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.2 }}
        >
          <div className="card-header">
            <h2 className="card-title">Число направленных на доп. обследование призывников по каждому члену медкомиссии</h2>
          </div>
          <div className="specialist-chart">
            <div className="bar-chart">
              {mockSpecialistExaminations.map((item, index) => {
                const maxCount = Math.max(...mockSpecialistExaminations.map(s => s.count))
                const heightPercentage = (item.count / maxCount) * 100

                return (
                  <div key={index} className="bar-item">
                    <div className="bar-wrapper">
                      <motion.div
                        className="bar"
                        initial={{ height: 0 }}
                        animate={{ height: `${heightPercentage}%` }}
                        transition={{ duration: 0.5, delay: 0.3 + index * 0.1 }}
                      >
                        <span className="bar-value">{item.count}</span>
                      </motion.div>
                    </div>
                    <div className="bar-label">{item.specialty}</div>
                  </div>
                )
              })}
            </div>
          </div>
        </motion.div>

        {/* Загруженность врачей-специалистов */}
        <motion.div
          className="dashboard-card card-table"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.25 }}
        >
          <div className="card-header">
            <h2 className="card-title">Загруженность врачей-специалистов</h2>
          </div>
          <div className="workload-table">
            <table>
              <thead>
                <tr>
                  <th>Специалист</th>
                  <th>Специальность</th>
                  <th>Завершено</th>
                  <th>В работе</th>
                  <th>Ожидает</th>
                  <th>Всего</th>
                  <th>Прогресс</th>
                </tr>
              </thead>
              <tbody>
                {mockSpecialistWorkload.map((specialist, index) => {
                  const progressPercentage = (specialist.completed / specialist.total) * 100

                  return (
                    <tr key={index}>
                      <td className="specialist-name">{specialist.name}</td>
                      <td className="specialist-specialty">{specialist.specialty}</td>
                      <td className="stat-completed">{specialist.completed}</td>
                      <td className="stat-in-progress">{specialist.inProgress}</td>
                      <td className="stat-pending">{specialist.pending}</td>
                      <td className="stat-total">{specialist.total}</td>
                      <td className="progress-cell">
                        <div className="progress-bar">
                          <motion.div
                            className="progress-fill"
                            initial={{ width: 0 }}
                            animate={{ width: `${progressPercentage}%` }}
                            transition={{ duration: 0.5, delay: 0.3 + index * 0.05 }}
                          />
                        </div>
                        <span className="progress-text">{Math.round(progressPercentage)}%</span>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        </motion.div>

        {/* Топ диагнозов по заключениям (КМК) */}
        <motion.div
          className="dashboard-card"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.3 }}
        >
          <div className="card-header">
            <h2 className="card-title">Топ диагнозов по заключениям (КМК)</h2>
          </div>
          <div className="diagnosis-list">
            {mockDiagnosisTop.map((diagnosis, index) => (
              <div key={index} className="diagnosis-item">
                <div className="diagnosis-rank">#{index + 1}</div>
                <div className="diagnosis-info">
                  <div className="diagnosis-name">{diagnosis.category}</div>
                  <div className="diagnosis-stats">
                    <span className="diagnosis-count">{diagnosis.count} чел.</span>
                    <span className="diagnosis-percentage">{diagnosis.percentage}%</span>
                  </div>
                </div>
                <div className="diagnosis-bar">
                  <motion.div
                    className="diagnosis-bar-fill"
                    initial={{ width: 0 }}
                    animate={{ width: `${diagnosis.percentage}%` }}
                    transition={{ duration: 0.5, delay: 0.4 + index * 0.1 }}
                  />
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Топ диагнозов по категориям (КМК) */}
        <motion.div
          className="dashboard-card"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.35 }}
        >
          <div className="card-header">
            <h2 className="card-title">Топ диагнозов по категориям (КМК)</h2>
          </div>
          <div className="diagnosis-list">
            {mockDiagnosisTop.map((diagnosis, index) => (
              <div key={index} className="diagnosis-item">
                <div className="diagnosis-rank">#{index + 1}</div>
                <div className="diagnosis-info">
                  <div className="diagnosis-name">{diagnosis.category}</div>
                  <div className="diagnosis-stats">
                    <span className="diagnosis-count">{diagnosis.count} чел.</span>
                    <span className="diagnosis-percentage">{diagnosis.percentage}%</span>
                  </div>
                </div>
                <div className="diagnosis-bar">
                  <motion.div
                    className="diagnosis-bar-fill"
                    initial={{ width: 0 }}
                    animate={{ width: `${diagnosis.percentage}%` }}
                    transition={{ duration: 0.5, delay: 0.5 + index * 0.1 }}
                  />
                </div>
              </div>
            ))}
          </div>
        </motion.div>

        {/* Количество пациентов состоящих на Д-учёте */}
        <motion.div
          className="dashboard-card"
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.4 }}
        >
          <div className="card-header">
            <h2 className="card-title">Количество пациентов состоящих на Д-учёте</h2>
          </div>
          <div className="dispensery-stats">
            {mockDispenseryStat.map((stat, index) => (
              <div key={index} className="dispensery-item">
                <div className="dispensery-label">{stat.name}</div>
                <div className="dispensery-value">{stat.count}</div>
              </div>
            ))}
          </div>
        </motion.div>
      </div>
    </div>
  )
}
