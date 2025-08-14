'use client'

import { BarChart3, TrendingUp, Users, FileText } from 'lucide-react'
import { Header } from '@/components/header'
import { Sidebar } from '@/components/sidebar'
import { useAuth } from '@/hooks/use-auth'

export default function AnalyticsPage() {
    const { user, isAuthenticated } = useAuth()

    if (!isAuthenticated) {
        return (
            <div className="flex h-screen items-center justify-center">
                <p>Please log in to view analytics</p>
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
                                <h1 className="text-2xl font-bold text-gray-900">Analytics</h1>
                                <p className="text-gray-600">View your scraping performance and insights</p>
                            </div>

                            {/* Stats Cards */}
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                                <div className="bg-white rounded-lg shadow p-6">
                                    <div className="flex items-center">
                                        <div className="p-2 bg-blue-100 rounded-lg">
                                            <BarChart3 className="w-6 h-6 text-blue-600" />
                                        </div>
                                        <div className="ml-4">
                                            <p className="text-sm font-medium text-gray-500">Total Jobs</p>
                                            <p className="text-2xl font-bold text-gray-900">0</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="bg-white rounded-lg shadow p-6">
                                    <div className="flex items-center">
                                        <div className="p-2 bg-green-100 rounded-lg">
                                            <TrendingUp className="w-6 h-6 text-green-600" />
                                        </div>
                                        <div className="ml-4">
                                            <p className="text-sm font-medium text-gray-500">Success Rate</p>
                                            <p className="text-2xl font-bold text-gray-900">0%</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="bg-white rounded-lg shadow p-6">
                                    <div className="flex items-center">
                                        <div className="p-2 bg-purple-100 rounded-lg">
                                            <FileText className="w-6 h-6 text-purple-600" />
                                        </div>
                                        <div className="ml-4">
                                            <p className="text-sm font-medium text-gray-500">Documents</p>
                                            <p className="text-2xl font-bold text-gray-900">0</p>
                                        </div>
                                    </div>
                                </div>

                                <div className="bg-white rounded-lg shadow p-6">
                                    <div className="flex items-center">
                                        <div className="p-2 bg-orange-100 rounded-lg">
                                            <Users className="w-6 h-6 text-orange-600" />
                                        </div>
                                        <div className="ml-4">
                                            <p className="text-sm font-medium text-gray-500">Active Users</p>
                                            <p className="text-2xl font-bold text-gray-900">1</p>
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Charts Placeholder */}
                            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                                <div className="bg-white rounded-lg shadow p-6">
                                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Job Performance</h3>
                                    <div className="h-64 flex items-center justify-center text-gray-500">
                                        <p>Chart coming soon...</p>
                                    </div>
                                </div>

                                <div className="bg-white rounded-lg shadow p-6">
                                    <h3 className="text-lg font-semibold text-gray-900 mb-4">Document Sources</h3>
                                    <div className="h-64 flex items-center justify-center text-gray-500">
                                        <p>Chart coming soon...</p>
                                    </div>
                                </div>
                            </div>

                            {/* Recent Activity */}
                            <div className="bg-white rounded-lg shadow">
                                <div className="p-6 border-b border-gray-200">
                                    <h3 className="text-lg font-semibold text-gray-900">Recent Activity</h3>
                                </div>
                                <div className="p-6">
                                    <div className="text-center text-gray-500">
                                        <p>No recent activity</p>
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

