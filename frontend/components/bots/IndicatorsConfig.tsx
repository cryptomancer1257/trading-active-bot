'use client'

import { useState } from 'react'
import { ChevronDownIcon, ChevronRightIcon, InformationCircleIcon } from '@heroicons/react/24/outline'

export interface IndicatorsConfigData {
  enabled_categories: {
    trend: boolean
    momentum: boolean
    volatility: boolean
    volume: boolean
    levels: boolean
    advanced: boolean
  }
  enabled_indicators: {
    // Trend
    sma?: number[]
    ema?: number[]
    adx?: boolean
    supertrend?: boolean
    ichimoku?: boolean
    // Momentum
    rsi?: boolean
    macd?: boolean
    stochastic?: boolean
    williams_r?: boolean
    cci?: boolean
    roc?: boolean
    // Volatility
    atr?: boolean
    bollinger_bands?: boolean
    keltner_channels?: boolean
    donchian_channels?: boolean
    // Volume
    obv?: boolean
    cmf?: boolean
    mfi?: boolean
    vwma?: boolean
    // Levels
    pivot_points?: boolean
    fibonacci?: boolean
    parabolic_sar?: boolean
  }
  indicator_periods: {
    rsi_period?: number
    macd_fast?: number
    macd_slow?: number
    macd_signal?: number
    stochastic_k?: number
    stochastic_d?: number
    atr_period?: number
    bollinger_period?: number
    bollinger_std?: number
  }
}

interface IndicatorsConfigProps {
  value: IndicatorsConfigData
  onChange: (value: IndicatorsConfigData) => void
}

// Mapping of categories to their indicators
const CATEGORY_INDICATORS_MAP: Record<string, string[]> = {
  trend: ['sma', 'ema', 'adx', 'supertrend', 'ichimoku'],
  momentum: ['rsi', 'macd', 'stochastic', 'williams_r', 'cci', 'roc'],
  volatility: ['atr', 'bollinger_bands', 'keltner_channels', 'donchian_channels'],
  volume: ['obv', 'cmf', 'mfi', 'vwma'],
  levels: ['pivot_points', 'fibonacci', 'parabolic_sar'],
}

const defaultConfig: IndicatorsConfigData = {
  enabled_categories: {
    trend: true,
    momentum: true,
    volatility: true,
    volume: true,
    levels: false,
    advanced: false,
  },
  enabled_indicators: {
    sma: [20, 50],
    ema: [12, 26],
    adx: true,
    supertrend: true,
    ichimoku: false,
    rsi: true,
    macd: true,
    stochastic: true,
    williams_r: false,
    cci: false,
    roc: false,
    atr: true,
    bollinger_bands: true,
    keltner_channels: false,
    donchian_channels: false,
    obv: true,
    cmf: true,
    mfi: true,
    vwma: false,
    pivot_points: false,
    fibonacci: false,
    parabolic_sar: false,
  },
  indicator_periods: {
    rsi_period: 14,
    macd_fast: 12,
    macd_slow: 26,
    macd_signal: 9,
    stochastic_k: 14,
    stochastic_d: 3,
    atr_period: 14,
    bollinger_period: 20,
    bollinger_std: 2.0,
  },
}

