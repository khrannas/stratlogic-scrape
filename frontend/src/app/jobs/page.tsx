'use client'

import { useQuery } from '@tanstack/react-query'
import { Play, CheckCircle, AlertCircle, Clock, Eye } from 'lucide-react'
import Link from 'next/link'
import api from '@/lib/api'
import { Job } from '@/types'
import { Header } from '@/components/header'
import { Sidebar } from '@/components/sidebar'
import { useAuth } from '@/hooks/use-auth'

export default function JobsPage() {
    const { user, isAuthenticated } = useAuth()

    const { data: jobs, isLoading } = useQuery({
        queryKey: ['jobs'],
        queryFn: async () => {
            const response = await api.get('/api/v1/jobs/')
            return response.data
        },
        enabled: isAuthenticated,
        refetchInterval: 5000, // Refresh every 5 seconds for real-time updates
    })

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'completed':
                return <CheckCircle className="w-5 h-5 text-green-500" />
            case 'failed':
                return <AlertCircle className="w-5 h-5 text-red-500" />
            case 'running':
                return <Play className="w-5 h-5 text-blue-500" />
            case 'pending':
                return <Clock className="w-5 h-5 text-yellow-500" />
            default:
                return <div className="w-5 h-5 bg-gray-300 rounded-full" />
        }
    }

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'completed':
                return 'bg-green-100 text-green-800'
            case 'failed':
                return 'bg-red-100 text-red-800'
            case 'running':
                return 'bg-blue-100 text-blue-800'
            case 'pending':
                return 'bg-yellow-100 text-yellow-800'
            default:
                return 'bg-gray-100 text-gray-800'
        }
    }

    if (!isAuthenticated) {
        return (
            <div className="flex h-screen items-center justify-center">
                <p>Please log in to view jobs</p>
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
                            <div className="flex items-center justify-between">
                                <div>
                                    <h1 className="text-2xl font-bold text-gray-900">Jobs</h1>
                                    <p className="text-gray-600">Monitor your scraping jobs</p>
                                </div>
                                <Link
                                    href="/scraping"
                                    className="btn btn-primary"
                                >
                                    <Play className="w-4 h-4 mr-2" />
                                    New Job
                                </Link>
                            </div>

                            {/* Jobs List */}
                            <div className="bg-white rounded-lg shadow">
                                {isLoading ? (
                                    <div className="p-8 text-center">
                                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
                                        <p className="mt-2 text-gray-600">Loading jobs...</p>
                                    </div>
                                ) : (
                                    <div className="divide-y divide-gray-200">
                                        {jobs?.map((job: Job) => (
                                            <div key={job.id} className="p-6">
                                                <div className="flex items-center justify-between">
                                                    <div className="flex items-center">
                                                        {getStatusIcon(job.status)}
                                                        <div className="ml-3">
                                                            <div className="flex items-center space-x-2">
                                                                <p className="text-sm font-medium text-gray-900">
                                                                    {job.keywords.join(', ')}
                                                                </p>
                                                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(job.status)}`}>
                                                                    {job.status}
                                                                </span>
                                                            </div>
                                                            <p className="text-sm text-gray-500">
                                                                {job.job_type} • {new Date(job.created_at).toLocaleDateString()}
                                                            </p>
                                                            {job.error_message && (
                                                                <p className="text-sm text-red-600 mt-1">
                                                                    Error: {job.error_message}
                                                                </p>
                                                            )}
                                                        </div>
                                                    </div>
                                                    <div className="flex items-center space-x-4">
                                                        <div className="text-right">
                                                            <p className="text-sm font-medium text-gray-900">
                                                                {job.total_items} results
                                                            </p>
                                                            <p className="text-sm text-gray-500">
                                                                {job.progress}% complete
                                                            </p>
                                                        </div>
                                                        <Link
                                                            href={`/jobs/${job.id}`}
                                                            className="btn btn-secondary"
                                                        >
                                                            <Eye className="w-4 h-4 mr-2" />
                                                            View
                                                        </Link>
                                                    </div>
                                                </div>

                                                {/* Progress Bar */}
                                                {job.status === 'running' && (
                                                    <div className="mt-4">
                                                        <div className="flex justify-between text-sm text-gray-600 mb-1">
                                                            <span>Progress</span>
                                                            <span>{job.progress}%</span>
                                                        </div>
                                                        <div className="w-full bg-gray-200 rounded-full h-2">
                                                            <div
                                                                className="bg-primary-600 h-2 rounded-full transition-all duration-300"
                                                                style={{ width: `${job.progress}%` }}
                                                            />
                                                        </div>
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                        {(!jobs || jobs.length === 0) && (
                                            <div className="p-8 text-center">
                                                <p className="text-gray-500">No jobs found</p>
                                                <Link
                                                    href="/scraping"
                                                    className="mt-2 inline-flex items-center text-primary-600 hover:text-primary-700"
                                                >
                                                    <Play className="w-4 h-4 mr-1" />
                                                    Create your first job
                                                </Link>
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </main>
            </div>
        </div>
    )
}
