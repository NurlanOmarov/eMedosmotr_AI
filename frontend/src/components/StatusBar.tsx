import { motion } from 'framer-motion'
import type { User } from '../App'
import './StatusBar.css'

interface StatusBarProps {
  systemStatus: 'healthy' | 'degraded' | 'down'
  currentUser: User
}

export default function StatusBar({ systemStatus, currentUser }: StatusBarProps) {
  const statusMessages = {
    healthy: 'ВСЕ СИСТЕМЫ РАБОТАЮТ НОРМАЛЬНО',
    degraded: 'РЕЖИМ ДЕМОНСТРАЦИИ (mock данные)',
    down: 'КРИТИЧЕСКАЯ ОШИБКА СИСТЕМЫ',
  }

  const statusIcons = {
    healthy: '✓',
    degraded: '⚠',
    down: '✕',
  }

  return (
    <motion.footer
      className={`status-bar status-bar-${systemStatus}`}
      initial={{ y: 100 }}
      animate={{ y: 0 }}
      transition={{ type: 'spring', stiffness: 100, damping: 20, delay: 0.2 }}
    >
      <div className="status-bar-content">
        {/* Left: System status */}
        <div className="status-bar-section">
          <div className="status-indicator">
            <span className="status-icon font-code">{statusIcons[systemStatus]}</span>
            <span className="status-message font-code">{statusMessages[systemStatus]}</span>
          </div>
        </div>

        {/* Center: Version & Info */}
        <div className="status-bar-section status-bar-center">
          <div className="status-info font-mono">
            <span className="status-info-item">v1.0.0-MVP</span>
            <span className="status-separator">|</span>
            <span className="status-info-item">AI: GPT-4O-MINI</span>
            <span className="status-separator">|</span>
            <span className="status-info-item">DB: PostgreSQL+pgvector</span>
            <span className="status-separator">|</span>
            <span className="status-info-item status-user">
              {currentUser.role === 'chairman' ? '★' : '●'} {currentUser.name}
            </span>
          </div>
        </div>

        {/* Right: Copyright */}
        <div className="status-bar-section status-bar-right">
          <div className="status-copyright font-mono">
            © 2025 eMedosmotr AI System
          </div>
        </div>
      </div>
    </motion.footer>
  )
}
