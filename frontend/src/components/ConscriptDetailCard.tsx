import { motion } from 'framer-motion'
import { useState, useEffect } from 'react'
import type { Conscript } from '../types'
import type { User } from '../App'
import ExaminationForm from './ExaminationForm'
import MedicalTestsTab from './MedicalTestsTab'
import './ConscriptDetailCard.css'

interface ConscriptDetailCardProps {
  conscript: Conscript
  currentUser: User
  onClose: () => void
  onOpenAIAnalysis?: (graphId?: number) => void
}

type TabId =
  | 'info'
  | 'medical_tests'
  | 'dispensary'
  | 'hospitalization'
  | 'vaccination'
  | 'examination'
  | 'conclusion'
  | 'referrals'
  | 'anthropometric'

interface Tab {
  id: TabId
  label: string
  roleAccess?: ('doctor' | 'chairman')[]
}

const tabs: Tab[] = [
  { id: 'info', label: 'Информация' },
  { id: 'anthropometric', label: 'Антропометрические данные' },
  { id: 'medical_tests', label: 'Результаты исследований' },
  { id: 'referrals', label: 'Направления' },
  { id: 'dispensary', label: 'Диспансерный учет' },
  { id: 'hospitalization', label: 'Госпитализация' },
  { id: 'vaccination', label: 'Вакцинация' },
  { id: 'examination', label: 'Освидетельствование' },
  { id: 'conclusion', label: 'Заключение председателя', roleAccess: ['chairman'] },
]

// Маппинг ID подгруппы графа -> номер основного графа (1-4)
const GRAPH_SUBGROUP_TO_MAIN_GRAPH: Record<number, number> = {
  1: 1, 2: 1, 3: 1, 4: 1,           // График I - подгруппы 1-4
  5: 2, 6: 2, 7: 2, 8: 2, 9: 2, 10: 2, 11: 2,  // График II - подгруппы 1-7
  12: 3, 13: 3, 14: 3, 15: 3, 16: 3, 17: 3,    // График III - подгруппы 1-6
  18: 4, 19: 4                      // График IV - подгруппы 1-2
}

