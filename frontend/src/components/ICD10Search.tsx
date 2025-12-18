import { useState, useEffect, useRef } from 'react'
import './ICD10Search.css'

interface ICD10Code {
  code: string
  name: string
}

interface ICD10SearchProps {
  value: string | null
  onChange: (code: string | null) => void
  disabled?: boolean
  placeholder?: string
  required?: boolean
}

// Мок-данные МКБ-10 для fallback, если загрузка JSON не удалась
const fallbackICD10Codes: ICD10Code[] = [
  { code: '000.0', name: 'ЗДОРОВ' },
  { code: '1111', name: 'НЕ ОПРЕДЕЛЕНО' },
  { code: 'H52.1', name: 'Миопия' },
  { code: 'K29.3', name: 'Хронический поверхностный гастрит' },
]

export default function ICD10Search({
  value,
  onChange,
  disabled = false,
  placeholder = 'Введите код или название болезни',
  required = false,
}: ICD10SearchProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [filteredCodes, setFilteredCodes] = useState<ICD10Code[]>([])
  const [isDropdownOpen, setIsDropdownOpen] = useState(false)
  const [selectedCode, setSelectedCode] = useState<ICD10Code | null>(null)
  const [allCodes, setAllCodes] = useState<ICD10Code[]>(fallbackICD10Codes)
  const [isLoading, setIsLoading] = useState(true)
  const dropdownRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Загрузить все коды МКБ-10 из JSON при монтировании компонента
  useEffect(() => {
    const loadICD10Codes = async () => {
      try {
        setIsLoading(true)
        const response = await fetch('/icd10_codes.json')
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        const codes: ICD10Code[] = await response.json()
        setAllCodes(codes)
        console.log(`✓ Загружено ${codes.length} кодов МКБ-10 из JSON`)
      } catch (error) {
        console.error('⚠ Ошибка загрузки кодов МКБ-10, используется fallback:', error)
        setAllCodes(fallbackICD10Codes)
      } finally {
        setIsLoading(false)
      }
    }

    loadICD10Codes()
  }, [])

  // Загрузить выбранный код при инициализации
  useEffect(() => {
    if (value) {
      const code = allCodes.find((c) => c.code === value)
      if (code) {
        setSelectedCode(code)
        setSearchQuery(`${code.code} - ${code.name}`)
      }
    }
  }, [value, allCodes])

  // Фильтрация кодов при вводе
  useEffect(() => {
    if (searchQuery.trim() === '') {
      setFilteredCodes([])
      setIsDropdownOpen(false)
      return
    }

    const query = searchQuery.toLowerCase()
    const filtered = allCodes.filter(
      (code) =>
        code.code.toLowerCase().includes(query) ||
        code.name.toLowerCase().includes(query)
    )

    setFilteredCodes(filtered)
    setIsDropdownOpen(filtered.length > 0)
  }, [searchQuery, allCodes])

  // Закрытие выпадающего списка при клике вне компонента
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setIsDropdownOpen(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newQuery = e.target.value
    setSearchQuery(newQuery)

    // Если поле очищено, сбросить выбор
    if (newQuery.trim() === '') {
      setSelectedCode(null)
      onChange(null)
    }
  }

  const handleSelectCode = (code: ICD10Code) => {
    setSelectedCode(code)
    setSearchQuery(`${code.code} - ${code.name}`)
    setIsDropdownOpen(false)
    onChange(code.code)
  }

  const handleInputFocus = () => {
    if (searchQuery.trim() !== '' && filteredCodes.length > 0) {
      setIsDropdownOpen(true)
    }
  }

  const handleClear = () => {
    setSearchQuery('')
    setSelectedCode(null)
    onChange(null)
    inputRef.current?.focus()
  }

  return (
    <div className="icd10-search" ref={dropdownRef}>
      <div className="icd10-search-input-wrapper">
        <input
          ref={inputRef}
          type="text"
          className={`icd10-search-input ${selectedCode ? 'icd10-search-input-selected' : ''}`}
          value={searchQuery}
          onChange={handleInputChange}
          onFocus={handleInputFocus}
          placeholder={isLoading ? 'Загрузка справочника МКБ-10...' : placeholder}
          disabled={disabled || isLoading}
          required={required}
        />
        {selectedCode && !disabled && (
          <button
            type="button"
            className="icd10-search-clear"
            onClick={handleClear}
            title="Очистить"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path
                d="M12 4L4 12M4 4L12 12"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
          </button>
        )}
      </div>

      {isDropdownOpen && (
        <div className="icd10-search-dropdown">
          {filteredCodes.length > 0 ? (
            <ul className="icd10-search-list">
              {filteredCodes.map((code) => (
                <li
                  key={code.code}
                  className="icd10-search-item"
                  onClick={() => handleSelectCode(code)}
                >
                  <span className="icd10-search-code">{code.code}</span>
                  <span className="icd10-search-name">{code.name}</span>
                </li>
              ))}
            </ul>
          ) : (
            <div className="icd10-search-no-results">
              Коды не найдены
            </div>
          )}
        </div>
      )}

      {required && !selectedCode && (
        <div className="icd10-search-hint">
          * Обязательное поле
        </div>
      )}
    </div>
  )
}
