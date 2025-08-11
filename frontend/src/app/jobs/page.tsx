'use client'

import { useState } from 'react'
import { useJobs, useCancelJob } from '@/hooks/use-jobs'
import { JobCard } from '@/components/jobs/job-card'
import { Clock, CheckCircle, XCircle, AlertCircle } from 'lucide-react'
import Link from 'next/link'

export default function JobsPage() {
  const [page, setPage] = useState(1)
  const { data: jobsData, isLoading, error } = useJobs(page, 20)
  const cancelJobMutation = useCancelJob()

  const handleCancelJob = (jobId: string) => {
    if (confirm('Are you sure you want to cancel this job?')) {
      cancelJobMutation.mutate(jobId)
    }
  }

  const getStatusStats = () => {
    if (!jobsData?.items) return null

    const stats = {
      pending: 0,
      running: 0,
      completed: 0,
      failed: 0,
    }

    jobsData.items.forEach(job => {
      stats[job.status as keyof typeof stats]++
    })

    return stats
  }

  const statusStats = getStatusStats()

  return (
    <div className="p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Scraping Jobs
              </h1>
              <p className="text-gray-600">
                Monitor and manage your scraping jobs.
              </p>
            </div>
            <Link
              href="/scraping"
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
            >
              New Job
            </Link>
          </div>
        </div>

        {/* Stats */}
        {statusStats && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="p-2 bg-yellow-100 rounded-lg">
                  <AlertCircle className="h-6 w-6 text-yellow-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Pending</p>
                  <p className="text-2xl font-bold text-gray-900">{statusStats.pending}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="p-2 bg-blue-100 rounded-lg">
                  <Clock className="h-6 w-6 text-blue-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Running</p>
                  <p className="text-2xl font-bold text-gray-900">{statusStats.running}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="p-2 bg-green-100 rounded-lg">
                  <CheckCircle className="h-6 w-6 text-green-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Completed</p>
                  <p className="text-2xl font-bold text-gray-900">{statusStats.completed}</p>
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center">
                <div className="p-2 bg-red-100 rounded-lg">
                  <XCircle className="h-6 w-6 text-red-600" />
                </div>
                <div className="ml-4">
                  <p className="text-sm font-medium text-gray-600">Failed</p>
                  <p className="text-2xl font-bold text-gray-900">{statusStats.failed}</p>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Jobs List */}
        {isLoading ? (
          <div className="flex justify-center items-center py-12">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading jobs...</p>
            </div>
          </div>
        ) : error ? (
          <div className="bg-red-50 border border-red-200 rounded-md p-6">
            <p className="text-red-600">Error loading jobs: {error.message}</p>
          </div>
        ) : jobsData?.items.length === 0 ? (
          <div className="bg-white rounded-lg shadow p-12 text-center">
            <Clock className="h-12 w-12 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No jobs found</h3>
            <p className="text-gray-600 mb-4">
              You haven't created any scraping jobs yet.
            </p>
            <Link
              href="/scraping"
              className="bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
            >
              Create Your First Job
            </Link>
          </div>
        ) : (
          <>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
              {jobsData?.items.map((job) => (
                <JobCard 
                  key={job.id} 
                  job={job} 
                  onCancel={handleCancelJob}
                />
              ))}
            </div>

            {/* Pagination */}
            {jobsData && jobsData.pages > 1 && (
              <div className="flex justify-center">
                <nav className="flex items-center space-x-2">
                  <button
                    onClick={() => setPage(Math.max(1, page - 1))}
                    disabled={page === 1}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Previous
                  </button>
                  
                  <span className="px-3 py-2 text-sm text-gray-700">
                    Page {page} of {jobsData.pages}
                  </span>
                  
                  <button
                    onClick={() => setPage(Math.min(jobsData.pages, page + 1))}
                    disabled={page === jobsData.pages}
                    className="px-3 py-2 border border-gray-300 rounded-md text-sm font-medium text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    Next
                  </button>
                </nav>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
