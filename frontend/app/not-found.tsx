import Link from 'next/link'
import { ExclamationTriangleIcon } from '@heroicons/react/24/outline'

export default function NotFound() {
  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full text-center">
        <div className="card-quantum p-8 space-y-6">
          <div className="flex justify-center">
            <ExclamationTriangleIcon className="h-24 w-24 text-quantum-500 animate-neural-pulse" />
          </div>
          
          <div>
            <h1 className="text-6xl font-bold cyber-text mb-4">404</h1>
            <h2 className="text-2xl font-bold text-gray-200 mb-2">
              Neural Path Not Found
            </h2>
            <p className="text-gray-400">
              The requested neural pathway does not exist in our quantum matrix.
            </p>
          </div>
          
          <div className="space-y-4">
            <Link
              href="/"
              className="btn btn-primary w-full py-3"
            >
              🏠 Return to Command Center
            </Link>
            <Link
              href="/dashboard"
              className="btn btn-secondary w-full py-3"
            >
              🎯 Access Control Panel
            </Link>
          </div>
          
          <div className="text-sm text-gray-500">
            <p>Error Code: QUANTUM_PATH_404</p>
            <p>Neural Network Status: Active</p>
          </div>
        </div>
      </div>
    </div>
  )
}
