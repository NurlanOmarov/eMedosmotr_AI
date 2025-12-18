import { motion, AnimatePresence } from 'framer-motion'
import { useState } from 'react'
import './ConscriptFilter.css'

interface FilterValues {
  fullName: string
  iin: string
  medicalCommissionDateFrom: string
  medicalCommissionDateTo: string
  status: string
  draftDistrict: string
}

interface ConscriptFilterProps {
  isOpen: boolean
  onClose: () => void
  onApply: (filters: FilterValues) => void
  onReset: () => void
}

export default function ConscriptFilter({
  isOpen,
  onClose,
  onApply,
  onReset,
}: ConscriptFilterProps) {
  const [filters, setFilters] = useState<FilterValues>({
    fullName: '',
    iin: '',
    medicalCommissionDateFrom: '',
    medicalCommissionDateTo: '',
    status: '',
    draftDistrict: '',
  })

  const handleChange = (field: keyof FilterValues, value: string) => {
    setFilters((prev) => ({ ...prev, [field]: value }))
  }

  const handleApply = () => {
    onApply(filters)
    onClose()
  }

  const handleReset = () => {
    setFilters({
      fullName: '',
      iin: '',
      medicalCommissionDateFrom: '',
      medicalCommissionDateTo: '',
      status: '',
      draftDistrict: '',
    })
    onReset()
  }

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="filter-panel"
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="filter-content">
            <div className="filter-header">
              <div className="filter-title font-code">ФИЛЬТРЫ</div>
              <button className="filter-close" onClick={onClose}>
                <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                  <path
                    d="M12 4L4 12M4 4L12 12"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="square"
                  />
                </svg>
              </button>
            </div>

            <div className="filter-grid">
              <div className="filter-field">
                <label className="filter-label">ФИО</label>
                <input
                  type="text"
                  className="filter-input"
                  placeholder="Поиск по ФИО"
                  value={filters.fullName}
                  onChange={(e) => handleChange('fullName', e.target.value)}
                />
              </div>

              <div className="filter-field">
                <label className="filter-label">ИИН</label>
                <input
                  type="text"
                  className="filter-input font-code"
                  placeholder="000000000000"
                  value={filters.iin}
                  onChange={(e) => handleChange('iin', e.target.value)}
                  maxLength={12}
                />
              </div>

              <div className="filter-field">
                <label className="filter-label">Дата медкомиссии от</label>
                <input
                  type="date"
                  className="filter-input font-code"
                  value={filters.medicalCommissionDateFrom}
                  onChange={(e) => handleChange('medicalCommissionDateFrom', e.target.value)}
                />
              </div>

              <div className="filter-field">
                <label className="filter-label">Дата медкомиссии до</label>
                <input
                  type="date"
                  className="filter-input font-code"
                  value={filters.medicalCommissionDateTo}
                  onChange={(e) => handleChange('medicalCommissionDateTo', e.target.value)}
                />
              </div>

              <div className="filter-field">
                <label className="filter-label">Призывной пункт</label>
                <select
                  className="filter-select"
                  value={filters.draftDistrict}
                  onChange={(e) => handleChange('draftDistrict', e.target.value)}
                >
                  <option value="">Все районы</option>
                  <option value="Каратальский район">Каратальский район</option>
                  <option value="Алакольский район">Алакольский район</option>
                  <option value="Уржарский район">Уржарский район</option>
                  <option value="Аксуатский район">Аксуатский район</option>
                </select>
              </div>

              <div className="filter-field">
                <label className="filter-label">Статус</label>
                <select
                  className="filter-select"
                  value={filters.status}
                  onChange={(e) => handleChange('status', e.target.value)}
                >
                  <option value="">Все</option>
                  <option value="pending">Ожидание</option>
                  <option value="in_progress">Осмотр</option>
                  <option value="completed">Завершён</option>
                </select>
              </div>
            </div>

            <div className="filter-actions">
              <button className="filter-btn filter-btn-reset" onClick={handleReset}>
                Сбросить
              </button>
              <button className="filter-btn filter-btn-apply" onClick={handleApply}>
                Применить
              </button>
            </div>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
