import RegisterForm from '@/components/auth/RegisterForm'
import Link from 'next/link'

export default function RegisterPage() {
  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="text-4xl font-extrabold cyber-text mb-2">
            Neural Profile Initialization
          </h2>
          <p className="text-gray-400">
            Create your quantum identity in the neural network
          </p>
        </div>
        
        <div className="card-quantum p-8">
          <RegisterForm />
        </div>
        
        <div className="text-center">
          <p className="text-gray-400">
            Already have a neural profile?{' '}
            <Link 
              href="/auth/login" 
              className="text-quantum-400 hover:text-quantum-300 font-medium"
            >
              Activate Neural Link
            </Link>
          </p>
        </div>
      </div>
    </div>
  )
}