export default function ConscriptDetailCard({
  conscript,
  currentUser,
  onClose,
  onOpenAIAnalysis,
}: ConscriptDetailCardProps) {
  const [activeTab, setActiveTab] = useState<TabId>('info')
  // Используем categoryGraphId для выбора подгруппы (1-19)
  const [selectedSubgraphId, setSelectedSubgraphId] = useState<number>(conscript.categoryGraphId || 1)
  const [isGraphSaved, setIsGraphSaved] = useState(true)

  // Фильтрация вкладок по ролям (должно быть до useEffect)
  const filteredTabs = tabs.filter((tab) => {
    if (!tab.roleAccess) return true
    return tab.roleAccess.includes(currentUser.role)
  })

  // Закрытие карточки по нажатию Escape и навигация по вкладкам с Tab
  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      // Закрытие по Escape
      if (event.key === 'Escape') {
        onClose()
        return
      }

      // Навигация по вкладкам с Tab (только если фокус не в полях ввода)
      if (event.key === 'Tab') {
        const activeElement = document.activeElement
        if (activeElement && (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA' || activeElement.tagName === 'SELECT')) {
          // Разрешаем стандартное поведение Tab для полей ввода
          return
        }

        event.preventDefault()

        const currentIndex = filteredTabs.findIndex((tab) => tab.id === activeTab)
        let newIndex: number

        if (event.shiftKey) {
          // Shift+Tab - переход на предыдущую вкладку
          newIndex = currentIndex > 0 ? currentIndex - 1 : filteredTabs.length - 1
        } else {
          // Tab - переход на следующую вкладку
          newIndex = currentIndex < filteredTabs.length - 1 ? currentIndex + 1 : 0
        }

        setActiveTab(filteredTabs[newIndex].id)
      }
    }

    document.addEventListener('keydown', handleKeyDown)
    return () => document.removeEventListener('keydown', handleKeyDown)
  }, [onClose, activeTab, filteredTabs])

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

  const handleGraphChange = (newSubgraphId: number) => {
    setSelectedSubgraphId(newSubgraphId)
    setIsGraphSaved(false)
  }

  const handleSaveGraph = () => {
    // Определяем основной граф (1-4) из подгруппы (1-19)
    const mainGraph = GRAPH_SUBGROUP_TO_MAIN_GRAPH[selectedSubgraphId] || 1

    // В реальном приложении здесь будет API запрос
    // await apiClient.updateConscriptGraph(conscript.id, selectedSubgraphId)

    // Для MVP обновляем локально
    conscript.graph = mainGraph // Основной граф (1-4) для API валидации
    conscript.categoryGraphId = selectedSubgraphId // Подгруппа (1-19) для UI
    setIsGraphSaved(true)

    console.log(`Подгруппа ${selectedSubgraphId} (Граф ${mainGraph}) сохранена для призывника ${conscript.fullName}`)
  }

  const handleOpenAIAnalysisWithGraph = () => {
    if (onOpenAIAnalysis) {
      // Передаем основной граф (1-4) при вызове AI анализа
      const mainGraph = GRAPH_SUBGROUP_TO_MAIN_GRAPH[selectedSubgraphId] || 1
      onOpenAIAnalysis(mainGraph)
    }
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case 'info':
        return (
          <div className="tab-content-info">
            <div className="info-photo-section">
              <div className="info-photo">
                {conscript.photo ? (
                  <img src={conscript.photo} alt={conscript.fullName} />
                ) : (
                  <div className="info-photo-placeholder">
                    <svg width="80" height="80" viewBox="0 0 48 48" fill="none">
                      <path
                        d="M24 24C28.4183 24 32 20.4183 32 16C32 11.5817 28.4183 8 24 8C19.5817 8 16 11.5817 16 16C16 20.4183 19.5817 24 24 24Z"
                        stroke="currentColor"
                        strokeWidth="2"
                      />
                      <path
                        d="M8 40C8 34.6957 10.1071 29.6086 13.8579 25.8579C17.6086 22.1071 22.6957 20 28 20H20C14.6957 20 9.60859 22.1071 5.85786 25.8579C2.10714 29.6086 0 34.6957 0 40"
                        stroke="currentColor"
                        strokeWidth="2"
                      />
                    </svg>
                  </div>
                )}
              </div>
              <div className="info-photo-label">ФОТО 3×4</div>
            </div>

            <div className="info-details">
              <div className="info-section">
                <div className="info-label">Фамилия Имя Отчество</div>
                <div className="info-value">{conscript.fullName}</div>
              </div>

              <div className="info-grid">
                <div className="info-field">
                  <div className="info-label">ИИН</div>
                  <div className="info-value font-code">{conscript.iin}</div>
                </div>

                <div className="info-field">
                  <div className="info-label">Дата рождения</div>
                  <div className="info-value font-code">
                    {formatDate(conscript.birthDate)}
                  </div>
                </div>

                <div className="info-field">
                  <div className="info-label">Возраст</div>
                  <div className="info-value font-code">
                    {calculateAge(conscript.birthDate)} лет
                  </div>
                </div>

                <div className="info-field">
                  <div className="info-label">Номер призывника</div>
                  <div className="info-value font-code">{conscript.draftNumber}</div>
                </div>

                <div className="info-field">
                  <div className="info-label">Пол</div>
                  <div className="info-value">Мужской</div>
                </div>

                <div className="info-field">
                  <div className="info-label">Гражданство</div>
                  <div className="info-value">Республика Казахстан</div>
                </div>

                <div className="info-field">
                  <div className="info-label">Национальность</div>
                  <div className="info-value">---</div>
                </div>
              </div>

              <div className="info-section">
                <div className="info-label">Адрес проживания</div>
                <div className="info-value">---</div>
              </div>

              <div className="info-section">
                <div className="info-label">Медицинская организация прикрепления</div>
                <div className="info-value">ТОО "Клиника AMD"</div>
              </div>

              <div className="info-section">
                <div className="info-label">Номер телефона</div>
                <div className="info-value font-code">+7 (747) 428-85-90</div>
              </div>
            </div>
          </div>
        )

      case 'medical_tests':
        return <MedicalTestsTab />

      case 'examination':
        return <ExaminationForm currentUser={currentUser} conscriptId={conscript.id} onOpenAIAnalysis={handleOpenAIAnalysisWithGraph} />

      case 'conclusion':
        return (
          <div className="tab-content-conclusion">
            <h3>Заключение председателя</h3>

            {/* Таблица с заключениями врачей */}
            <div className="doctors-conclusions-wrapper">
              <table className="doctors-conclusions-table">
                <thead>
                  <tr>
                    <th>Врачи</th>
                    <th>Заключения</th>
                    <th>Диагноз</th>
                    <th>Заключения района</th>
                    <th>Диагноз района</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>Фтизиатр</td>
                    <td>-</td>
                    <td>-</td>
                    <td>-</td>
                    <td>-</td>
                  </tr>
                  <tr>
                    <td>Дерматолог</td>
                    <td>-</td>
                    <td>-</td>
                    <td>А - Годен к воинской службе</td>
                    <td>000.0 - ЗДОРОВ</td>
                  </tr>
                  <tr>
                    <td>Невропатолог</td>
                    <td>-</td>
                    <td>-</td>
                    <td>А - Годен к воинской службе</td>
                    <td>000.0 - ЗДОРОВ</td>
                  </tr>
                  <tr>
                    <td>Психиатр</td>
                    <td>-</td>
                    <td>-</td>
                    <td>А - Годен к воинской службе</td>
                    <td>000.0 - ЗДОРОВ</td>
                  </tr>
                  <tr>
                    <td>Офтальмолог</td>
                    <td>-</td>
                    <td>-</td>
                    <td>А - Годен к воинской службе</td>
                    <td>000.0 - ЗДОРОВ</td>
                  </tr>
                  <tr>
                    <td>Отоларинголог</td>
                    <td>-</td>
                    <td>-</td>
                    <td>А - Годен к воинской службе</td>
                    <td>000.0 - ЗДОРОВ</td>
                  </tr>
                  <tr>
                    <td>Хирург</td>
                    <td>-</td>
                    <td>-</td>
                    <td>А - Годен к воинской службе</td>
                    <td>000.0 - ЗДОРОВ</td>
                  </tr>
                  <tr>
                    <td>Стоматолог</td>
                    <td>-</td>
                    <td>-</td>
                    <td>А - Годен к воинской службе</td>
                    <td>000.0 - ЗДОРОВ</td>
                  </tr>
                  <tr>
                    <td>Терапевт</td>
                    <td>-</td>
                    <td>-</td>
                    <td>-</td>
                    <td>-</td>
                  </tr>
                </tbody>
              </table>
            </div>

            {/* Форма заключения председателя */}
            <div className="chairman-conclusion-form">
              <div className="form-field">
                <label className="form-label">Дата и время приема:</label>
                <input
                  type="text"
                  className="form-input"
                  value="04.12.2025 15:07"
                  disabled
                />
              </div>

              <div className="form-field">
                <label className="form-label">Диагноз:</label>
                <textarea
                  className="form-textarea"
                  rows={3}
                  placeholder="Введите диагноз"
                />
              </div>

              <div className="form-field">
                <label className="form-label">Данные объективного обследования:</label>
                <textarea
                  className="form-textarea"
                  rows={4}
                  placeholder="Введите данные объективного обследования"
                />
              </div>

              <div className="form-field">
                <label className="form-label">Результаты специальных исследований:</label>
                <textarea
                  className="form-textarea"
                  rows={3}
                  placeholder="Введите результаты исследований"
                />
              </div>

              <div className="form-field">
                <label className="form-label">Примечания:</label>
                <textarea
                  className="form-textarea"
                  rows={3}
                  placeholder="Введите примечания"
                />
              </div>

              <div className="form-field">
                <label className="form-label">Категории годности:</label>
                <div className="radio-group">
                  <label className="radio-label">
                    <input type="radio" name="chairman_category" value="А" />
                    <span>Годен к воинской службе</span>
                  </label>
                  <label className="radio-label">
                    <input type="radio" name="chairman_category" value="Б" />
                    <span>Годен к воинской службе с незначительными ограничениями</span>
                  </label>
                  <label className="radio-label">
                    <input type="radio" name="chairman_category" value="В" />
                    <span>Ограниченно годен к воинской службе</span>
                  </label>
                  <label className="radio-label">
                    <input type="radio" name="chairman_category" value="Г" />
                    <span>Временно не годен к воинской службе</span>
                  </label>
                  <label className="radio-label">
                    <input type="radio" name="chairman_category" value="Д" />
                    <span>Не годен к воинской службе в мирное время, ограниченно годен в военное время</span>
                  </label>
                  <label className="radio-label">
                    <input type="radio" name="chairman_category" value="Е" />
                    <span>Не годен к воинской службе с исключением с воинского учета</span>
                  </label>
                  <label className="radio-label">
                    <input type="radio" name="chairman_category" value="направить" />
                    <span>Направить на обследование</span>
                  </label>
                </div>
              </div>

              <div className="form-actions">
                <button className="btn-save">Сохранить заключение</button>
              </div>
            </div>
          </div>
        )

      case 'anthropometric':
        return (
          <div className="tab-content-anthropometric">
            <h3>Антропометрические данные</h3>
            <div className="anthropometric-form">
              <div className="form-group">
                <label>Рост (см)*:</label>
                <input type="text" className="form-input" placeholder="Введите рост" />
              </div>

              <div className="form-group">
                <label>Рост сидя (см):</label>
                <input type="text" className="form-input" placeholder="Введите рост сидя" />
              </div>

              <div className="form-group">
                <label>Вес (кг)*</label>
                <input type="text" className="form-input" placeholder="Введите вес" />
              </div>

              <div className="form-group">
                <label>Индекс массы тела:</label>
                <input type="text" className="form-input" placeholder="Автоматический расчет" disabled />
              </div>

              <div className="form-group">
                <label>Окружность груди (см) при Дыхательной паузы*:</label>
                <input type="text" className="form-input" placeholder="Введите значение" />
              </div>

              <div className="form-group">
                <label>Максимальном вдохе:</label>
                <input type="text" className="form-input" placeholder="Введите значение" />
              </div>

              <div className="form-group">
                <label>Максимальном выдохе:</label>
                <input type="text" className="form-input" placeholder="Введите значение" />
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Сила кистей:</label>
                  <div className="form-inline-group">
                    <div>
                      <span className="inline-label">Левая</span>
                      <input type="text" className="form-input-inline" placeholder="" />
                    </div>
                    <div>
                      <span className="inline-label">Правая</span>
                      <input type="text" className="form-input-inline" placeholder="" />
                    </div>
                  </div>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Длина рук (см):</label>
                  <div className="form-inline-group">
                    <div>
                      <span className="inline-label">Левая</span>
                      <input type="text" className="form-input-inline" placeholder="" />
                    </div>
                    <div>
                      <span className="inline-label">Правая</span>
                      <input type="text" className="form-input-inline" placeholder="" />
                    </div>
                  </div>
                </div>
              </div>

              <div className="form-row">
                <div className="form-group">
                  <label>Длина ног (см):</label>
                  <div className="form-inline-group">
                    <div>
                      <span className="inline-label">Левая</span>
                      <input type="text" className="form-input-inline" placeholder="" />
                    </div>
                    <div>
                      <span className="inline-label">Правая</span>
                      <input type="text" className="form-input-inline" placeholder="" />
                    </div>
                  </div>
                </div>
              </div>

              <div className="form-group">
                <label>Становая сила:</label>
                <input type="text" className="form-input" placeholder="Введите значение" />
              </div>

              <div className="form-group">
                <label>АД(артериальное давление):</label>
                <div className="form-inline-group">
                  <div>
                    <span className="inline-label">SYS</span>
                    <input type="text" className="form-input-inline" placeholder="" />
                  </div>
                  <div>
                    <span className="inline-label">DIA</span>
                    <input type="text" className="form-input-inline" placeholder="" />
                  </div>
                </div>
              </div>

              <div className="form-group">
                <label>Температура:</label>
                <input type="text" className="form-input" placeholder="Введите температуру" />
              </div>

              <div className="form-group">
                <label>Пульс (уд/мин):</label>
                <input type="text" className="form-input" placeholder="Введите пульс" />
              </div>

              <div className="form-group">
                <label>Граф (категория призывника)*:</label>
                <select
                  className="form-select"
                  value={selectedSubgraphId}
                  onChange={(e) => handleGraphChange(Number(e.target.value))}
                >
                  <option value="1">Граф I — гражданам при приписке к призывным участкам</option>
                  <option value="2">Граф I — гражданам при призыве на срочную воинскую службу</option>
                  <option value="3">Граф I — гражданам при отборе для подготовки по военно-техническим специальностям</option>
                  <option value="4">Граф I — гражданам, поступающим в военные учебные заведения (школы)</option>
                  <option value="5">Граф II — гражданам (военнослужащим) при поступлении в ВУЗ</option>
                  <option value="6">Граф II — гражданам при поступлении и обучающимся в военных кафедрах</option>
                  <option value="7">Граф II — гражданам при поступлении на воинскую службу по контракту</option>
                  <option value="8">Граф II — гражданам при отборе для подготовки на возмездной основе</option>
                  <option value="9">Граф II — военнослужащим срочной воинской службы</option>
                  <option value="10">Граф II — курсантам (кадетам) ВУЗ до заключения контракта</option>
                  <option value="11">Граф II — рядовым и сержантам запаса при призыве на воинские сборы</option>
                  <option value="12">Граф III — офицерам запаса при призыве на воинскую службу</option>
                  <option value="13">Граф III — военнослужащим, проходящим воинскую службу по контракту</option>
                  <option value="14">Граф III — офицерам, проходящим воинскую службу по призыву</option>
                  <option value="15">Граф III — военнослужащим при поступлении в ВУЗ (послевузовское образование)</option>
                  <option value="16">Граф III — курсантам (кадетам) ВУЗ после заключения контракта</option>
                  <option value="17">Граф III — офицерам запаса при призыве на воинские сборы</option>
                  <option value="18">Граф IV — военнослужащим в ДШВ, ВМС, ЧСН (спецназ, морская пехота, разведка)</option>
                  <option value="19">Граф IV — военнослужащим, привлекаемым к подводному вождению танков</option>
                </select>
                <div className="form-hint">
                  Выбранный граф влияет на определение категории годности по справочнику Приказа МО РК №722
                </div>
                {!isGraphSaved && (
                  <button
                    className="btn-save-graph"
                    onClick={handleSaveGraph}
                  >
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M19 21H5a2 2 0 01-2-2V5a2 2 0 012-2h11l5 5v11a2 2 0 01-2 2z" />
                      <polyline points="17 21 17 13 7 13 7 21" />
                      <polyline points="7 3 7 8 15 8" />
                    </svg>
                    Сохранить граф
                  </button>
                )}
                {isGraphSaved && (
                  <div className="graph-saved-message">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <polyline points="20 6 9 17 4 12" />
                    </svg>
                    Граф сохранен
                  </div>
                )}
              </div>

              <div className="form-group">
                <label>Дата и время приема</label>
                <input type="text" className="form-input" placeholder="04.12.2025 15:01" disabled />
              </div>
            </div>
          </div>
        )

      case 'referrals':
        return (
          <div className="tab-content-referrals">
            <h3>Направления</h3>
            <div className="referrals-tabs">
              <button className="referral-tab-btn active">Обязательные обследования</button>
              <button className="referral-tab-btn">Доп. обследования</button>
              <button className="referral-tab-btn">ЕПС</button>
              <button className="referral-tab-btn">Повторный осмотр</button>
            </div>
            <div className="referrals-table-wrapper">
              <table className="referrals-table">
                <thead>
                  <tr>
                    <th>Дата</th>
                    <th>Статус</th>
                    <th>Организация</th>
                    <th>Услуга</th>
                    <th>Результат</th>
                    <th>Детали</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>11.09.2025</td>
                    <td>
                      <span className="status-badge-small status-not-completed">Не выполнено</span>
                    </td>
                    <td>ГКП на ПХВ "Алакольская ЦРБ"</td>
                    <td>Электрокардиографическое исследование (в 12 отведениях) с расшифровкой</td>
                    <td></td>
                    <td>
                      <button className="btn-download">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                          <path d="M21 15V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M7 10L12 15L17 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M12 15V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </button>
                    </td>
                  </tr>
                  <tr>
                    <td>11.09.2025</td>
                    <td>
                      <span className="status-badge-small status-not-completed">Не выполнено</span>
                    </td>
                    <td>ГКП на ПХВ "Алакольская ЦРБ"</td>
                    <td>Диагностическая флюорография (1 проекция)</td>
                    <td></td>
                    <td>
                      <button className="btn-download">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                          <path d="M21 15V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M7 10L12 15L17 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M12 15V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </button>
                    </td>
                  </tr>
                  <tr>
                    <td>11.09.2025</td>
                    <td>
                      <span className="status-badge-small status-not-completed">Не выполнено</span>
                    </td>
                    <td>ГКП на ПХВ "Алакольская ЦРБ"</td>
                    <td>Эхокардиография</td>
                    <td></td>
                    <td>
                      <button className="btn-download">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                          <path d="M21 15V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M7 10L12 15L17 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M12 15V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </button>
                    </td>
                  </tr>
                  <tr>
                    <td>11.09.2025</td>
                    <td>
                      <span className="status-badge-small status-not-completed">Не выполнено</span>
                    </td>
                    <td>ГКП на ПХВ "Алакольская ЦРБ"</td>
                    <td>Ультразвуковая диагностика комплексная (печень, желчный пузырь, поджелудочная железа, селезенка, почек)</td>
                    <td></td>
                    <td>
                      <button className="btn-download">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                          <path d="M21 15V19C21 19.5304 20.7893 20.0391 20.4142 20.4142C20.0391 20.7893 19.5304 21 19 21H5C4.46957 21 3.96086 20.7893 3.58579 20.4142C3.21071 20.0391 3 19.5304 3 19V15" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M7 10L12 15L17 10" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                          <path d="M12 15V3" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                        </svg>
                      </button>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )

      case 'vaccination':
        return (
          <div className="tab-content-vaccination">
            <h3>Вакцинация</h3>
            <div className="data-table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Дата вакцинации</th>
                    <th>Название вакцины</th>
                    <th>Серия</th>
                    <th>Доза</th>
                    <th>Организация</th>
                    <th>Медработник</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>15.03.2023</td>
                    <td>Вакцина против гепатита B</td>
                    <td>А-12345</td>
                    <td>0.5 мл</td>
                    <td>ГКП на ПХВ "Алакольская ЦРБ"</td>
                    <td>Иванова М.С.</td>
                  </tr>
                  <tr>
                    <td>10.01.2024</td>
                    <td>Вакцина против дифтерии и столбняка (АДС-М)</td>
                    <td>Б-67890</td>
                    <td>0.5 мл</td>
                    <td>ГКП на ПХВ "Алакольская ЦРБ"</td>
                    <td>Петрова А.К.</td>
                  </tr>
                  <tr>
                    <td>05.06.2024</td>
                    <td>Вакцина против кори, краснухи, паротита</td>
                    <td>В-11223</td>
                    <td>0.5 мл</td>
                    <td>ГКП на ПХВ "Алакольская ЦРБ"</td>
                    <td>Сидорова Н.П.</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )

      case 'dispensary':
        return (
          <div className="tab-content-dispensary">
            <h3>Диспансерный учет</h3>
            <div className="data-table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Диагноз (МКБ-10)</th>
                    <th>Дата постановки</th>
                    <th>Организация</th>
                    <th>Врач</th>
                    <th>Группа учета</th>
                    <th>Статус</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>J35.0 - Хронический тонзиллит</td>
                    <td>12.02.2023</td>
                    <td>ГКП на ПХВ "Алакольская ЦРБ"</td>
                    <td>Смирнов П.А. (ЛОР)</td>
                    <td>Д-III</td>
                    <td><span className="status-badge-small status-completed">Активен</span></td>
                  </tr>
                  <tr>
                    <td>K29.3 - Хронический поверхностный гастрит</td>
                    <td>08.09.2022</td>
                    <td>ГКП на ПХВ "Алакольская ЦРБ"</td>
                    <td>Смирнова А.В. (Терапевт)</td>
                    <td>Д-II</td>
                    <td><span className="status-badge-small status-completed">Активен</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )

      case 'hospitalization':
        return (
          <div className="tab-content-hospitalization">
            <h3>Госпитализация</h3>
            <div className="data-table-wrapper">
              <table className="data-table">
                <thead>
                  <tr>
                    <th>Дата поступления</th>
                    <th>Дата выписки</th>
                    <th>Диагноз</th>
                    <th>Организация</th>
                    <th>Отделение</th>
                    <th>Исход</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td>18.07.2023</td>
                    <td>25.07.2023</td>
                    <td>J18.9 - Пневмония неуточненная</td>
                    <td>ГКП на ПХВ "Алакольская ЦРБ"</td>
                    <td>Терапевтическое отделение</td>
                    <td><span className="status-badge-small status-completed">Выздоровление</span></td>
                  </tr>
                  <tr>
                    <td>03.11.2024</td>
                    <td>05.11.2024</td>
                    <td>S06.0 - Сотрясение головного мозга</td>
                    <td>ГКП на ПХВ "Алакольская ЦРБ"</td>
                    <td>Неврологическое отделение</td>
                    <td><span className="status-badge-small status-completed">Улучшение</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        )

      default:
        return (
          <div className="tab-content-mock">
            <div className="mock-data">Данные раздела "{filteredTabs.find((t) => t.id === activeTab)?.label}" (в разработке)</div>
          </div>
        )
    }
  }

  return (
    <motion.div
      className="conscript-detail-overlay"
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      exit={{ opacity: 0 }}
    >
      <motion.div
        className="conscript-detail-container"
        initial={{ x: '100%' }}
        animate={{ x: 0 }}
        exit={{ x: '100%' }}
        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
      >
        <div className="conscript-detail-layout">
          {/* Main Content */}
          <div className="conscript-detail-main">
            {/* Header */}
            <div className="conscript-detail-header">
              <div className="header-left">
                <button className="btn-back" onClick={onClose}>
                  <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                    <path
                      d="M12.5 15L7.5 10L12.5 5"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="square"
                    />
                  </svg>
                  Назад
                </button>
                <div className="header-title">
                  <div className="title-main">Карта призывника</div>
                  <div className="title-sub">{conscript.fullName}</div>
                </div>
              </div>
              <div className="header-right">
                <div className={`status-badge status-${conscript.status}`}>
                  <div className="status-dot" />
                  <span>
                    {conscript.status === 'pending' && 'ОЖИДАНИЕ'}
                    {conscript.status === 'in_progress' && 'ОСМОТР'}
                    {conscript.status === 'completed' && 'ЗАВЕРШЁН'}
                  </span>
                </div>
              </div>
            </div>

            {/* Tabs */}
            <div className="tabs-container">
              <div className="tabs-list">
                {filteredTabs.map((tab) => (
                  <button
                    key={tab.id}
                    className={`tab-button ${activeTab === tab.id ? 'active' : ''}`}
                    onClick={() => setActiveTab(tab.id)}
                  >
                    {tab.label}
                  </button>
                ))}
              </div>
            </div>

            {/* Tab Content */}
            <div className="tab-content-wrapper">{renderTabContent()}</div>
          </div>
        </div>
      </motion.div>
    </motion.div>
  )
}
