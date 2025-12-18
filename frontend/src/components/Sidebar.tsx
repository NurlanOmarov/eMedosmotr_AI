import { motion } from 'framer-motion'
import { useState } from 'react'
import type { User } from '../App'
import './Sidebar.css'

interface SidebarItem {
  id: string
  icon: string
  label: string
  badge?: string
  status?: 'active' | 'inactive' | 'warning'
  roleAccess?: ('doctor' | 'chairman')[]
}

interface SidebarProps {
  currentUser: User
  activeSection: string
  onSectionChange: (sectionId: string) => void
}

const sidebarItems: SidebarItem[] = [
  {
    id: 'dashboard',
    icon: '📊',
    label: 'Дэшборд',
    roleAccess: ['chairman'],
    status: 'active',
  },
  {
    id: 'conscripts',
    icon: '👥',
    label: 'Призывники',
    status: 'active',
  },
  {
    id: 'specialists',
    icon: '👨‍⚕️',
    label: 'Врачи-специалисты',
    roleAccess: ['chairman'],
  },
  {
    id: 'dispensary',
    icon: '📋',
    label: 'Диспансер',
    roleAccess: ['doctor'],
    status: 'inactive',
  },
  {
    id: 'hospital',
    icon: '🏥',
    label: 'Госпитализация',
    roleAccess: ['doctor'],
    status: 'inactive',
  },
  {
    id: 'vaccination',
    icon: '💉',
    label: 'Вакцинация',
    roleAccess: ['doctor'],
    badge: '✓',
  },
  {
    id: 'reports',
    icon: '📈',
    label: 'Отчёты',
    roleAccess: ['chairman'],
  },
  {
    id: 'history',
    icon: '📜',
    label: 'История',
    roleAccess: ['doctor'],
  },
  {
    id: 'analytics',
    icon: '🤖',
    label: 'Аналитика AI',
    roleAccess: ['chairman'],
  },
]

export default function Sidebar({ currentUser, activeSection, onSectionChange }: SidebarProps) {
  const [activeId, setActiveId] = useState(activeSection)
  const [collapsed, setCollapsed] = useState(false)

  // Фильтруем элементы по ролям
  const filteredItems = sidebarItems.filter(item => {
    if (!item.roleAccess) return true
    return item.roleAccess.includes(currentUser.role)
  })

  return (
    <motion.aside
      className={`sidebar ${collapsed ? 'sidebar-collapsed' : ''}`}
      initial={{ x: -100, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ type: 'spring', stiffness: 100, damping: 20, delay: 0.1 }}
    >
      {/* Collapse toggle */}
      <button
        className="sidebar-toggle"
        onClick={() => setCollapsed(!collapsed)}
        title={collapsed ? 'Развернуть' : 'Свернуть'}
      >
        <svg
          width="16"
          height="16"
          viewBox="0 0 16 16"
          fill="none"
          style={{
            transform: collapsed ? 'rotate(180deg)' : 'rotate(0deg)',
            transition: 'transform 0.3s ease',
          }}
        >
          <path
            d="M10 12L6 8L10 4"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="square"
          />
        </svg>
      </button>

      {/* Role indicator */}
      {!collapsed && (
        <div className={`sidebar-role-indicator role-${currentUser.role}`}>
          <span className="sidebar-role-icon">
            {currentUser.role === 'chairman' ? '★' : '●'}
          </span>
          <span className="sidebar-role-text">
            {currentUser.role === 'chairman' ? 'ПРЕДСЕДАТЕЛЬ' : currentUser.specialty || 'ВРАЧ'}
          </span>
        </div>
      )}

      {/* Sidebar items */}
      <nav className="sidebar-nav">
        {filteredItems.map((item, index) => (
          <motion.button
            key={item.id}
            className={`sidebar-item ${activeSection === item.id ? 'sidebar-item-active' : ''}`}
            onClick={() => {
              setActiveId(item.id)
              onSectionChange(item.id)
            }}
            initial={{ x: -50, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            transition={{ delay: 0.1 + index * 0.05 }}
            whileHover={{ x: 4 }}
            whileTap={{ scale: 0.98 }}
          >
            {/* Icon */}
            <div className="sidebar-item-icon">
              <span className="sidebar-icon-emoji">{item.icon}</span>
              {item.status && (
                <div className={`sidebar-status-dot sidebar-status-${item.status}`} />
              )}
            </div>

            {/* Content */}
            {!collapsed && (
              <div className="sidebar-item-content">
                <div className="sidebar-item-label">{item.label}</div>
                {item.badge && <div className="sidebar-item-badge">{item.badge}</div>}
              </div>
            )}

            {/* Active indicator */}
            {activeSection === item.id && <div className="sidebar-item-indicator" />}
          </motion.button>
        ))}
      </nav>

      {/* Bottom section */}
      {!collapsed && (
        <motion.div
          className="sidebar-footer"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.5 }}
        >
          <div className="sidebar-footer-label">БЫСТРЫЕ ДЕЙСТВИЯ</div>
          <button className="sidebar-footer-btn">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path
                d="M8 2V14M2 8H14"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="square"
              />
            </svg>
            <span>Новый призывник</span>
          </button>
          <button className="sidebar-footer-btn">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
              <path
                d="M14 10V12.6667C14 13.0203 13.8595 13.3594 13.6095 13.6095C13.3594 13.8595 13.0203 14 12.6667 14H3.33333C2.97971 14 2.64057 13.8595 2.39052 13.6095C2.14048 13.3594 2 13.0203 2 12.6667V10M11.3333 5.33333L8 2M8 2L4.66667 5.33333M8 2V10"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="square"
              />
            </svg>
            <span>Экспорт данных</span>
          </button>
        </motion.div>
      )}
    </motion.aside>
  )
}
