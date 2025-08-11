'use client'

import { ScrapingJob } from '@/types'
import { formatDateTime } from '@/lib/utils'
import { Clock, CheckCircle, XCircle, AlertCircle, Globe, FileText, Building } from 'lucide-react'
import Link from 'next/link'

interface JobCardProps {
  job: ScrapingJob
  onCancel?: (id: string) => void
}

export function JobCard({ job, onCancel }: JobCardProps) {
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'failed':
        return <XCircle className="h-5 w-5 text-red-600" />
      case 'running':
        return <Clock className="h-5 w-5 text-blue-600" />
      case 'pending':
        return <AlertCircle className="h-5 w-5 text-yellow-600" />
      default:
        return <Clock className="h-5 w-5 text-gray-600" />
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
        return <Globe className="h-4 w-4 text-blue-600" />
      case 'paper':
        return <FileText className="h-4 w-4 text-green-600" />
      case 'government':
        return <Building className="h-4 w-4 text-purple-600" />
      default:
        return <FileText className="h-4 w-4 text-gray-600" />
    }
  }

  return (
    <div className="bg-white rounded-lg shadow hover:shadow-md transition-shadow">
      <div className="p-6">
        <div className="flex items-start justify-between mb-4">
          <div className="flex items-center space-x-2">
            {getScraperIcon(job.scraper_type)}
            <span className="text-xs font-medium px-2 py-1 rounded-full bg-gray-100 text-gray-800">
              {job.scraper_type}
            </span>
          </div>
          <div className="flex items-center space-x-2">
            {getStatusIcon(job.status)}
            <span className={`text-xs font-medium px-2 py-1 rounded-full ${getStatusColor(job.status)}`}>
              {job.status}
            </span>
          </div>
        </div>

        <Link href={`/jobs/${job.id}`}>
          <h3 className="text-lg font-medium text-gray-900 mb-2 hover:text-blue-600 transition-colors">
            Job #{job.id.slice(0, 8)}
          </h3>
        </Link>

        <div className="mb-4">
          <p className="text-sm text-gray-600 mb-2">
            <strong>Keywords:</strong> {job.keywords.join(', ')}
          </p>
          
          {job.results_count !== undefined && (
            <p className="text-sm text-gray-600 mb-2">
              <strong>Results:</strong> {job.results_count} documents
            </p>
          )}

          {job.error_message && (
            <p className="text-sm text-red-600 mb-2">
              <strong>Error:</strong> {job.error_message}
            </p>
          )}
        </div>

        {/* Progress Bar */}
        {job.status === 'running' && (
          <div className="mb-4">
            <div className="flex justify-between text-sm text-gray-600 mb-1">
              <span>Progress</span>
              <span>{job.progress}%</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${job.progress}%` }}
              />
            </div>
          </div>
        )}

        <div className="flex items-center justify-between text-xs text-gray-500">
          <span>Created: {formatDateTime(job.created_at)}</span>
          <span>Updated: {formatDateTime(job.updated_at)}</span>
        </div>

        {/* Actions */}
        <div className="mt-4 pt-4 border-t border-gray-200 flex justify-between">
          <Link
            href={`/jobs/${job.id}`}
            className="text-sm text-blue-600 hover:text-blue-800 font-medium"
          >
            View Details
          </Link>
          
          {job.status === 'running' && onCancel && (
            <button
              onClick={() => onCancel(job.id)}
              className="text-sm text-red-600 hover:text-red-800 font-medium"
            >
              Cancel Job
            </button>
          )}
        </div>
      </div>
    </div>
  )
}
