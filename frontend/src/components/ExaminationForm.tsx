import { useState, useEffect } from 'react'
import type { User } from '../App'
import { useData } from '../contexts/DataContext'
import ICD10Search from './ICD10Search'
import DentistChart from './DentistChart'
import './ExaminationForm.css'

interface ICD10Code {
  code: string
  name: string
}

interface ExaminationFormProps {
  currentUser: User
  conscriptId?: string
  onOpenAIAnalysis?: () => void
}

// Мок-данные освидетельствования (по примеру из API_REQUEST_EXAMPLE.json)
const mockExaminationData: Record<string, any> = {
  'Офтальмолог': {
    complain: 'На плохое зрение',
    anamnesis: 'Очки не носит',
    objective_data: 'OU спокойный, роговица чистая, зрачок с реакцией, п/к средней глубины, влага чистая, хрусталик прозрачный. Глазное дно без патологии.',
    special_research_results: 'Скиаскопия: OD -4.5 D, OS -4.0 D. Миопия средней степени.',
    od_vision_without_correction: '0.3',
    os_vision_without_correction: '0.4',
    valid_category: 'В',
    diagnosis_main_id: 'H52.1', // Основной диагноз: Миопия (обязательное поле!)
    diagnosis_accompany_id: null, // Сопутствующий диагноз
    additional_act_comment: 'Миопия средней степени (OD -4.5, OS -4.0)',
  },
  'Хирург': {
    complain: 'нет',
    anamnesis: 'без особенностей',
    objective_data: 'Жалоб нет. Объективно: кожные покровы чистые, периферические лимфоузлы не увеличены. Живот мягкий, безболезненный. Грыжевых выпячиваний нет.',
    special_research_results: null,
    od_vision_without_correction: null,
    os_vision_without_correction: null,
    valid_category: 'А',
    diagnosis_main_id: '000.0', // Основной диагноз: ЗДОРОВ (обязательное поле!)
    diagnosis_accompany_id: null, // Сопутствующий диагноз
    additional_act_comment: null,
  },
  'Терапевт': {
    complain: 'Периодическая изжога, тяжесть в эпигастральной области после еды',
    anamnesis: 'Хронический гастрит около 2 лет',
    objective_data: 'Живот мягкий, безболезненный при пальпации. Печень не увеличена.',
    special_research_results: 'ФГДС: хронический поверхностный гастрит',
    od_vision_without_correction: null,
    os_vision_without_correction: null,
    valid_category: 'А',
    diagnosis_main_id: 'K29.3', // Основной диагноз: Хронический поверхностный гастрит (обязательное поле!)
    diagnosis_accompany_id: null, // Сопутствующий диагноз
    additional_act_comment: null,
  },
  'Невролог': {
    complain: 'нет',
    anamnesis: 'без особенностей',
    objective_data: 'Сознание ясное. Менингеальных и очаговых неврологических симптомов нет. Черепно-мозговые нервы без патологии. Мышечный тонус в норме. Сухожильные рефлексы живые, симметричные. Чувствительность сохранена. Координация не нарушена.',
    special_research_results: null,
    od_vision_without_correction: null,
    os_vision_without_correction: null,
    valid_category: 'А',
    diagnosis_main_id: 'Z00.0', // Основной диагноз: ЗДОРОВ (обязательное поле!)
    diagnosis_accompany_id: null, // Сопутствующий диагноз
    additional_act_comment: 'Неврологических отклонений не выявлено',
  },
}

