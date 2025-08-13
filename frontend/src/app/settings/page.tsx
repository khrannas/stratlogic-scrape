'use client'

import { Settings, User, Shield, Bell, Database } from 'lucide-react'
import { Header } from '@/components/header'
import { Sidebar } from '@/components/sidebar'
import { useAuth } from '@/hooks/use-auth'

export default function SettingsPage() {
    const { user, isAuthenticated } = useAuth()

    if (!isAuthenticated) {
        return (
            <div className="flex h-screen items-center justify-center">
                <p>Please log in to view settings</p>
            </div>
        )
    }

    return (
        <div className="flex h-screen bg-gray-50">
            <Sidebar />
            <div className="flex-1 flex flex-col overflow-hidden">
                <Header user={user} />
                <main className="flex-1 overflow-x-hidden overflow-y-auto bg-gray-50">
                    <div className="container mx-auto px-6 py-8">
                        <div className="space-y-6">
                            <div>
                                <h1 className="text-2xl font-bold text-gray-900">Settings</h1>
                                <p className="text-gray-600">Manage your account and application preferences</p>
                            </div>

                            {/* Settings Sections */}
                            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                {/* Navigation */}
                                <div className="lg:col-span-1">
                                    <nav className="space-y-1">
                                        <a
                                            href="#profile"
                                            className="group flex items-center px-3 py-2 text-sm font-medium text-gray-900 bg-gray-100 rounded-md"
                                        >
                                            <User className="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500" />
                                            Profile
                                        </a>
                                        <a
                                            href="#security"
                                            className="group flex items-center px-3 py-2 text-sm font-medium text-gray-600 rounded-md hover:text-gray-900 hover:bg-gray-50"
                                        >
                                            <Shield className="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500" />
                                            Security
                                        </a>
                                        <a
                                            href="#notifications"
                                            className="group flex items-center px-3 py-2 text-sm font-medium text-gray-600 rounded-md hover:text-gray-900 hover:bg-gray-50"
                                        >
                                            <Bell className="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500" />
                                            Notifications
                                        </a>
                                        <a
                                            href="#storage"
                                            className="group flex items-center px-3 py-2 text-sm font-medium text-gray-600 rounded-md hover:text-gray-900 hover:bg-gray-50"
                                        >
                                            <Database className="mr-3 h-5 w-5 text-gray-400 group-hover:text-gray-500" />
                                            Storage
                                        </a>
                                    </nav>
                                </div>

                                {/* Content */}
                                <div className="lg:col-span-2 space-y-6">
                                    {/* Profile Section */}
                                    <div id="profile" className="bg-white shadow rounded-lg">
                                        <div className="px-4 py-5 sm:p-6">
                                            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Profile Information</h3>
                                            <div className="space-y-4">
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700">Email</label>
                                                    <p className="mt-1 text-sm text-gray-900">{user?.email}</p>
                                                </div>
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700">Username</label>
                                                    <p className="mt-1 text-sm text-gray-900">{user?.username}</p>
                                                </div>
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700">Role</label>
                                                    <p className="mt-1 text-sm text-gray-900 capitalize">{user?.role}</p>
                                                </div>
                                                <div>
                                                    <label className="block text-sm font-medium text-gray-700">Member Since</label>
                                                    <p className="mt-1 text-sm text-gray-900">
                                                        {user?.created_at ? new Date(user.created_at).toLocaleDateString() : 'N/A'}
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Security Section */}
                                    <div id="security" className="bg-white shadow rounded-lg">
                                        <div className="px-4 py-5 sm:p-6">
                                            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Security Settings</h3>
                                            <div className="space-y-4">
                                                <div>
                                                    <button className="btn btn-primary">
                                                        Change Password
                                                    </button>
                                                </div>
                                                <div>
                                                    <button className="btn btn-secondary">
                                                        Enable Two-Factor Authentication
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Notifications Section */}
                                    <div id="notifications" className="bg-white shadow rounded-lg">
                                        <div className="px-4 py-5 sm:p-6">
                                            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Notification Preferences</h3>
                                            <div className="space-y-4">
                                                <div className="flex items-center justify-between">
                                                    <div>
                                                        <p className="text-sm font-medium text-gray-900">Job Completion Notifications</p>
                                                        <p className="text-sm text-gray-500">Get notified when your scraping jobs complete</p>
                                                    </div>
                                                    <button className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 bg-gray-200">
                                                        <span className="translate-x-0 pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"></span>
                                                    </button>
                                                </div>
                                                <div className="flex items-center justify-between">
                                                    <div>
                                                        <p className="text-sm font-medium text-gray-900">Error Notifications</p>
                                                        <p className="text-sm text-gray-500">Get notified when jobs fail</p>
                                                    </div>
                                                    <button className="relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 bg-gray-200">
                                                        <span className="translate-x-0 pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out"></span>
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Storage Section */}
                                    <div id="storage" className="bg-white shadow rounded-lg">
                                        <div className="px-4 py-5 sm:p-6">
                                            <h3 className="text-lg leading-6 font-medium text-gray-900 mb-4">Storage Management</h3>
                                            <div className="space-y-4">
                                                <div>
                                                    <p className="text-sm text-gray-500">Storage usage and management features coming soon...</p>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    )
}
