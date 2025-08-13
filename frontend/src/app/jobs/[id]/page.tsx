'use client'

import { useQuery } from '@tanstack/react-query'
import { ArrowLeft, Eye, Download } from 'lucide-react'
import Link from 'next/link'
import { useParams } from 'next/navigation'
import api from '@/lib/api'
import { Job, Artifact } from '@/types'
import { Header } from '@/components/header'
import { Sidebar } from '@/components/sidebar'
import { useAuth } from '@/hooks/use-auth'

// Helper function to get the correct artifacts endpoint based on job type
const getArtifactsEndpoint = (jobType: string, jobId: string) => {
    switch (jobType) {
        case 'web_scraper':
            return `/api/web_scraper/job/${jobId}/artifacts`
        case 'paper_scraper':
            return `/api/paper_scraper/artifacts/${jobId}`
        case 'government_scraper':
            // Government scraper doesn't have a specific job artifacts endpoint
            // We'll use the general artifacts endpoint with filtering
            return `/api/artifacts?job_id=${jobId}`
        default:
            return `/api/artifacts?job_id=${jobId}`
    }
}

export default function JobDetailPage() {
    const { id } = useParams()
    const { user, isAuthenticated } = useAuth()

    const { data: job, isLoading: jobLoading } = useQuery({
        queryKey: ['job', id],
        queryFn: async () => {
            const response = await api.get(`/api/jobs/${id}`)
            return response.data
        },
        enabled: isAuthenticated && !!id,
    })

    const { data: artifacts, isLoading: artifactsLoading } = useQuery({
        queryKey: ['job-artifacts', id, job?.job_type],
        queryFn: async () => {
            if (!job) return []
            const endpoint = getArtifactsEndpoint(job.job_type, id as string)
            const response = await api.get(endpoint)
            return response.data
        },
        enabled: isAuthenticated && !!id && !!job,
    })

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'completed':
                return <div className="w-3 h-3 bg-green-500 rounded-full" />
            case 'failed':
                return <div className="w-3 h-3 bg-red-500 rounded-full" />
            case 'running':
                return <div className="w-3 h-3 bg-blue-500 rounded-full animate-pulse" />
            case 'pending':
                return <div className="w-3 h-3 bg-yellow-500 rounded-full" />
            default:
                return <div className="w-3 h-3 bg-gray-300 rounded-full" />
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
                <p>Please log in to view job details</p>
            </div>
        )
    }

    if (jobLoading) {
        return (
            <div className="flex h-screen items-center justify-center">
                <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
                    <p className="mt-4 text-gray-600">Loading job details...</p>
                </div>
            </div>
        )
    }

    if (!job) {
        return (
            <div className="flex h-screen items-center justify-center">
                <div className="text-center">
                    <p className="text-gray-600">Job not found</p>
                    <Link href="/jobs" className="mt-4 inline-flex items-center text-primary-600 hover:text-primary-700">
                        <ArrowLeft className="w-4 h-4 mr-1" />
                        Back to Jobs
                    </Link>
                </div>
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
                            {/* Header */}
                            <div className="flex items-center justify-between">
                                <div className="flex items-center space-x-4">
                                    <Link
                                        href="/jobs"
                                        className="inline-flex items-center text-gray-600 hover:text-gray-900"
                                    >
                                        <ArrowLeft className="w-4 h-4 mr-1" />
                                        Back to Jobs
                                    </Link>
                                    <div>
                                        <h1 className="text-2xl font-bold text-gray-900">Job Details</h1>
                                        <p className="text-gray-600">Job ID: {job.id}</p>
                                    </div>
                                </div>
                                <span className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(job.status)}`}>
                                    {getStatusIcon(job.status)}
                                    <span className="ml-2">{job.status}</span>
                                </span>
                            </div>

                            {/* Job Information */}
                            <div className="bg-white rounded-lg shadow p-6">
                                <h2 className="text-lg font-semibold text-gray-900 mb-4">Job Information</h2>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-sm font-medium text-gray-500">Keywords</label>
                                        <p className="text-sm text-gray-900">{job.keywords.join(', ')}</p>
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium text-gray-500">Scraper Type</label>
                                        <p className="text-sm text-gray-900 capitalize">{job.scraper_type}</p>
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium text-gray-500">Max Results</label>
                                        <p className="text-sm text-gray-900">{job.max_results}</p>
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium text-gray-500">Progress</label>
                                        <p className="text-sm text-gray-900">{job.progress}%</p>
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium text-gray-500">Created</label>
                                        <p className="text-sm text-gray-900">{new Date(job.created_at).toLocaleString()}</p>
                                    </div>
                                    <div>
                                        <label className="text-sm font-medium text-gray-500">Updated</label>
                                        <p className="text-sm text-gray-900">{new Date(job.updated_at).toLocaleString()}</p>
                                    </div>
                                </div>
                                {job.error_message && (
                                    <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
                                        <label className="text-sm font-medium text-red-800">Error Message</label>
                                        <p className="text-sm text-red-700 mt-1">{job.error_message}</p>
                                    </div>
                                )}
                            </div>

                            {/* Progress Bar */}
                            {job.status === 'running' && (
                                <div className="bg-white rounded-lg shadow p-6">
                                    <h2 className="text-lg font-semibold text-gray-900 mb-4">Progress</h2>
                                    <div className="space-y-2">
                                        <div className="flex justify-between text-sm text-gray-600">
                                            <span>Progress</span>
                                            <span>{job.progress}%</span>
                                        </div>
                                        <div className="w-full bg-gray-200 rounded-full h-3">
                                            <div
                                                className="bg-primary-600 h-3 rounded-full transition-all duration-300"
                                                style={{ width: `${job.progress}%` }}
                                            />
                                        </div>
                                    </div>
                                </div>
                            )}

                            {/* Results */}
                            <div className="bg-white rounded-lg shadow">
                                <div className="p-6 border-b border-gray-200">
                                    <h2 className="text-lg font-semibold text-gray-900">Results ({artifacts?.data?.length || 0})</h2>
                                </div>
                                {artifactsLoading ? (
                                    <div className="p-8 text-center">
                                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
                                        <p className="mt-2 text-gray-600">Loading results...</p>
                                    </div>
                                ) : (
                                    <div className="divide-y divide-gray-200">
                                        {artifacts?.data?.map((artifact: Artifact) => (
                                            <div key={artifact.id} className="p-6">
                                                <div className="flex items-start justify-between">
                                                    <div className="flex-1">
                                                        <h3 className="text-sm font-medium text-gray-900 mb-2">
                                                            {artifact.title}
                                                        </h3>
                                                        <p className="text-sm text-gray-600 mb-2 line-clamp-3">
                                                            {artifact.content}
                                                        </p>
                                                        <div className="flex items-center space-x-4 text-xs text-gray-500">
                                                            <span className="capitalize">{artifact.source_type}</span>
                                                            {artifact.url && (
                                                                <a
                                                                    href={artifact.url}
                                                                    target="_blank"
                                                                    rel="noopener noreferrer"
                                                                    className="text-primary-600 hover:text-primary-700"
                                                                >
                                                                    View Source
                                                                </a>
                                                            )}
                                                            <span>{new Date(artifact.created_at).toLocaleDateString()}</span>
                                                        </div>
                                                    </div>
                                                    <button className="ml-4 p-2 text-gray-400 hover:text-gray-600">
                                                        <Download className="w-4 h-4" />
                                                    </button>
                                                </div>
                                            </div>
                                        ))}
                                        {(!artifacts?.data || artifacts.data.length === 0) && (
                                            <div className="p-8 text-center">
                                                <p className="text-gray-500">No results found</p>
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
