'use client'

import { useAuth } from '@/hooks/use-auth'
import { FileText, Search, Clock, CheckCircle } from 'lucide-react'
import Link from 'next/link'

export default function DashboardPage() {
  const { user } = useAuth()

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        {/* Welcome Section */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">
            Welcome back, {user?.username}!
          </h1>
          <p className="text-gray-600 mt-2">
            Manage your scraping jobs and explore collected documents.
          </p>
        </div>

        {/* Quick Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-blue-100 rounded-lg">
                <FileText className="h-6 w-6 text-blue-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Total Documents</p>
                <p className="text-2xl font-bold text-gray-900">1,234</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-green-100 rounded-lg">
                <CheckCircle className="h-6 w-6 text-green-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Completed Jobs</p>
                <p className="text-2xl font-bold text-gray-900">89</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-yellow-100 rounded-lg">
                <Clock className="h-6 w-6 text-yellow-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Active Jobs</p>
                <p className="text-2xl font-bold text-gray-900">3</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Search className="h-6 w-6 text-purple-600" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-600">Search Queries</p>
                <p className="text-2xl font-bold text-gray-900">156</p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          <Link
            href="/scraping"
            className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center mb-4">
              <div className="p-2 bg-blue-100 rounded-lg">
                <Search className="h-6 w-6 text-blue-600" />
              </div>
              <h3 className="ml-3 text-lg font-medium text-gray-900">
                Start New Scraping Job
              </h3>
            </div>
            <p className="text-gray-600">
              Create a new scraping job to collect documents from web, academic papers, or government sources.
            </p>
          </Link>

          <Link
            href="/documents"
            className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center mb-4">
              <div className="p-2 bg-green-100 rounded-lg">
                <FileText className="h-6 w-6 text-green-600" />
              </div>
              <h3 className="ml-3 text-lg font-medium text-gray-900">
                Browse Documents
              </h3>
            </div>
            <p className="text-gray-600">
              Explore and search through all collected documents with advanced filtering options.
            </p>
          </Link>

          <Link
            href="/jobs"
            className="bg-white rounded-lg shadow p-6 hover:shadow-md transition-shadow"
          >
            <div className="flex items-center mb-4">
              <div className="p-2 bg-purple-100 rounded-lg">
                <Clock className="h-6 w-6 text-purple-600" />
              </div>
              <h3 className="ml-3 text-lg font-medium text-gray-900">
                Manage Jobs
              </h3>
            </div>
            <p className="text-gray-600">
              Monitor and manage your scraping jobs, view progress, and download results.
            </p>
          </Link>
        </div>

        {/* Recent Activity */}
        <div className="mt-8 bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
          </div>
          <div className="p-6">
            <div className="space-y-4">
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-green-400 rounded-full"></div>
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Web scraping job completed</span> - Collected 45 documents from search results
                </p>
                <span className="text-xs text-gray-400">2 hours ago</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-blue-400 rounded-full"></div>
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Paper scraping job started</span> - Searching for "machine learning" papers
                </p>
                <span className="text-xs text-gray-400">4 hours ago</span>
              </div>
              <div className="flex items-center space-x-3">
                <div className="w-2 h-2 bg-yellow-400 rounded-full"></div>
                <p className="text-sm text-gray-600">
                  <span className="font-medium">Government document job in progress</span> - 75% complete
                </p>
                <span className="text-xs text-gray-400">6 hours ago</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
