import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { Conscript } from '../types'
import type { User, UserRole } from '../App'
import './Header.css'

interface HeaderProps {
  conscript: Conscript | null
  systemStatus: 'healthy' | 'degraded' | 'down'
  currentUser: User
  availableUsers: User[]
  onUserChange: (user: User) => void
}

export default function Header({
  conscript,
  systemStatus,
  currentUser,
  availableUsers,
  onUserChange
}: HeaderProps) {
  const [isUserMenuOpen, setIsUserMenuOpen] = useState(false)

  const statusColors = {
    healthy: 'var(--color-primary)',
    degraded: 'var(--color-warning)',
    down: 'var(--color-danger)',
  }

  const statusLabels = {
    healthy: 'СИСТЕМА АКТИВНА',
    degraded: 'ОГРАНИЧЕННАЯ РАБОТА',
    down: 'СИСТЕМА НЕДОСТУПНА',
  }

  const roleLabels: Record<UserRole, string> = {
    doctor: 'ВРАЧ-СПЕЦИАЛИСТ',
    chairman: 'ПРЕДСЕДАТЕЛЬ ВВК',
  }

  const roleColors: Record<UserRole, string> = {
    doctor: 'var(--color-warning)',
    chairman: 'var(--color-primary)',
  }

  return (
    <motion.header
      className="header"
      initial={{ y: -100 }}
      animate={{ y: 0 }}
      transition={{ type: 'spring', stiffness: 100, damping: 20 }}
    >
      <div className="header-grid">
        {/* Left: System info */}
        <div className="header-section">
          <div className="header-logo">
            <img src="/logo.png" alt="eMedosmotr" className="logo-image" />
            <div className="logo-text">
              <div className="logo-title font-code">eMEDOSMOTR</div>
              <div className="logo-subtitle">AI Powered</div>
            </div>
          </div>
        </div>

        {/* Center: Empty space for cleaner look */}
        <div className="header-section header-center">
        </div>

        {/* Right: User selector & Status */}
        <div className="header-section header-right">
          {/* User/Role Selector */}
          <div className="user-selector-wrapper">
            <button
              className="user-selector"
              onClick={() => setIsUserMenuOpen(!isUserMenuOpen)}
              style={{ '--role-color': roleColors[currentUser.role] } as React.CSSProperties}
            >
              <div className="user-avatar">
                {currentUser.role === 'chairman' ? (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                ) : (
                  <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path
                      d="M20 21V19C20 17.9391 19.5786 16.9217 18.8284 16.1716C18.0783 15.4214 17.0609 15 16 15H8C6.93913 15 5.92172 15.4214 5.17157 16.1716C4.42143 16.9217 4 17.9391 4 19V21"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                    <circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="2" />
                  </svg>
                )}
              </div>
              <div className="user-info">
                <div className="user-name font-code">{currentUser.name}</div>
                <div className="user-role" style={{ color: roleColors[currentUser.role] }}>
                  {roleLabels[currentUser.role]}
                  {currentUser.specialty && ` • ${currentUser.specialty}`}
                </div>
              </div>
              <div className={`user-dropdown-arrow ${isUserMenuOpen ? 'open' : ''}`}>
                <svg width="12" height="12" viewBox="0 0 12 12" fill="none">
                  <path
                    d="M3 4.5L6 7.5L9 4.5"
                    stroke="currentColor"
                    strokeWidth="1.5"
                    strokeLinecap="square"
                  />
                </svg>
              </div>
            </button>

            {/* User Dropdown Menu */}
            <AnimatePresence>
              {isUserMenuOpen && (
                <>
                  <motion.div
                    className="user-menu-backdrop"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={() => setIsUserMenuOpen(false)}
                  />
                  <motion.div
                    className="user-menu"
                    initial={{ opacity: 0, y: -10, scale: 0.95 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -10, scale: 0.95 }}
                    transition={{ duration: 0.15 }}
                  >
                    <div className="user-menu-header">
                      <span className="user-menu-title font-code">ВЫБОР АККАУНТА</span>
                      <span className="user-menu-hint">(без авторизации)</span>
                    </div>

                    <div className="user-menu-section">
                      <div className="user-menu-section-title">ПРЕДСЕДАТЕЛЬ</div>
                      {availableUsers
                        .filter(u => u.role === 'chairman')
                        .map(user => (
                          <button
                            key={user.id}
                            className={`user-menu-item ${currentUser.id === user.id ? 'active' : ''}`}
                            onClick={() => {
                              onUserChange(user)
                              setIsUserMenuOpen(false)
                            }}
                          >
                            <div className="user-menu-item-icon chairman">
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                                <path
                                  d="M12 2L15.09 8.26L22 9.27L17 14.14L18.18 21.02L12 17.77L5.82 21.02L7 14.14L2 9.27L8.91 8.26L12 2Z"
                                  stroke="currentColor"
                                  strokeWidth="2"
                                />
                              </svg>
                            </div>
                            <span className="user-menu-item-name">{user.name}</span>
                            {currentUser.id === user.id && (
                              <span className="user-menu-item-check">✓</span>
                            )}
                          </button>
                        ))}
                    </div>

                    <div className="user-menu-section">
                      <div className="user-menu-section-title">ВРАЧИ-СПЕЦИАЛИСТЫ</div>
                      {availableUsers
                        .filter(u => u.role === 'doctor')
                        .map(user => (
                          <button
                            key={user.id}
                            className={`user-menu-item ${currentUser.id === user.id ? 'active' : ''}`}
                            onClick={() => {
                              onUserChange(user)
                              setIsUserMenuOpen(false)
                            }}
                          >
                            <div className="user-menu-item-icon doctor">
                              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                                <path
                                  d="M20 21V19C20 16.79 18.21 15 16 15H8C5.79 15 4 16.79 4 19V21"
                                  stroke="currentColor"
                                  strokeWidth="2"
                                />
                                <circle cx="12" cy="7" r="4" stroke="currentColor" strokeWidth="2" />
                              </svg>
                            </div>
                            <div className="user-menu-item-info">
                              <span className="user-menu-item-name">{user.name}</span>
                              <span className="user-menu-item-specialty">{user.specialty}</span>
                            </div>
                            {currentUser.id === user.id && (
                              <span className="user-menu-item-check">✓</span>
                            )}
                          </button>
                        ))}
                    </div>
                  </motion.div>
                </>
              )}
            </AnimatePresence>
          </div>

          <button className="header-btn" title="Уведомления">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path
                d="M15 6.66667C15 5.34058 14.4732 4.06881 13.5355 3.13113C12.5979 2.19345 11.3261 1.66667 10 1.66667C8.67392 1.66667 7.40215 2.19345 6.46447 3.13113C5.52678 4.06881 5 5.34058 5 6.66667C5 12.5 2.5 14.1667 2.5 14.1667H17.5C17.5 14.1667 15 12.5 15 6.66667Z"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
              <path
                d="M11.4417 17.5C11.2952 17.7526 11.0849 17.9622 10.8319 18.1079C10.5789 18.2537 10.2922 18.3304 10 18.3304C9.70781 18.3304 9.42116 18.2537 9.16816 18.1079C8.91515 17.9622 8.70486 17.7526 8.55835 17.5"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>

          <button className="header-btn" title="Настройки">
            <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
              <path
                d="M10 12.5C11.3807 12.5 12.5 11.3807 12.5 10C12.5 8.61929 11.3807 7.5 10 7.5C8.61929 7.5 7.5 8.61929 7.5 10C7.5 11.3807 8.61929 12.5 10 12.5Z"
                stroke="currentColor"
                strokeWidth="1.5"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>
      </div>

      {/* Brutal bottom border */}
      <div className="header-border"></div>
    </motion.header>
  )
}
