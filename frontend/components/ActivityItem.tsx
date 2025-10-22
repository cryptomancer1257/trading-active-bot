'use client'

import { formatDistanceToNow } from 'date-fns'
import Link from 'next/link'

interface Activity {
  id: string
  type: 'TRADE' | 'RISK_ALERT' | 'BOT_EXECUTION'
  timestamp: string
  bot_name: string
  bot_id?: number
  subscription_id?: number
  
  // Trade specific
  action?: string
  symbol?: string
  price?: number
  quantity?: number
  balance?: number
  pnl?: number
  is_profit?: boolean
  status?: string  // OPEN or CLOSED
  exchange?: string
  details?: string
  
  // Risk alert specific
  alert_type?: string
  message?: string
  severity?: string
  
  // Bot execution specific
  next_run?: string
}

export default function ActivityItem({ activity }: { activity: Activity }) {
  const getTimeAgo = (timestamp: string) => {
    try {
      return formatDistanceToNow(new Date(timestamp), { addSuffix: true })
    } catch {
      return 'Recently'
    }
  }

  // Render TRADE activity
  if (activity.type === 'TRADE') {
    const actionColor = activity.action === 'BUY' ? 'text-green-400' : 'text-red-400'
    const actionBg = activity.action === 'BUY' ? 'bg-green-500/10' : 'bg-red-500/10'
    const actionBorder = activity.action === 'BUY' ? 'border-green-500/20' : 'border-red-500/20'
    const pnlColor = activity.is_profit ? 'text-green-400' : 'text-red-400'
    
    // Status badge
    const statusBadge = activity.status === 'CLOSED' 
      ? <span className="text-xs px-2 py-0.5 bg-gray-600/50 text-gray-300 rounded">CLOSED</span>
      : <span className="text-xs px-2 py-0.5 bg-blue-500/20 text-blue-400 rounded">OPEN</span>

    return (
      <div className={`bg-gradient-to-r ${actionBg} border ${actionBorder} rounded-lg p-4 transition-all hover:shadow-lg hover:shadow-quantum-500/10`}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-2xl">📈</span>
              <div className="flex-1">
                <div className="flex items-center space-x-2">
                  <Link 
                    href={`/creator/entities/${activity.bot_id}`}
                    className="font-medium text-white hover:text-quantum-400 transition-colors"
                  >
                    {activity.bot_name}
                  </Link>
                  {statusBadge}
                </div>
                <p className="text-xs text-gray-500">{activity.exchange}</p>
              </div>
            </div>
            
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 text-sm">
              <div>
                <p className="text-gray-500 text-xs">Action</p>
                <p className={`font-bold ${actionColor}`}>{activity.action}</p>
              </div>
              <div>
                <p className="text-gray-500 text-xs">Symbol</p>
                <p className="text-white font-medium">{activity.symbol}</p>
              </div>
              <div>
                <p className="text-gray-500 text-xs">Price</p>
                <p className="text-white font-medium">
                  ${activity.price?.toLocaleString()}
                </p>
              </div>
              <div>
                <p className="text-gray-500 text-xs">P&L</p>
                <p className={`font-bold ${pnlColor}`}>
                  {activity.is_profit ? '+' : ''}${activity.pnl?.toFixed(2)}
                </p>
              </div>
            </div>

            {activity.details && (
              <p className="text-xs text-gray-400 mt-2">{activity.details}</p>
            )}
          </div>
          
          <div className="text-right ml-4">
            <p className="text-xs text-gray-500">{getTimeAgo(activity.timestamp)}</p>
          </div>
        </div>
      </div>
    )
  }

  // Render RISK_ALERT activity
  if (activity.type === 'RISK_ALERT') {
    const severityColors = {
      INFO: { bg: 'bg-blue-500/10', border: 'border-blue-500/20', text: 'text-blue-400', icon: 'ℹ️' },
      WARNING: { bg: 'bg-yellow-500/10', border: 'border-yellow-500/20', text: 'text-yellow-400', icon: '⚠️' },
      ERROR: { bg: 'bg-red-500/10', border: 'border-red-500/20', text: 'text-red-400', icon: '🚨' }
    }
    
    const severity = activity.severity || 'INFO'
    const colors = severityColors[severity as keyof typeof severityColors] || severityColors.INFO

    return (
      <div className={`bg-gradient-to-r ${colors.bg} border ${colors.border} rounded-lg p-4 transition-all hover:shadow-lg`}>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-2xl">{colors.icon}</span>
              <div>
                <p className={`font-medium ${colors.text}`}>Risk Management Alert</p>
                <Link 
                  href={`/creator/entities/${activity.bot_id}`}
                  className="text-xs text-gray-400 hover:text-quantum-400 transition-colors"
                >
                  {activity.bot_name}
                </Link>
              </div>
            </div>
            
            <p className="text-sm text-gray-300">{activity.message}</p>
            
            {activity.alert_type && (
              <p className="text-xs text-gray-500 mt-1">
                Type: <span className={colors.text}>{activity.alert_type}</span>
              </p>
            )}
          </div>
          
          <div className="text-right ml-4">
            <p className="text-xs text-gray-500">{getTimeAgo(activity.timestamp)}</p>
          </div>
        </div>
      </div>
    )
  }

  // Render BOT_EXECUTION activity
  if (activity.type === 'BOT_EXECUTION') {
    return (
      <div className="bg-gradient-to-r from-purple-500/10 to-purple-600/10 border border-purple-500/20 rounded-lg p-4 transition-all hover:shadow-lg">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center space-x-2 mb-2">
              <span className="text-2xl">🤖</span>
              <div>
                <Link 
                  href={`/creator/entities/${activity.bot_id}`}
                  className="font-medium text-white hover:text-quantum-400 transition-colors"
                >
                  {activity.bot_name}
                </Link>
                <p className="text-xs text-gray-500">Bot Execution</p>
              </div>
            </div>
            
            <p className="text-sm text-gray-300">{activity.message}</p>
            
            {activity.next_run && (
              <p className="text-xs text-purple-400 mt-1">
                Next run: {getTimeAgo(activity.next_run)}
              </p>
            )}
          </div>
          
          <div className="text-right ml-4">
            <p className="text-xs text-gray-500">{getTimeAgo(activity.timestamp)}</p>
          </div>
        </div>
      </div>
    )
  }

  return null
}

