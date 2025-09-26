import { NextRequest, NextResponse } from 'next/server'
import crypto from 'crypto'

// Real Binance API integration (following binance_futures_bot.py pattern)
export async function POST(request: NextRequest) {
  let apiKey: string = '', secret: string = '', testnet: boolean = false, botType: string = 'SPOT'
  
  try {
    const requestData = await request.json()
    apiKey = requestData.apiKey
    secret = requestData.secret
    testnet = requestData.testnet
    botType = requestData.botType

    if (!apiKey || !secret) {
      return NextResponse.json(
        { error: 'API Key and Secret are required' },
        { status: 400 }
      )
    }

    console.log('🔗 Connecting to Binance API...', { testnet, botType, apiKey: apiKey.substring(0, 10) + '...' })

    // Determine correct endpoints based on bot type from template
    let baseUrl
    
    if (testnet) {
      // Testnet endpoints
      if (botType === 'FUTURES' || botType === 'FUTURES_RPA') {
        baseUrl = 'https://testnet.binancefuture.com'
        console.log('🎯 Using FUTURES Testnet API')
      } else if (botType === 'SPOT') {
        baseUrl = 'https://testnet.binance.vision'
        console.log('🎯 Using SPOT Testnet API')
      } else {
        // Default to SPOT for other types (LLM, TECHNICAL, etc.)
        baseUrl = 'https://testnet.binance.vision'
        console.log('🎯 Using SPOT Testnet API (default for', botType, ')')
      }
    } else {
      // Production endpoints
      if (botType === 'FUTURES' || botType === 'FUTURES_RPA') {
        baseUrl = 'https://fapi.binance.com'
        console.log('🎯 Using FUTURES Production API')
      } else if (botType === 'SPOT') {
        baseUrl = 'https://api.binance.com'
        console.log('🎯 Using SPOT Production API')
      } else {
        // Default to SPOT for other types (LLM, TECHNICAL, etc.)
        baseUrl = 'https://api.binance.com'
        console.log('🎯 Using SPOT Production API (default for', botType, ')')
      }
    }

    console.log('🔧 Using API endpoint:', baseUrl)
    console.log('🎯 Bot type:', botType, '| Testnet:', testnet)

    // Generate signature (following binance_futures_bot.py pattern)
    const generateSignature = (params: Record<string, any>) => {
      const queryString = Object.keys(params)
        .map(key => `${key}=${params[key]}`)
        .join('&')
      return crypto
        .createHmac('sha256', secret)
        .update(queryString)
        .digest('hex')
    }

    // Make authenticated request (following binance_futures_bot.py pattern)
    const makeRequest = async (endpoint: string, params: any = {}) => {
      const url = `${baseUrl}${endpoint}`
      const headers = {
        'X-MBX-APIKEY': apiKey,
        'Content-Type': 'application/x-www-form-urlencoded'
      }

      // Add timestamp and signature for signed requests
      params.recvWindow = 50000
      params.timestamp = Date.now()
      params.signature = generateSignature(params)

      const queryString = Object.keys(params)
        .map(key => `${key}=${params[key]}`)
        .join('&')

      console.log('📡 Making request to:', url)
      console.log('🔐 Query params:', Object.keys(params).join(', '))

      const response = await fetch(`${url}?${queryString}`, {
        method: 'GET',
        headers
      })

      console.log('📡 Response status:', response.status)
      console.log('📡 Response headers:', Object.fromEntries(response.headers.entries()))

      if (!response.ok) {
        const errorText = await response.text()
        console.error('❌ API Error Response:', errorText)
        
        // Try to parse as JSON for better error details
        try {
          const errorJson = JSON.parse(errorText)
          throw new Error(`Binance API Error ${errorJson.code}: ${errorJson.msg}`)
        } catch {
          throw new Error(`HTTP ${response.status}: ${errorText}`)
        }
      }

      const responseText = await response.text()
      console.log('📡 Raw response:', responseText.substring(0, 200) + '...')

      if (!responseText) {
        throw new Error('Empty response from Binance API')
      }

      try {
        return JSON.parse(responseText)
      } catch (parseError: any) {
        console.error('❌ JSON Parse Error:', parseError)
        console.error('❌ Response text:', responseText)
        throw new Error(`Invalid JSON response: ${parseError.message || 'Unknown parse error'}`)
      }
    }

    // Get account information (different endpoints for Futures vs Spot)
    let accountInfo
    if (botType === 'FUTURES' || botType === 'FUTURES_RPA') {
      // Futures account endpoint
      accountInfo = await makeRequest('/fapi/v2/account')
    } else {
      // Spot account endpoint
      accountInfo = await makeRequest('/api/v3/account')
    }
    
    console.log('✅ Binance API connection successful!')
    console.log('Account type:', accountInfo.accountType || 'FUTURES')
    console.log('Can trade:', accountInfo.canTrade)
    
    // Process balance data based on account type
    let processedBalances = []
    
    if (botType === 'FUTURES' || botType === 'FUTURES_RPA') {
      // Futures account has different structure
      console.log('Available balance:', accountInfo.availableBalance)
      console.log('Total wallet balance:', accountInfo.totalWalletBalance)
      
      // Futures assets are in 'assets' array
      if (accountInfo.assets) {
        processedBalances = accountInfo.assets
          .filter((asset: any) => parseFloat(asset.walletBalance) > 0)
          .map((asset: any) => ({
            asset: asset.asset,
            free: asset.availableBalance || asset.walletBalance,
            locked: (parseFloat(asset.walletBalance) - parseFloat(asset.availableBalance || asset.walletBalance)).toString()
          }))
      } else {
        // Fallback: create USDT balance from availableBalance
        processedBalances = [{
          asset: 'USDT',
          free: accountInfo.availableBalance || '0',
          locked: '0'
        }]
      }
    } else {
      // Spot account structure
      console.log('Balance count:', accountInfo.balances?.length || 0)
      
      if (accountInfo.balances) {
        processedBalances = accountInfo.balances.filter((balance: any) => 
          parseFloat(balance.free) > 0 || parseFloat(balance.locked) > 0
        )
      }
    }

    const responseData = {
      makerCommission: accountInfo.makerCommission || 10,
      takerCommission: accountInfo.takerCommission || 10,
      buyerCommission: accountInfo.buyerCommission || 0,
      sellerCommission: accountInfo.sellerCommission || 0,
      canTrade: accountInfo.canTrade || true,
      canWithdraw: accountInfo.canWithdraw || true,
      canDeposit: accountInfo.canDeposit || true,
      updateTime: accountInfo.updateTime || Date.now(),
      accountType: testnet ? `${botType}_TESTNET` : (accountInfo.accountType || botType),
      balances: processedBalances.length > 0 ? processedBalances : [
        { asset: 'USDT', free: '0.00000000', locked: '0.00000000' }
      ],
      // Additional futures-specific data
      ...(botType === 'FUTURES' || botType === 'FUTURES_RPA' ? {
        totalWalletBalance: accountInfo.totalWalletBalance,
        availableBalance: accountInfo.availableBalance,
        totalMarginBalance: accountInfo.totalMarginBalance,
        totalUnrealizedProfit: accountInfo.totalUnrealizedProfit
      } : {})
    }

    return NextResponse.json(responseData)

  } catch (error: any) {
    console.error('❌ Binance API error:', error)
    console.error('❌ Error stack:', error.stack)
    
    let errorMessage = 'Failed to connect to Binance'
    let statusCode = 500

    // Handle specific error types
    if (error.message?.includes('Binance API Error')) {
      // Already formatted Binance error
      errorMessage = error.message
      statusCode = 400
    } else if (error.message?.includes('Invalid JSON response')) {
      errorMessage = `Binance API returned invalid response: ${error.message}`
      statusCode = 502
    } else if (error.message?.includes('Empty response')) {
      errorMessage = 'Binance API returned empty response'
      statusCode = 502
    } else if (error.message?.includes('ENOTFOUND') || error.message?.includes('ECONNREFUSED')) {
      errorMessage = 'Network error. Unable to reach Binance servers.'
      statusCode = 503
    } else if (error.message?.includes('timeout')) {
      errorMessage = 'Request timeout. Binance servers may be overloaded.'
      statusCode = 408
    } else if (error.message?.includes('fetch')) {
      errorMessage = `Network request failed: ${error.message}`
      statusCode = 503
    } else if (error.message) {
      errorMessage = error.message
    }

    // For API key permission errors, test both Spot and Futures endpoints
    if (error.message?.includes('-2015') || error.message?.includes('Invalid API-key')) {
      console.log('❌ API key permission error. Testing alternative endpoints...')
      
      // Try Spot endpoint if Futures failed
      if (botType === 'FUTURES' || botType === 'FUTURES_RPA') {
        console.log('🔄 Futures failed, trying Spot endpoint as fallback...')
        
        try {
          const spotUrl = testnet ? 'https://testnet.binance.vision' : 'https://api.binance.com'
          const spotParams: any = {
            recvWindow: 50000,
            timestamp: Date.now()
          }
          spotParams.signature = crypto
            .createHmac('sha256', secret)
            .update(Object.keys(spotParams).map(key => `${key}=${spotParams[key]}`).join('&'))
            .digest('hex')
          
          const spotQueryString = Object.keys(spotParams)
            .map(key => `${key}=${spotParams[key]}`)
            .join('&')
          
          console.log('📡 Testing Spot endpoint:', `${spotUrl}/api/v3/account`)
          
          const spotResponse = await fetch(`${spotUrl}/api/v3/account?${spotQueryString}`, {
            method: 'GET',
            headers: {
              'X-MBX-APIKEY': apiKey,
              'Content-Type': 'application/x-www-form-urlencoded'
            }
          })
          
          console.log('📡 Spot response status:', spotResponse.status)
          
          if (spotResponse.ok) {
            const spotData = await spotResponse.json()
            console.log('✅ Spot API works! Using Spot data for Futures bot.')
            
            return NextResponse.json({
              ...spotData,
              accountType: 'SPOT_FALLBACK',
              message: 'Using Spot API - Futures API restricted',
              balances: spotData.balances?.filter((b: any) => 
                parseFloat(b.free) > 0 || parseFloat(b.locked) > 0
              ) || []
            })
          }
        } catch (spotError: any) {
          console.log('❌ Spot endpoint also failed:', spotError.message)
        }
      }
      
      // If both failed, return proper error instead of demo data
      console.log('❌ Both endpoints failed, returning API key error')
      
      return NextResponse.json({
        error: 'API Key Invalid or Restricted',
        code: -2015,
        message: 'Invalid API-key, IP, or permissions for action',
        instructions: [
          '1. Check API Key permissions: Enable Reading + Enable Futures/Spot Trading',
          '2. Remove IP restrictions or whitelist your IP',
          '3. For Testnet: Use different API keys',
          '4. Verify API key is active and not expired'
        ],
        apiKeyIssue: true
      }, { status: 401 })
    }

    // Only return demo data for development/testing when no API keys provided
    if (!apiKey || !secret) {
      console.log('🔄 No API keys provided, returning demo data for UI testing...')
      
      const demoBalanceData = {
        makerCommission: 15,
        takerCommission: 15,
        buyerCommission: 0,
        sellerCommission: 0,
        canTrade: false, // Demo mode
        canWithdraw: false,
        canDeposit: false,
        updateTime: Date.now(),
        accountType: 'DEMO_TESTNET', // Fixed: testnet variable not in scope
        balances: [
          {
            asset: 'BTC',
            free: '0.00100000',
            locked: '0.00000000'
          },
          {
            asset: 'ETH',
            free: '0.05000000',
            locked: '0.00000000'
          },
          {
            asset: 'USDT',
            free: '1000.00000000',
            locked: '0.00000000'
          },
          {
            asset: 'BNB',
            free: '5.00000000',
            locked: '0.00000000'
          }
        ],
        demoMode: true,
        message: 'Demo data - API key needs proper permissions'
      }

      return NextResponse.json(demoBalanceData, { status: 200 })
    }

      return NextResponse.json(
        { 
          error: errorMessage,
          code: error.code || 'UNKNOWN_ERROR',
          testnet: false // Fixed: testnet variable not in scope
        },
        { status: statusCode }
      )
  }
}
