import { useState } from 'react'
import { motion } from 'framer-motion'
import './MedicalTestsTab.css'

// Типы медицинских исследований
interface MedicalTest {
  id: string
  date: string
  serviceName: string
  doctorName: string
  hasFile?: boolean
}

interface MedicalTestCategory {
  id: string
  name: string
  tests: MedicalTest[]
  status: 'completed' | 'pending' | 'not_done'
}

// Моковые данные
const mockMedicalTests: MedicalTestCategory[] = [
  {
    id: 'oak',
    name: 'ОАК',
    status: 'completed',
    tests: [
      {
        id: '1',
        date: '04.12.2025',
        serviceName: 'Общий анализ крови 6 параметров на анализаторе',
        doctorName: 'ДУЛИКАНОВА КЛАРА ТЕМИРГАЛИЕВНА',
        hasFile: true,
      },
      {
        id: '2',
        date: '09.10.2025',
        serviceName: 'Общий анализ крови 6 параметров на анализаторе',
        doctorName: 'ДУЛИКАНОВА КЛАРА ТЕМИРГАЛИЕВНА',
        hasFile: true,
      },
    ],
  },
  {
    id: 'oam',
    name: 'ОАМ',
    status: 'completed',
    tests: [
      {
        id: '3',
        date: '04.12.2025',
        serviceName: 'Общий анализ мочи',
        doctorName: 'ДУЛИКАНОВА КЛАРА ТЕМИРГАЛИЕВНА',
        hasFile: true,
      },
    ],
  },
  {
    id: 'microreaction',
    name: 'Микрореакция',
    status: 'completed',
    tests: [
      {
        id: '4',
        date: '04.12.2025',
        serviceName: 'Постановка реакции Хеддельсона в сыворотке крови на бруцеллез',
        doctorName: 'ДУЛИКАНОВА КЛАРА ТЕМИРГАЛИЕВНА',
        hasFile: true,
      },
    ],
  },
  {
    id: 'ecg',
    name: 'ЭКГ',
    status: 'completed',
    tests: [
      {
        id: '5',
        date: '03.12.2025',
        serviceName: 'Электрокардиография',
        doctorName: 'СМИРНОВА А.В.',
        hasFile: true,
      },
    ],
  },
  {
    id: 'fluorography',
    name: 'Флюорография',
    status: 'completed',
    tests: [
      {
        id: '6',
        date: '02.12.2025',
        serviceName: 'Флюорография органов грудной клетки',
        doctorName: 'ИВАНОВ С.П.',
        hasFile: true,
      },
    ],
  },
  {
    id: 'ultrasound',
    name: 'УЗИ',
    status: 'completed',
    tests: [
      {
        id: '7',
        date: '01.12.2025',
        serviceName: 'УЗИ органов брюшной полости',
        doctorName: 'ПЕТРОВА Е.С.',
        hasFile: true,
      },
    ],
  },
  {
    id: 'echocardiography',
    name: 'Эхокардиография',
    status: 'not_done',
    tests: [],
  },
  {
    id: 'additional',
    name: 'Доп.обследования',
    status: 'pending',
    tests: [
      {
        id: '8',
        date: '05.12.2025',
        serviceName: 'Консультация невролога',
        doctorName: 'ПЕТРОВА Е.С.',
        hasFile: false,
      },
    ],
  },
  {
    id: 'acts',
    name: 'Акты',
    status: 'completed',
    tests: [
      {
        id: '9',
        date: '18.09.2025',
        serviceName: 'Акт медицинского освидетельствования',
        doctorName: 'УГИЕВА МАРЖАН КАРИМОВНА',
        hasFile: true,
      },
    ],
  },
]

export default function MedicalTestsTab() {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null)

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return (
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="status-icon completed">
            <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="2" />
            <path d="M6 10L9 13L14 7" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
        )
      case 'pending':
        return (
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="status-icon pending">
            <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="2" />
            <path d="M10 6V10L13 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
        )
      case 'not_done':
        return (
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="status-icon not-done">
            <circle cx="10" cy="10" r="9" stroke="currentColor" strokeWidth="2" />
            <path d="M7 7L13 13M13 7L7 13" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
          </svg>
        )
      default:
        return null
    }
  }

  return (
    <div className="medical-tests-tab">
      {/* Категории исследований */}
      <div className="test-categories">
        {mockMedicalTests.map((category) => (
          <motion.button
            key={category.id}
            className={`test-category-btn ${selectedCategory === category.id ? 'active' : ''} ${category.status}`}
            onClick={() =>
              setSelectedCategory(selectedCategory === category.id ? null : category.id)
            }
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
          >
            <div className="category-header">
              {getStatusIcon(category.status)}
              <span className="category-name">{category.name}</span>
              {category.tests.length > 0 && (
                <span className="category-count">{category.tests.length}</span>
              )}
            </div>
            {selectedCategory === category.id && (
              <svg
                width="16"
                height="16"
                viewBox="0 0 16 16"
                fill="none"
                className="category-arrow"
              >
                <path
                  d="M4 6L8 10L12 6"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
            )}
          </motion.button>
        ))}
      </div>

      {/* Кнопка прикрепления анализов */}
      <div className="attach-files-section">
        <button className="attach-files-btn">
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path
              d="M10 4V16M4 10H16"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
          <span>Прикрепить анализы</span>
        </button>
      </div>

      {/* Результаты выбранной категории */}
      {selectedCategory && (
        <motion.div
          className="test-results"
          initial={{ opacity: 0, height: 0 }}
          animate={{ opacity: 1, height: 'auto' }}
          exit={{ opacity: 0, height: 0 }}
        >
          {mockMedicalTests
            .find((cat) => cat.id === selectedCategory)
            ?.tests.map((test, index) => (
              <motion.div
                key={test.id}
                className="test-result-item"
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <div className="test-result-header">
                  <div className="test-date font-code">{test.date}</div>
                  {test.hasFile && (
                    <button className="test-file-btn">
                      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                        <path
                          d="M8 2V8M8 8V14M8 8H14M8 8H2"
                          stroke="currentColor"
                          strokeWidth="2"
                          strokeLinecap="round"
                        />
                      </svg>
                      Детали
                    </button>
                  )}
                </div>
                <div className="test-service-name">{test.serviceName}</div>
                <div className="test-doctor-name">{test.doctorName}</div>
              </motion.div>
            ))}
          {mockMedicalTests.find((cat) => cat.id === selectedCategory)?.tests.length === 0 && (
            <div className="test-results-empty">
              <svg width="48" height="48" viewBox="0 0 48 48" fill="none">
                <path
                  d="M24 44C35.0457 44 44 35.0457 44 24C44 12.9543 35.0457 4 24 4C12.9543 4 4 12.9543 4 24C4 35.0457 12.9543 44 24 44Z"
                  stroke="currentColor"
                  strokeWidth="2"
                />
                <path
                  d="M24 16V24M24 32H24.02"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
              <p>Исследования не проводились</p>
            </div>
          )}
        </motion.div>
      )}
    </div>
  )
}
