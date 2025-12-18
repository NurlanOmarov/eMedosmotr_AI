import { useState, useEffect } from 'react'
import './DentistChart.css'

interface DentistChartProps {
  value: Record<string, string> | null
  onChange: (value: Record<string, string>) => void
  disabled?: boolean
}

// Зубная формула: 32 зуба взрослого человека
// Верхняя челюсть: 18-11 (справа налево), 21-28 (слева направо)
// Нижняя челюсть: 48-41 (справа налево), 31-38 (слева направо)
const TEETH_UPPER_RIGHT = ['18', '17', '16', '15', '14', '13', '12', '11']
const TEETH_UPPER_LEFT = ['21', '22', '23', '24', '25', '26', '27', '28']
const TEETH_LOWER_RIGHT = ['48', '47', '46', '45', '44', '43', '42', '41']
const TEETH_LOWER_LEFT = ['31', '32', '33', '34', '35', '36', '37', '38']

// Коды состояния зубов
const TOOTH_STATUS = [
  { code: '', label: 'Норма' },
  { code: 'C', label: 'Кариес' },
  { code: 'P', label: 'Пломба' },
  { code: 'X', label: 'Удален' },
  { code: 'K', label: 'Коронка' },
  { code: 'I', label: 'Имплант' },
  { code: 'M', label: 'Требует лечения' },
]

const DentistChart = ({ value, onChange, disabled = false }: DentistChartProps) => {
  // Инициализируем состояние зубов
  const [teethData, setTeethData] = useState<Record<string, string>>(() => {
    if (value && typeof value === 'object') {
      return value
    }
    // Если нет данных, создаем пустую формулу для всех 32 зубов
    const initialData: Record<string, string> = {}
    ;[...TEETH_UPPER_RIGHT, ...TEETH_UPPER_LEFT, ...TEETH_LOWER_RIGHT, ...TEETH_LOWER_LEFT].forEach(tooth => {
      initialData[tooth] = ''
    })
    return initialData
  })

  // Обновляем состояние при изменении value извне
  useEffect(() => {
    if (value && typeof value === 'object') {
      setTeethData(value)
    }
  }, [value])

  const handleToothChange = (toothNumber: string, status: string) => {
    if (disabled) return

    const newData = { ...teethData, [toothNumber]: status }
    setTeethData(newData)
    onChange(newData)
  }

  const renderTooth = (toothNumber: string) => {
    const status = teethData[toothNumber] || ''
    const statusLabel = TOOTH_STATUS.find(s => s.code === status)?.label || 'Норма'

    return (
      <div key={toothNumber} className="tooth-item">
        <div className="tooth-number">{toothNumber}</div>
        <select
          className={`tooth-status ${status ? 'tooth-status-filled' : ''}`}
          value={status}
          onChange={(e) => handleToothChange(toothNumber, e.target.value)}
          disabled={disabled}
          title={statusLabel}
        >
          {TOOTH_STATUS.map(s => (
            <option key={s.code} value={s.code}>
              {s.label}
            </option>
          ))}
        </select>
      </div>
    )
  }

  return (
    <div className="dentist-chart">
      <div className="dentist-chart-legend">
        <div className="legend-title">Обозначения:</div>
        {TOOTH_STATUS.map(s => (
          <div key={s.code} className="legend-item">
            <span className="legend-code">{s.code || '—'}</span> — {s.label}
          </div>
        ))}
      </div>

      <div className="dentist-chart-grid">
        {/* Верхняя челюсть */}
        <div className="jaw-section jaw-upper">
          <div className="jaw-label">Верхняя челюсть</div>
          <div className="teeth-row">
            <div className="teeth-side">
              {TEETH_UPPER_RIGHT.map(renderTooth)}
            </div>
            <div className="teeth-divider" />
            <div className="teeth-side">
              {TEETH_UPPER_LEFT.map(renderTooth)}
            </div>
          </div>
        </div>

        {/* Нижняя челюсть */}
        <div className="jaw-section jaw-lower">
          <div className="teeth-row">
            <div className="teeth-side">
              {TEETH_LOWER_RIGHT.map(renderTooth)}
            </div>
            <div className="teeth-divider" />
            <div className="teeth-side">
              {TEETH_LOWER_LEFT.map(renderTooth)}
            </div>
          </div>
          <div className="jaw-label">Нижняя челюсть</div>
        </div>
      </div>

      {!disabled && (
        <div className="dentist-chart-hint">
          Выберите состояние для каждого зуба. Пустое значение означает здоровый зуб.
        </div>
      )}
    </div>
  )
}

export default DentistChart