export default function IndicatorsConfig({ value = defaultConfig, onChange }: IndicatorsConfigProps) {
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(['trend', 'momentum']))

  // Helper to check if indicator is enabled (handles both boolean and array types)
  const isIndicatorEnabled = (indicatorId: string): boolean => {
    const indicatorValue = value.enabled_indicators[indicatorId as keyof typeof value.enabled_indicators]
    
    // For array types (SMA, EMA), check if array has elements
    if (Array.isArray(indicatorValue)) {
      return indicatorValue.length > 0
    }
    
    // For boolean types, return the boolean value
    return Boolean(indicatorValue)
  }

  const toggleSection = (section: string) => {
    setExpandedSections(prev => {
      const newSet = new Set(prev)
      if (newSet.has(section)) {
        newSet.delete(section)
      } else {
        newSet.add(section)
      }
      return newSet
    })
  }

  const handleCategoryChange = (category: keyof IndicatorsConfigData['enabled_categories']) => {
    const isCurrentlyEnabled = value.enabled_categories[category]
    const newEnabledState = !isCurrentlyEnabled
    
    // Get indicators in this category
    const indicatorsInCategory = CATEGORY_INDICATORS_MAP[category] || []
    
    // If disabling category, also disable all indicators in it
    const updatedIndicators = { ...value.enabled_indicators }
    if (!newEnabledState) {
      // Disable all indicators in this category
      indicatorsInCategory.forEach(indicatorId => {
        if (indicatorId === 'sma' || indicatorId === 'ema') {
          // For array-type indicators (SMA/EMA), set to empty array
          updatedIndicators[indicatorId] = []
        } else {
          // For boolean indicators, set to false
          updatedIndicators[indicatorId as keyof typeof updatedIndicators] = false as any
        }
      })
    }
    
    onChange({
      ...value,
      enabled_categories: {
        ...value.enabled_categories,
        [category]: newEnabledState,
      },
      enabled_indicators: updatedIndicators,
    })
  }

  const handleIndicatorChange = (indicator: string, checked: boolean) => {
    let indicatorValue: any
    
    // Handle array-type indicators (SMA/EMA)
    if (indicator === 'sma') {
      indicatorValue = checked ? [20, 50, 200] : [] // Default SMA periods or empty
    } else if (indicator === 'ema') {
      indicatorValue = checked ? [12, 26] : [] // Default EMA periods or empty
    } else {
      // Handle boolean indicators
      indicatorValue = checked
    }
    
    onChange({
      ...value,
      enabled_indicators: {
        ...value.enabled_indicators,
        [indicator]: indicatorValue,
      },
    })
  }

  const handleSMAPeriodChange = (periods: string) => {
    const periodsArray = periods.split(',').map(p => parseInt(p.trim())).filter(p => !isNaN(p))
    onChange({
      ...value,
      enabled_indicators: {
        ...value.enabled_indicators,
        sma: periodsArray,
      },
    })
  }

  const handleEMAPeriodChange = (periods: string) => {
    const periodsArray = periods.split(',').map(p => parseInt(p.trim())).filter(p => !isNaN(p))
    onChange({
      ...value,
      enabled_indicators: {
        ...value.enabled_indicators,
        ema: periodsArray,
      },
    })
  }

  const handlePeriodChange = (period: string, val: number) => {
    onChange({
      ...value,
      indicator_periods: {
        ...value.indicator_periods,
        [period]: val,
      },
    })
  }

  const categories = [
    {
      id: 'trend',
      name: 'Trend Indicators',
      description: 'Trend indicators (SMA, EMA, ADX, Supertrend, Ichimoku)',
      indicators: [
        { id: 'sma', name: 'SMA (Simple Moving Average)', type: 'periods' },
        { id: 'ema', name: 'EMA (Exponential Moving Average)', type: 'periods' },
        { id: 'adx', name: 'ADX (Average Directional Index)', type: 'boolean' },
        { id: 'supertrend', name: 'Supertrend', type: 'boolean' },
        { id: 'ichimoku', name: 'Ichimoku Cloud', type: 'boolean', requiresAdvanced: true },
      ],
    },
    {
      id: 'momentum',
      name: 'Momentum Indicators',
      description: 'Momentum indicators (RSI, MACD, Stochastic)',
      indicators: [
        { id: 'rsi', name: 'RSI (Relative Strength Index)', type: 'boolean' },
        { id: 'macd', name: 'MACD (Moving Average Convergence Divergence)', type: 'boolean' },
        { id: 'stochastic', name: 'Stochastic Oscillator', type: 'boolean' },
        { id: 'williams_r', name: 'Williams %R', type: 'boolean' },
        { id: 'cci', name: 'CCI (Commodity Channel Index)', type: 'boolean' },
        { id: 'roc', name: 'ROC (Rate of Change)', type: 'boolean' },
      ],
    },
    {
      id: 'volatility',
      name: 'Volatility Indicators',
      description: 'Volatility indicators (ATR, Bollinger Bands)',
      indicators: [
        { id: 'atr', name: 'ATR (Average True Range)', type: 'boolean' },
        { id: 'bollinger_bands', name: 'Bollinger Bands', type: 'boolean' },
        { id: 'keltner_channels', name: 'Keltner Channels', type: 'boolean' },
        { id: 'donchian_channels', name: 'Donchian Channels', type: 'boolean' },
      ],
    },
    {
      id: 'volume',
      name: 'Volume Indicators',
      description: 'Volume indicators (OBV, CMF, MFI)',
      indicators: [
        { id: 'obv', name: 'OBV (On-Balance Volume)', type: 'boolean' },
        { id: 'cmf', name: 'CMF (Chaikin Money Flow)', type: 'boolean' },
        { id: 'mfi', name: 'MFI (Money Flow Index)', type: 'boolean' },
        { id: 'vwma', name: 'VWMA (Volume Weighted Moving Average)', type: 'boolean' },
      ],
    },
    {
      id: 'levels',
      name: 'Support/Resistance Levels',
      description: 'Support/Resistance levels (Pivot Points, Fibonacci)',
      indicators: [
        { id: 'pivot_points', name: 'Pivot Points', type: 'boolean' },
        { id: 'fibonacci', name: 'Fibonacci Retracement', type: 'boolean' },
        { id: 'parabolic_sar', name: 'Parabolic SAR', type: 'boolean' },
      ],
    },
  ]

  return (
    <div className="space-y-6">
      {/* Info Banner */}
      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <div className="flex">
          <InformationCircleIcon className="h-5 w-5 text-blue-400 mr-3 flex-shrink-0" />
          <div>
            <h3 className="text-sm font-medium text-blue-800">
              Configure Technical Indicators for LLM
            </h3>
            <p className="mt-1 text-sm text-blue-700">
              Select technical indicators to calculate and send to LLM. 
              Only enabled indicators will be calculated and sent to the LLM for analysis.
            </p>
          </div>
        </div>
      </div>

      {/* Quick Presets */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-3">Quick Presets</h3>
        <div className="flex flex-wrap gap-2">
          <button
            onClick={() => onChange({
              ...defaultConfig,
              enabled_categories: {
                trend: true,
                momentum: true,
                volatility: true,
                volume: false,
                levels: false,
                advanced: false,
              },
            })}
            className="px-3 py-1.5 text-sm bg-blue-100 text-blue-700 rounded-md hover:bg-blue-200"
          >
            Basic (Trend + Momentum)
          </button>
          <button
            onClick={() => onChange({
              ...defaultConfig,
              enabled_categories: {
                trend: true,
                momentum: true,
                volatility: true,
                volume: true,
                levels: false,
                advanced: false,
              },
            })}
            className="px-3 py-1.5 text-sm bg-green-100 text-green-700 rounded-md hover:bg-green-200"
          >
            Standard (All except Levels)
          </button>
          <button
            onClick={() => onChange({
              ...defaultConfig,
              enabled_categories: {
                trend: true,
                momentum: true,
                volatility: true,
                volume: true,
                levels: true,
                advanced: true,
              },
            })}
            className="px-3 py-1.5 text-sm bg-purple-100 text-purple-700 rounded-md hover:bg-purple-200"
          >
            Advanced (All Indicators)
          </button>
        </div>
      </div>

      {/* Categories */}
      {categories.map(category => (
        <div key={category.id} className="bg-white rounded-lg border border-gray-200">
          {/* Category Header */}
          <button
            onClick={() => toggleSection(category.id)}
            className="w-full px-4 py-3 flex items-center justify-between hover:bg-gray-50"
          >
            <div className="flex items-center space-x-3">
              {expandedSections.has(category.id) ? (
                <ChevronDownIcon className="h-5 w-5 text-gray-400" />
              ) : (
                <ChevronRightIcon className="h-5 w-5 text-gray-400" />
              )}
              <div className="text-left">
                <h3 className="text-base font-medium text-gray-900">{category.name}</h3>
                <p className="text-sm text-gray-500">{category.description}</p>
              </div>
            </div>
            <label className="flex items-center" onClick={(e) => e.stopPropagation()}>
              <input
                type="checkbox"
                checked={value.enabled_categories[category.id as keyof typeof value.enabled_categories]}
                onChange={() => handleCategoryChange(category.id as keyof typeof value.enabled_categories)}
                className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
              />
              <span className="ml-2 text-sm text-gray-700">Enable</span>
            </label>
          </button>

          {/* Category Content */}
          {expandedSections.has(category.id) && (
            <div className="px-4 py-3 border-t border-gray-200 bg-gray-50">
              <div className="space-y-3">
                {category.indicators.map(indicator => (
                  <div key={indicator.id} className="flex items-center justify-between">
                    <label className="flex items-center">
                      <input
                        type="checkbox"
                        checked={isIndicatorEnabled(indicator.id)}
                        onChange={(e) => handleIndicatorChange(indicator.id, e.target.checked)}
                        disabled={!value.enabled_categories[category.id as keyof typeof value.enabled_categories]}
                        className="h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded disabled:opacity-50"
                      />
                      <span className={`ml-3 text-sm ${!value.enabled_categories[category.id as keyof typeof value.enabled_categories] ? 'text-gray-400' : 'text-gray-700'}`}>
                        {indicator.name}
                        {indicator.requiresAdvanced && !value.enabled_categories.advanced && (
                          <span className="ml-2 text-xs text-orange-600">(requires Advanced)</span>
                        )}
                      </span>
                    </label>
                    
                    {/* Special inputs for SMA/EMA */}
                    {indicator.type === 'periods' && indicator.id === 'sma' && isIndicatorEnabled('sma') && (
                      <input
                        type="text"
                        value={value.enabled_indicators.sma?.join(', ') || ''}
                        onChange={(e) => handleSMAPeriodChange(e.target.value)}
                        placeholder="20, 50, 200"
                        disabled={!value.enabled_categories[category.id as keyof typeof value.enabled_categories]}
                        className="ml-4 w-32 px-2 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50"
                      />
                    )}
                    {indicator.type === 'periods' && indicator.id === 'ema' && isIndicatorEnabled('ema') && (
                      <input
                        type="text"
                        value={value.enabled_indicators.ema?.join(', ') || ''}
                        onChange={(e) => handleEMAPeriodChange(e.target.value)}
                        placeholder="12, 26"
                        disabled={!value.enabled_categories[category.id as keyof typeof value.enabled_categories]}
                        className="ml-4 w-32 px-2 py-1 text-sm border border-gray-300 rounded-md disabled:opacity-50"
                      />
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      ))}

      {/* Custom Periods */}
      <div className="bg-white rounded-lg border border-gray-200 p-4">
        <h3 className="text-base font-medium text-gray-900 mb-4">Indicator Periods (Advanced)</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">RSI Period</label>
            <input
              type="number"
              value={value.indicator_periods.rsi_period}
              onChange={(e) => handlePeriodChange('rsi_period', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">MACD Fast</label>
            <input
              type="number"
              value={value.indicator_periods.macd_fast}
              onChange={(e) => handlePeriodChange('macd_fast', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">MACD Slow</label>
            <input
              type="number"
              value={value.indicator_periods.macd_slow}
              onChange={(e) => handlePeriodChange('macd_slow', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">MACD Signal</label>
            <input
              type="number"
              value={value.indicator_periods.macd_signal}
              onChange={(e) => handlePeriodChange('macd_signal', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">ATR Period</label>
            <input
              type="number"
              value={value.indicator_periods.atr_period}
              onChange={(e) => handlePeriodChange('atr_period', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Bollinger Period</label>
            <input
              type="number"
              value={value.indicator_periods.bollinger_period}
              onChange={(e) => handlePeriodChange('bollinger_period', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Bollinger Std Dev</label>
            <input
              type="number"
              step="0.1"
              value={value.indicator_periods.bollinger_std}
              onChange={(e) => handlePeriodChange('bollinger_std', parseFloat(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Stochastic K</label>
            <input
              type="number"
              value={value.indicator_periods.stochastic_k}
              onChange={(e) => handlePeriodChange('stochastic_k', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Stochastic D</label>
            <input
              type="number"
              value={value.indicator_periods.stochastic_d}
              onChange={(e) => handlePeriodChange('stochastic_d', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-md"
            />
          </div>
        </div>
      </div>

      {/* Summary */}
      <div className="bg-gray-50 rounded-lg border border-gray-200 p-4">
        <h3 className="text-sm font-medium text-gray-900 mb-2">Configuration Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-gray-500">Enabled Categories:</span>
            <span className="ml-2 font-medium text-gray-900">
              {Object.values(value.enabled_categories).filter(Boolean).length}/6
            </span>
          </div>
          <div>
            <span className="text-gray-500">Enabled Indicators:</span>
            <span className="ml-2 font-medium text-gray-900">
              {Object.values(value.enabled_indicators).filter(v => v === true || (Array.isArray(v) && v.length > 0)).length}
            </span>
          </div>
          <div>
            <span className="text-gray-500">Cost Impact:</span>
            <span className="ml-2 font-medium text-green-600">Optimized</span>
          </div>
        </div>
      </div>
    </div>
  )
}

