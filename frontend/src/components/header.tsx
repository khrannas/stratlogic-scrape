'use client'

import { useState } from 'react'
import { User, LogOut, Settings } from 'lucide-react'
import { useAuth } from '@/hooks/use-auth'
import type { User as UserType } from '@/types'

interface HeaderProps {
    user: UserType | null
}

export function Header({ user }: HeaderProps) {
    const { logout } = useAuth()
    const [isMenuOpen, setIsMenuOpen] = useState(false)

    return (
        <header className="bg-white shadow-sm border-b border-gray-200">
            <div className="flex items-center justify-between h-16 px-6">
                <div className="flex items-center">
                    <h1 className="text-xl font-semibold text-gray-900">StratLogic Scraper</h1>
                </div>

                <div className="flex items-center space-x-4">
                    <div className="relative">
                        <button
                            onClick={() => setIsMenuOpen(!isMenuOpen)}
                            className="flex items-center space-x-2 text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                        >
                            <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
                                <User className="w-4 h-4 text-white" />
                            </div>
                            <span className="text-gray-700">{user?.username}</span>
                        </button>

                        {isMenuOpen && (
                            <div className="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-50">
                                <div className="px-4 py-2 text-sm text-gray-700 border-b border-gray-100">
                                    <p className="font-medium">{user?.username}</p>
                                    <p className="text-gray-500">{user?.email}</p>
                                </div>
                                <button
                                    onClick={() => {
                                        setIsMenuOpen(false)
                                        // Navigate to settings
                                    }}
                                    className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                >
                                    <Settings className="w-4 h-4 mr-2" />
                                    Settings
                                </button>
                                <button
                                    onClick={() => {
                                        setIsMenuOpen(false)
                                        logout()
                                    }}
                                    className="flex items-center w-full px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                >
                                    <LogOut className="w-4 h-4 mr-2" />
                                    Sign out
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Overlay to close menu when clicking outside */}
            {isMenuOpen && (
                <div
                    className="fixed inset-0 z-40"
                    onClick={() => setIsMenuOpen(false)}
                />
            )}
        </header>
    )
}
