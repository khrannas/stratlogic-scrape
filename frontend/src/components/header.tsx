'use client'

import { useAuth } from '@/hooks/use-auth'
import { User, LogOut, Settings } from 'lucide-react'
import Link from 'next/link'

export function Header() {
  const { user, logout, isLoggingOut } = useAuth()

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <Link href="/dashboard" className="text-xl font-bold text-gray-900">
            StratLogic Scraper
          </Link>
          <nav className="hidden md:flex space-x-6">
            <Link 
              href="/dashboard" 
              className="text-gray-600 hover:text-gray-900 transition-colors"
            >
              Dashboard
            </Link>
            <Link 
              href="/documents" 
              className="text-gray-600 hover:text-gray-900 transition-colors"
            >
              Documents
            </Link>
            <Link 
              href="/scraping" 
              className="text-gray-600 hover:text-gray-900 transition-colors"
            >
              Scraping
            </Link>
            <Link 
              href="/jobs" 
              className="text-gray-600 hover:text-gray-900 transition-colors"
            >
              Jobs
            </Link>
          </nav>
        </div>

        <div className="flex items-center space-x-4">
          {user && (
            <div className="flex items-center space-x-3">
              <div className="flex items-center space-x-2">
                <User className="h-5 w-5 text-gray-400" />
                <span className="text-sm text-gray-700">{user.username}</span>
                <span className="text-xs text-gray-500 bg-gray-100 px-2 py-1 rounded">
                  {user.role}
                </span>
              </div>
              <button
                onClick={() => logout()}
                disabled={isLoggingOut}
                className="flex items-center space-x-1 text-gray-600 hover:text-gray-900 transition-colors disabled:opacity-50"
              >
                <LogOut className="h-4 w-4" />
                <span className="text-sm">Logout</span>
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  )
}
