import { NextRequest, NextResponse } from 'next/server'

export async function POST(request: NextRequest) {
  try {
    const requestData = await request.json()
    const { symbol, testnet, botType } = requestData
    
    console.log(`💰 Getting price for ${symbol}...`, { testnet, botType })
    
    // Determine correct endpoints based on bot type and testnet
    let baseUrl
    let endpoint
    
    if (testnet) {
      if (botType === 'FUTURES' || botType === 'FUTURES_RPA') {
        baseUrl = 'https://testnet.binancefuture.com'
        endpoint = '/fapi/v1/ticker/price'
        console.log('🎯 Using FUTURES Testnet API for price')
      } else {
        baseUrl = 'https://testnet.binance.vision'
        endpoint = '/api/v3/ticker/price'
        console.log('🎯 Using SPOT Testnet API for price')
      }
    } else {
      if (botType === 'FUTURES' || botType === 'FUTURES_RPA') {
        baseUrl = 'https://fapi.binance.com'
        endpoint = '/fapi/v1/ticker/price'
        console.log('🎯 Using FUTURES Production API for price')
      } else {
        baseUrl = 'https://api.binance.com'
        endpoint = '/api/v3/ticker/price'
        console.log('🎯 Using SPOT Production API for price')
      }
    }
    
    const url = `${baseUrl}${endpoint}?symbol=${symbol}`
    console.log('📡 Making request to:', url)
    
    const response = await fetch(url, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    console.log('📡 Response status:', response.status)
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('❌ Price API Error Response:', errorText)
      throw new Error(`HTTP ${response.status}: ${errorText}`)
    }
    
    const priceData = await response.json()
    console.log('✅ Price data received:', priceData)
    
    return NextResponse.json({
      symbol: priceData.symbol,
      price: priceData.price,
      timestamp: Date.now(),
      source: testnet ? 'testnet' : 'production',
      exchange: botType === 'FUTURES' || botType === 'FUTURES_RPA' ? 'futures' : 'spot'
    })
    
  } catch (error: any) {
    console.error('❌ Price API error:', error)
    
    // Fallback to reasonable price for testing
    const fallbackPrice = '112000'
    console.log(`🔄 Using fallback price: $${fallbackPrice}`)
    
    return NextResponse.json({
      symbol: 'BTCUSDT',
      price: fallbackPrice,
      timestamp: Date.now(),
      source: 'fallback',
      exchange: 'unknown',
      error: error.message
    })
  }
}
