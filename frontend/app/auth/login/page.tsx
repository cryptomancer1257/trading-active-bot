import LoginForm from '@/components/auth/LoginForm'
import Link from 'next/link'

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="text-4xl font-extrabold cyber-text mb-2">
            Neural Link Activation
          </h2>
          <p className="text-gray-400">
            Connect to the QuantumForge neural network
          </p>
        </div>
        
        <div className="card-quantum p-8">
          <LoginForm />
        </div>
        
        <div className="text-center">
          <p className="text-gray-400">
            New to QuantumForge?{' '}
            <Link 
              href="/auth/register" 
              className="text-quantum-400 hover:text-quantum-300 font-medium"
            >
              Initialize Neural Profile
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

