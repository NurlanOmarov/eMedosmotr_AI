import { motion } from 'framer-motion'
import { useState, useEffect, useRef } from 'react'
import type { Conscript } from '../types'
import ConscriptFilter from './ConscriptFilter'
import './ConscriptTable.css'

interface ConscriptTableProps {
  conscripts: Conscript[]
  selectedId?: string
  onSelect: (conscript: Conscript) => void
  isDetailCardOpen?: boolean
}

interface FilterValues {
  fullName: string
  iin: string
  medicalCommissionDateFrom: string
  medicalCommissionDateTo: string
  status: string
  draftDistrict: string
}

const statusLabels = {
  pending: 'ОЖИДАНИЕ',
  in_progress: 'ОСМОТР',
  completed: 'ЗАВЕРШЁН',
}

const statusColors = {
  pending: 'var(--color-text-tertiary)',
  in_progress: 'var(--color-warning)',
  completed: 'var(--color-primary)',
}

export default function ConscriptTable({ conscripts, selectedId, onSelect, isDetailCardOpen = false }: ConscriptTableProps) {
  const [isFilterOpen, setIsFilterOpen] = useState(false)
  const [filters, setFilters] = useState<FilterValues>({
    fullName: '',
    iin: '',
    medicalCommissionDateFrom: '',
    medicalCommissionDateTo: '',
    status: '',
    draftDistrict: '',
  })
  const [focusedIndex, setFocusedIndex] = useState<number>(-1)
  const rowRefs = useRef<(HTMLTableRowElement | null)[]>([])

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

  const handleApplyFilters = (newFilters: FilterValues) => {
    setFilters(newFilters)
  }

  const handleResetFilters = () => {
    setFilters({
      fullName: '',
      iin: '',
      medicalCommissionDateFrom: '',
      medicalCommissionDateTo: '',
      status: '',
      draftDistrict: '',
    })
  }

  // Фильтрация списка призывников
  const filteredConscripts = conscripts.filter((conscript) => {
    // ФИО
    if (filters.fullName && !conscript.fullName.toLowerCase().includes(filters.fullName.toLowerCase())) {
      return false
    }

    // ИИН
    if (filters.iin && !conscript.iin.includes(filters.iin)) {
      return false
    }

    // Дата медкомиссии от
    if (filters.medicalCommissionDateFrom && conscript.medicalCommissionDate) {
      if (new Date(conscript.medicalCommissionDate) < new Date(filters.medicalCommissionDateFrom)) {
        return false
      }
    }

    // Дата медкомиссии до
    if (filters.medicalCommissionDateTo && conscript.medicalCommissionDate) {
      if (new Date(conscript.medicalCommissionDate) > new Date(filters.medicalCommissionDateTo)) {
        return false
      }
    }

    // Призывной пункт
    if (filters.draftDistrict && conscript.draftDistrict !== filters.draftDistrict) {
      return false
    }

    // Статус
    if (filters.status && conscript.status !== filters.status) {
      return false
    }

    return true
  })

  // Проверка активности фильтров
  const hasActiveFilters = Object.values(filters).some((value) => value !== '')

  // Навигация по клавиатуре
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Игнорируем нажатия клавиш если открыты модальные окна, карточка призывника или фокус в input
      if (isFilterOpen || isDetailCardOpen) return
      const activeElement = document.activeElement
      if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA')) {
        return
      }

      if (event.key === 'ArrowDown') {
        event.preventDefault()
        setFocusedIndex((prev) => {
          const newIndex = prev < filteredConscripts.length - 1 ? prev + 1 : prev
          return newIndex
        })
      } else if (event.key === 'ArrowUp') {
        event.preventDefault()
        setFocusedIndex((prev) => {
          const newIndex = prev > 0 ? prev - 1 : 0
          return newIndex
        })
      } else if (event.key === 'Enter') {
        event.preventDefault()
        if (focusedIndex >= 0 && focusedIndex < filteredConscripts.length) {
          onSelect(filteredConscripts[focusedIndex])
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [focusedIndex, filteredConscripts, onSelect, isFilterOpen, isDetailCardOpen])

  // Устанавливаем фокус на выбранный элемент при первой загрузке
  useEffect(() => {
    if (selectedId && focusedIndex === -1) {
      const index = filteredConscripts.findIndex((c) => c.id === selectedId)
      if (index !== -1) {
        setFocusedIndex(index)
      } else if (filteredConscripts.length > 0) {
        setFocusedIndex(0)
      }
    } else if (filteredConscripts.length > 0 && focusedIndex === -1) {
      setFocusedIndex(0)
    }
  }, [selectedId, filteredConscripts, focusedIndex])

  // Автопрокрутка к фокусированному элементу
  useEffect(() => {
    if (focusedIndex >= 0 && rowRefs.current[focusedIndex]) {
      rowRefs.current[focusedIndex]?.scrollIntoView({
        behavior: 'smooth',
        block: 'nearest',
      })
    }
  }, [focusedIndex])

  return (
    <motion.div
      className="conscript-table-container"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
    >
      {/* Table header */}
      <div className="table-header">
        <div className="table-title">
          <div className="table-title-text font-code">СПИСОК ПРИЗЫВНИКОВ</div>
          <div className="table-title-count">
            <span className="font-mono">{conscripts.length}</span>
            <span className="table-title-label">записей</span>
          </div>
        </div>

        <div className="table-controls">
          <button
            className={`table-control-btn ${hasActiveFilters ? 'table-control-btn-active' : ''}`}
            onClick={() => setIsFilterOpen(!isFilterOpen)}
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path
                d="M2 3H14L9.33333 8.66667V12.6667L6.66667 14V8.66667L2 3Z"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="square"
              />
            </svg>
            <span>Фильтры</span>
            {hasActiveFilters && <span className="filter-badge">{Object.values(filters).filter(v => v !== '').length}</span>}
          </button>

          <button className="table-control-btn">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path
                d="M2 4.66667H14M4.66667 4.66667V2.66667C4.66667 2.48986 4.7369 2.32029 4.86193 2.19526C4.98695 2.07024 5.15652 2 5.33333 2H10.6667C10.8435 2 11.013 2.07024 11.1381 2.19526C11.2631 2.32029 11.3333 2.48986 11.3333 2.66667V4.66667M13.3333 4.66667V13.3333C13.3333 13.5101 13.2631 13.6797 13.1381 13.8047C13.013 13.9298 12.8435 14 12.6667 14H3.33333C3.15652 14 2.98695 13.9298 2.86193 13.8047C2.7369 13.6797 2.66667 13.5101 2.66667 13.3333V4.66667H13.3333Z"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="square"
              />
              <path d="M6.66667 7.33333V11.3333M9.33333 7.33333V11.3333" stroke="currentColor" strokeWidth="1.5" strokeLinecap="square" />
            </svg>
            <span>Архив</span>
          </button>

          <button className="table-control-btn table-control-btn-primary">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path d="M8 2V14M2 8H14" stroke="currentColor" strokeWidth="2" strokeLinecap="square" />
            </svg>
            <span>Новый</span>
          </button>
        </div>
      </div>

      {/* Filter panel */}
      <ConscriptFilter
        isOpen={isFilterOpen}
        onClose={() => setIsFilterOpen(false)}
        onApply={handleApplyFilters}
        onReset={handleResetFilters}
      />

      {/* Table */}
      <div className="table-scroll">
        <table className="conscript-table">
          <thead>
            <tr>
              <th className="table-th">
                <div className="table-th-content">
                  <span>№</span>
                </div>
              </th>
              <th className="table-th">
                <div className="table-th-content">
                  <span>ИИН</span>
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                    <path d="M6 3V9M3 6H9" stroke="currentColor" strokeWidth="1.5" />
                  </svg>
                </div>
              </th>
              <th className="table-th">
                <div className="table-th-content">
                  <span>ФИО</span>
                </div>
              </th>
              <th className="table-th">
                <div className="table-th-content">
                  <span>ДАТА МЕДКОМИССИИ</span>
                </div>
              </th>
              <th className="table-th">
                <div className="table-th-content">
                  <span>КАТЕГОРИЯ</span>
                </div>
              </th>
              <th className="table-th">
                <div className="table-th-content">
                  <span>ПРИЗЫВНОЙ ПУНКТ</span>
                </div>
              </th>
              <th className="table-th">
                <div className="table-th-content">
                  <span>СТАТУС</span>
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            {filteredConscripts.map((conscript, index) => (
              <motion.tr
                key={conscript.id}
                ref={(el) => (rowRefs.current[index] = el)}
                className={`table-row ${selectedId === conscript.id ? 'table-row-selected' : ''} ${focusedIndex === index ? 'table-row-focused' : ''}`}
                onClick={() => {
                  setFocusedIndex(index)
                  onSelect(conscript)
                }}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
                whileHover={{ x: 4 }}
              >
                <td className="table-td">
                  <div className="table-cell">
                    <span className="table-cell-number font-code">{index + 1}</span>
                  </div>
                </td>
                <td className="table-td">
                  <div className="table-cell">
                    <span className="table-cell-mono font-code">{conscript.iin}</span>
                  </div>
                </td>
                <td className="table-td">
                  <div className="table-cell">
                    <span className="table-cell-name font-mono">{conscript.fullName}</span>
                  </div>
                </td>
                <td className="table-td">
                  <div className="table-cell">
                    <span className="table-cell-date font-code">
                      {conscript.medicalCommissionDate
                        ? new Date(conscript.medicalCommissionDate).toLocaleDateString('ru-RU')
                        : '—'}
                    </span>
                  </div>
                </td>
                <td className="table-td">
                  <div className="table-cell">
                    <div className="table-badge table-badge-category">
                      <span className="font-code">призывник</span>
                    </div>
                  </div>
                </td>
                <td className="table-td">
                  <div className="table-cell">
                    <span className="table-cell-text">{conscript.draftDistrict || '—'}</span>
                  </div>
                </td>
                <td className="table-td">
                  <div className="table-cell">
                    <div
                      className="table-status"
                      style={{ '--status-color': statusColors[conscript.status] } as any}
                    >
                      <div className="table-status-dot" />
                      <span className="table-status-text font-code">
                        {statusLabels[conscript.status]}
                      </span>
                    </div>
                  </div>
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Table footer */}
      <div className="table-footer">
        <div className="table-footer-info font-mono">
          Показано {filteredConscripts.length} из {conscripts.length}
        </div>
        <div className="table-pagination">
          <button className="pagination-btn" disabled>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M7.5 9L4.5 6L7.5 3" stroke="currentColor" strokeWidth="1.5" strokeLinecap="square" />
            </svg>
          </button>
          <div className="pagination-page font-code">1</div>
          <button className="pagination-btn" disabled>
            <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
              <path d="M4.5 3L7.5 6L4.5 9" stroke="currentColor" strokeWidth="1.5" strokeLinecap="square" />
            </svg>
          </button>
        </div>
      </div>
    </motion.div>
  )
}
