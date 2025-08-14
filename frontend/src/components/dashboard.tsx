'use client'

import { useQuery } from '@tanstack/react-query'
import { FileText, Play, CheckCircle, AlertCircle } from 'lucide-react'
import api from '@/lib/api'
import { Job, Artifact } from '@/types'

export function Dashboard() {
    const { data: stats } = useQuery({
        queryKey: ['dashboard-stats'],
        queryFn: async () => {
            const [jobsRes, artifactsRes] = await Promise.all([
                api.get('/api/v1/jobs/'),
                api.get('/api/v1/artifacts/')
            ])
            return {
                jobs: jobsRes.data,
                artifacts: artifactsRes.data
            }
        }
    })

    const { data: recentJobs } = useQuery({
        queryKey: ['recent-jobs'],
        queryFn: async () => {
            const response = await api.get('/api/v1/jobs/?limit=5')
            return response.data
        }
    })

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'completed':
                return <CheckCircle className="w-5 h-5 text-green-500" />
            case 'failed':
                return <AlertCircle className="w-5 h-5 text-red-500" />
            case 'running':
                return <Play className="w-5 h-5 text-blue-500" />
            default:
                return <div className="w-5 h-5 bg-gray-300 rounded-full" />
        }
    }

    return (
        <div className="space-y-6">
            <div>
                <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
                <p className="text-gray-600">Welcome to StratLogic Scraper</p>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                        <div className="p-2 bg-blue-100 rounded-lg">
                            <Play className="w-6 h-6 text-blue-600" />
                        </div>
                        <div className="ml-4">
                            <p className="text-sm font-medium text-gray-600">Total Jobs</p>
                            <p className="text-2xl font-bold text-gray-900">
                                {stats?.jobs?.total || 0}
                            </p>
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                        <div className="p-2 bg-green-100 rounded-lg">
                            <CheckCircle className="w-6 h-6 text-green-600" />
                        </div>
                        <div className="ml-4">
                            <p className="text-sm font-medium text-gray-600">Completed Jobs</p>
                            <p className="text-2xl font-bold text-gray-900">
                                {stats?.jobs?.filter((job: Job) => job.status === 'completed').length || 0}
                            </p>
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                        <div className="p-2 bg-yellow-100 rounded-lg">
                            <AlertCircle className="w-6 h-6 text-yellow-600" />
                        </div>
                        <div className="ml-4">
                            <p className="text-sm font-medium text-gray-600">Failed Jobs</p>
                            <p className="text-2xl font-bold text-gray-900">
                                {stats?.jobs?.filter((job: Job) => job.status === 'failed').length || 0}
                            </p>
                        </div>
                    </div>
                </div>

                <div className="bg-white rounded-lg shadow p-6">
                    <div className="flex items-center">
                        <div className="p-2 bg-purple-100 rounded-lg">
                            <FileText className="w-6 h-6 text-purple-600" />
                        </div>
                        <div className="ml-4">
                            <p className="text-sm font-medium text-gray-600">Total Documents</p>
                            <p className="text-2xl font-bold text-gray-900">
                                {stats?.artifacts?.total || 0}
                            </p>
                        </div>
                    </div>
                </div>
            </div>

            {/* Recent Jobs */}
            <div className="bg-white rounded-lg shadow">
                <div className="px-6 py-4 border-b border-gray-200">
                    <h2 className="text-lg font-medium text-gray-900">Recent Jobs</h2>
                </div>
                <div className="divide-y divide-gray-200">
                    {recentJobs?.map((job: Job) => (
                        <div key={job.id} className="px-6 py-4">
                            <div className="flex items-center justify-between">
                                <div className="flex items-center">
                                    {getStatusIcon(job.status)}
                                    <div className="ml-3">
                                        <p className="text-sm font-medium text-gray-900">
                                            {job.keywords.join(', ')}
                                        </p>
                                        <p className="text-sm text-gray-500">
                                            {job.job_type} • {new Date(job.created_at).toLocaleDateString()}
                                        </p>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <p className="text-sm font-medium text-gray-900">
                                        {job.total_items} results
                                    </p>
                                    <p className="text-sm text-gray-500">
                                        {job.progress}% complete
                                    </p>
                                </div>
                            </div>
                        </div>
                    ))}
                    {(!recentJobs || recentJobs.length === 0) && (
                        <div className="px-6 py-8 text-center">
                            <p className="text-gray-500">No recent jobs</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
