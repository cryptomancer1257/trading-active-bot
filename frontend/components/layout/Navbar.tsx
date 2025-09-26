'use client'

import { Fragment, useEffect } from 'react'
import { Disclosure, Menu, Transition } from '@headlessui/react'
import { Bars3Icon, XMarkIcon, UserIcon, CogIcon, ArrowRightOnRectangleIcon } from '@heroicons/react/24/outline'
import { useAuth } from '@/contexts/AuthContext'
import { UserRole } from '@/lib/types'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import clsx from 'clsx'

const navigation = [
  { name: 'Command Center', href: '/', current: false },
  { name: 'Bot Arsenal', href: '/arsenal', current: false },
  { name: 'Control Panel', href: '/dashboard', current: false, requireAuth: true },
]

const creatorNavigation = [
  { name: 'My AI Entities', href: '/creator/entities', current: false },
  { name: 'Forge New Bot', href: '/creator/forge', current: false },
  { name: 'API Credentials', href: '/creator/credentials', current: false },
  { name: 'Neural Analytics', href: '/creator/analytics', current: false },
  { name: 'Market Intelligence', href: '/creator/intelligence', current: false },
]

const adminNavigation = [
  { name: 'System Override', href: '/admin/override', current: false },
  { name: 'User Matrix', href: '/admin/matrix', current: false },
  { name: 'Core Systems', href: '/admin/core', current: false },
]

