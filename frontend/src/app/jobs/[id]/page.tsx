'use client'

import { useParams } from 'next/navigation'
import { useJob, useCancelJob } from '@/hooks/use-jobs'
import { useJobArtifacts } from '@/hooks/use-jobs'
import { formatDateTime } from '@/lib/utils'
import { Clock, CheckCircle, XCircle, AlertCircle, Globe, FileText, Building, Download, ExternalLink } from 'lucide-react'
import Link from 'next/link'

export default function JobDetailPage() {
  const params = useParams()
  const jobId = params.id as string
  
  const { data: job, isLoading, error } = useJob(jobId)
  const { data: artifacts, isLoading: artifactsLoading } = useJobArtifacts(jobId)
  const cancelJobMutation = useCancelJob()

  const handleCancelJob = () => {
    if (confirm('Are you sure you want to cancel this job?')) {
      cancelJobMutation.mutate(jobId)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-6 w-6 text-green-600" />
      case 'failed':
        return <XCircle className="h-6 w-6 text-red-600" />
      case 'running':
        return <Clock className="h-6 w-6 text-blue-600" />
      case 'pending':
        return <AlertCircle className="h-6 w-6 text-yellow-600" />
      default:
        return <Clock className="h-6 w-6 text-gray-600" />
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

  const getScraperIcon = (scraperType: string) => {
    switch (scraperType) {
      case 'web':
        return <Globe className="h-5 w-5 text-blue-600" />
      case 'paper':
        return <FileText className="h-5 w-5 text-green-600" />
      case 'government':
        return <Building className="h-5 w-5 text-purple-600" />
      default:
        return <FileText className="h-5 w-5 text-gray-600" />
    }
  }

  if (isLoading) {
    return (
      <div className="p-6">
        <div className="flex justify-center items-center py-12">
          <div className="text-center">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading job details...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error || !job) {
    return (
      <div className="p-6">
        <div className="bg-red-50 border border-red-200 rounded-md p-6">
          <p className="text-red-600">Error loading job: {error?.message || 'Job not found'}</p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <Link href="/jobs" className="text-blue-600 hover:text-blue-800 mb-2 inline-block">
                ← Back to Jobs
              </Link>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Job #{job.id.slice(0, 8)}
              </h1>
              <p className="text-gray-600">
                {job.scraper_type} scraping job
              </p>
            </div>
            {job.status === 'running' && (
              <button
                onClick={handleCancelJob}
                disabled={cancelJobMutation.isPending}
                className="bg-red-600 text-white px-4 py-2 rounded-md hover:bg-red-700 disabled:opacity-50 transition-colors"
              >
                {cancelJobMutation.isPending ? 'Cancelling...' : 'Cancel Job'}
              </button>
            )}
          </div>
        </div>

        {/* Job Details */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          {/* Main Info */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center space-x-3">
                  {getScraperIcon(job.scraper_type)}
                  <div>
                    <h2 className="text-xl font-semibold text-gray-900">
                      {job.scraper_type.charAt(0).toUpperCase() + job.scraper_type.slice(1)} Scraper
                    </h2>
                    <p className="text-sm text-gray-600">Job ID: {job.id}</p>
                  </div>
                </div>
                <div className="flex items-center space-x-2">
                  {getStatusIcon(job.status)}
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(job.status)}`}>
                    {job.status}
                  </span>
                </div>
              </div>

              <div className="space-y-4">
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-1">Keywords</h3>
                  <div className="flex flex-wrap gap-2">
                    {job.keywords.map((keyword, index) => (
                      <span
                        key={index}
                        className="bg-blue-100 text-blue-800 text-sm px-2 py-1 rounded"
                      >
                        {keyword}
                      </span>
                    ))}
                  </div>
                </div>

                {job.results_count !== undefined && (
                  <div>
                    <h3 className="text-sm font-medium text-gray-700 mb-1">Results</h3>
                    <p className="text-gray-900">{job.results_count} documents collected</p>
                  </div>
                )}

                {job.error_message && (
                  <div>
                    <h3 className="text-sm font-medium text-red-700 mb-1">Error</h3>
                    <p className="text-red-600">{job.error_message}</p>
                  </div>
                )}

                <div className="grid grid-cols-2 gap-4 text-sm">
                  <div>
                    <span className="text-gray-600">Created:</span>
                    <p className="text-gray-900">{formatDateTime(job.created_at)}</p>
                  </div>
                  <div>
                    <span className="text-gray-600">Updated:</span>
                    <p className="text-gray-900">{formatDateTime(job.updated_at)}</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Progress */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h3 className="text-lg font-medium text-gray-900 mb-4">Progress</h3>
              
              <div className="mb-4">
                <div className="flex justify-between text-sm text-gray-600 mb-1">
                  <span>Completion</span>
                  <span>{job.progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-3">
                  <div
                    className="bg-blue-600 h-3 rounded-full transition-all duration-300"
                    style={{ width: `${job.progress}%` }}
                  />
                </div>
              </div>

              {job.status === 'running' && (
                <div className="text-center">
                  <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto mb-2"></div>
                  <p className="text-sm text-gray-600">Processing...</p>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Artifacts */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <h3 className="text-lg font-medium text-gray-900">Collected Documents</h3>
          </div>
          <div className="p-6">
            {artifactsLoading ? (
              <div className="flex justify-center items-center py-8">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-blue-600 mx-auto mb-2"></div>
                <p className="text-gray-600">Loading artifacts...</p>
              </div>
            ) : artifacts && artifacts.length > 0 ? (
              <div className="space-y-4">
                {artifacts.map((artifact) => (
                  <div key={artifact.id} className="border border-gray-200 rounded-lg p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <h4 className="font-medium text-gray-900 mb-1">{artifact.title}</h4>
                        <p className="text-sm text-gray-600 mb-2">
                          {artifact.content.length > 200 
                            ? artifact.content.substring(0, 200) + '...' 
                            : artifact.content
                          }
                        </p>
                        <div className="flex items-center space-x-4 text-xs text-gray-500">
                          <span>Type: {artifact.source_type}</span>
                          {artifact.file_size && (
                            <span>Size: {(artifact.file_size / 1024).toFixed(1)} KB</span>
                          )}
                          <span>Created: {formatDateTime(artifact.created_at)}</span>
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 ml-4">
                        {artifact.source_url && (
                          <a
                            href={artifact.source_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-gray-400 hover:text-gray-600"
                          >
                            <ExternalLink className="h-4 w-4" />
                          </a>
                        )}
                        {artifact.file_path && (
                          <button
                            onClick={() => {
                              // Download functionality would be implemented here
                              console.log('Download artifact:', artifact.id)
                            }}
                            className="text-gray-400 hover:text-gray-600"
                          >
                            <Download className="h-4 w-4" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="text-center py-8">
                <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <p className="text-gray-600">
                  {job.status === 'completed' 
                    ? 'No documents were collected from this job.' 
                    : 'Documents will appear here once the job completes.'
                  }
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}
