'use client'

import Link from 'next/link'
import { EnvelopeIcon, ChatBubbleBottomCenterTextIcon } from '@heroicons/react/24/outline'

export default function Footer() {
  return (
    <footer className="relative z-10 border-t border-purple-500/10 bg-dark-800/50 backdrop-blur-sm mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand Section */}
          <div className="col-span-1">
            <h3 className="text-2xl font-bold bg-gradient-to-r from-purple-400 to-cyan-400 bg-clip-text text-transparent mb-4">
              QuantumForge
            </h3>
            <p className="text-gray-400 text-sm mb-4">
              Forge the future of autonomous trading. Create AI entities that dominate financial markets.
            </p>
          </div>

          {/* Quick Links */}
          <div className="col-span-1">
            <h4 className="text-white font-semibold mb-4">Quick Links</h4>
            <ul className="space-y-2">
              <li>
                <Link href="/arsenal" className="text-gray-400 hover:text-purple-400 transition-colors text-sm">
                  AI Entity Arsenal
                </Link>
              </li>
              <li>
                <Link href="/creator/forge" className="text-gray-400 hover:text-purple-400 transition-colors text-sm">
                  Entity Forge
                </Link>
              </li>
              <li>
                <Link href="/plans" className="text-gray-400 hover:text-purple-400 transition-colors text-sm">
                  Plans & Pricing
                </Link>
              </li>
              <li>
                <Link href="/dashboard" className="text-gray-400 hover:text-purple-400 transition-colors text-sm">
                  Dashboard
                </Link>
              </li>
            </ul>
          </div>

          {/* Resources */}
          <div className="col-span-1">
            <h4 className="text-white font-semibold mb-4">Resources</h4>
            <ul className="space-y-2">
              <li>
                <Link href="/creator/intelligence" className="text-gray-400 hover:text-purple-400 transition-colors text-sm">
                  Market Intelligence
                </Link>
              </li>
              <li>
                <Link href="/creator/prompts/new" className="text-gray-400 hover:text-purple-400 transition-colors text-sm">
                  Strategy Templates
                </Link>
              </li>
              <li>
                <Link href="/creator/analytics" className="text-gray-400 hover:text-purple-400 transition-colors text-sm">
                  Analytics
                </Link>
              </li>
              <li>
                <Link href="/creator/credentials" className="text-gray-400 hover:text-purple-400 transition-colors text-sm">
                  API Credentials
                </Link>
              </li>
            </ul>
          </div>

          {/* Support & Contact */}
          <div className="col-span-1">
            <h4 className="text-white font-semibold mb-4">Support & Contact</h4>
            <ul className="space-y-3">
              <li>
                <a 
                  href="mailto:support@cryptomancer.ai" 
                  className="flex items-center gap-2 text-gray-400 hover:text-purple-400 transition-colors text-sm group"
                >
                  <EnvelopeIcon className="w-5 h-5 text-purple-500 group-hover:text-purple-400" />
                  <span>support@cryptomancer.ai</span>
                </a>
              </li>
              <li>
                <a 
                  href="https://t.me/cryptomanceraibot" 
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-gray-400 hover:text-cyan-400 transition-colors text-sm group"
                >
                  <ChatBubbleBottomCenterTextIcon className="w-5 h-5 text-cyan-500 group-hover:text-cyan-400" />
                  <span>Telegram Support Bot</span>
                </a>
              </li>
              <li>
                <a 
                  href="https://x.com/cryptomancerai" 
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-2 text-gray-400 hover:text-blue-400 transition-colors text-sm group"
                >
                  <svg className="w-5 h-5 text-blue-500 group-hover:text-blue-400" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                  </svg>
                  <span>@cryptomancerai</span>
                </a>
              </li>
            </ul>
            
            {/* Social Media */}
            <div className="mt-6 flex gap-3">
              <a 
                href="https://t.me/cryptomanceraibot" 
                target="_blank"
                rel="noopener noreferrer"
                className="w-8 h-8 rounded-lg bg-cyan-500/10 hover:bg-cyan-500/20 border border-cyan-500/30 flex items-center justify-center transition-all group"
                aria-label="Telegram"
              >
                <svg className="w-4 h-4 text-cyan-400 group-hover:text-cyan-300" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.562 8.161c-.18.717-1.558 7.842-2.21 10.4-.276 1.084-.82 1.447-1.345 1.483-.572.053-1.008-.378-1.563-.74-.867-.567-1.357-.92-2.2-1.473-.975-.639-.343-1.001.213-1.582.145-.152 2.667-2.447 2.717-2.657.007-.027.013-.126-.047-.179-.06-.053-.149-.035-.213-.021-.09.02-1.525.966-4.305 2.835-.408.28-.775.416-1.102.408-.363-.009-1.06-.205-1.579-.373-.635-.207-1.14-.316-1.096-.668.023-.183.285-.37.785-.561 3.08-1.343 5.134-2.23 6.162-2.662 2.935-1.225 3.545-1.439 3.945-1.447.088-.001.284.02.411.127.108.09.137.211.152.297.014.086.033.283.019.437z"/>
                </svg>
              </a>
              <a 
                href="https://x.com/cryptomancerai" 
                target="_blank"
                rel="noopener noreferrer"
                className="w-8 h-8 rounded-lg bg-blue-500/10 hover:bg-blue-500/20 border border-blue-500/30 flex items-center justify-center transition-all group"
                aria-label="X (Twitter)"
              >
                <svg className="w-4 h-4 text-blue-400 group-hover:text-blue-300" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/>
                </svg>
              </a>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-12 pt-8 border-t border-purple-500/10">
          <div className="flex flex-col md:flex-row justify-between items-center gap-4">
            <p className="text-gray-500 text-sm">
              © {new Date().getFullYear()} QuantumForge. All rights reserved.
            </p>
            <div className="flex gap-6 text-sm">
              <Link href="/privacy" className="text-gray-500 hover:text-gray-400 transition-colors">
                Privacy Policy
              </Link>
              <Link href="/terms" className="text-gray-500 hover:text-gray-400 transition-colors">
                Terms of Service
              </Link>
            </div>
          </div>
        </div>
      </div>
    </footer>
  )
}