export default function Navbar() {
  const { user, logout, refreshAuth } = useAuth()
  const pathname = usePathname()

  // Refresh auth state when pathname changes (with debouncing)
  useEffect(() => {
    // Only refresh auth on first load or when navigating to protected routes
    const protectedRoutes = ['/dashboard', '/creator/', '/admin/']
    const isProtectedRoute = protectedRoutes.some(route => pathname.startsWith(route))
    
    if (user && isProtectedRoute) {
      console.log('🛡️ Navigated to protected route, checking auth:', pathname)
      // Add a small delay to prevent rapid successive calls
      const timeoutId = setTimeout(() => {
        refreshAuth()
      }, 1000) // 1 second delay
      
      return () => clearTimeout(timeoutId)
    }
  }, [pathname, user, refreshAuth])

  const getNavigationItems = () => {
    let items = navigation.filter(item => !item.requireAuth || user)
    
    if (user?.role === UserRole.DEVELOPER || user?.role === UserRole.ADMIN) {
      items = [...items, ...creatorNavigation]
    }
    
    if (user?.role === UserRole.ADMIN) {
      items = [...items, ...adminNavigation]
    }
    
    return items.map(item => ({
      ...item,
      current: pathname === item.href
    }))
  }

  const navigationItems = getNavigationItems()

  return (
    <Disclosure as="nav" className="bg-dark-800/80 backdrop-blur-md shadow-lg border-b border-quantum-500/20">
      {({ open }) => (
        <>
          <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <div className="flex-shrink-0 flex items-center">
                  <Link href="/" className="text-xl font-bold bg-gradient-to-r from-purple-600 via-blue-600 to-cyan-600 bg-clip-text text-transparent">
                    ⚡ QuantumForge
                  </Link>
                </div>
                <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                  {navigationItems.map((item) => (
                    <Link
                      key={item.name}
                      href={item.href}
                      className={clsx(
                        item.current
                          ? 'border-quantum-500 text-gray-200 shadow-quantum-500/20'
                          : 'border-transparent text-gray-400 hover:border-cyber-300 hover:text-gray-200',
                        'inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium transition-all duration-300'
                      )}
                    >
                      {item.name}
                    </Link>
                  ))}
                </div>
              </div>

              <div className="hidden sm:ml-6 sm:flex sm:items-center">
                {user ? (
                  <Menu as="div" className="ml-3 relative">
                    <div>
                      <Menu.Button className="bg-dark-700/50 backdrop-blur-sm flex text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-quantum-500 border border-quantum-500/30 animate-neural-pulse">
                        <span className="sr-only">Open user menu</span>
                        <div className="h-8 w-8 rounded-full bg-gradient-to-r from-quantum-600 to-cyber-600 flex items-center justify-center">
                          <UserIcon className="h-5 w-5 text-white" />
                        </div>
                      </Menu.Button>
                    </div>
                    <Transition
                      as={Fragment}
                      enter="transition ease-out duration-200"
                      enterFrom="transform opacity-0 scale-95"
                      enterTo="transform opacity-100 scale-100"
                      leave="transition ease-in duration-75"
                      leaveFrom="transform opacity-100 scale-100"
                      leaveTo="transform opacity-0 scale-95"
                    >
                      <Menu.Items className="origin-top-right absolute right-0 mt-2 w-48 rounded-md shadow-xl py-1 bg-dark-800/90 backdrop-blur-md ring-1 ring-quantum-500/20 focus:outline-none border border-quantum-500/30">
                        <div className="px-4 py-2 text-sm text-gray-200 border-b border-quantum-500/20">
                          <div className="font-medium cyber-text">{user.developer_name || user.email}</div>
                          <div className="text-xs text-gray-400">
                            {user.role === UserRole.ADMIN && '🔐 System Architect'}
                            {user.role === UserRole.DEVELOPER && '⚡ Bot Creator'}
                            {user.role === UserRole.USER && '🎯 Operator'}
                          </div>
                        </div>
                        <Menu.Item>
                          {({ active }) => (
                            <Link
                              href="/profile"
                              className={clsx(
                                active ? 'bg-quantum-500/20 text-gray-100' : 'text-gray-300',
                                'flex items-center px-4 py-2 text-sm hover:bg-quantum-500/10 transition-colors duration-200'
                              )}
                            >
                              <UserIcon className="h-4 w-4 mr-2" />
                              Neural Profile
                            </Link>
                          )}
                        </Menu.Item>
                        <Menu.Item>
                          {({ active }) => (
                            <Link
                              href="/settings"
                              className={clsx(
                                active ? 'bg-gray-100' : '',
                                'flex items-center px-4 py-2 text-sm text-gray-700'
                              )}
                            >
                              <CogIcon className="h-4 w-4 mr-2" />
                              Settings
                            </Link>
                          )}
                        </Menu.Item>
                        <Menu.Item>
                          {({ active }) => (
                            <button
                              onClick={logout}
                              className={clsx(
                                active ? 'bg-gray-100' : '',
                                'flex items-center w-full px-4 py-2 text-sm text-gray-700 text-left'
                              )}
                            >
                              <ArrowRightOnRectangleIcon className="h-4 w-4 mr-2" />
                              Logout
                            </button>
                          )}
                        </Menu.Item>
                      </Menu.Items>
                    </Transition>
                  </Menu>
                ) : (
                  <div className="flex items-center space-x-4">
                    <Link
                      href="/auth/login"
                      className="text-gray-500 hover:text-gray-700 px-3 py-2 rounded-md text-sm font-medium"
                    >
                      Login
                    </Link>
                    <Link
                      href="/auth/register"
                      className="btn btn-primary px-4 py-2 text-sm"
                    >
                      Register
                    </Link>
                  </div>
                )}
              </div>

              <div className="-mr-2 flex items-center sm:hidden">
                <Disclosure.Button className="bg-white inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500">
                  <span className="sr-only">Open main menu</span>
                  {open ? (
                    <XMarkIcon className="block h-6 w-6" aria-hidden="true" />
                  ) : (
                    <Bars3Icon className="block h-6 w-6" aria-hidden="true" />
                  )}
                </Disclosure.Button>
              </div>
            </div>
          </div>

          <Disclosure.Panel className="sm:hidden">
            <div className="pt-2 pb-3 space-y-1">
              {navigationItems.map((item) => (
                <Disclosure.Button
                  key={item.name}
                  as={Link}
                  href={item.href}
                  className={clsx(
                    item.current
                      ? 'bg-primary-50 border-primary-500 text-primary-700'
                      : 'border-transparent text-gray-600 hover:bg-gray-50 hover:border-gray-300 hover:text-gray-800',
                    'block pl-3 pr-4 py-2 border-l-4 text-base font-medium'
                  )}
                >
                  {item.name}
                </Disclosure.Button>
              ))}
            </div>
            {user ? (
              <div className="pt-4 pb-3 border-t border-gray-200">
                <div className="flex items-center px-4">
                  <div className="flex-shrink-0">
                    <div className="h-10 w-10 rounded-full bg-primary-100 flex items-center justify-center">
                      <UserIcon className="h-6 w-6 text-primary-600" />
                    </div>
                  </div>
                  <div className="ml-3">
                    <div className="text-base font-medium text-gray-800">
                      {user.developer_name || user.email}
                    </div>
                    <div className="text-sm font-medium text-gray-500">
                      {user.email}
                    </div>
                  </div>
                </div>
                <div className="mt-3 space-y-1">
                  <Disclosure.Button
                    as={Link}
                    href="/profile"
                    className="block px-4 py-2 text-base font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100"
                  >
                    Hồ sơ cá nhân
                  </Disclosure.Button>
                  <Disclosure.Button
                    as={Link}
                    href="/settings"
                    className="block px-4 py-2 text-base font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100"
                  >
                    Cài đặt
                  </Disclosure.Button>
                  <Disclosure.Button
                    as="button"
                    onClick={logout}
                    className="block w-full text-left px-4 py-2 text-base font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100"
                  >
                    Đăng xuất
                  </Disclosure.Button>
                </div>
              </div>
            ) : (
              <div className="pt-4 pb-3 border-t border-gray-200">
                <div className="space-y-1">
                  <Disclosure.Button
                    as={Link}
                    href="/auth/login"
                    className="block px-4 py-2 text-base font-medium text-gray-500 hover:text-gray-800 hover:bg-gray-100"
                  >
                    Đăng nhập
                  </Disclosure.Button>
                  <Disclosure.Button
                    as={Link}
                    href="/auth/register"
                    className="block px-4 py-2 text-base font-medium text-primary-600 hover:text-primary-800 hover:bg-primary-50"
                  >
                    Đăng ký
                  </Disclosure.Button>
                </div>
              </div>
            )}
          </Disclosure.Panel>
        </>
      )}
    </Disclosure>
  )
}

