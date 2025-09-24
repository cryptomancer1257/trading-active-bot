import Link from 'next/link'
import { CpuChipIcon, ShieldCheckIcon, RocketLaunchIcon, BoltIcon } from '@heroicons/react/24/outline'

const features = [
  {
    name: 'Neural Architecture',
    description: 'Advanced AI algorithms that learn, adapt, and evolve. Create autonomous entities capable of making split-second financial decisions.',
    icon: CpuChipIcon,
    gradient: 'from-quantum-500 to-purple-600',
  },
  {
    name: 'Quantum Security',
    description: 'Military-grade encryption and quantum-resistant security protocols. Your AI entities operate in complete stealth mode.',
    icon: ShieldCheckIcon,
    gradient: 'from-cyber-500 to-blue-600',
  },
  {
    name: 'Market Domination',
    description: 'Deploy your AI entities across global markets. Watch as they execute complex strategies with inhuman precision.',
    icon: RocketLaunchIcon,
    gradient: 'from-neural-500 to-green-600',
  },
  {
    name: 'Real-time Control',
    description: 'Command center interface for monitoring and controlling your AI army. Override decisions in real-time when needed.',
    icon: BoltIcon,
    gradient: 'from-yellow-500 to-orange-600',
  },
]

const stats = [
  { name: 'AI Entities Created', value: '2,847', suffix: '+' },
  { name: 'Market Dominance', value: '94.7', suffix: '%' },
  { name: 'Profit Optimization', value: '340', suffix: '%' },
  { name: 'Neural Networks', value: '∞', suffix: '' },
]

export default function HomePage() {
  return (
    <div className="relative">
      {/* Hero Section */}
      <div className="relative overflow-hidden">
        <div className="absolute inset-0 bg-gradient-to-br from-quantum-900/20 via-dark-900/50 to-cyber-900/20"></div>
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-24">
          <div className="text-center">
            <div className="mb-8">
              <span className="inline-flex items-center px-4 py-2 rounded-full text-sm font-medium bg-gradient-to-r from-quantum-500/20 to-cyber-500/20 text-quantum-300 border border-quantum-500/30 backdrop-blur-sm">
                ⚡ Neural Network Active
              </span>
            </div>
            
            <h1 className="text-5xl md:text-7xl font-extrabold mb-6">
              <span className="block cyber-text glitch-effect" data-text="FORGE THE FUTURE">
                FORGE THE FUTURE
              </span>
              <span className="block text-gray-300 text-3xl md:text-5xl mt-4">
                of Autonomous Trading
              </span>
            </h1>
            
            <p className="mt-6 text-xl text-gray-400 max-w-3xl mx-auto leading-8">
              Enter the QuantumForge - where artificial intelligence transcends human limitations. 
              Create AI entities that don't just trade markets, they <span className="text-quantum-400 font-semibold">dominate</span> them.
            </p>
            
            <div className="mt-10 flex flex-col sm:flex-row gap-4 justify-center">
              <Link
                href="/auth/register"
                className="btn btn-cyber px-8 py-4 text-lg font-semibold rounded-lg transform hover:scale-105 transition-all duration-300"
              >
                🧠 Initialize Neural Link
              </Link>
              <Link
                href="/arsenal"
                className="btn btn-secondary px-8 py-4 text-lg font-semibold rounded-lg border border-quantum-500/30 hover:border-quantum-400 transition-all duration-300"
              >
                🔍 Analyze Entities
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Section */}
      <div className="py-16 bg-dark-800/30 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
            {stats.map((stat) => (
              <div key={stat.name} className="text-center">
                <div className="text-4xl font-bold cyber-text animate-neural-pulse">
                  {stat.value}{stat.suffix}
                </div>
                <div className="text-sm text-gray-400 mt-2">{stat.name}</div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Features Section */}
      <div className="py-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-16">
            <h2 className="text-4xl font-extrabold cyber-text mb-4">
              Neural Capabilities
            </h2>
            <p className="text-xl text-gray-400 max-w-2xl mx-auto">
              Harness the power of quantum computing and artificial intelligence to create 
              trading entities that operate beyond human comprehension.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            {features.map((feature, index) => (
              <div
                key={feature.name}
                className="card-quantum p-8 hover:shadow-2xl transition-all duration-500 transform hover:-translate-y-2 animate-fade-in"
                style={{ animationDelay: `${index * 0.1}s` }}
              >
                <div className="flex items-center mb-6">
                  <div className={`p-3 rounded-lg bg-gradient-to-r ${feature.gradient} shadow-lg`}>
                    <feature.icon className="h-8 w-8 text-white" />
                  </div>
                  <h3 className="ml-4 text-xl font-bold text-gray-200">{feature.name}</h3>
                </div>
                <p className="text-gray-400 leading-relaxed">{feature.description}</p>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* CTA Section */}
      <div className="py-20 bg-gradient-to-r from-quantum-900/30 via-dark-800/50 to-cyber-900/30 backdrop-blur-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h2 className="text-4xl font-extrabold mb-6">
            <span className="cyber-text">Ready to Transcend</span>
            <span className="block text-gray-300 text-2xl mt-2">Human Trading Limitations?</span>
          </h2>
          
          <p className="text-xl text-gray-400 mb-10 max-w-2xl mx-auto">
            Join the elite circle of AI architects. Create, deploy, and command 
            an army of autonomous trading entities.
          </p>
          
          <div className="flex flex-col sm:flex-row gap-6 justify-center">
            <Link
              href="/auth/register"
              className="btn btn-primary px-10 py-4 text-lg font-bold rounded-lg transform hover:scale-105 transition-all duration-300 shadow-2xl"
            >
              🚀 Begin Neural Synthesis
            </Link>
            <Link
              href="/creator/forge"
              className="btn btn-cyber px-10 py-4 text-lg font-bold rounded-lg transform hover:scale-105 transition-all duration-300"
            >
              ⚡ Enter the Forge
            </Link>
          </div>
          
          <div className="mt-8 text-sm text-gray-500">
            <span className="inline-flex items-center">
              🔒 Quantum-encrypted • 🧠 AI-powered • ⚡ Neural-enhanced
            </span>
          </div>
        </div>
      </div>

      {/* Floating Elements */}
      <div className="fixed top-20 left-10 w-2 h-2 bg-quantum-500 rounded-full animate-neural-pulse opacity-60"></div>
      <div className="fixed top-40 right-20 w-1 h-1 bg-cyber-400 rounded-full animate-neural-pulse opacity-40" style={{ animationDelay: '1s' }}></div>
      <div className="fixed bottom-40 left-20 w-1.5 h-1.5 bg-neural-500 rounded-full animate-neural-pulse opacity-50" style={{ animationDelay: '2s' }}></div>
      <div className="fixed bottom-20 right-10 w-2 h-2 bg-quantum-400 rounded-full animate-neural-pulse opacity-30" style={{ animationDelay: '3s' }}></div>
    </div>
  )
}