export default function ExaminationForm({ currentUser, conscriptId, onOpenAIAnalysis }: ExaminationFormProps) {
  const { updateConscriptExamination, getConscript } = useData()

  const [isEditing, setIsEditing] = useState(false)
  const [selectedDoctor, setSelectedDoctor] = useState<string | null>(
    currentUser.role === 'chairman' ? null : currentUser.specialty || null
  )

  const [formData, setFormData] = useState(
    selectedDoctor ? mockExaminationData[selectedDoctor] || {} : {}
  )

  const [icd10Codes, setIcd10Codes] = useState<ICD10Code[]>([])

  // Список врачей-специалистов из API
  const [requiredSpecialists, setRequiredSpecialists] = useState<string[]>([])

  // Получаем данные призывника для проверки статуса освидетельствования
  const conscript = conscriptId ? getConscript(conscriptId) : undefined

  // Загружаем список обязательных специалистов из API
  useEffect(() => {
    const fetchRequiredSpecialists = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/ai/required-specialists')
        const data = await response.json()
        setRequiredSpecialists(data.required_specialists || [])
      } catch (error) {
        console.error('Ошибка загрузки списка специалистов:', error)
      }
    }
    fetchRequiredSpecialists()
  }, [])

  // Функция для проверки завершения освидетельствования у конкретного врача
  const isDoctorCompleted = (specialty: string): boolean => {
    if (!conscript) return false

    // Ищем по specialtyRu (русское название с заглавной буквы)
    const examination = conscript.examinations?.find(exam =>
      exam.specialtyRu === specialty || exam.specialty === specialty
    )

    // Врач считается завершившим освидетельствование, если:
    // 1. Есть запись обследования
    // 2. Есть категория годности (обязательное поле)
    // 3. Есть диагноз (код МКБ-10 и текст диагноза - оба обязательные поля)
    // 4. Есть заключение (conclusion_text - обязательное поле)
    // 5. Указано имя врача (doctor_name)
    if (!examination) {
      console.log(`[isDoctorCompleted] ${specialty} => false (нет записи обследования)`)
      return false
    }

    // Проверяем обязательные поля из модели SpecialistExamination
    const hasCategory = examination.doctorCategory && examination.doctorCategory.trim() !== ''
    const hasIcd10Code = examination.icd10Codes && examination.icd10Codes.length > 0 && examination.icd10Codes[0].trim() !== ''
    const hasDiagnosisText = examination.conclusion && examination.conclusion.trim() !== ''
    const hasDoctorName = examination.doctorName && examination.doctorName.trim() !== ''

    const result = Boolean(hasCategory && hasIcd10Code && hasDiagnosisText && hasDoctorName)

    console.log(`[isDoctorCompleted] ${specialty} => ${result}`, {
      hasCategory,
      hasIcd10Code,
      hasDiagnosisText,
      hasDoctorName,
      examination
    })

    return result
  }

  // Функция для получения категории годности врача
  const getDoctorCategory = (specialty: string): string | null => {
    if (!conscript) return null
    const examination = conscript.examinations?.find(exam =>
      exam.specialtyRu === specialty || exam.specialty === specialty
    )

    // Показываем категорию только если освидетельствование завершено
    if (!examination) return null

    // Используем ту же логику проверки, что и в isDoctorCompleted
    const isCompleted = isDoctorCompleted(specialty)
    return isCompleted ? examination.doctorCategory : null
  }

  // Загрузить коды МКБ-10 при монтировании компонента
  useEffect(() => {
    const loadICD10Codes = async () => {
      try {
        const response = await fetch('/icd10_codes.json')
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`)
        }
        const codes: ICD10Code[] = await response.json()
        setIcd10Codes(codes)
      } catch (error) {
        console.error('⚠ Ошибка загрузки кодов МКБ-10:', error)
      }
    }

    loadICD10Codes()
  }, [])

  // Загрузить данные при изменении выбранного врача или призывника
  useEffect(() => {
    if (selectedDoctor && conscript) {
      const examination = conscript.examinations?.find(exam => exam.specialty === selectedDoctor)
      if (examination) {
        // Загружаем реальные данные
        setFormData({
          complain: examination.complaints || '',
          anamnesis: examination.anamnesis || '',
          objective_data: examination.objectiveData || '',
          special_research_results: examination.specialResearchResults || '',
          valid_category: examination.doctorCategory || '',
          diagnosis_main_id: examination.icd10Codes?.[0] || '',
          additional_act_comment: examination.conclusion || '',
          od_vision_without_correction: examination.od_vision_without_correction || null,
          os_vision_without_correction: examination.os_vision_without_correction || null,
          dentist_json: examination.dentist_json || null,
        })
      }
    }
  }, [selectedDoctor, conscript])

  // Вспомогательная функция для получения полного названия диагноза
  const getDiagnosisDisplay = (code: string | null): string => {
    if (!code) return '---'
    const diagnosis = icd10Codes.find((d) => d.code === code)
    return diagnosis ? `${diagnosis.code} - ${diagnosis.name}` : code
  }

  const handleDoctorSelect = (specialty: string) => {
    setSelectedDoctor(specialty)

    // Загружаем ТОЛЬКО реальные данные из призывника
    if (conscript) {
      const examination = conscript.examinations?.find(exam =>
        exam.specialty === specialty || exam.specialtyRu === specialty
      )

      console.log(`[handleDoctorSelect] specialty="${specialty}", найден осмотр:`, examination)
      console.log(`[handleDoctorSelect] complaints:`, examination?.complaints)
      console.log(`[handleDoctorSelect] anamnesis:`, examination?.anamnesis)
      console.log(`[handleDoctorSelect] objectiveData:`, examination?.objectiveData)

      if (examination) {
        // Есть реальные данные - загружаем их
        const formDataToSet = {
          complain: examination.complaints || '',
          anamnesis: examination.anamnesis || '',
          objective_data: examination.objectiveData || '',
          special_research_results: examination.specialResearchResults || '',
          valid_category: examination.doctorCategory || '',
          diagnosis_main_id: examination.icd10Codes?.[0] || '',
          additional_act_comment: examination.conclusion || '',
          // Специфичные поля для офтальмолога
          od_vision_without_correction: examination.od_vision_without_correction || null,
          os_vision_without_correction: examination.os_vision_without_correction || null,
          // Специфичное поле для стоматолога
          dentist_json: examination.dentist_json || null,
        }
        console.log(`[handleDoctorSelect] Устанавливаем formData:`, formDataToSet)
        setFormData(formDataToSet)
      } else {
        // Нет данных - пустая форма
        setFormData({
          complain: '',
          anamnesis: '',
          objective_data: '',
          special_research_results: '',
          valid_category: '',
          diagnosis_main_id: '',
          additional_act_comment: '',
          od_vision_without_correction: null,
          os_vision_without_correction: null,
          dentist_json: null,
        })
      }
    } else {
      // Нет призывника - пустая форма
      setFormData({})
    }

    setIsEditing(false)
  }

  const handleInputChange = (field: string, value: string | Record<string, string>) => {
    setFormData((prev: any) => ({
      ...prev,
      [field]: value,
    }))
  }

  const handleSave = async () => {
    if (!conscriptId || !selectedDoctor) {
      console.warn('Не указан призывник или специалист')
      return
    }

    try {
      // Подготавливаем данные для API
      const apiData = {
        conscript_draft_id: conscriptId,
        specialty: selectedDoctor,
        specialty_ru: selectedDoctor,
        doctor_name: currentUser.name,
        complaints: formData.complain || null,
        anamnesis: formData.anamnesis || null,
        objective_data: formData.objective_data || null,
        special_research_results: formData.special_research_results || null,
        conclusion_text: formData.objective_data || formData.additional_act_comment || 'Осмотр проведен',
        icd10_code: formData.diagnosis_main_id || 'Z00.0',
        diagnosis_text: formData.additional_act_comment || 'Диагноз не указан',
        doctor_category: formData.valid_category || 'А',
        additional_comment: formData.additional_act_comment || null,
        examination_date: new Date().toISOString().split('T')[0], // YYYY-MM-DD
        // Специфичные поля для офтальмолога
        od_vision_without_correction: formData.od_vision_without_correction || null,
        os_vision_without_correction: formData.os_vision_without_correction || null,
        // Специфичное поле для стоматолога
        dentist_json: formData.dentist_json || null,
      }

      // Проверяем, существует ли уже осмотр (обновление или создание)
      const checkResponse = await fetch(
        `http://localhost:8000/api/v1/examinations/${conscriptId}/${selectedDoctor}`
      )

      let response
      if (checkResponse.ok) {
        // Осмотр существует - обновляем (PUT)
        response = await fetch(
          `http://localhost:8000/api/v1/examinations/${conscriptId}/${selectedDoctor}`,
          {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify(apiData),
          }
        )
      } else {
        // Осмотр не существует - создаем (POST)
        response = await fetch('http://localhost:8000/api/v1/examinations', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify(apiData),
        })
      }

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Ошибка при сохранении данных')
      }

      const savedExamination = await response.json()
      console.log('✅ Данные успешно сохранены на сервере:', savedExamination)

      // Обновляем локальный Context
      const examination = {
        specialty: selectedDoctor,
        doctorName: currentUser.name,
        conclusion: formData.objective_data || '',
        icd10Codes: formData.diagnosis_main_id ? [formData.diagnosis_main_id] : [],
        doctorCategory: formData.valid_category || 'А',
        isSaved: true,
        savedAt: new Date().toISOString(),
      }

      updateConscriptExamination(conscriptId, selectedDoctor, examination)
      setIsEditing(false)

      console.log(`✅ Сохранено заключение ${selectedDoctor} для призывника #${conscriptId}`)
    } catch (error) {
      console.error('❌ Ошибка при сохранении:', error)
      alert(`Ошибка при сохранении данных: ${error}`)
    }
  }

  const handleCancel = () => {
    setIsEditing(false)
    // Восстановить данные
    if (selectedDoctor) {
      setFormData(mockExaminationData[selectedDoctor] || {})
    }
  }

  return (
    <div className="examination-form">
      <div className="examination-header">
        <h3>Освидетельствование</h3>
        <div className="examination-actions">
          {currentUser.role === 'chairman' && onOpenAIAnalysis && (
            <button className="btn-ai-analysis" onClick={onOpenAIAnalysis}>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path
                  d="M12 2L2 7L12 12L22 7L12 2Z"
                  stroke="currentColor"
                  strokeWidth="2"
                />
              </svg>
              ИИ Анализ
            </button>
          )}
          {selectedDoctor && !isEditing && currentUser.role === 'doctor' && (
            <button className="btn-edit" onClick={() => setIsEditing(true)}>
              <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
                <path
                  d="M11.3333 2.00004C11.5084 1.82494 11.7163 1.68605 11.9451 1.59129C12.1739 1.49653 12.4191 1.44775 12.6666 1.44775C12.9142 1.44775 13.1594 1.49653 13.3882 1.59129C13.617 1.68605 13.8249 1.82494 14 2.00004C14.1751 2.17513 14.314 2.383 14.4087 2.61178C14.5035 2.84055 14.5523 3.08575 14.5523 3.33337C14.5523 3.58099 14.5035 3.82619 14.4087 4.05497C14.314 4.28374 14.1751 4.49161 14 4.66671L5.00001 13.6667L1.33334 14.6667L2.33334 11L11.3333 2.00004Z"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
              Редактировать
            </button>
          )}
        </div>
      </div>

      {/* Список врачей для председателя */}
      {currentUser.role === 'chairman' && (
        <div className="doctors-list">
          {requiredSpecialists.map((specialty, index) => {
            const isCompleted = isDoctorCompleted(specialty)
            const category = getDoctorCategory(specialty)
            // Получаем данные врача из examinations призывника
            const examination = conscript?.examinations?.find(e => e.specialtyRu === specialty || e.specialty === specialty)
            const doctorName = examination?.doctorName || specialty

            return (
              <button
                key={index}
                className={`doctor-card ${selectedDoctor === specialty ? 'active' : ''} ${isCompleted ? 'completed' : 'pending'}`}
                onClick={() => handleDoctorSelect(specialty)}
              >
                <div className="doctor-photo">
                  <svg width="40" height="40" viewBox="0 0 48 48" fill="none">
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
                <div className="doctor-info">
                  <div className="doctor-name">{doctorName}</div>
                  <div className="doctor-specialty">{specialty}</div>
                  {/* Категория годности */}
                  {category && (
                    <div className="doctor-category-badge">{category}</div>
                  )}
                </div>
                {/* Индикатор статуса завершения */}
                <div className={`completion-indicator ${isCompleted ? 'completed' : 'pending'}`}>
                  {isCompleted ? (
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                      <circle cx="10" cy="10" r="10" fill="#10b981"/>
                      <path d="M6 10L8.5 12.5L14 7" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                    </svg>
                  ) : (
                    <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
                      <circle cx="10" cy="10" r="9" stroke="#94a3b8" strokeWidth="2" fill="none"/>
                      <circle cx="10" cy="10" r="3" fill="#94a3b8"/>
                    </svg>
                  )}
                </div>
              </button>
            )
          })}
        </div>
      )}

      {/* Форма освидетельствования */}
      {selectedDoctor ? (
        <div className="examination-form-content">
          <div className="form-section">
            <div className="form-field">
              <label className="form-label">Дата и время приема:</label>
              {isEditing ? (
                <input
                  type="text"
                  className="form-input"
                  value={formData.appointment_date || '04.12.2025 15:05'}
                  onChange={(e) => handleInputChange('appointment_date', e.target.value)}
                  disabled
                />
              ) : (
                <div className="form-value">{formData.appointment_date || '04.12.2025 15:05'}</div>
              )}
            </div>

            <div className="form-field">
              <label className="form-label">Жалобы:</label>
              {isEditing ? (
                <textarea
                  className="form-textarea"
                  value={formData.complain || ''}
                  onChange={(e) => handleInputChange('complain', e.target.value)}
                  rows={3}
                />
              ) : (
                <div className="form-value">{formData.complain || '---'}</div>
              )}
            </div>

            <div className="form-field">
              <label className="form-label">Анамнез:</label>
              {isEditing ? (
                <textarea
                  className="form-textarea"
                  value={formData.anamnesis || ''}
                  onChange={(e) => handleInputChange('anamnesis', e.target.value)}
                  rows={3}
                />
              ) : (
                <div className="form-value">{formData.anamnesis || '---'}</div>
              )}
            </div>

            <div className="form-field">
              <label className="form-label">Основной диагноз (МКБ-10): *</label>
              {isEditing ? (
                <ICD10Search
                  value={formData.diagnosis_main_id || null}
                  onChange={(code) => handleInputChange('diagnosis_main_id', code || '')}
                  placeholder="Введите код или название болезни"
                  required={true}
                />
              ) : (
                <div className="form-value">{getDiagnosisDisplay(formData.diagnosis_main_id)}</div>
              )}
            </div>

            <div className="form-field">
              <label className="form-label">Сопутствующий диагноз (МКБ-10):</label>
              {isEditing ? (
                <ICD10Search
                  value={formData.diagnosis_accompany_id || null}
                  onChange={(code) => handleInputChange('diagnosis_accompany_id', code || '')}
                  placeholder="Введите код или название болезни (необязательно)"
                  required={false}
                />
              ) : (
                <div className="form-value">{getDiagnosisDisplay(formData.diagnosis_accompany_id)}</div>
              )}
            </div>

            <div className="form-field">
              <label className="form-label">Данные объективного обследования:</label>
              {isEditing ? (
                <textarea
                  className="form-textarea"
                  value={formData.objective_data || ''}
                  onChange={(e) => handleInputChange('objective_data', e.target.value)}
                  rows={4}
                />
              ) : (
                <div className="form-value">{formData.objective_data || '---'}</div>
              )}
            </div>

            <div className="form-field">
              <label className="form-label">Результаты специальных исследований:</label>
              {isEditing ? (
                <textarea
                  className="form-textarea"
                  value={formData.special_research_results || ''}
                  onChange={(e) =>
                    handleInputChange('special_research_results', e.target.value)
                  }
                  rows={3}
                />
              ) : (
                <div className="form-value">
                  {formData.special_research_results || '---'}
                </div>
              )}
            </div>

            <div className="form-field">
              <label className="form-label">Примечания</label>
              {isEditing ? (
                <textarea
                  className="form-textarea"
                  value={formData.notes || ''}
                  onChange={(e) => handleInputChange('notes', e.target.value)}
                  rows={3}
                />
              ) : (
                <div className="form-value">{formData.notes || '---'}</div>
              )}
            </div>

            {/* Поля для офтальмолога */}
            {selectedDoctor === 'Офтальмолог' && (
              <div className="form-grid">
                <div className="form-field">
                  <label className="form-label">
                    Зрение OD без коррекции (od_vision_without_correction)
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      className="form-input"
                      value={formData.od_vision_without_correction || ''}
                      onChange={(e) =>
                        handleInputChange('od_vision_without_correction', e.target.value)
                      }
                    />
                  ) : (
                    <div className="form-value font-code">
                      {formData.od_vision_without_correction || '---'}
                    </div>
                  )}
                </div>

                <div className="form-field">
                  <label className="form-label">
                    Зрение OS без коррекции (os_vision_without_correction)
                  </label>
                  {isEditing ? (
                    <input
                      type="text"
                      className="form-input"
                      value={formData.os_vision_without_correction || ''}
                      onChange={(e) =>
                        handleInputChange('os_vision_without_correction', e.target.value)
                      }
                    />
                  ) : (
                    <div className="form-value font-code">
                      {formData.os_vision_without_correction || '---'}
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Поля для стоматолога */}
            {selectedDoctor === 'Стоматолог' && (
              <div className="form-field">
                <label className="form-label">Зубная формула (dentist_json):</label>
                {isEditing ? (
                  <DentistChart
                    value={formData.dentist_json}
                    onChange={(value) => handleInputChange('dentist_json', value)}
                  />
                ) : (
                  <DentistChart
                    value={formData.dentist_json}
                    onChange={() => {}}
                    disabled={true}
                  />
                )}
              </div>
            )}

            <div className="form-field">
              <label className="form-label">Категории годности: *</label>
              <div className="radio-group">
                <label className="radio-label">
                  <input
                    type="radio"
                    name="valid_category"
                    value="А"
                    checked={formData.valid_category === 'А'}
                    onChange={(e) => handleInputChange('valid_category', e.target.value)}
                    disabled={!isEditing}
                  />
                  <span><strong>А</strong> — Годен к воинской службе</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="valid_category"
                    value="Б"
                    checked={formData.valid_category === 'Б'}
                    onChange={(e) => handleInputChange('valid_category', e.target.value)}
                    disabled={!isEditing}
                  />
                  <span><strong>Б</strong> — Годен к воинской службе с незначительными ограничениями</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="valid_category"
                    value="В"
                    checked={formData.valid_category === 'В'}
                    onChange={(e) => handleInputChange('valid_category', e.target.value)}
                    disabled={!isEditing}
                  />
                  <span><strong>В</strong> — Ограниченно годен к воинской службе</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="valid_category"
                    value="Г"
                    checked={formData.valid_category === 'Г'}
                    onChange={(e) => handleInputChange('valid_category', e.target.value)}
                    disabled={!isEditing}
                  />
                  <span><strong>Г</strong> — Временно не годен к воинской службе</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="valid_category"
                    value="Д"
                    checked={formData.valid_category === 'Д'}
                    onChange={(e) => handleInputChange('valid_category', e.target.value)}
                    disabled={!isEditing}
                  />
                  <span><strong>Д</strong> — Не годен к воинской службе в мирное время, ограниченно годен в военное время</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="valid_category"
                    value="Е"
                    checked={formData.valid_category === 'Е'}
                    onChange={(e) => handleInputChange('valid_category', e.target.value)}
                    disabled={!isEditing}
                  />
                  <span><strong>Е</strong> — Не годен к воинской службе с исключением с воинского учета</span>
                </label>
                <label className="radio-label">
                  <input
                    type="radio"
                    name="valid_category"
                    value="направить"
                    checked={formData.valid_category === 'направить'}
                    onChange={(e) => handleInputChange('valid_category', e.target.value)}
                    disabled={!isEditing}
                  />
                  <span>Направить на обследование</span>
                </label>
              </div>
            </div>

            <div className="form-grid">

              <div className="form-field">
                <label className="form-label">
                  Код сопутствующего диагноза (diagnosis_accompany_id)
                </label>
                {isEditing ? (
                  <input
                    type="text"
                    className="form-input"
                    value={formData.diagnosis_accompany_id || ''}
                    onChange={(e) =>
                      handleInputChange('diagnosis_accompany_id', e.target.value)
                    }
                  />
                ) : (
                  <div className="form-value font-code">
                    {formData.diagnosis_accompany_id || '---'}
                  </div>
                )}
              </div>
            </div>

            <div className="form-field">
              <label className="form-label">
                Дополнительный комментарий (additional_act_comment)
              </label>
              {isEditing ? (
                <textarea
                  className="form-textarea"
                  value={formData.additional_act_comment || ''}
                  onChange={(e) =>
                    handleInputChange('additional_act_comment', e.target.value)
                  }
                  rows={2}
                />
              ) : (
                <div className="form-value">
                  {formData.additional_act_comment || '---'}
                </div>
              )}
            </div>
          </div>

          {/* Кнопки сохранения/отмены */}
          {isEditing && (
            <div className="form-actions">
              <button className="btn-cancel" onClick={handleCancel}>
                Отмена
              </button>
              <button className="btn-save" onClick={handleSave}>
                Сохранить
              </button>
            </div>
          )}
        </div>
      ) : (
        <div className="examination-empty">
          <div className="empty-message">
            Выберите врача для просмотра данных освидетельствования
          </div>
        </div>
      )}
    </div>
  )
}
