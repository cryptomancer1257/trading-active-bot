import './globals.css'
import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { AuthProvider } from '@/contexts/AuthContext'
import { Toaster } from 'react-hot-toast'
import Navbar from '@/components/layout/Navbar'
import Footer from '@/components/layout/Footer'
import QueryProvider from '@/components/providers/QueryProvider'
import GoogleOAuthProvider from '@/components/providers/GoogleOAuthProvider'
import BackendStatus from '@/components/debug/BackendStatus'
import QuotaWarningBanner from '@/components/QuotaWarningBanner'
import GlobalQuotaHandler from '@/components/GlobalQuotaHandler'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'QuantumForge - AI Trading Bot Creation Studio',
  description: 'Forge the future of autonomous trading. Create AI entities that dominate financial markets.',
  keywords: 'AI trading, bot creation, cryptocurrency, neural networks, quantum computing',
  authors: [{ name: 'QuantumForge Team' }],
  robots: 'index, follow',
}

export const viewport = {
  width: 'device-width',
  initialScale: 1,
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <GoogleOAuthProvider>
          <QueryProvider>
            <AuthProvider>
              <div className="min-h-screen bg-dark-900 neural-grid flex flex-col">
                <Navbar />
                <QuotaWarningBanner />
                <main className="flex-1 relative z-10">
                  {children}
                </main>
                <Footer />
              </div>
              <GlobalQuotaHandler />
              <Toaster
              position="top-right"
              toastOptions={{
                duration: 4000,
                style: {
                  background: 'rgba(30, 41, 59, 0.95)',
                  color: '#e2e8f0',
                  border: '1px solid rgba(168, 85, 247, 0.2)',
                  backdropFilter: 'blur(8px)',
                  boxShadow: '0 0 20px rgba(168, 85, 247, 0.1)',
                },
                success: {
                  duration: 3000,
                  iconTheme: {
                    primary: '#22c55e',
                    secondary: '#fff',
                  },
                  style: {
                    background: 'rgba(30, 41, 59, 0.95)',
                    border: '1px solid rgba(34, 197, 94, 0.3)',
                    boxShadow: '0 0 20px rgba(34, 197, 94, 0.1)',
                  },
                },
                error: {
                  duration: 5000,
                  iconTheme: {
                    primary: '#ef4444',
                    secondary: '#fff',
                  },
                  style: {
                    background: 'rgba(30, 41, 59, 0.95)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    boxShadow: '0 0 20px rgba(239, 68, 68, 0.1)',
                  },
                },
              }}
            />
            <BackendStatus />
          </AuthProvider>
        </QueryProvider>
        </GoogleOAuthProvider>
      </body>
    </html>
  )
}

